from typing import Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends, BackgroundTasks
from sqlalchemy.orm import Session
import shutil
import os
from pathlib import Path
import uuid
import zipfile
import tempfile

from app.db.session import get_db
from app.core.config import settings
from app.db.models.project import Project
from app.db.models.test_case import TestCase
from app.db.models.test_execution import TestExecution
from app.worker.tasks import execute_tests

router = APIRouter()


@router.post("/project/{project_id}/source")
def upload_project_source(
    project_id: int,
    file: UploadFile = File(...),
    extract: str = Form("true"),  # 是否解压ZIP文件（字符串格式）
    db: Session = Depends(get_db)
):
    """上传项目源代码（支持ZIP文件自动解压）"""
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
    
    # 创建项目上传目录
    project_upload_dir = Path(settings.UPLOAD_DIR) / str(project_id)
    project_upload_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        file_ext = Path(file.filename or '').suffix.lower()
        
        # 如果是ZIP文件且需要解压（extract可能是字符串"true"或布尔值）
        should_extract = extract == "true" or extract is True
        if file_ext == '.zip' and should_extract:
            # 保存ZIP文件到临时位置
            temp_zip = project_upload_dir / f"{uuid.uuid4()}.zip"
            with open(temp_zip, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            # 解压ZIP文件
            extract_dir = project_upload_dir / "source"
            if extract_dir.exists():
                shutil.rmtree(extract_dir)
            extract_dir.mkdir(parents=True, exist_ok=True)
            
            with zipfile.ZipFile(temp_zip, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)
            
            # 删除临时ZIP文件
            temp_zip.unlink()
            
            # 更新项目source_path为解压后的目录
            project.source_path = str(extract_dir)
            
            # 尝试自动检测构建路径
            build_path = extract_dir / "build"
            if not build_path.exists():
                build_path.mkdir(parents=True, exist_ok=True)
            
            db.commit()
            
            return {
                "message": "ZIP文件上传并解压成功",
                "filename": file.filename,
                "extracted_path": str(extract_dir),
                "size": file_size,
                "extracted": True
            }
        else:
            # 普通文件上传
            unique_filename = f"{uuid.uuid4()}{file_ext}"
            file_path = project_upload_dir / unique_filename
            
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            # 更新项目source_path
            project.source_path = str(file_path)
            db.commit()
            
            return {
                "message": "文件上传成功",
                "filename": file.filename,
                "path": str(file_path),
                "size": file_size,
                "extracted": False
            }
            
    except zipfile.BadZipFile:
        raise HTTPException(status_code=400, detail="无效的ZIP文件")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文件处理失败: {str(e)}")
    finally:
        file.file.close()


@router.post("/artifact")
def upload_artifact(
    file: UploadFile = File(...),
):
    """上传测试artifact（截图、日志等）"""
    # 创建artifact目录
    artifact_dir = Path(settings.ARTIFACT_STORAGE_PATH)
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
    name: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
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
    project = Project(
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
    
    # 检查名称是否重复，如果重复则自动添加编号
    base_name = f"静态分析（{tool.capitalize()}）"
    final_name = base_name
    counter = 1
    
    while db.query(TestCase).filter(
        TestCase.project_id == project.id,
        TestCase.name == final_name
    ).first():
        counter += 1
        final_name = f"{base_name}_{counter}"
         
    testcase = TestCase(
        project_id=project.id,
        name=final_name,
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
