"""
报告生成模块
用于生成代码检测、修复与测试验证报告，并打包为ZIP文件
"""

import os
import time
import zipfile
from typing import Dict, Optional, Tuple, List, Any


def generate_report_zip(
    workflow_id: str,
    workflow_data: Dict[str, Any],
    output_dir: str,
    project_name: Optional[str] = None
) -> Tuple[Optional[str], Optional[str]]:
    """
    根据工作流结果生成报告与修复后代码的zip文件
    
    Args:
        workflow_id: 工作流ID
        workflow_data: 工作流数据字典，包含以下键：
            - bug_detection: 包含 'bugs' 列表的字典
            - code_fixing: 包含 'files_results' 列表或 'fixed_code' 字符串的字典
            - testing: 包含 'test_results' 列表和 'pass_rate' 数字的字典
            - file_path: 可选，原始文件路径
        output_dir: 输出目录路径
        project_name: 可选，项目名称，用于生成报告标题
    
    Returns:
        Tuple[zip_path, download_url]: 
            - zip_path: 生成的ZIP文件路径，失败返回None
            - download_url: 下载URL路径，失败返回None
    
    Example:
        >>> workflow_data = {
        ...     'bug_detection': {'bugs': [...]},
        ...     'code_fixing': {'files_results': [...]},
        ...     'testing': {'test_results': [...], 'pass_rate': 85}
        ... }
        >>> zip_path, url = generate_report_zip(
        ...     'workflow_123',
        ...     workflow_data,
        ...     '/path/to/output'
        ... )
    """
    try:
        # 创建输出目录
        out_dir = os.path.join(output_dir, f"report_{workflow_id}")
        os.makedirs(out_dir, exist_ok=True)
        
        # 报告文件路径
        report_md = os.path.join(out_dir, '报告.md')
        
        # 提取数据
        bugs = []
        if workflow_data.get('bug_detection'):
            bugs = workflow_data['bug_detection'].get('bugs', [])
        
        code_fix = workflow_data.get('code_fixing', {})
        files_results = code_fix.get('files_results', [])
        fixed_code_single = code_fix.get('fixed_code')
        
        testing = workflow_data.get('testing', {})
        test_results = testing.get('test_results', [])
        
        # 生成报告内容
        lines = []
        title = project_name if project_name else "代码检测、修复与测试验证报告"
        lines.append(f"# {title}\n")
        lines.append(f"- 工作流ID: {workflow_id}\n")
        lines.append(f"- 生成时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        # 一、Bug检测结果
        lines.append(f"\n## 一、Bug检测结果\n")
        lines.append(f"共检测到 {len(bugs)} 个问题。\n")
        for i, bug in enumerate(bugs, 1):
            btype = bug.get('type', '未知类型')
            sev = bug.get('severity', '未知')
            desc = bug.get('description', '无描述')
            file_name = bug.get('file_name') or ''
            file_path = bug.get('file_path') or ''
            line_no = bug.get('line_number', '?')
            lines.append(f"{i}. [{sev}] {btype} - {desc} ({file_name or file_path} 行{line_no})\n")
        
        # 二、修复摘要
        lines.append(f"\n## 二、修复摘要\n")
        if files_results:
            total_fixed = sum(fr.get('bugs_fixed', 0) for fr in files_results)
            lines.append(f"涉及文件 {len(files_results)} 个，修复 {total_fixed} 个问题。\n")
        elif fixed_code_single is not None:
            lines.append("单文件修复完成。\n")
        else:
            lines.append("暂无修复记录。\n")
        
        # 三、测试验证结果
        lines.append(f"\n## 三、测试验证结果\n")
        pass_rate = testing.get('pass_rate', 0)
        lines.append(f"通过率: {pass_rate}%\n")
        if test_results:
            for r in test_results:
                status = '通过' if r.get('passed') else '失败'
                test_name = r.get('test_name', '未知测试')
                message = r.get('message', '')
                lines.append(f"- {test_name}: {status} - {message}\n")
        else:
            lines.append("暂无测试结果。\n")
        
        # 写入报告文件
        with open(report_md, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
        
        # 创建修复代码目录
        fixed_root = os.path.join(out_dir, 'fixed')
        os.makedirs(fixed_root, exist_ok=True)
        
        # 保存修复后的代码文件
        if files_results:
            # 多文件修复结果
            for fr in files_results:
                rel_path = fr.get('file_path') or fr.get('file_name') or 'fixed_code'
                rel_path = rel_path.lstrip('/\\')
                dest_path = os.path.join(fixed_root, rel_path)
                os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                with open(dest_path, 'w', encoding='utf-8') as fw:
                    fw.write(fr.get('fixed_code', ''))
        elif fixed_code_single is not None:
            # 单文件修复结果
            original_path = workflow_data.get('file_path') or ''
            original_name = os.path.basename(original_path) if original_path else 'fixed_code.txt'
            dest_single = os.path.join(fixed_root, original_name)
            os.makedirs(os.path.dirname(dest_single), exist_ok=True)
            with open(dest_single, 'w', encoding='utf-8') as fw:
                fw.write(fixed_code_single)
        
        # 创建ZIP文件
        zip_name = os.path.join(output_dir, f"report_{workflow_id}.zip")
        with zipfile.ZipFile(zip_name, 'w', zipfile.ZIP_DEFLATED) as zf:
            zf.write(report_md, arcname='报告.md')
            for root, _, files in os.walk(fixed_root):
                for fn in files:
                    full = os.path.join(root, fn)
                    arc = os.path.relpath(full, out_dir)
                    zf.write(full, arcname=arc)
        
        download_url = f"/api/download-report/{workflow_id}"
        return zip_name, download_url
        
    except Exception as e:
        print(f"生成报告失败: {e}")
        import traceback
        traceback.print_exc()
        return None, None


def generate_report_markdown(
    workflow_id: str,
    workflow_data: Dict[str, Any],
    output_path: str,
    project_name: Optional[str] = None
) -> bool:
    """
    仅生成Markdown报告文件，不打包ZIP
    
    Args:
        workflow_id: 工作流ID
        workflow_data: 工作流数据字典
        output_path: 输出文件路径（包含文件名）
        project_name: 可选，项目名称
    
    Returns:
        bool: 是否成功生成
    """
    try:
        # 提取数据
        bugs = []
        if workflow_data.get('bug_detection'):
            bugs = workflow_data['bug_detection'].get('bugs', [])
        
        code_fix = workflow_data.get('code_fixing', {})
        files_results = code_fix.get('files_results', [])
        fixed_code_single = code_fix.get('fixed_code')
        
        testing = workflow_data.get('testing', {})
        test_results = testing.get('test_results', [])
        
        # 生成报告内容
        lines = []
        title = project_name if project_name else "代码检测、修复与测试验证报告"
        lines.append(f"# {title}\n")
        lines.append(f"- 工作流ID: {workflow_id}\n")
        lines.append(f"- 生成时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        # 一、Bug检测结果
        lines.append(f"\n## 一、Bug检测结果\n")
        lines.append(f"共检测到 {len(bugs)} 个问题。\n")
        for i, bug in enumerate(bugs, 1):
            btype = bug.get('type', '未知类型')
            sev = bug.get('severity', '未知')
            desc = bug.get('description', '无描述')
            file_name = bug.get('file_name') or ''
            file_path = bug.get('file_path') or ''
            line_no = bug.get('line_number', '?')
            lines.append(f"{i}. [{sev}] {btype} - {desc} ({file_name or file_path} 行{line_no})\n")
        
        # 二、修复摘要
        lines.append(f"\n## 二、修复摘要\n")
        if files_results:
            total_fixed = sum(fr.get('bugs_fixed', 0) for fr in files_results)
            lines.append(f"涉及文件 {len(files_results)} 个，修复 {total_fixed} 个问题。\n")
        elif fixed_code_single is not None:
            lines.append("单文件修复完成。\n")
        else:
            lines.append("暂无修复记录。\n")
        
        # 三、测试验证结果
        lines.append(f"\n## 三、测试验证结果\n")
        pass_rate = testing.get('pass_rate', 0)
        lines.append(f"通过率: {pass_rate}%\n")
        if test_results:
            for r in test_results:
                status = '通过' if r.get('passed') else '失败'
                test_name = r.get('test_name', '未知测试')
                message = r.get('message', '')
                lines.append(f"- {test_name}: {status} - {message}\n")
        else:
            lines.append("暂无测试结果。\n")
        
        # 确保输出目录存在
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # 写入报告文件
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
        
        return True
        
    except Exception as e:
        print(f"生成报告失败: {e}")
        import traceback
        traceback.print_exc()
        return False

