"""静态分析结果存储管理"""
import os
import json
import time
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime


class StaticAnalysisStorage:
    """静态分析结果存储管理（文件系统）"""
    
    def __init__(self, storage_path: str = "./artifacts/static_analysis"):
        """
        初始化存储管理器
        
        Args:
            storage_path: 存储根目录路径
        """
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
    
    def save_results(
        self,
        project_id: int,
        analysis_results: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        保存分析结果
        
        Args:
            project_id: 项目ID
            analysis_results: 分析结果字典
            metadata: 元数据（状态、开始时间等）
        
        Returns:
            保存的文件路径
        """
        # 创建项目目录
        project_dir = self.storage_path / str(project_id)
        project_dir.mkdir(parents=True, exist_ok=True)
        
        # 创建时间戳目录
        timestamp = int(time.time())
        timestamp_dir = project_dir / str(timestamp)
        timestamp_dir.mkdir(parents=True, exist_ok=True)
        
        # 保存结果文件
        results_file = timestamp_dir / "results.json"
        
        result_data = {
            'project_id': project_id,
            'timestamp': timestamp,
            'created_at': datetime.utcnow().isoformat(),
            'metadata': metadata or {},
            'results': analysis_results
        }
        
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(result_data, f, indent=2, ensure_ascii=False)
        
        return str(results_file)
    
    def load_results(
        self,
        project_id: int,
        timestamp: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """
        加载分析结果
        
        Args:
            project_id: 项目ID
            timestamp: 时间戳，如果为None则加载最新的
        
        Returns:
            分析结果字典，如果不存在则返回None
        """
        project_dir = self.storage_path / str(project_id)
        if not project_dir.exists():
            return None
        
        if timestamp:
            # 加载指定时间戳的结果
            results_file = project_dir / str(timestamp) / "results.json"
        else:
            # 加载最新的结果
            timestamps = [int(d.name) for d in project_dir.iterdir() if d.is_dir() and d.name.isdigit()]
            if not timestamps:
                return None
            latest_timestamp = max(timestamps)
            results_file = project_dir / str(latest_timestamp) / "results.json"
        
        if not results_file.exists():
            return None
        
        try:
            with open(results_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"加载结果失败: {e}")
            return None
    
    def list_analysis_history(
        self,
        project_id: int
    ) -> List[Dict[str, Any]]:
        """
        列出项目的所有分析历史
        
        Args:
            project_id: 项目ID
        
        Returns:
            分析历史列表
        """
        project_dir = self.storage_path / str(project_id)
        if not project_dir.exists():
            return []
        
        history = []
        for timestamp_dir in project_dir.iterdir():
            if not timestamp_dir.is_dir():
                continue
            
            try:
                timestamp = int(timestamp_dir.name)
                results_file = timestamp_dir / "results.json"
                
                if results_file.exists():
                    with open(results_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        history.append({
                            'timestamp': timestamp,
                            'created_at': data.get('created_at'),
                            'metadata': data.get('metadata', {}),
                            'summary': data.get('results', {}).get('summary', {})
                        })
            except (ValueError, json.JSONDecodeError):
                continue
        
        # 按时间戳降序排序
        history.sort(key=lambda x: x['timestamp'], reverse=True)
        return history
    
    def delete_results(
        self,
        project_id: int,
        timestamp: Optional[int] = None
    ) -> bool:
        """
        删除分析结果
        
        Args:
            project_id: 项目ID
            timestamp: 时间戳，如果为None则删除所有
        
        Returns:
            是否成功删除
        """
        project_dir = self.storage_path / str(project_id)
        if not project_dir.exists():
            return False
        
        try:
            if timestamp:
                # 删除指定时间戳的结果
                timestamp_dir = project_dir / str(timestamp)
                if timestamp_dir.exists():
                    import shutil
                    shutil.rmtree(timestamp_dir)
                    return True
            else:
                # 删除所有结果
                import shutil
                shutil.rmtree(project_dir)
                return True
        except Exception as e:
            print(f"删除结果失败: {e}")
            return False
        
        return False

