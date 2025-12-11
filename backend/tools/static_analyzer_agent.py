#!/usr/bin/env python3
"""
静态分析工具Agent
调用现有的静态代码分析工具（pylint、flake8、cppcheck等）
并将结果传递给Bug检测Agent
"""

import os
import json
import subprocess
import tempfile
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

@dataclass
class StaticAnalysisIssue:
    """静态分析发现的问题"""
    tool: str  # 工具名称（pylint、flake8、cppcheck等）
    type: str  # 问题类型
    description: str  # 问题描述
    line_number: int  # 行号
    severity: str  # 严重程度
    code: Optional[str] = None  # 错误代码
    column: Optional[int] = None  # 列号
    file_path: Optional[str] = None  # 文件路径


class StaticAnalyzerAgent:
    """静态分析工具Agent"""
    
    def __init__(self):
        """初始化静态分析器"""
        self.available_tools = self._detect_available_tools()
        logger.info(f"静态分析器初始化完成，可用工具: {', '.join(self.available_tools)}")
    
    def _detect_available_tools(self) -> List[str]:
        """检测系统中可用的静态分析工具"""
        tools = []
        
        # 检测Python静态分析工具
        for tool in ['pylint', 'flake8', 'mypy', 'bandit']:
            try:
                result = subprocess.run(
                    [tool, '--version'],
                    capture_output=True,
                    timeout=5,
                    text=True
                )
                if result.returncode == 0:
                    tools.append(tool)
                    logger.info(f"✅ 检测到工具: {tool}")
            except (FileNotFoundError, subprocess.TimeoutExpired):
                logger.debug(f"⚠️  工具不可用: {tool}")
        
        # 检测C/C++静态分析工具
        for tool in ['cppcheck', 'clang-tidy']:
            try:
                result = subprocess.run(
                    [tool, '--version'],
                    capture_output=True,
                    timeout=5,
                    text=True
                )
                if result.returncode == 0:
                    tools.append(tool)
                    logger.info(f"✅ 检测到工具: {tool}")
            except (FileNotFoundError, subprocess.TimeoutExpired):
                logger.debug(f"⚠️  工具不可用: {tool}")
        
        return tools
    
    def analyze_code(self, code: str, file_path: Optional[str] = None, language: Optional[str] = None) -> Dict[str, Any]:
        """
        分析代码
        
        Args:
            code: 源代码
            file_path: 文件路径（可选）
            language: 编程语言（可选，如果不提供则自动检测）
        
        Returns:
            包含所有静态分析结果的字典
        """
        logger.info("🔍 [静态分析] 开始静态代码分析...")
        
        # 检测语言
        if not language:
            language = self._detect_language(code, file_path)
        logger.info(f"📝 [静态分析] 检测到语言: {language}")
        
        # 根据语言选择合适的工具
        all_issues = []
        analysis_results = {}
        
        if language == 'python':
            all_issues, analysis_results = self._analyze_python(code, file_path)
        elif language in ['cpp', 'c']:
            all_issues, analysis_results = self._analyze_cpp(code, file_path)
        else:
            logger.warning(f"⚠️  [静态分析] 不支持的语言: {language}")
            return {
                'language': language,
                'issues': [],
                'tool_results': {},
                'summary': f"不支持的语言: {language}"
            }
        
        # 统计信息
        severity_count = {}
        for issue in all_issues:
            severity = issue.severity
            severity_count[severity] = severity_count.get(severity, 0) + 1
        
        logger.info(f"✅ [静态分析] 静态分析完成，发现 {len(all_issues)} 个问题")
        logger.info(f"📊 [静态分析] 严重程度统计: {severity_count}")
        
        return {
            'language': language,
            'issues': [self._issue_to_dict(issue) for issue in all_issues],
            'tool_results': analysis_results,
            'summary': f"使用 {', '.join(analysis_results.keys())} 分析 {language} 代码，共发现 {len(all_issues)} 个问题",
            'severity_count': severity_count
        }
    
    def _analyze_python(self, code: str, file_path: Optional[str] = None) -> tuple[List[StaticAnalysisIssue], Dict[str, Any]]:
        """分析Python代码"""
        all_issues = []
        results = {}
        
        # 创建临时文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as f:
            f.write(code)
            temp_file = f.name
        
        try:
            # 1. 运行 pylint
            if 'pylint' in self.available_tools:
                logger.info("🔧 [静态分析] 运行 pylint...")
                pylint_issues, pylint_result = self._run_pylint(temp_file)
                all_issues.extend(pylint_issues)
                results['pylint'] = pylint_result
                logger.info(f"✅ [静态分析] pylint 完成，发现 {len(pylint_issues)} 个问题")
            
            # 2. 运行 flake8
            if 'flake8' in self.available_tools:
                logger.info("🔧 [静态分析] 运行 flake8...")
                flake8_issues, flake8_result = self._run_flake8(temp_file)
                all_issues.extend(flake8_issues)
                results['flake8'] = flake8_result
                logger.info(f"✅ [静态分析] flake8 完成，发现 {len(flake8_issues)} 个问题")
            
            # 3. 运行 mypy (类型检查)
            if 'mypy' in self.available_tools:
                logger.info("🔧 [静态分析] 运行 mypy...")
                mypy_issues, mypy_result = self._run_mypy(temp_file)
                all_issues.extend(mypy_issues)
                results['mypy'] = mypy_result
                logger.info(f"✅ [静态分析] mypy 完成，发现 {len(mypy_issues)} 个问题")
            
            # 4. 运行 bandit (安全检查)
            if 'bandit' in self.available_tools:
                logger.info("🔧 [静态分析] 运行 bandit...")
                bandit_issues, bandit_result = self._run_bandit(temp_file)
                all_issues.extend(bandit_issues)
                results['bandit'] = bandit_result
                logger.info(f"✅ [静态分析] bandit 完成，发现 {len(bandit_issues)} 个问题")
        
        finally:
            # 清理临时文件
            try:
                os.unlink(temp_file)
            except Exception as e:
                logger.warning(f"清理临时文件失败: {e}")
        
        return all_issues, results
    
    def _analyze_cpp(self, code: str, file_path: Optional[str] = None) -> tuple[List[StaticAnalysisIssue], Dict[str, Any]]:
        """分析C/C++代码"""
        all_issues = []
        results = {}
        
        # 创建临时文件
        suffix = '.cpp' if '#include' in code and ('class ' in code or 'std::' in code) else '.c'
        with tempfile.NamedTemporaryFile(mode='w', suffix=suffix, delete=False, encoding='utf-8') as f:
            f.write(code)
            temp_file = f.name
        
        try:
            # 1. 运行 cppcheck
            if 'cppcheck' in self.available_tools:
                logger.info("🔧 [静态分析] 运行 cppcheck...")
                cppcheck_issues, cppcheck_result = self._run_cppcheck(temp_file)
                all_issues.extend(cppcheck_issues)
                results['cppcheck'] = cppcheck_result
                logger.info(f"✅ [静态分析] cppcheck 完成，发现 {len(cppcheck_issues)} 个问题")
            
            # 2. 运行 clang-tidy (如果可用)
            if 'clang-tidy' in self.available_tools:
                logger.info("🔧 [静态分析] 运行 clang-tidy...")
                clang_issues, clang_result = self._run_clang_tidy(temp_file)
                all_issues.extend(clang_issues)
                results['clang-tidy'] = clang_result
                logger.info(f"✅ [静态分析] clang-tidy 完成，发现 {len(clang_issues)} 个问题")
        
        finally:
            # 清理临时文件
            try:
                os.unlink(temp_file)
            except Exception as e:
                logger.warning(f"清理临时文件失败: {e}")
        
        return all_issues, results
    
    def _run_pylint(self, file_path: str) -> tuple[List[StaticAnalysisIssue], Dict[str, Any]]:
        """运行pylint"""
        issues = []
        result = {'success': False, 'output': '', 'error': ''}
        
        try:
            # 运行pylint并获取JSON输出
            process = subprocess.run(
                ['pylint', '--output-format=json', '--disable=C0111,C0103', file_path],
                capture_output=True,
                timeout=30,
                text=True
            )
            
            result['output'] = process.stdout
            result['error'] = process.stderr
            result['success'] = True
            
            # 解析JSON输出
            if process.stdout:
                try:
                    pylint_results = json.loads(process.stdout)
                    for item in pylint_results:
                        severity_map = {
                            'error': 'HIGH',
                            'warning': 'MEDIUM',
                            'refactor': 'LOW',
                            'convention': 'LOW',
                            'fatal': 'HIGH'
                        }
                        
                        issue = StaticAnalysisIssue(
                            tool='pylint',
                            type=item.get('type', 'unknown'),
                            description=item.get('message', ''),
                            line_number=item.get('line', 1),
                            severity=severity_map.get(item.get('type', ''), 'MEDIUM'),
                            code=item.get('symbol', ''),
                            column=item.get('column', None),
                            file_path=file_path
                        )
                        issues.append(issue)
                except json.JSONDecodeError:
                    logger.warning("pylint输出解析失败")
        
        except subprocess.TimeoutExpired:
            logger.warning("pylint执行超时")
            result['error'] = "执行超时"
        except Exception as e:
            logger.error(f"pylint执行失败: {e}")
            result['error'] = str(e)
        
        return issues, result
    
    def _run_flake8(self, file_path: str) -> tuple[List[StaticAnalysisIssue], Dict[str, Any]]:
        """运行flake8"""
        issues = []
        result = {'success': False, 'output': '', 'error': ''}
        
        try:
            # 运行flake8
            process = subprocess.run(
                ['flake8', '--format=%(row)d:%(col)d:%(code)s:%(text)s', file_path],
                capture_output=True,
                timeout=30,
                text=True
            )
            
            result['output'] = process.stdout
            result['error'] = process.stderr
            result['success'] = True
            
            # 解析输出
            for line in process.stdout.strip().split('\n'):
                if not line:
                    continue
                
                try:
                    parts = line.split(':', 3)
                    if len(parts) >= 4:
                        line_num = int(parts[0])
                        col = int(parts[1])
                        code = parts[2]
                        message = parts[3]
                        
                        # 根据错误代码判断严重程度
                        severity = 'LOW'
                        if code.startswith('E'):
                            severity = 'MEDIUM'
                        elif code.startswith('F'):
                            severity = 'HIGH'
                        
                        issue = StaticAnalysisIssue(
                            tool='flake8',
                            type=code,
                            description=message.strip(),
                            line_number=line_num,
                            severity=severity,
                            code=code,
                            column=col,
                            file_path=file_path
                        )
                        issues.append(issue)
                except (ValueError, IndexError):
                    continue
        
        except subprocess.TimeoutExpired:
            logger.warning("flake8执行超时")
            result['error'] = "执行超时"
        except Exception as e:
            logger.error(f"flake8执行失败: {e}")
            result['error'] = str(e)
        
        return issues, result
    
    def _run_mypy(self, file_path: str) -> tuple[List[StaticAnalysisIssue], Dict[str, Any]]:
        """运行mypy"""
        issues = []
        result = {'success': False, 'output': '', 'error': ''}
        
        try:
            # 运行mypy
            process = subprocess.run(
                ['mypy', '--ignore-missing-imports', file_path],
                capture_output=True,
                timeout=30,
                text=True
            )
            
            result['output'] = process.stdout
            result['error'] = process.stderr
            result['success'] = True
            
            # 解析输出 (格式: file.py:line: error: message)
            for line in process.stdout.strip().split('\n'):
                if not line or ':' not in line:
                    continue
                
                try:
                    parts = line.split(':', 3)
                    if len(parts) >= 3:
                        line_num = int(parts[1])
                        message = parts[2].strip()
                        
                        issue = StaticAnalysisIssue(
                            tool='mypy',
                            type='type-error',
                            description=message,
                            line_number=line_num,
                            severity='MEDIUM',
                            file_path=file_path
                        )
                        issues.append(issue)
                except (ValueError, IndexError):
                    continue
        
        except subprocess.TimeoutExpired:
            logger.warning("mypy执行超时")
            result['error'] = "执行超时"
        except Exception as e:
            logger.error(f"mypy执行失败: {e}")
            result['error'] = str(e)
        
        return issues, result
    
    def _run_bandit(self, file_path: str) -> tuple[List[StaticAnalysisIssue], Dict[str, Any]]:
        """运行bandit (安全检查)"""
        issues = []
        result = {'success': False, 'output': '', 'error': ''}
        
        try:
            # 运行bandit并获取JSON输出
            process = subprocess.run(
                ['bandit', '-f', 'json', file_path],
                capture_output=True,
                timeout=30,
                text=True
            )
            
            result['output'] = process.stdout
            result['error'] = process.stderr
            result['success'] = True
            
            # 解析JSON输出
            if process.stdout:
                try:
                    bandit_results = json.loads(process.stdout)
                    for item in bandit_results.get('results', []):
                        severity_map = {
                            'HIGH': 'HIGH',
                            'MEDIUM': 'MEDIUM',
                            'LOW': 'LOW'
                        }
                        
                        issue = StaticAnalysisIssue(
                            tool='bandit',
                            type=item.get('test_id', 'unknown'),
                            description=item.get('issue_text', ''),
                            line_number=item.get('line_number', 1),
                            severity=severity_map.get(item.get('issue_severity', 'MEDIUM'), 'MEDIUM'),
                            code=item.get('test_id', ''),
                            file_path=file_path
                        )
                        issues.append(issue)
                except json.JSONDecodeError:
                    logger.warning("bandit输出解析失败")
        
        except subprocess.TimeoutExpired:
            logger.warning("bandit执行超时")
            result['error'] = "执行超时"
        except Exception as e:
            logger.error(f"bandit执行失败: {e}")
            result['error'] = str(e)
        
        return issues, result
    
    def _run_cppcheck(self, file_path: str) -> tuple[List[StaticAnalysisIssue], Dict[str, Any]]:
        """运行cppcheck"""
        issues = []
        result = {'success': False, 'output': '', 'error': ''}
        
        try:
            # 运行cppcheck并获取XML输出
            process = subprocess.run(
                ['cppcheck', '--enable=all', '--xml', '--xml-version=2', file_path],
                capture_output=True,
                timeout=30,
                text=True
            )
            
            result['output'] = process.stdout
            result['error'] = process.stderr  # cppcheck输出到stderr
            result['success'] = True
            
            # 解析XML输出（cppcheck的输出在stderr中）
            import xml.etree.ElementTree as ET
            if process.stderr:
                try:
                    root = ET.fromstring(process.stderr)
                    for error_elem in root.findall('.//error'):
                        severity_map = {
                            'error': 'HIGH',
                            'warning': 'MEDIUM',
                            'style': 'LOW',
                            'performance': 'MEDIUM',
                            'portability': 'LOW',
                            'information': 'LOW'
                        }
                        
                        location = error_elem.find('location')
                        line_num = 1
                        if location is not None:
                            line_num = int(location.get('line', 1))
                        
                        issue = StaticAnalysisIssue(
                            tool='cppcheck',
                            type=error_elem.get('id', 'unknown'),
                            description=error_elem.get('msg', ''),
                            line_number=line_num,
                            severity=severity_map.get(error_elem.get('severity', 'warning'), 'MEDIUM'),
                            code=error_elem.get('id', ''),
                            file_path=file_path
                        )
                        issues.append(issue)
                except ET.ParseError:
                    logger.warning("cppcheck XML输出解析失败")
        
        except subprocess.TimeoutExpired:
            logger.warning("cppcheck执行超时")
            result['error'] = "执行超时"
        except Exception as e:
            logger.error(f"cppcheck执行失败: {e}")
            result['error'] = str(e)
        
        return issues, result
    
    def _run_clang_tidy(self, file_path: str) -> tuple[List[StaticAnalysisIssue], Dict[str, Any]]:
        """运行clang-tidy"""
        issues = []
        result = {'success': False, 'output': '', 'error': ''}
        
        try:
            # 运行clang-tidy
            process = subprocess.run(
                ['clang-tidy', file_path, '--'],
                capture_output=True,
                timeout=30,
                text=True
            )
            
            result['output'] = process.stdout
            result['error'] = process.stderr
            result['success'] = True
            
            # 解析输出 (格式: file.cpp:line:col: warning: message [check-name])
            for line in process.stdout.strip().split('\n'):
                if not line or ':' not in line:
                    continue
                
                try:
                    # 查找行号和消息
                    if 'warning:' in line or 'error:' in line:
                        parts = line.split(':', 4)
                        if len(parts) >= 4:
                            line_num = int(parts[1])
                            message_part = parts[3].strip()
                            
                            severity = 'MEDIUM'
                            if 'error:' in line:
                                severity = 'HIGH'
                            
                            issue = StaticAnalysisIssue(
                                tool='clang-tidy',
                                type='clang-tidy-warning',
                                description=message_part,
                                line_number=line_num,
                                severity=severity,
                                file_path=file_path
                            )
                            issues.append(issue)
                except (ValueError, IndexError):
                    continue
        
        except subprocess.TimeoutExpired:
            logger.warning("clang-tidy执行超时")
            result['error'] = "执行超时"
        except Exception as e:
            logger.error(f"clang-tidy执行失败: {e}")
            result['error'] = str(e)
        
        return issues, result
    
    def _detect_language(self, code: str, file_path: Optional[str] = None) -> str:
        """检测编程语言（支持30+主流编程语言，使用多特征分析）
        
        Args:
            code: 源代码内容
            file_path: 文件路径（可选）
            
        Returns:
            语言标识字符串（如 'python', 'cpp', 'java' 等），如果无法确定则返回 'unknown'
        """
        # 第一优先级：文件扩展名检测（最可靠）
        if file_path:
            ext = os.path.splitext(file_path)[1].lower()
            language_map = {
                # C/C++ 系列
                '.c': 'c',
                '.h': 'c',  # C头文件，但可能是C++，需要结合代码内容判断
                '.cpp': 'cpp',
                '.cxx': 'cpp',
                '.cc': 'cpp',
                '.c++': 'cpp',
                '.hpp': 'cpp',
                '.hxx': 'cpp',
                '.hh': 'cpp',
                
                # Qt 相关
                '.pro': 'cpp',  # Qt项目文件，通常是C++
                '.pri': 'cpp',  # Qt项目包含文件
                '.prf': 'cpp',  # Qt项目特性文件
                '.ui': 'cpp',   # Qt Designer UI文件
                '.qml': 'qml',  # Qt Quick/QML
                '.qmltypes': 'qml',
                
                # Java 系列
                '.java': 'java',
                '.kt': 'kotlin',
                '.kts': 'kotlin',
                '.scala': 'scala',
                '.sc': 'scala',
                '.groovy': 'groovy',
                '.gvy': 'groovy',
                '.gy': 'groovy',
                '.clj': 'clojure',
                '.cljs': 'clojure',
                '.cljc': 'clojure',
                
                # JavaScript/TypeScript 系列
                '.js': 'javascript',
                '.jsx': 'javascript',  # React JSX
                '.mjs': 'javascript',
                '.cjs': 'javascript',
                '.ts': 'typescript',
                '.tsx': 'typescript',
                '.coffee': 'coffeescript',
                '.cson': 'coffeescript',
                '.dart': 'dart',
                
                # Python 系列
                '.py': 'python',
                '.pyw': 'python',
                '.pyi': 'python',
                '.pyx': 'python',
                '.pyc': 'python',
                '.pyo': 'python',
                
                # Web 相关
                '.html': 'html',
                '.htm': 'html',
                '.css': 'css',
                '.scss': 'css',
                '.sass': 'css',
                '.less': 'css',
                '.vue': 'javascript',  # Vue.js
                
                # Go/Rust 系列
                '.go': 'go',
                '.rs': 'rust',
                '.rlib': 'rust',
                
                # C# / .NET
                '.cs': 'csharp',
                '.csx': 'csharp',
                '.vb': 'vb',
                '.vbx': 'vb',
                '.fs': 'fsharp',
                '.fsx': 'fsharp',
                '.fsi': 'fsharp',
                
                # 其他主流语言
                '.swift': 'swift',
                '.rb': 'ruby',
                '.rbw': 'ruby',
                '.php': 'php',
                '.phtml': 'php',
                '.r': 'r',
                '.R': 'r',
                '.m': 'objectivec',  # Objective-C
                '.mm': 'objectivec',  # Objective-C++
                '.pl': 'perl',
                '.pm': 'perl',
                '.t': 'perl',
                '.lua': 'lua',
                '.sh': 'shell',
                '.bash': 'shell',
                '.zsh': 'shell',
                '.sql': 'sql',
                
                # 配置文件（通常不用于代码分析，但列出以便识别）
                '.xml': 'xml',
                '.json': 'json',
                '.yaml': 'yaml',
                '.yml': 'yaml',
            }
            
            detected = language_map.get(ext)
            if detected:
                # 特殊处理：.h文件需要结合代码内容判断是C还是C++
                if ext == '.h':
                    if self._has_cpp_features(code):
                        return 'cpp'
                    return 'c'
                return detected
        
        # 第二优先级：代码内容检测（多特征分析）
        return self._detect_language_from_content(code)
    
    def _has_cpp_features(self, code: str) -> bool:
        """检测代码是否包含C++特征"""
        cpp_keywords = ['namespace', 'class ', 'struct ', 'template', 'std::', 
                       'using namespace', 'public:', 'private:', 'protected:',
                       'virtual', 'override', 'constexpr', 'nullptr']
        code_lower = code.lower()
        for keyword in cpp_keywords:
            if keyword.lower() in code_lower:
                return True
        return False
    
    def _detect_language_from_content(self, code: str) -> str:
        """根据代码内容检测语言（多特征分析）"""
        if not code or len(code.strip()) == 0:
            return 'unknown'
        
        code_lower = code.lower()
        
        # 统计各语言特征得分
        scores = {}
        
        # 1. C/C++特征检测
        cpp_score = 0
        if '#include' in code:
            cpp_score += 3
        if 'int main(' in code_lower or 'void main(' in code_lower:
            cpp_score += 2
        if any(kw in code for kw in ['namespace', 'class ', 'struct ', 'template']):
            cpp_score += 2
        if 'std::' in code or 'using namespace std' in code_lower:
            cpp_score += 2
        if '#define' in code or '#ifdef' in code:
            cpp_score += 1
        scores['cpp'] = cpp_score
        
        # C特征（与C++区分）
        c_score = 0
        if '#include' in code and cpp_score < 3:
            c_score += 2
        if 'int main(' in code_lower and 'class ' not in code:
            c_score += 1
        scores['c'] = c_score
        
        # 2. Qt特征检测（高优先级，覆盖C++）
        qt_score = 0
        qt_keywords = ['Q_OBJECT', 'QT_BEGIN_NAMESPACE', 'QT_END_NAMESPACE',
                      'QThread', 'QObject', 'QWidget', 'QMainWindow',
                      'QString', 'QList', 'QMap', 'QVariant', 'QByteArray']
        qt_includes = ['#include <Q', '#include "Q']
        for keyword in qt_keywords:
            if keyword in code:
                qt_score += 2
        for include in qt_includes:
            if include in code:
                qt_score += 3
        if qt_score > 0:
            scores['cpp'] = max(scores.get('cpp', 0), qt_score)  # Qt是C++，提升C++得分
        
        # 3. Java特征检测
        java_score = 0
        if 'public class' in code_lower or 'public interface' in code_lower:
            java_score += 3
        if 'package ' in code_lower:
            java_score += 2
        if 'import java' in code_lower:
            java_score += 2
        if '@Override' in code or '@Deprecated' in code or '@SuppressWarnings' in code:
            java_score += 1
        if 'extends ' in code_lower or 'implements ' in code_lower:
            java_score += 1
        scores['java'] = java_score
        
        # 4. JavaScript/TypeScript特征检测
        js_score = 0
        ts_score = 0
        if 'function ' in code_lower or 'const ' in code_lower or 'let ' in code_lower:
            js_score += 2
        if 'var ' in code_lower:
            js_score += 1
        if 'export ' in code_lower or 'import ' in code_lower:
            js_score += 2
        if 'require(' in code_lower:
            js_score += 1
        if '=>' in code or 'async ' in code_lower or 'await ' in code_lower:
            js_score += 1
        # TypeScript特有特征
        if 'interface ' in code_lower or 'type ' in code_lower:
            ts_score += 2
        if ': string' in code_lower or ': number' in code_lower or ': boolean' in code_lower:
            ts_score += 2
        if ts_score > 0:
            scores['typescript'] = js_score + ts_score
        else:
            scores['javascript'] = js_score
        
        # 5. Python特征检测
        python_score = 0
        if 'def ' in code_lower:
            python_score += 3
        if 'import ' in code_lower or 'from ' in code_lower:
            python_score += 2
        if 'if __name__ == "__main__"' in code_lower:
            python_score += 3
        if 'lambda ' in code_lower or 'yield ' in code_lower:
            python_score += 1
        if 'async def' in code_lower:
            python_score += 1
        scores['python'] = python_score
        
        # 6. Go特征检测
        go_score = 0
        if 'package ' in code_lower and 'func ' in code_lower:
            go_score += 3
        if ':=' in code:
            go_score += 2
        if 'go func()' in code_lower or 'chan ' in code_lower:
            go_score += 1
        scores['go'] = go_score
        
        # 7. Rust特征检测
        rust_score = 0
        if 'fn ' in code_lower and 'let ' in code_lower:
            rust_score += 3
        if 'mut ' in code_lower or 'pub ' in code_lower:
            rust_score += 2
        if 'use ' in code_lower and 'mod ' in code_lower:
            rust_score += 1
        if any(kw in code for kw in ['impl ', 'trait ', '&str', 'String', 'Vec<', 'Option<']):
            rust_score += 2
        scores['rust'] = rust_score
        
        # 8. C#特征检测
        csharp_score = 0
        if 'namespace ' in code_lower and 'using ' in code_lower:
            csharp_score += 2
        if 'public class' in code_lower and 'using System' in code_lower:
            csharp_score += 3
        if any(kw in code_lower for kw in ['public ', 'private ', 'protected ', 'internal ']):
            csharp_score += 1
        if '[' in code and ']' in code and 'Attribute' in code:  # 特性语法
            csharp_score += 1
        scores['csharp'] = csharp_score
        
        # 9. 其他语言特征检测
        # Swift
        if 'import Swift' in code or ('func ' in code_lower and 'var ' in code_lower and 'let ' in code_lower):
            scores['swift'] = 2
        
        # Ruby
        if 'def ' in code_lower and 'end' in code_lower and 'class ' in code_lower:
            if 'require ' in code_lower or 'module ' in code_lower:
                scores['ruby'] = 2
        
        # PHP
        if '<?php' in code_lower or '<?=' in code:
            scores['php'] = 3
        
        # R语言
        if '<-' in code or '->' in code:
            if 'function(' in code_lower or 'library(' in code_lower:
                scores['r'] = 2
        
        # 找到得分最高的语言
        if not scores:
            return 'unknown'
        
        max_score = max(scores.values())
        if max_score == 0:
            return 'unknown'
        
        # 返回得分最高的语言
        for lang, score in scores.items():
            if score == max_score:
                return lang
        
        return 'unknown'
    
    def _issue_to_dict(self, issue: StaticAnalysisIssue) -> Dict[str, Any]:
        """将StaticAnalysisIssue转换为字典"""
        return {
            'tool': issue.tool,
            'type': issue.type,
            'description': issue.description,
            'line_number': issue.line_number,
            'severity': issue.severity,
            'code': issue.code,
            'column': issue.column,
            'file_path': issue.file_path
        }


def main():
    """测试静态分析器"""
    analyzer = StaticAnalyzerAgent()
    
    # 测试Python代码
    python_code = '''
def divide(a, b):
    return a / b

def unused_function():
    x = 1
    return x

result = divide(10, 0)
'''
    
    print("=" * 60)
    print("测试Python代码静态分析")
    print("=" * 60)
    print(python_code)
    print("\n分析结果:")
    result = analyzer.analyze_code(python_code, language='python')
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    # 测试C++代码
    cpp_code = '''
#include <iostream>
#include <vector>

int main() {
    std::vector<int> numbers = {1, 2, 3};
    std::cout << numbers[10] << std::endl;  // 越界访问
    
    int* ptr = new int[10];
    // 内存泄漏 - 没有delete
    
    return 0;
}
'''
    
    print("\n" + "=" * 60)
    print("测试C++代码静态分析")
    print("=" * 60)
    print(cpp_code)
    print("\n分析结果:")
    result = analyzer.analyze_code(cpp_code, language='cpp')
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()

