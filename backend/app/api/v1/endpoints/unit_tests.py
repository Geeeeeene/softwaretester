from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
import os
import sys
import traceback
from pathlib import Path
from pydantic import BaseModel

from app.db.session import get_db
from app.db.models.project import Project
from app.core.config import settings
from app.services.test_generation import TestGenerationService
from app.executors.catch2_executor import Catch2Executor

router = APIRouter()

class GenerateRequest(BaseModel):
    file_path: str
    additional_info: Optional[str] = None

class ExecuteRequest(BaseModel):
    file_path: str
    test_code: str

def log(msg: str):
    print(f"DEBUG_LOG: {msg}", file=sys.stderr, flush=True)

@router.get("/{project_id}/files")
async def list_source_files(project_id: int, db: Session = Depends(get_db)):
    log(f"收到文件列表请求: ID={project_id}")
    
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        log(f"❌ 项目 {project_id} 在数据库中不存在")
        raise HTTPException(status_code=404, detail="项目不存在")
    
    log(f"📂 数据库路径记录: {project.source_path}")
    
    source_path = None
    if project.source_path:
        normalized_path = project.source_path.replace('\\', '/')
        source_path = Path(normalized_path).resolve()
        log(f"📍 检查物理路径: {source_path}")
        if not source_path.exists():
            log(f"⚠️  警告: 文件夹在硬盘上不存在! {source_path}")
            source_path = None

    if not source_path:
        log("🔎 尝试自动寻找源码目录...")
        alt_paths = [
            Path(settings.UPLOAD_DIR).resolve() / str(project.id) / "source",
            Path(settings.ARTIFACT_STORAGE_PATH).resolve() / "projects"
        ]
        
        for alt in alt_paths:
            if alt.exists():
                if alt.name == "source":
                    source_path = alt
                    break
                else:
                    for sub in alt.iterdir():
                        if sub.is_dir() and any(sub.rglob("*.cpp")):
                            source_path = sub
                            break
            if source_path: break

    if not source_path or not source_path.exists():
        log("❌ 最终还是没找到源码路径")
        raise HTTPException(status_code=404, detail="未找到源代码文件夹，请重新上传 ZIP")
    
    if str(source_path) != project.source_path:
        project.source_path = str(source_path)
        db.commit()
        log(f"🔄 已更新项目源码路径为: {source_path}")
    
    cpp_extensions = {'.cpp', '.cc', '.cxx', '.c++', '.C', '.c', '.h', '.hpp'}
    source_files = []
    
    for file_path in source_path.rglob('*'):
        if file_path.is_file() and file_path.suffix.lower() in cpp_extensions:
            rel_path = file_path.relative_to(source_path)
            rel_path_str = str(rel_path).lower().replace('\\', '/')
            
            if any(skip in rel_path_str for skip in ['node_modules', '.git']):
                continue
            if 'build/' in rel_path_str or rel_path_str.startswith('build/'):
                continue
                
            source_files.append({
                "path": str(rel_path).replace('\\', '/'),
                "name": file_path.name,
                "size": file_path.stat().st_size
            })
    
    log(f"✅ 扫描完成: 找到 {len(source_files)} 个文件")
    return {"project_id": project_id, "files": source_files}

@router.post("/{project_id}/generate")
async def generate_tests(
    project_id: int, 
    request: GenerateRequest,
    db: Session = Depends(get_db)
):
    """为指定文件生成测试用例"""
    log(f"收到生成请求: ID={project_id}, File={request.file_path}")
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    full_path = Path(project.source_path) / request.file_path
    if not full_path.exists():
        log(f"❌ 文件不存在: {full_path}")
        raise HTTPException(status_code=404, detail=f"文件不存在: {request.file_path}")
    
    try:
        content = full_path.read_text(encoding='utf-8', errors='ignore')
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"读取文件失败: {str(e)}")

    service = TestGenerationService()
    try:
        test_code = await service.generate_catch2_test(content, request.file_path)
        return {
            "project_id": project_id,
            "file_path": request.file_path,
            "test_code": test_code
        }
    except Exception as e:
        log(f"❌ AI 生成失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{project_id}/execute")
async def execute_tests(
    project_id: int,
    request: ExecuteRequest,
    db: Session = Depends(get_db)
):
    """编译并运行生成的测试"""
    log(f"收到执行请求: ID={project_id}, File={request.file_path}")
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    source_file_path = Path(project.source_path) / request.file_path
    
    executor = Catch2Executor()
    try:
        result = await executor.execute(
            project.source_path,
            request.test_code,
            str(source_file_path)
        )
        return result
    except Exception as e:
        error_detail = traceback.format_exc()
        log(f"❌ 执行异常详情:\n{error_detail}")
        raise HTTPException(status_code=500, detail=f"执行失败: {str(e)}")
