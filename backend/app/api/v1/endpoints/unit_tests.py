from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Body, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
import os
import sys
import traceback
import json
from pathlib import Path
from pydantic import BaseModel, ValidationError, field_validator, model_validator

from app.db.session import get_db
from app.db.models.project import Project
from app.core.config import settings
from app.services.test_generation import TestGenerationService
from app.services.document_analysis import DocumentAnalysisService
from app.executors.catch2_executor import Catch2Executor
from fastapi import UploadFile, File

router = APIRouter()

class GenerateRequest(BaseModel):
    file_path: str
    additional_info: Optional[str] = None

class ExecuteRequest(BaseModel):
    file_path: str
    test_code: Optional[str] = None  # 可选，如果不提供则从文件读取
    
    @model_validator(mode='before')
    @classmethod
    def validate_test_code(cls, data: Any):
        """将空字符串和None转换为None，确保字段可选"""
        if isinstance(data, dict):
            # 如果test_code是空字符串，转换为None
            if 'test_code' in data and (data['test_code'] == '' or data['test_code'] is None):
                data['test_code'] = None
            # 如果test_code字段不存在，确保它被设置为None
            elif 'test_code' not in data:
                data['test_code'] = None
        return data

class UpdateTestFileRequest(BaseModel):
    file_path: str
    test_code: str

def log(msg: str):
    print(f"DEBUG_LOG: {msg}", file=sys.stderr, flush=True)

<<<<<<< HEAD
def get_document_summary_path(project_source_path: str) -> Path:
    """获取文档要点存储路径"""
    source_path = Path(project_source_path)
    summary_file = source_path / ".test_doc_summary.txt"
    return summary_file

def save_document_summary(project_source_path: str, summary: str):
    """保存文档要点到文件"""
    summary_file = get_document_summary_path(project_source_path)
    summary_file.write_text(summary, encoding='utf-8')
    log(f"💾 文档要点已保存到: {summary_file}")

def load_document_summary(project_source_path: str) -> Optional[str]:
    """从文件加载文档要点"""
    summary_file = get_document_summary_path(project_source_path)
    if summary_file.exists():
        try:
            summary = summary_file.read_text(encoding='utf-8')
            log(f"📖 已加载文档要点，长度: {len(summary)} 字符")
            return summary
        except Exception as e:
            log(f"⚠️ 读取文档要点失败: {str(e)}")
            return None
    return None

def get_test_file_path(project_source_path: str, source_file_path: str) -> Path:
    """获取测试文件的保存路径"""
    # 规范化路径，处理Windows路径分隔符
    source_path = Path(project_source_path).resolve()
    test_dir = source_path / "tests"
    test_dir.mkdir(parents=True, exist_ok=True)
    
    # 生成测试文件名：test_{源文件名}.cpp
    # 处理包含目录的路径，只取文件名部分
    # 先规范化路径分隔符
    normalized_source_path = source_file_path.replace('\\', '/')
    source_file = Path(normalized_source_path)
    
    # 如果路径包含目录，只取文件名部分
    file_name = source_file.name  # 获取文件名（包含扩展名）
    file_stem = source_file.stem  # 获取文件名（不含扩展名）
    test_file_name = f"test_{file_stem}.cpp"
    
    result_path = test_dir / test_file_name
    
    log(f"📝 源文件路径: {source_file_path}")
    log(f"📝 规范化后路径: {normalized_source_path}")
    log(f"📝 文件名: {file_name}, 文件stem: {file_stem}")
    log(f"📝 测试文件名: {test_file_name}")
    log(f"📝 完整测试文件路径: {result_path}")
    log(f"📝 测试目录是否存在: {test_dir.exists()}")
    
    return result_path

@router.get("/{project_id}/files")
async def list_source_files(project_id: int, db: Session = Depends(get_db)):
    log(f"收到文件列表请求: ID={project_id}")
    
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        log(f"❌ 项目 {project_id} 在数据库中不存在")
        raise HTTPException(status_code=404, detail="项目不存在")
    
=======
def _get_source_path(project_id: int, project: Project) -> Optional[Path]:
    """获取项目源码路径"""
