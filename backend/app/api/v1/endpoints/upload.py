from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends, BackgroundTasks
from sqlalchemy.orm import Session
import shutil
import os
from pathlib import Path
import uuid
import zipfile

from app.db.session import get_db
from app.core.config import settings
from app.db.models.project import Project as ProjectModel
from app.db.models.test_case import TestCase
from app.db.models.test_execution import TestExecution
from app.worker.tasks import execute_tests

router = APIRouter()


@router.post("/project/{project_id}/source")
async def upload_project_source(
    project_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """上传项目源代码"""
    # 验证项目
    from sqlalchemy import select
    result = db.execute(
        select(Project).where(Project.id == project_id)
    )
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    # 验证文件大小
    file.file.seek(0, 2)
    file_size = file.file.tell()
    file.file.seek(0)
    
    if file_size > settings.MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"文件过大，最大支持 {settings.MAX_UPLOAD_SIZE / 1024 / 1024}MB"
        )
    
    # 创建上传目录
    upload_dir = Path(settings.UPLOAD_DIR) / str(project_id)
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    # 生成唯一文件名
    file_ext = Path(file.filename).suffix
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    file_path = upload_dir / unique_filename
    
    # 保存文件
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文件保存失败: {str(e)}")
    finally:
        file.file.close()
    
    # 更新项目source_path
    project.source_path = str(file_path)
    db.commit()
    
    return {
        "message": "文件上传成功",
        "filename": file.filename,
        "path": str(file_path),
        "size": file_size
    }


@router.post("/artifact")
async def upload_artifact(
    file: UploadFile = File(...),
):
    """上传测试artifact（截图、日志等）"""
    # 创建artifact目录
    artifact_dir = Path(settings.UPLOAD_DIR) / "artifacts"
    artifact_dir.mkdir(parents=True, exist_ok=True)
    
    # 生成唯一文件名
    file_ext = Path(file.filename).suffix
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    file_path = artifact_dir / unique_filename
    
    # 保存文件
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文件保存失败: {str(e)}")
    finally:
        file.file.close()
    
    return {
        "message": "Artifact上传成功",
        "filename": file.filename,
        "path": str(file_path),
        "url": f"/artifacts/{unique_filename}"
    }


@router.post("/static-zip")
def upload_static_zip(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    name: str | None = Form(None),
    description: str | None = Form(None),
    tool: str = Form("cppcheck"),
    db: Session = Depends(get_db),
):
    """上传压缩包，创建静态分析项目、用例并立即执行（支持 Cppcheck 或 Clazy）"""
    # 校验文件类型
    if not file.filename.lower().endswith(".zip"):
        raise HTTPException(status_code=400, detail="仅支持 zip 压缩包")

    # 校验工具类型
    tool = tool.lower()
    if tool not in ["cppcheck", "clazy"]:
        raise HTTPException(status_code=400, detail="不支持的分析工具，仅支持 cppcheck 或 clazy")
    
    # 校验大小
    file.file.seek(0, os.SEEK_END)
    file_size = file.file.tell()
    file.file.seek(0)
    if file_size > settings.MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"文件过大，最大支持 {settings.MAX_UPLOAD_SIZE / 1024 / 1024:.0f}MB"
        )
    
    # 路径准备
    uploads_dir = Path(settings.UPLOAD_DIR)
    uploads_dir.mkdir(parents=True, exist_ok=True)
    project_uuid = uuid.uuid4().hex
    zip_path = uploads_dir / f"{project_uuid}.zip"
    project_dir = Path(settings.ARTIFACT_STORAGE_PATH) / "projects" / project_uuid
    project_dir.mkdir(parents=True, exist_ok=True)
    
    # 保存 zip
    try:
        with open(zip_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文件保存失败: {str(e)}")
    finally:
        file.file.close()
    
    # 解压，防止目录穿越
    try:
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            for member in zip_ref.namelist():
                if member.startswith("/") or ".." in Path(member).parts:
                    raise HTTPException(status_code=400, detail="检测到不安全的压缩路径")
            zip_ref.extractall(project_dir)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"解压失败: {str(e)}")
    
    # 创建项目
    project = ProjectModel(
        name=name or f"Static Project {project_uuid[:8]}",
        description=description or "上传压缩包自动创建的静态分析项目",
        project_type="static",
        source_path=str(project_dir),
        language="C++",
        framework=None,
        is_active=True,
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    
    # 创建测试用例（根据选择的工具）
    test_ir = {
        "type": "static",
        "tool": tool,
        "name": f"代码静态分析({tool})",
        "description": f"使用 {tool} 进行静态分析",
        "target_files": [],
        "target_directories": [str(project_dir)],
        "rules": [],
        "enable": "all",
        "exclude_patterns": [],
        "tags": [],
    }
    
    # Clazy 特有配置
    if tool == "clazy":
         test_ir["checks"] = ["level1"] # 默认 level1
         
    testcase = TestCase(
        project_id=project.id,
        name=f"静态分析（{tool.capitalize()}）",
        description="上传压缩包自动创建",
        test_type="static",
        test_ir=test_ir,
        priority="medium",
        tags=[],
    )
    db.add(testcase)
    db.commit()
    db.refresh(testcase)
    
    # 创建执行记录
    execution = TestExecution(
        project_id=project.id,
        executor_type=tool,
        status="pending",
        total_tests=1,
    )
    db.add(execution)
    db.commit()
    db.refresh(execution)
    
    # 提交后台任务
    if background_tasks is not None:
        background_tasks.add_task(execute_tests, execution.id, [testcase.id])
    
    return {
        "message": "上传成功，已创建项目并启动静态分析",
        "project_id": project.id,
        "test_case_id": testcase.id,
        "execution_id": execution.id,
        "project_path": str(project_dir),
    }

