"""静态分析服务层"""
import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from concurrent.futures import ThreadPoolExecutor, as_completed

from .agent import StaticAnalysisAgent
from .storage import StaticAnalysisStorage
from app.core.config import settings

logger = logging.getLogger(__name__)


class StaticAnalysisService:
    """静态分析服务层"""
    
    def __init__(self):
        """初始化服务"""
        self.agent = StaticAnalysisAgent(api_key=settings.DASHSCOPE_API_KEY)
        self.storage = StaticAnalysisStorage(storage_path=settings.STATIC_ANALYSIS_STORAGE_PATH)
    
    def run_analysis(
        self,
        project_id: int,
        project_path: str,
        language: Optional[str] = None,
        use_llm: bool = True
    ) -> Dict[str, Any]:
        """
        运行静态分析
        
        Args:
            project_id: 项目ID
            project_path: 项目源代码路径
            language: 主要编程语言
            use_llm: 是否使用大模型分析
        
        Returns:
            分析结果
        """
        try:
            logger.info(f"开始分析项目 {project_id}: {project_path}")
            
            # 运行分析
            results = self.agent.analyze_project(
                project_path=project_path,
                language=language,
                use_llm=use_llm
            )
            
            # 保存结果
            metadata = {
                'status': 'completed',
                'project_path': project_path,
                'language': language,
                'use_llm': use_llm
            }
            saved_path = self.storage.save_results(project_id, results, metadata)
            logger.info(f"分析结果已保存: {saved_path}")
            
            return {
                'success': True,
                'project_id': project_id,
                'results': results,
                'saved_path': saved_path
            }
        
        except Exception as e:
            logger.error(f"分析失败: {str(e)}")
            # 保存错误信息
            error_metadata = {
                'status': 'failed',
                'error': str(e),
                'project_path': project_path
            }
            self.storage.save_results(
                project_id,
                {'error': str(e)},
                error_metadata
            )
            return {
                'success': False,
                'error': str(e),
                'project_id': project_id
            }
    
    def get_analysis_status(
        self,
        project_id: int
    ) -> Dict[str, Any]:
        """
        获取分析状态
        
        Args:
            project_id: 项目ID
        
        Returns:
            状态信息
        """
        history = self.storage.list_analysis_history(project_id)
        
        if not history:
            return {
                'has_analysis': False,
                'latest': None
            }
        
        latest = history[0]
        return {
            'has_analysis': True,
            'latest': latest,
            'total_count': len(history)
        }
    
    def get_analysis_results(
        self,
        project_id: int,
        timestamp: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """
        获取分析结果
        
        Args:
            project_id: 项目ID
            timestamp: 时间戳，如果为None则返回最新的
        
        Returns:
            分析结果
        """
        return self.storage.load_results(project_id, timestamp)
    
    def get_file_tree(
        self,
        project_path: str
    ) -> List[Dict[str, Any]]:
        """
        获取项目文件树
        
        Args:
            project_path: 项目路径
        
        Returns:
            文件树结构
        """
        project_path_obj = Path(project_path)
        if not project_path_obj.exists():
            return []
        
        # 需要排除的目录
        exclude_dirs = {'.git', 'node_modules', '__pycache__', '.venv', 'venv', 
                        'build', 'dist', '.pytest_cache', '.mypy_cache', '.idea', '.vscode'}
        
        # 代码文件扩展名
        code_extensions = {'.py', '.cpp', '.c', '.h', '.hpp', '.java', '.js', '.ts', 
                          '.go', '.rs', '.cs', '.php', '.rb', '.swift', '.kt'}
        
        def build_tree(path: Path, relative_path: str = "") -> List[Dict[str, Any]]:
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
                        tree.append({
                            'name': item.name,
                            'path': current_path,
                            'type': 'directory',
                            'children': children
                        })
                    elif item.is_file() and item.suffix in code_extensions:
                        tree.append({
                            'name': item.name,
                            'path': current_path,
                            'type': 'file',
                            'size': item.stat().st_size
                        })
            except PermissionError:
                logger.warning(f"无权限访问: {path}")
            
            return tree
        
        return build_tree(project_path_obj)
    
    def get_file_content(
        self,
        project_path: str,
        file_path: str
    ) -> Dict[str, Any]:
        """
        获取文件内容（支持中文编码）
        
        Args:
            project_path: 项目根路径
            file_path: 相对文件路径
        
        Returns:
            文件内容字典
        """
        import chardet
        
        full_path = Path(project_path) / file_path
        
        if not full_path.exists() or not full_path.is_file():
            raise FileNotFoundError(f"文件不存在: {file_path}")
        
        # 检测文件编码
        with open(full_path, 'rb') as f:
            raw_data = f.read()
            detected = chardet.detect(raw_data)
            encoding = detected.get('encoding', 'utf-8')
            confidence = detected.get('confidence', 0)
        
        # 尝试读取文件
        encodings_to_try = [encoding, 'utf-8', 'gbk', 'gb2312', 'latin-1']
        content = None
        
        for enc in encodings_to_try:
            try:
                with open(full_path, 'r', encoding=enc) as f:
                    content = f.read()
                encoding = enc
                break
            except UnicodeDecodeError:
                continue
        
        if content is None:
            raise ValueError(f"无法读取文件: {file_path}，尝试了多种编码都失败")
        
        return {
            'path': file_path,
            'content': content,
            'encoding': encoding,
            'detected_encoding': detected.get('encoding'),
            'confidence': confidence,
            'size': len(raw_data),
            'lines': content.split('\n')
        }

