"""静态分析API端点"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.db.session import get_db
from app.db.models.project import Project
from app.static_analysis.service import StaticAnalysisService

router = APIRouter()


class AnalysisRequest(BaseModel):
    """分析请求"""
    use_llm: bool = True
    language: Optional[str] = None


class AnalysisStatusResponse(BaseModel):
    """分析状态响应"""
    has_analysis: bool
    latest: Optional[dict] = None
    total_count: int = 0


@router.post("/projects/{project_id}/static-analysis/run")
async def run_static_analysis(
    project_id: int,
    request: AnalysisRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """启动静态分析"""
    # 验证项目存在
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    if not project.source_path:
        raise HTTPException(
            status_code=400,
            detail="项目未上传源代码，请先上传源代码文件"
        )
    
    # 创建服务实例
    service = StaticAnalysisService()
    
    # 在后台任务中运行分析
    def run_analysis_task():
        service.run_analysis(
            project_id=project_id,
            project_path=project.source_path,
            language=request.language or project.language,
            use_llm=request.use_llm
        )
    
    background_tasks.add_task(run_analysis_task)
    
    return {
        "message": "静态分析任务已提交",
        "project_id": project_id,
        "status": "pending"
    }


@router.get("/projects/{project_id}/static-analysis/status", response_model=AnalysisStatusResponse)
def get_analysis_status(
    project_id: int,
    db: Session = Depends(get_db)
):
    """获取分析状态"""
    # 验证项目存在
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    service = StaticAnalysisService()
    status = service.get_analysis_status(project_id)
    
    return status


@router.get("/projects/{project_id}/static-analysis/results")
def get_analysis_results(
    project_id: int,
    timestamp: Optional[int] = Query(None, description="时间戳，如果不提供则返回最新的"),
    db: Session = Depends(get_db)
):
    """获取分析结果"""
    # 验证项目存在
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    service = StaticAnalysisService()
    results = service.get_analysis_results(project_id, timestamp)
    
    if not results:
        raise HTTPException(status_code=404, detail="分析结果不存在")
    
    return results


@router.get("/projects/{project_id}/static-analysis/files")
def get_project_files(
    project_id: int,
    db: Session = Depends(get_db)
):
    """获取项目文件树"""
    # 验证项目存在
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    if not project.source_path:
        raise HTTPException(
            status_code=400,
            detail="项目未上传源代码"
        )
    
    service = StaticAnalysisService()
    file_tree = service.get_file_tree(project.source_path)
    
    return {
        "project_id": project_id,
        "file_tree": file_tree
    }


@router.get("/projects/{project_id}/static-analysis/file-content")
def get_file_content(
    project_id: int,
    file_path: str = Query(..., description="相对文件路径"),
    db: Session = Depends(get_db)
):
    """获取文件内容（支持中文编码）"""
    # 验证项目存在
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    if not project.source_path:
        raise HTTPException(
            status_code=400,
            detail="项目未上传源代码"
        )
    
    service = StaticAnalysisService()
    
    try:
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"获取文件内容: project_id={project_id}, source_path={project.source_path}, file_path={file_path}")
        file_content = service.get_file_content(project.source_path, file_path)
        return file_content
    except FileNotFoundError as e:
        logger.error(f"文件未找到: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        import traceback
        logger.error(f"读取文件失败: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"读取文件失败: {str(e)}")

