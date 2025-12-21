"""系统测试（Robot Framework + SikuliLibrary）相关 API"""

import os
import uuid
import zipfile
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.db.models.project import Project
from app.db.models.test_case import TestCase
from app.db.models.test_execution import TestExecution
from app.worker.tasks import execute_tests
from app.system_tests.agent import SystemTestAgent

router = APIRouter()


class SystemTestGenerateRequest(BaseModel):
    requirements: str = Field(..., description="系统测试需求/测试点描述（中文即可）")
    image_files: List[str] = Field(default_factory=list, description="将要提供的图片文件名列表（例如 open.png/save.png）")
    entry: str = Field(default="main.robot", description="生成的入口 .robot 文件名")
    use_claude: bool = Field(default=True, description="优先使用 Claude，否则使用通义千问")
    model: Optional[str] = Field(default=None, description="可选：指定模型名")
    base_url: Optional[str] = Field(default=None, description="可选：Claude 代理 base_url")
    create_execution: bool = Field(default=False, description="是否生成后立即创建执行记录并后台运行")


class SystemTestGenerateResponse(BaseModel):
    message: str
    project_id: int
    test_case_id: int
    suite_path: str
    entry: str
    model: Optional[str] = None


def _safe_extract_zip(zip_path: Path, dest_dir: Path) -> None:
    with zipfile.ZipFile(zip_path, "r") as z:
        for member in z.namelist():
            if member.startswith("/") or ".." in Path(member).parts:
                raise HTTPException(status_code=400, detail="检测到不安全的压缩路径")
        z.extractall(dest_dir)