>>>>>>> origin/tzf
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
    """构建文件树结构（参考集成测试实现）"""
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

@router.post("/{project_id}/upload-document")
async def upload_document(
    project_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """上传设计文档（docx格式）并分析总结要点"""
    log(f"收到文档上传请求: ID={project_id}, 文件名={file.filename}")
    
    # 验证文件格式
    if not file.filename or not file.filename.lower().endswith('.docx'):
        raise HTTPException(status_code=400, detail="只支持 .docx 格式的文档")
    
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    if not project.source_path:
        raise HTTPException(status_code=404, detail="项目没有源码路径，请先上传源代码")
    
    # 保存上传的文档
    source_path = Path(project.source_path)
    doc_dir = source_path / ".docs"
    doc_dir.mkdir(parents=True, exist_ok=True)
    
    doc_file_path = doc_dir / file.filename
    try:
        # 保存文件
        content = await file.read()
        doc_file_path.write_bytes(content)
        log(f"💾 文档已保存到: {doc_file_path}")
        
        # 分析文档
        analysis_service = DocumentAnalysisService()
        summary = await analysis_service.analyze_document(doc_file_path)
        
        # 保存要点
        save_document_summary(project.source_path, summary)
        
        return {
            "project_id": project_id,
            "filename": file.filename,
            "summary": summary,
            "message": "文档上传并分析成功"
        }
    except Exception as e:
        error_detail = traceback.format_exc()
        log(f"❌ 文档处理失败: {str(e)}")
        log(f"❌ 详细错误:\n{error_detail}")
        raise HTTPException(status_code=500, detail=f"文档处理失败: {str(e)}")

@router.get("/{project_id}/document-summary")
async def get_document_summary(
    project_id: int,
    db: Session = Depends(get_db)
):
    """获取项目的文档要点"""
    log(f"收到获取文档要点请求: ID={project_id}")
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    if not project.source_path:
        raise HTTPException(status_code=404, detail="项目没有源码路径")
    
    summary = load_document_summary(project.source_path)
    if summary:
        return {
            "project_id": project_id,
            "summary": summary,
            "has_summary": True
        }
    else:
        return {
            "project_id": project_id,
            "summary": None,
            "has_summary": False,
            "message": "尚未上传设计文档"
        }

class UpdateDocumentSummaryRequest(BaseModel):
    summary: str

@router.put("/{project_id}/document-summary")
async def update_document_summary(
    project_id: int,
    request: UpdateDocumentSummaryRequest,
    db: Session = Depends(get_db)
):
    """更新项目的文档要点"""
    log(f"收到更新文档要点请求: ID={project_id}")
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    if not project.source_path:
        raise HTTPException(status_code=404, detail="项目没有源码路径")
    
    try:
        save_document_summary(project.source_path, request.summary)
        log(f"✅ 文档要点已更新，长度: {len(request.summary)} 字符")
        return {
            "project_id": project_id,
            "summary": request.summary,
            "has_summary": True,
            "message": "文档要点已更新"
        }
    except Exception as e:
        error_detail = traceback.format_exc()
        log(f"❌ 更新文档要点失败: {str(e)}")
        log(f"❌ 详细错误:\n{error_detail}")
        raise HTTPException(status_code=500, detail=f"更新文档要点失败: {str(e)}")

@router.post("/{project_id}/generate")
async def generate_tests(
    project_id: int, 
    request: GenerateRequest,
    db: Session = Depends(get_db)
):
    """为指定文件生成测试用例"""
    log(f"收到生成请求: ID={project_id}, File={request.file_path}")
    try:
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            log(f"❌ 项目不存在: {project_id}")
            raise HTTPException(status_code=404, detail="项目不存在")
        
        if not project.source_path:
            log(f"❌ 项目没有源码路径: {project_id}")
            raise HTTPException(status_code=404, detail="项目没有源码路径，请先上传源代码")
        
        full_path = Path(project.source_path) / request.file_path
        if not full_path.exists():
            log(f"❌ 文件不存在: {full_path}")
            raise HTTPException(status_code=404, detail=f"文件不存在: {request.file_path}")
        
        log(f"📖 读取源文件: {full_path}")
        try:
            content = full_path.read_text(encoding='utf-8', errors='ignore')
            log(f"✅ 文件读取成功，长度: {len(content)} 字符")
        except Exception as e:
            error_detail = traceback.format_exc()
            log(f"❌ 读取文件失败: {str(e)}")
            log(f"❌ 详细错误:\n{error_detail}")
            raise HTTPException(status_code=500, detail=f"读取文件失败: {str(e)}")

        # 加载文档要点（如果存在）
        doc_summary = load_document_summary(project.source_path)
        if doc_summary:
            log(f"📄 已加载文档要点，长度: {len(doc_summary)} 字符")
        
        log(f"🤖 开始调用 AI 生成测试用例...")
        service = TestGenerationService()
        try:
            test_code = await service.generate_catch2_test(content, request.file_path, doc_summary)
            log(f"✅ AI 生成成功，测试代码长度: {len(test_code)} 字符")
            
            # 保存测试文件到文件系统
            test_file_path = get_test_file_path(project.source_path, request.file_path)
            try:
                # 确保目录存在
                test_file_path.parent.mkdir(parents=True, exist_ok=True)
                test_file_path.write_text(test_code, encoding='utf-8')
                log(f"💾 测试文件已保存到: {test_file_path}")
                log(f"💾 文件大小: {test_file_path.stat().st_size} 字节")
                log(f"💾 文件是否存在: {test_file_path.exists()}")
            except Exception as save_error:
                error_detail = traceback.format_exc()
                log(f"❌ 保存测试文件失败: {str(save_error)}")
                log(f"❌ 详细错误:\n{error_detail}")
                raise HTTPException(status_code=500, detail=f"保存测试文件失败: {str(save_error)}")
            
            return {
                "project_id": project_id,
                "file_path": request.file_path,
                "test_code": test_code,
                "test_file_path": str(test_file_path.relative_to(Path(project.source_path))).replace('\\', '/')
            }
        except HTTPException:
            # 重新抛出 HTTP 异常
            raise
        except Exception as e:
            error_detail = traceback.format_exc()
            log(f"❌ AI 生成失败: {str(e)}")
            log(f"❌ 详细错误:\n{error_detail}")
            raise HTTPException(status_code=500, detail=f"AI 生成失败: {str(e)}")
    except HTTPException:
        # 重新抛出 HTTP 异常
        raise
    except Exception as e:
        error_detail = traceback.format_exc()
        log(f"❌ 生成测试用例异常: {str(e)}")
        log(f"❌ 详细错误:\n{error_detail}")
        raise HTTPException(status_code=500, detail=f"生成测试用例失败: {str(e)}")

@router.get("/{project_id}/test-file")
async def get_test_file(
    project_id: int,
    file_path: str = Query(..., description="源文件路径"),
    db: Session = Depends(get_db)
):
    """获取测试文件内容"""
    log(f"收到获取测试文件请求: ID={project_id}, File={file_path}")
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    test_file_path = get_test_file_path(project.source_path, file_path)
    log(f"📖 查找测试文件: {test_file_path}")
    log(f"📖 文件是否存在: {test_file_path.exists()}")
    
    if not test_file_path.exists():
        log(f"❌ 测试文件不存在: {test_file_path}")
        raise HTTPException(
            status_code=404, 
            detail=f"测试文件不存在: {test_file_path.relative_to(Path(project.source_path))}，请先生成测试用例"
        )
    
    try:
        test_code = test_file_path.read_text(encoding='utf-8')
        log(f"✅ 成功读取测试文件，长度: {len(test_code)}")
        return {
            "project_id": project_id,
            "file_path": file_path,
            "test_file_path": str(test_file_path.relative_to(Path(project.source_path))).replace('\\', '/'),
            "test_code": test_code
        }
    except Exception as e:
        error_detail = traceback.format_exc()
        log(f"❌ 读取测试文件失败: {str(e)}")
        log(f"❌ 详细错误:\n{error_detail}")
        raise HTTPException(status_code=500, detail=f"读取测试文件失败: {str(e)}")

@router.put("/{project_id}/test-file")
async def update_test_file(
    project_id: int,
    request: UpdateTestFileRequest,
    db: Session = Depends(get_db)
):
    """更新测试文件内容"""
    log(f"收到更新测试文件请求: ID={project_id}, File={request.file_path}")
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        log(f"❌ 项目 {project_id} 不存在")
        raise HTTPException(status_code=404, detail=f"项目 {project_id} 不存在")
    
    if not project.source_path:
        log(f"❌ 项目 {project_id} 没有源码路径")
        raise HTTPException(status_code=404, detail="项目没有源码路径，请先上传源代码")
    
    log(f"📂 项目源码路径: {project.source_path}")
    log(f"📄 源文件路径: {request.file_path}")
    
    # 检查源码路径是否存在
    source_path = Path(project.source_path)
    if not source_path.exists():
        log(f"❌ 源码路径不存在: {source_path}")
        raise HTTPException(status_code=404, detail=f"源码路径不存在: {source_path}")
    
    test_file_path = get_test_file_path(project.source_path, request.file_path)
    log(f"💾 测试文件完整路径: {test_file_path}")
    log(f"📝 测试代码长度: {len(request.test_code)} 字符")
    
    # 确保目录存在
    try:
        test_file_path.parent.mkdir(parents=True, exist_ok=True)
        log(f"📁 测试目录: {test_file_path.parent} (已确保存在)")
    except Exception as dir_error:
        log(f"❌ 创建测试目录失败: {str(dir_error)}")
        raise HTTPException(status_code=500, detail=f"创建测试目录失败: {str(dir_error)}")
    
    try:
        test_file_path.write_text(request.test_code, encoding='utf-8')
        log(f"✅ 测试文件已成功更新: {test_file_path}")
        log(f"📊 文件大小: {test_file_path.stat().st_size} 字节")
        log(f"📊 文件是否存在: {test_file_path.exists()}")
        
        return {
            "project_id": project_id,
            "file_path": request.file_path,
            "test_file_path": str(test_file_path.relative_to(Path(project.source_path))).replace('\\', '/'),
            "message": "测试文件已更新"
        }
    except Exception as e:
        error_detail = traceback.format_exc()
        log(f"❌ 更新测试文件失败: {str(e)}")
        log(f"❌ 详细错误:\n{error_detail}")
        raise HTTPException(status_code=500, detail=f"更新测试文件失败: {str(e)}")

@router.post("/{project_id}/execute")
async def execute_tests(
    project_id: int,
    request_body: ExecuteRequest = Body(...),
    db: Session = Depends(get_db)
):
    """编译并运行生成的测试"""
    log(f"收到执行请求: ID={project_id}")
    log(f"📝 请求参数 - file_path: {request_body.file_path}")
    log(f"📝 test_code 是否提供: {request_body.test_code is not None}")
    if request_body.test_code:
        log(f"📝 test_code 长度: {len(request_body.test_code)}")
    else:
        log(f"📝 test_code 为 None，将从文件读取")
    
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    source_file_path = Path(project.source_path) / request_body.file_path
    
    # 如果提供了 test_code，使用提供的代码；否则从文件读取
    if request_body.test_code:
        test_code = request_body.test_code
        log(f"📝 使用请求中提供的测试代码，长度: {len(test_code)}")
    else:
        test_file_path = get_test_file_path(project.source_path, request_body.file_path)
        log(f"📖 尝试从文件读取测试代码: {test_file_path}")
        if not test_file_path.exists():
            log(f"❌ 测试文件不存在: {test_file_path}")
            raise HTTPException(status_code=404, detail=f"测试文件不存在: {test_file_path.relative_to(Path(project.source_path))}，请先生成测试用例或提供测试代码")
        test_code = test_file_path.read_text(encoding='utf-8')
        log(f"✅ 从文件读取测试代码成功，长度: {len(test_code)}")
    
    executor = Catch2Executor()
    try:
        result = await executor.execute(
            project.source_path,
            test_code,
            str(source_file_path)
        )
        return result
    except Exception as e:
        error_detail = traceback.format_exc()
        log(f"❌ 执行异常详情:\n{error_detail}")
        # 返回更详细的错误信息
        error_msg = str(e) if e else "未知错误"
        raise HTTPException(status_code=500, detail=f"执行失败: {error_msg}")
