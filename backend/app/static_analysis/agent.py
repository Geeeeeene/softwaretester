"""集成大模型的静态分析Agent"""
import os
import sys
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path
from app.core.config import settings

# 添加tools目录到路径
# agent.py位于: backend/app/static_analysis/agent.py
# tools位于: backend/tools/
# 所以需要往上3级（static_analysis -> app -> backend）
tools_path = Path(__file__).parent.parent.parent / "tools"
sys.path.insert(0, str(tools_path))

from static_analyzer_agent import StaticAnalyzerAgent as BaseStaticAnalyzerAgent

logger = logging.getLogger(__name__)


class StaticAnalysisAgent:
    """集成大模型的静态分析Agent"""
    
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None, use_claude: bool = True, base_url: Optional[str] = None):
        """
        初始化静态分析Agent
        
        Args:
            api_key: API密钥（Claude或通义千问），如果为None则从 settings 读取
            model: 模型名称
            use_claude: 是否使用Claude API（默认True），否则使用通义千问
            base_url: API base URL（用于第三方代理）
        """
        self.base_analyzer = BaseStaticAnalyzerAgent()
        self.use_claude = use_claude
        
        if use_claude:
            self.api_key = api_key or settings.CLAUDE_API_KEY
            self.model = model or settings.CLAUDE_MODEL
            self.base_url = base_url or settings.CLAUDE_BASE_URL
            if not self.api_key:
                logger.warning("CLAUDE_API_KEY未设置，大模型分析功能将不可用")
        else:
            self.api_key = api_key or settings.DASHSCOPE_API_KEY
            self.model = "qwen-plus"
            self.base_url = None
            if not self.api_key:
                logger.warning("DASHSCOPE_API_KEY未设置，大模型分析功能将不可用")
    
    def analyze_code(
        self,
        code: str,
        file_path: Optional[str] = None,
        language: Optional[str] = None,
        use_llm: bool = True
    ) -> Dict[str, Any]:
        """
        分析代码（先使用传统工具，再用大模型深度分析）
        
        Args:
            code: 源代码
            file_path: 文件路径
            language: 编程语言
            use_llm: 是否使用大模型进行深度分析
        
        Returns:
            分析结果字典
        """
        # 1. 使用传统工具进行静态分析
        print(f"\n{'='*60}")
        print(f"📁 分析文件: {file_path or '未知'}")
        print(f"🔤 语言: {language or '未知'}")
        print(f"📝 代码长度: {len(code)} 字符")
        print(f"{'='*60}")
        print("🔍 开始传统工具静态分析...")
        logger.info("🔍 开始传统工具静态分析...")
        base_result = self.base_analyzer.analyze_code(code, file_path, language)
        print(f"✅ 传统工具分析完成，发现 {len(base_result.get('issues', []))} 个问题")
        
        # 2. 如果启用大模型且API密钥可用，进行深度分析
        if use_llm and self.api_key:
            print(f"\n🤖 开始 Claude AI 深度分析...")
            logger.info("🤖 开始大模型深度分析...")
            llm_result = self._analyze_with_llm(base_result, code, file_path, language)
            base_result['llm_analysis'] = llm_result
        else:
            print("⚠️  跳过大模型分析（未启用或API密钥不可用）")
            logger.info("⚠️  跳过大模型分析（未启用或API密钥不可用）")
            base_result['llm_analysis'] = None
        
        return base_result
    
    def _analyze_with_llm(
        self,
        tool_results: Dict[str, Any],
        code: str,
        file_path: Optional[str] = None,
        language: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        使用大模型对传统工具的分析结果进行深度分析
        
        Args:
            tool_results: 传统工具的分析结果
            code: 源代码
            file_path: 文件路径
            language: 编程语言
        
        Returns:
            大模型分析结果
        """
        # 构建提示词
        issues = tool_results.get('issues', [])
        print(f"🔨 准备 AI 分析提示词...")
        print(f"   - 传统工具发现 {len(issues)} 个问题")
        
        issues_text = "\n".join([
            f"- [{issue.get('severity', 'UNKNOWN')}] {issue.get('type', 'unknown')}: "
            f"{issue.get('description', '')} (行{issue.get('line_number', '?')})"
            for issue in issues[:20]  # 限制问题数量，避免token过多
        ])
        
        prompt = f"""你是一个专业的代码审查专家。请对以下代码进行深度分析，重点关注：

1. 传统工具已发现的问题（见下方列表）
2. 潜在的逻辑错误、安全漏洞、性能问题
3. 代码质量和最佳实践建议

**代码语言**: {language or '未知'}
**文件路径**: {file_path or '未知'}
**代码内容**:
```{language or ''}
{code[:2000]}  # 限制代码长度
```

**传统工具发现的问题**:
{issues_text if issues_text else "未发现问题"}

请提供：
1. 对已发现问题的详细解释和建议
2. 传统工具可能遗漏的潜在问题
3. 代码改进建议

请用中文回答，格式清晰。"""
        
        if self.use_claude:
            return self._analyze_with_claude(prompt)
        else:
            return self._analyze_with_dashscope(prompt)
    
    def _analyze_with_claude(self, prompt: str) -> Dict[str, Any]:
        """
        使用Claude API进行分析
        
        Args:
            prompt: 提示词
        
        Returns:
            分析结果
        """
        try:
            import anthropic
            
            # 根据是否有base_url来初始化客户端
            if self.base_url:
                client = anthropic.Anthropic(api_key=self.api_key, base_url=self.base_url)
                print(f"\n{'='*60}")
                print(f"🔧 使用自定义 API endpoint: {self.base_url}")
                print(f"🤖 模型: {self.model}")
                print(f"{'='*60}\n")
                logger.info(f"使用自定义 API endpoint: {self.base_url}")
            else:
                client = anthropic.Anthropic(api_key=self.api_key)
                print(f"\n{'='*60}")
                print(f"🤖 使用 Claude 官方 API")
                print(f"🤖 模型: {self.model}")
                print(f"{'='*60}\n")
            
            print(f"📤 正在发送请求到 Claude API...")
            print(f"📝 提示词长度: {len(prompt)} 字符")
            
            # 调用Claude API
            message = client.messages.create(
                model=self.model,
                max_tokens=2000,
                temperature=0.3,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            analysis_text = message.content[0].text
            print(f"\n{'='*60}")
            print(f"✅ Claude API 调用成功！")
            print(f"📊 响应长度: {len(analysis_text)} 字符")
            print(f"{'='*60}")
            print(f"\n📋 Claude 分析结果:")
            print(f"{'-'*60}")
            print(analysis_text)
            print(f"{'-'*60}\n")
            
            logger.info("✅ Claude 大模型分析完成")
            return {
                'success': True,
                'analysis': analysis_text,
                'model': self.model
            }
        
        except ImportError as e:
            error_msg = "anthropic模块未安装，请运行: pip install anthropic"
            print(f"\n{'='*60}")
            print(f"❌ 错误: {error_msg}")
            print(f"{'='*60}\n")
            logger.error(f"❌ {error_msg}")
            return {
                'success': False,
                'error': error_msg,
                'analysis': None
            }
        except Exception as e:
            error_msg = str(e)
            print(f"\n{'='*60}")
            print(f"❌ Claude API调用失败!")
            print(f"错误类型: {type(e).__name__}")
            print(f"错误信息: {error_msg}")
            print(f"{'='*60}\n")
            logger.error(f"❌ Claude API调用失败: {error_msg}")
            return {
                'success': False,
                'error': error_msg,
                'analysis': None
            }
    
    def _analyze_with_dashscope(self, prompt: str) -> Dict[str, Any]:
        """
        使用通义千问API进行分析
        
        Args:
            prompt: 提示词
        
        Returns:
            分析结果
        """
        try:
            import dashscope
            dashscope.api_key = self.api_key
            
            # 调用通义千问API
            response = dashscope.Generation.call(
                model='qwen-plus',
                prompt=prompt,
                max_tokens=2000,
                temperature=0.3
            )
            
            if response.status_code == 200:
                analysis_text = response.output.choices[0].message.content
                logger.info("✅ 通义千问分析完成")
                return {
                    'success': True,
                    'analysis': analysis_text,
                    'model': 'qwen-plus'
                }
            else:
                logger.error(f"❌ 大模型API调用失败: {response.status_code}, {response.message}")
                return {
                    'success': False,
                    'error': f"API调用失败: {response.message}",
                    'analysis': None
                }
        
        except ImportError:
            logger.error("❌ dashscope模块未安装，请运行: pip install dashscope")
            return {
                'success': False,
                'error': 'dashscope模块未安装',
                'analysis': None
            }
        except Exception as e:
            logger.error(f"❌ 大模型分析失败: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'analysis': None
            }
    
    def analyze_project(
        self,
        project_path: str,
        language: Optional[str] = None,
        use_llm: bool = True
    ) -> Dict[str, Any]:
        """
        分析整个项目
        
        Args:
            project_path: 项目根目录路径
            language: 主要编程语言
            use_llm: 是否使用大模型分析
        
        Returns:
            项目分析结果
        """
        project_path_obj = Path(project_path)
        if not project_path_obj.exists():
            raise ValueError(f"项目路径不存在: {project_path}")
        
        all_results = {}
        total_issues = []
        
        # 扫描代码文件
        code_extensions = {'.py', '.cpp', '.c', '.h', '.hpp', '.java', '.js', '.ts', '.go', '.rs'}
        
        # 先收集所有文件
        code_files = []
        for code_file in project_path_obj.rglob('*'):
            if code_file.is_file() and code_file.suffix in code_extensions:
                # 跳过一些目录
                if any(skip in str(code_file) for skip in ['.git', 'node_modules', '__pycache__', '.venv', 'venv']):
                    continue
                code_files.append(code_file)
        
        total_files = len(code_files)
        print(f"\n{'='*60}")
        print(f"📦 项目分析开始")
        print(f"📂 项目路径: {project_path}")
        print(f"📊 找到 {total_files} 个代码文件")
        print(f"🤖 AI分析: {'开启' if use_llm else '关闭'}")
        print(f"{'='*60}\n")
        
        for idx, code_file in enumerate(code_files, 1):
            try:
                # 读取文件内容
                with open(code_file, 'r', encoding='utf-8', errors='ignore') as f:
                    code = f.read()
                
                # 分析文件
                relative_path = str(code_file.relative_to(project_path_obj))
                print(f"\n[{idx}/{total_files}] 正在分析: {relative_path}")
                result = self.analyze_code(code, relative_path, language, use_llm)
                
                all_results[relative_path] = result
                total_issues.extend(result.get('issues', []))
                print(f"✅ [{idx}/{total_files}] 完成")
                
            except Exception as e:
                print(f"❌ [{idx}/{total_files}] 分析失败: {str(e)}")
                logger.warning(f"分析文件失败 {code_file}: {e}")
        
        # 汇总结果
        severity_count = self._count_severity(total_issues)
        
        print(f"\n{'='*60}")
        print(f"✅ 项目分析完成!")
        print(f"{'='*60}")
        print(f"📊 分析统计:")
        print(f"   - 分析文件数: {len(all_results)}")
        print(f"   - 发现问题数: {len(total_issues)}")
        print(f"   - 高危问题: {severity_count.get('HIGH', 0)}")
        print(f"   - 中危问题: {severity_count.get('MEDIUM', 0)}")
        print(f"   - 低危问题: {severity_count.get('LOW', 0)}")
        print(f"{'='*60}\n")
        
        return {
            'project_path': project_path,
            'language': language,
            'files_analyzed': len(all_results),
            'total_issues': len(total_issues),
            'file_results': all_results,
            'summary': {
                'total_files': len(all_results),
                'total_issues': len(total_issues),
                'severity_count': severity_count
            }
        }
    
    def _count_severity(self, issues: List[Dict[str, Any]]) -> Dict[str, int]:
        """统计问题严重程度"""
        count = {'HIGH': 0, 'MEDIUM': 0, 'LOW': 0}
        for issue in issues:
            severity = issue.get('severity', 'MEDIUM')
            if severity in count:
                count[severity] += 1
        return count