@router.post("/projects/{project_id}/system-tests/generate", response_model=SystemTestGenerateResponse)
def generate_system_tests(
    project_id: int,
    payload: SystemTestGenerateRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """使用大模型生成 RobotFramework 系统测试脚本，并在平台创建一条 system 测试用例。"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    if not payload.requirements.strip():
        raise HTTPException(status_code=400, detail="requirements 不能为空")

    # 选择实际使用的提供方：
    # - 前端目前不传 use_claude/model/base_url，因此默认会走 Claude。
    # - 但很多用户只配置了 DASHSCOPE_API_KEY，所以这里自动兜底：Claude key 缺失时切换到 DashScope。
    claude_key = (settings.CLAUDE_API_KEY or "").strip() if settings.CLAUDE_API_KEY else ""
    dashscope_key = (settings.DASHSCOPE_API_KEY or "").strip() if settings.DASHSCOPE_API_KEY else ""
    use_claude = bool(payload.use_claude)
    if use_claude and not claude_key and dashscope_key:
        use_claude = False

    # 创建 suite 目录
    suite_uuid = uuid.uuid4().hex
    suite_dir = Path(settings.ARTIFACT_STORAGE_PATH) / "system_suites" / suite_uuid
    images_dir = suite_dir / "images"
    images_dir.mkdir(parents=True, exist_ok=True)

    # 绑定明确的 api_key，避免只写在 backend/.env 时无法通过 os.getenv 读取
    api_key = claude_key if use_claude else dashscope_key
    if not api_key:
        raise HTTPException(status_code=400, detail="未配置大模型 API Key（CLAUDE_API_KEY 或 DASHSCOPE_API_KEY）")

    agent = SystemTestAgent(
        api_key=api_key,
        model=payload.model,
        use_claude=use_claude,
        base_url=payload.base_url,
    )
    gen = agent.generate_robot_suite(
        app_name=project.name,
        app_desc=project.description or "",
        requirements=payload.requirements,
        image_files=payload.image_files,
    )
    if not gen.get("success"):
        raise HTTPException(status_code=400, detail=gen.get("error") or "生成失败")

    entry = (payload.entry or "main.robot").strip() or "main.robot"
    if not entry.endswith(".robot"):
        entry += ".robot"

    (suite_dir / entry).write_text(gen["content"], encoding="utf-8", errors="replace")
    (suite_dir / "README.txt").write_text(
        "将图片资源放到 images/ 目录下，文件名需与脚本中的变量一致。\n",
        encoding="utf-8",
        errors="replace",
    )

    # 创建测试用例（executor 选择在执行时由前端传 executor_type=robot）
    test_ir = {
        "type": "system",
        "suite_path": str(suite_dir),
        "entry": entry,
        "use_xvfb": True,
        "xvfb_screen": "1920x1080x24",
        "robot_args": [],
    }
    
    # 检查名称是否重复，如果重复则自动添加编号
    base_name = "系统测试（AI生成 · RobotFramework）"
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
        description="AI 生成的系统测试脚本（Robot Framework + SikuliLibrary）",
        test_type="system",
        test_ir=test_ir,
        priority="medium",
        tags=["system", "robotframework", "sikuli", "ai-generated"],
    )
    db.add(testcase)
    db.commit()
    db.refresh(testcase)

    # 可选：直接创建执行并后台跑
    if payload.create_execution:
        execution = TestExecution(
            project_id=project.id,
            executor_type="robot",
            status="pending",
            total_tests=1,
        )
        db.add(execution)
        db.commit()
        db.refresh(execution)
        background_tasks.add_task(execute_tests, execution.id, [testcase.id])

    return SystemTestGenerateResponse(
        message="生成成功",
        project_id=project.id,
        test_case_id=testcase.id,
        suite_path=str(suite_dir),
        entry=entry,
        model=gen.get("model"),
    )


@router.post("/projects/{project_id}/system-tests/assets-zip")
def upload_system_test_assets_zip(
    project_id: int,
    test_case_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """上传系统测试图片/资源 zip，并解压到该测试用例的 suite/images 目录下。"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    testcase = db.query(TestCase).filter(TestCase.id == test_case_id, TestCase.project_id == project_id).first()
    if not testcase:
        raise HTTPException(status_code=404, detail="测试用例不存在")

    test_ir = testcase.test_ir or {}
    suite_path = test_ir.get("suite_path")
    if not suite_path:
        raise HTTPException(status_code=400, detail="该用例缺少 suite_path")

    suite_dir = Path(str(suite_path))
    if not suite_dir.is_absolute():
        suite_dir = Path(settings.ARTIFACT_STORAGE_PATH) / suite_dir
    images_dir = suite_dir / "images"
    images_dir.mkdir(parents=True, exist_ok=True)

    if not file.filename or not file.filename.lower().endswith(".zip"):
        raise HTTPException(status_code=400, detail="仅支持 zip 压缩包")

    tmp_dir = Path(settings.ARTIFACT_STORAGE_PATH) / "uploads"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    zip_path = tmp_dir / f"assets_{uuid.uuid4().hex}.zip"
    try:
        with open(zip_path, "wb") as f:
            f.write(file.file.read())
    finally:
        file.file.close()

    # 解压到临时目录，再把内容拷贝到 images/（避免覆盖 suite 根）
    extract_dir = tmp_dir / f"assets_extract_{uuid.uuid4().hex}"
    extract_dir.mkdir(parents=True, exist_ok=True)
    _safe_extract_zip(zip_path, extract_dir)

    extracted = []
    for p in extract_dir.rglob("*"):
        if p.is_file():
            rel = p.relative_to(extract_dir)
            dest = images_dir / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(p.read_bytes())
            extracted.append(str((Path("images") / rel).as_posix()))

    # 清理
    try:
        zip_path.unlink(missing_ok=True)  # py>=3.8
    except Exception:
        pass

    return {"message": "上传成功", "project_id": project_id, "test_case_id": test_case_id, "files": extracted}


@router.get("/test-cases/{test_case_id}/system-suite/download")
def download_system_suite(test_case_id: int, db: Session = Depends(get_db)):
    """下载某条 system 测试用例对应的 Robot suite（zip），用于在 Ubuntu 桌面测试机上直接执行。"""
    testcase = db.query(TestCase).filter(TestCase.id == test_case_id).first()
    if not testcase:
        raise HTTPException(status_code=404, detail="测试用例不存在")

    test_ir = testcase.test_ir or {}
    suite_path = test_ir.get("suite_path")
    if not suite_path:
        raise HTTPException(status_code=400, detail="该用例缺少 suite_path")

    suite_dir = Path(str(suite_path))
    if not suite_dir.is_absolute():
        suite_dir = Path(settings.ARTIFACT_STORAGE_PATH) / suite_dir
    if not suite_dir.exists():
        raise HTTPException(status_code=404, detail=f"suite_path 不存在: {suite_dir}")

    tmp_dir = Path(settings.ARTIFACT_STORAGE_PATH) / "downloads"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    zip_path = tmp_dir / f"system_suite_{test_case_id}_{uuid.uuid4().hex[:8]}.zip"

    # 打包整个 suite 目录
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for p in suite_dir.rglob("*"):
            if p.is_file():
                z.write(p, arcname=str(p.relative_to(suite_dir)))

    return FileResponse(
        path=str(zip_path),
        media_type="application/zip",
        filename=f"system_suite_{test_case_id}.zip",
    )


