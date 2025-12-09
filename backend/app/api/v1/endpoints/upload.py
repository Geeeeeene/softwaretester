from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
import shutil
import os
from pathlib import Path
import uuid

from app.db.session import get_db
from app.core.config import settings
from app.models.project import Project

router = APIRouter()


@router.post("/project/{project_id}/source")
async def upload_project_source(
    project_id: int,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    """上传项目源代码"""
    # 验证项目
    from sqlalchemy import select
    result = await db.execute(
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
    await db.commit()
    
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

