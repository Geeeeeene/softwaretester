"""集成测试API端点"""
from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
import sys
import traceback
from pathlib import Path
from pydantic import BaseModel

from app.db.session import get_db
from app.db.models.project import Project
from app.core.config import settings
from app.test_ir.schemas import IntegrationTestIR
from app.services.test_generation import TestGenerationService
from app.executors.catch2_executor import Catch2Executor

router = APIRouter()


# 保留原有的GenerateIntegrationTestRequest用于基于Test IR的生成（如果需要）
class GenerateIntegrationTestRequest(BaseModel):
    """生成集成测试请求（基于Test IR）"""
    test_ir: IntegrationTestIR
    additional_info: Optional[str] = None


class ExecuteRequest(BaseModel):
    """执行集成测试请求（与单元测试保持一致）"""
    file_path: str
    test_code: str


def log(msg: str):
    """日志输出"""
    print(f"DEBUG_LOG: {msg}", file=sys.stderr, flush=True)


def _get_source_path(project_id: int, project: Project) -> Optional[Path]:
    """获取项目源码路径（与单元测试保持一致）"""
    log(f"📂 数据库路径记录: {project.source_path}")
    
    source_path = None
    if project.source_path:
        try:
            normalized_path = project.source_path.replace('\\', '/')
            source_path = Path(normalized_path).resolve()
            log(f"📍 检查物理路径: {source_path}")
            if not source_path.exists():
                log(f"⚠️  警告: 文件夹在硬盘上不存在! {source_path}")
                source_path = None
        except Exception as e:
            log(f"⚠️  路径解析失败: {str(e)}")
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
        return None
    
    return source_path


def _build_file_tree(project_path: Path) -> list:
    """构建文件树结构（参考静态分析实现）"""
    if not project_path.exists():
        return []
    
    # 需要排除的目录
    exclude_dirs = {'.git', 'node_modules', '__pycache__', '.venv', 'venv', 
                    'build', 'dist', '.pytest_cache', '.mypy_cache', '.idea', '.vscode'}
    
    # C++ 代码文件扩展名
    cpp_extensions = {'.cpp', '.cc', '.cxx', '.c++', '.C', '.c', '.h', '.hpp'}
    
    def build_tree(path: Path, relative_path: str = "") -> list:
        """递归构建文件树"""
        tree = []
        
        try:
            items = sorted(path.iterdir(), key=lambda x: (x.is_file(), x.name.lower()))
            
            for item in items:
                # 跳过排除的目录
                if item.name in exclude_dirs or item.name.startswith('.'):
                    continue
                
                current_path = f"{relative_path}/{item.name}" if relative_path else item.name
                
                if item.is_dir():
                    children = build_tree(item, current_path)
                    # 只包含有子节点的目录（至少有一个代码文件）
                    if children:
                        tree.append({
                            'name': item.name,
                            'path': current_path,
                            'type': 'directory',
                            'children': children
                        })
                elif item.is_file() and item.suffix.lower() in cpp_extensions:
                    tree.append({
                        'name': item.name,
                        'path': current_path,
                        'type': 'file',
                        'size': item.stat().st_size
                    })
        except PermissionError:
            log(f"无权限访问: {path}")
        
        return tree
    
    return build_tree(project_path)


@router.get("/{project_id}/files")
async def list_source_files(project_id: int, db: Session = Depends(get_db)):
    """获取项目的源文件列表（返回文件树结构）"""
    log(f"收到文件列表请求: ID={project_id}")
    
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        log(f"❌ 项目 {project_id} 在数据库中不存在")
        raise HTTPException(status_code=404, detail="项目不存在")
    
    source_path = _get_source_path(project_id, project)
    
    if not source_path:
        # 返回空文件树而不是404错误，让前端显示友好提示
        return {"project_id": project_id, "file_tree": []}
    
    # 更新数据库中的路径（如果不同）
    source_path_str = str(source_path)
    if project.source_path != source_path_str:
        project.source_path = source_path_str
        db.commit()
        log(f"🔄 已更新项目源码路径为: {source_path_str}")
    
    # 构建文件树
    file_tree = _build_file_tree(source_path)
    
    log(f"✅ 扫描完成: 构建文件树，包含 {len(file_tree)} 个根节点")
    return {"project_id": project_id, "file_tree": file_tree}


class GenerateRequest(BaseModel):
    """生成集成测试请求（与单元测试保持一致）"""
    file_path: str
    additional_info: Optional[str] = None


@router.post("/{project_id}/generate")
async def generate_tests(
    project_id: int, 
    request: GenerateRequest,
    db: Session = Depends(get_db)
):
    """为指定文件生成集成测试用例（与单元测试API结构一致）"""
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
        test_code = await service.generate_integration_test_from_code(
            file_content=content,
            file_name=request.file_path,
            project_info={
                "name": project.name,
                "source_path": project.source_path,
                "language": project.language or "cpp"
            },
            additional_info=request.additional_info
        )
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
    """编译并运行生成的集成测试（与单元测试API结构一致）"""
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

