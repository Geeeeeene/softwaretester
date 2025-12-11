from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
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
    project = db.query(Project).filter(Project.id == project_id).first()
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

