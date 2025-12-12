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
        # API key是可选的，如果没有配置则使用None（仅使用传统工具分析）
        self.agent = StaticAnalysisAgent(api_key=settings.DASHSCOPE_API_KEY) if settings.DASHSCOPE_API_KEY else None
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
            logger.info(f"开始分析项目 {project_id}: {project_path}, use_llm={use_llm}")
            
            # 检查是否需要大模型但未配置
            if use_llm and not self.agent:
                raise ValueError("需要大模型分析但未配置 DASHSCOPE_API_KEY，请设置环境变量或在配置文件中添加")
            
            # 运行分析
            if use_llm and self.agent:
                # 使用大模型进行深度分析
                results = self.agent.analyze_project(
                    project_path=project_path,
                    language=language,
                    use_llm=use_llm
                )
            else:
                # 仅使用传统工具分析（不使用大模型）
                logger.info("使用传统工具（Cppcheck）进行静态分析")
                from app.executors.factory import ExecutorFactory
                from pathlib import Path
                
                # 创建Cppcheck执行器
                executor = ExecutorFactory.get_executor("cppcheck")
                
                # 构建Test IR
                test_ir = {
                    "type": "static",
                    "tool": "cppcheck",
                    "name": "代码静态分析(cppcheck)",
                    "description": "使用 cppcheck 进行静态分析",
                    "target_files": [],
                    "target_directories": [str(Path(project_path).resolve())],
                    "rules": [],
                    "enable": "all",
                    "exclude_patterns": [],
                    "tags": [],
                }
                
                # 执行分析
                result = executor.execute(test_ir)
                
                # 转换为统一的结果格式
                issues = result.get("metadata", {}).get("issues", [])
                results = {
                    "project_path": project_path,
                    "language": language or "C++",
                    "files_analyzed": result.get("metadata", {}).get("files_analyzed", 0),
                    "total_issues": len(issues),
                    "file_results": {},
                    "summary": {
                        "total_files": result.get("metadata", {}).get("files_analyzed", 0),
                        "total_issues": len(issues),
                        "severity_count": {
                            "HIGH": len([i for i in issues if i.get("severity") in ["error", "critical"]]),
                            "MEDIUM": len([i for i in issues if i.get("severity") == "warning"]),
                            "LOW": len([i for i in issues if i.get("severity") in ["information", "style"]])
                        }
                    }
                }
                
                # 按文件组织问题
                for issue in issues:
                    file_path = issue.get("file", "unknown")
                    if file_path not in results["file_results"]:
                        results["file_results"][file_path] = {"issues": []}
                    results["file_results"][file_path]["issues"].append(issue)
            
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
        # 尝试导入chardet，如果没有则使用简单检测
        try:
            import chardet
            use_chardet = True
        except ImportError:
            use_chardet = False
        
        # 处理文件路径（可能是URL编码的）
        import urllib.parse
        file_path = urllib.parse.unquote(file_path)
        
        logger.info(f"获取文件内容: project_path={project_path}, file_path={file_path}")
        
        # 构建完整路径
        project_path_obj = Path(project_path).resolve()
        if not project_path_obj.exists():
            raise FileNotFoundError(f"项目路径不存在: {project_path}")
        
        # 处理相对路径（可能包含路径分隔符）
        file_path_normalized = file_path.replace('\\', '/').lstrip('/')
        
        # 尝试多种路径组合
        possible_paths = [
            project_path_obj / file_path_normalized,  # 直接拼接
            project_path_obj / file_path,  # 原始路径
            Path(project_path) / file_path_normalized,  # 未resolve的路径
            Path(project_path) / file_path,
        ]
        
        # 如果file_path看起来是绝对路径的一部分，尝试提取相对部分
        if 'artifacts' in file_path or 'projects' in file_path:
            # 尝试从完整路径中提取相对路径
            parts = file_path.replace('\\', '/').split('/')
            if 'projects' in parts:
                idx = parts.index('projects')
                relative_parts = parts[idx+2:]  # 跳过projects和UUID
                if relative_parts:
                    possible_paths.append(project_path_obj / '/'.join(relative_parts))
        
        full_path = None
        for possible_path in possible_paths:
            try:
                possible_path = Path(possible_path).resolve()
                if possible_path.exists() and possible_path.is_file():
                    full_path = possible_path
                    logger.info(f"找到文件: {full_path}")
                    break
            except Exception as e:
                logger.debug(f"尝试路径失败: {possible_path}, error: {e}")
                continue
        
        if full_path is None or not full_path.exists() or not full_path.is_file():
            error_msg = f"文件不存在: {file_path}\n尝试的路径:\n" + "\n".join([str(p) for p in possible_paths])
            logger.error(error_msg)
            raise FileNotFoundError(error_msg)
        
        # 先读取文件大小
        file_size = full_path.stat().st_size
        
        # 检测文件编码
        detected_encoding = None
        confidence = 0
        raw_data = None
        if use_chardet:
            try:
                with open(full_path, 'rb') as f:
                    raw_data = f.read()
                    detected = chardet.detect(raw_data)
                    detected_encoding = detected.get('encoding', 'utf-8')
                    confidence = detected.get('confidence', 0)
            except Exception as e:
                logger.warning(f"编码检测失败: {e}")
                detected_encoding = 'utf-8'
        else:
            detected_encoding = 'utf-8'
        
        # 尝试读取文件
        encodings_to_try = [detected_encoding, 'utf-8', 'gbk', 'gb2312', 'latin-1', 'cp1252']
        content = None
        used_encoding = None
        
        for enc in encodings_to_try:
            if not enc:
                continue
            try:
                with open(full_path, 'r', encoding=enc, errors='replace') as f:
                    content = f.read()
                used_encoding = enc
                logger.info(f"成功读取文件，使用编码: {enc}")
                break
            except (UnicodeDecodeError, LookupError) as e:
                logger.debug(f"尝试编码 {enc} 失败: {e}")
                continue
        
        if content is None:
            raise ValueError(f"无法读取文件: {file_path}，尝试了多种编码都失败")
        
        # 将内容按行分割
        lines = content.split('\n')
        
        return {
            'path': file_path,
            'content': content,
            'encoding': used_encoding or 'utf-8',
            'detected_encoding': detected_encoding,
            'confidence': confidence,
            'size': file_size,
            'lines': lines
        }

