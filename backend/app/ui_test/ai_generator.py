"""
UI测试AI生成器
使用Claude API生成Robot Framework + SikuliLibrary测试脚本
"""
import anthropic
from typing import Dict, Any, Optional
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


class UITestAIGenerator:
    """UI测试AI生成器"""
    
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None, base_url: Optional[str] = None):
        """
        初始化AI生成器
        
        Args:
            api_key: Claude API密钥，如果为None则从配置读取
            model: 模型名称，如果为None则从配置读取
            base_url: API base URL，如果为None则从配置读取
        """
        self.api_key = api_key or settings.CLAUDE_API_KEY
        self.model = model or settings.CLAUDE_MODEL
        self.base_url = base_url or settings.CLAUDE_BASE_URL
        
        if not self.api_key:
            raise ValueError("未配置Claude API密钥，请在config.py中设置CLAUDE_API_KEY")
        
        self.client = anthropic.Anthropic(
            api_key=self.api_key,
            base_url=self.base_url
        )
    
    def generate_robot_script(
        self,
        test_name: str,
        test_description: str,
        project_info: Dict[str, Any]
    ) -> str:
        """
        生成Robot Framework测试脚本
        
        Args:
            test_name: 测试用例名称
            test_description: 测试描述
            project_info: 项目信息字典，包含：
                - name: 项目名称
                - source_path: 应用程序路径
                - description: 项目描述
        
        Returns:
            生成的Robot Framework脚本内容
        """
        prompt = self._build_prompt(test_name, test_description, project_info)
        
        try:
            logger.info(f"开始生成Robot Framework脚本: {test_name}")
            
            message = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            
            # 提取生成的脚本
            robot_script = message.content[0].text.strip()
            
            # 清理markdown代码块标记
            robot_script = self._clean_script(robot_script)
            
            logger.info(f"成功生成Robot Framework脚本，长度: {len(robot_script)} 字符")
            
            return robot_script
            
        except anthropic.APIError as e:
            logger.error(f"Claude API调用失败: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"生成脚本失败: {str(e)}")
            raise
    
    def _build_prompt(
        self,
        test_name: str,
        test_description: str,
        project_info: Dict[str, Any]
    ) -> str:
        """构建AI提示词"""
        project_name = project_info.get('name', '未知项目')
        app_path = project_info.get('source_path', 'C:\\\\path\\\\to\\\\app.exe')
        project_desc = project_info.get('description', '无')
        
        prompt = f"""你是一个Robot Framework + SikuliLibrary专家。请根据以下需求生成一个完整的UI自动化测试脚本。

【测试需求】
测试用例名称：{test_name}
测试描述：{test_description}

【项目信息】
- 项目名称：{project_name}
- 应用程序路径：{app_path}
- 项目描述：{project_desc}

【技术要求】
1. 使用Robot Framework语法编写测试脚本
2. 使用SikuliLibrary进行基于图像识别的UI自动化测试
3. 使用Process库来启动和管理应用程序进程
4. 必须包含以下部分：
   - *** Settings *** : 导入必要的库（SikuliLibrary、Process、OperatingSystem）
   - *** Variables *** : 定义应用程序路径、图像路径等变量
   - *** Test Cases *** : 包含测试步骤和断言

【脚本结构示例】
*** Settings ***
Library    SikuliLibrary
Library    Process
Library    OperatingSystem

*** Variables ***
${{APP_PATH}}           {app_path.replace('\\\\', '/') if app_path else 'C:/path/to/app.exe'}
${{IMAGE_PATH}}         examples/robot_resources
${{TIMEOUT}}            30

*** Test Cases ***
{test_name}
    [Documentation]    {test_description}
    [Tags]    ui-test    auto-generated
    
    # 1. 启动应用程序
    Start Process    ${{APP_PATH}}    alias=app_under_test
    Sleep    5s    # 等待应用启动
    
    # 2. 设置图像识别参数
    Add Image Path    ${{IMAGE_PATH}}
    Set Min Similarity    0.7
    
    # 3. 执行测试步骤（根据测试描述生成具体步骤）
    # 例如：Wait Until Screen Contain    main_window.png    ${{TIMEOUT}}
    # 例如：Click    button.png    （注意：Click会自动找到图像并移动鼠标，不需要单独的Hover步骤）
    # 例如：Input Text    input_field.png    测试文本
    # 例如：Screen Should Contain    success_message.png
    # 注意：不要使用 Hover 关键字，SikuliLibrary中没有这个关键字！
    
    # 4. 清理：关闭应用程序
    [Teardown]    Terminate Process    app_under_test    kill=True

【重要说明】
1. 图像文件需要提前准备，放在 examples/robot_resources 目录下
2. 使用 Start Process 而不是 Run 来启动GUI应用
3. 使用 Terminate Process 来确保应用被正确关闭
4. 所有Windows路径使用双反斜杠（\\\\）或正斜杠（/）
5. 添加适当的 Sleep 等待应用启动和响应
6. 使用 Set Min Similarity 设置图像匹配相似度（建议0.7）
7. 在 [Teardown] 中确保应用被关闭，即使测试失败也要执行

【常用SikuliLibrary关键字】
- Wait Until Screen Contain <image> <timeout>: 等待屏幕出现某个图像
- Click <image>: 点击图像（会自动找到图像并移动鼠标到该位置，然后点击）
- Double Click <image>: 双击图像
- Right Click <image>: 右键点击图像
- Input Text <image> <text>: 在图像位置输入文本
- Screen Should Contain <image>: 断言屏幕包含某个图像
- Screen Should Not Contain <image>: 断言屏幕不包含某个图像
- Capture Screen: 截取屏幕（自动保存到sikuli_captured目录）

【重要提示】
- SikuliLibrary 中没有 Hover 关键字！不要使用 Hover
- Click 关键字会自动找到图像并移动鼠标到该位置，然后点击，所以不需要单独的移动鼠标步骤
- 如果测试描述中提到"移动鼠标到XX位置"，直接使用 Click 即可，不需要先移动鼠标再点击

请根据测试描述"{test_description}"生成具体的测试步骤。只输出Robot Framework脚本内容，不要包含markdown代码块标记或其他说明文字。"""
        
        return prompt
    
    def _clean_script(self, script: str) -> str:
        """清理生成的脚本，去除markdown标记等"""
        lines = script.split("\n")
        
        # 去除开头的markdown代码块标记
        if lines and lines[0].strip().startswith("```"):
            lines = lines[1:]
        
        # 去除结尾的markdown代码块标记
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        
        # 去除开头和结尾的空行
        while lines and not lines[0].strip():
            lines = lines[1:]
        
        while lines and not lines[-1].strip():
            lines = lines[:-1]
        
        return "\n".join(lines)
    
    def validate_script(self, script: str) -> tuple[bool, Optional[str]]:
        """
        验证生成的脚本是否符合基本要求
        
        Returns:
            (是否有效, 错误信息)
        """
        if not script or not script.strip():
            return False, "脚本为空"
        
        # 检查必需的部分
        required_sections = ["*** Settings ***", "*** Test Cases ***"]
        for section in required_sections:
            if section not in script:
                return False, f"缺少必需的部分: {section}"
        
        # 检查是否包含SikuliLibrary
        if "SikuliLibrary" not in script:
            return False, "未导入SikuliLibrary"
        
        return True, None

