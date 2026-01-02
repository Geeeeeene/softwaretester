"""
UI测试AI生成器
使用Claude API生成Robot Framework + SikuliLibrary测试脚本
"""
import anthropic
import json
import httpx
import time
from pathlib import Path
from typing import Dict, Any, Optional
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


class UITestAIGenerator:
    """UI测试AI生成器 - 使用Claude Sonnet 4.5模型"""
    
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
        
        # 当前使用的AI模型信息
        self.ai_model_name = "Claude Sonnet 4.5"
        self.ai_model_id = self.model or "claude-sonnet-4-5-20250929"
        
        if not self.api_key:
            # 允许在没有API Key的情况下初始化，但在调用时会失败
            pass
            
        if self.api_key:
            # 设置超时时间：连接超时30秒，读取超时300秒（5分钟）
            # 因为通过代理可能较慢，且AI生成需要较长时间
            import httpx
            http_client = httpx.Client(
                timeout=httpx.Timeout(
                    connect=30.0,  # 连接超时30秒
                    read=300.0,    # 读取超时300秒（5分钟）
                    write=30.0,    # 写入超时30秒
                    pool=30.0      # 连接池超时30秒
                )
            )
            self.client = anthropic.Anthropic(
                api_key=self.api_key,
                base_url=self.base_url,
                http_client=http_client
            )
        else:
            self.client = None
        
        # 加载图片知识库
        self.knowledge_base = self._load_knowledge_base()
    
    def _load_knowledge_base(self) -> Dict[str, Any]:
        """
        加载图片资源知识库
        
        Returns:
            知识库字典，如果加载失败则返回空字典
        """
        try:
            # 获取知识库文件路径
            current_dir = Path(__file__).parent
            kb_path = current_dir / "image_knowledge_base.json"
            
            if kb_path.exists():
                with open(kb_path, 'r', encoding='utf-8') as f:
                    kb = json.load(f)
                logger.info(f"成功加载图片知识库，包含 {len(kb.get('categories', {}))} 个分类")
                return kb
            else:
                logger.warning(f"知识库文件不存在: {kb_path}")
                return {}
        except Exception as e:
            logger.error(f"加载知识库失败: {str(e)}")
            return {}
    
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
        if not self.client:
            raise ValueError("未配置Claude API密钥，无法生成脚本")

        prompt = self._build_prompt(test_name, test_description, project_info)
        
        # 重试机制：最多重试3次
        max_retries = 3
        retry_delay = 2  # 重试延迟（秒）
        
        for attempt in range(max_retries):
            try:
                logger.info(f"开始生成Robot Framework脚本: {test_name} (尝试 {attempt + 1}/{max_retries})")
                logger.info(f"提示词长度: {len(prompt)} 字符")
                
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
                error_msg = str(e)
                logger.error(f"Claude API调用失败 (尝试 {attempt + 1}/{max_retries}): {error_msg}")
                
                # 如果是超时错误且还有重试机会，则重试
                if "timeout" in error_msg.lower() or "timed out" in error_msg.lower():
                    if attempt < max_retries - 1:
                        logger.info(f"检测到超时错误，{retry_delay}秒后重试...")
                        time.sleep(retry_delay)
                        retry_delay *= 2  # 指数退避
                        continue
                    else:
                        raise ValueError(f"Claude API请求超时（已重试{max_retries}次）。可能原因：\n1. 网络连接不稳定\n2. 代理服务器响应慢\n3. 提示词内容过大\n\n建议：\n1. 检查网络连接\n2. 尝试简化测试描述\n3. 稍后重试")
                else:
                    # 其他API错误直接抛出
                    raise ValueError(f"Claude API调用失败: {error_msg}")
                    
            except Exception as e:
                error_msg = str(e)
                logger.error(f"生成脚本失败 (尝试 {attempt + 1}/{max_retries}): {error_msg}")
                
                # 如果是超时相关的错误且还有重试机会，则重试
                if ("timeout" in error_msg.lower() or "timed out" in error_msg.lower() or 
                    "interrupted" in error_msg.lower() or "connection" in error_msg.lower()):
                    if attempt < max_retries - 1:
                        logger.info(f"检测到网络错误，{retry_delay}秒后重试...")
                        time.sleep(retry_delay)
                        retry_delay *= 2  # 指数退避
                        continue
                    else:
                        raise ValueError(f"请求超时或被中断（已重试{max_retries}次）。可能原因：\n1. 网络连接不稳定\n2. 代理服务器响应慢\n3. 提示词内容过大\n\n建议：\n1. 检查网络连接和代理设置\n2. 尝试简化测试描述\n3. 稍后重试")
                else:
                    # 其他错误直接抛出
                    raise ValueError(f"生成测试用例失败: {error_msg}")
        
        # 如果所有重试都失败，抛出错误
        raise ValueError(f"生成测试用例失败：已重试{max_retries}次，均失败")
    
    def _build_image_knowledge_section(self) -> str:
        """
        构建图片知识库部分，包含所有可用图片及其使用规则
        
        Returns:
            知识库文本描述
        """
        if not self.knowledge_base:
            return "【图片资源】\n暂无图片资源信息。\n"
        
        kb = self.knowledge_base
        sections = []
        
        sections.append("【图片资源知识库】")
        sections.append(f"当前AI模型: {kb.get('ai_model', self.ai_model_name)}")
        sections.append(f"基础路径: {kb.get('base_path', 'robot_resources')}")
        sections.append("")
        
        # 按分类列出所有图片
        categories = kb.get('categories', {})
        for cat_name, cat_info in categories.items():
            sections.append(f"【{cat_name.upper()}】({cat_info.get('count', 0)}个文件) - {cat_info.get('description', '')}")
            images = cat_info.get('images', [])
            for img in images:
                img_name = img.get('name', '')
                img_path = img.get('path', '')
                img_desc = img.get('description', '')
                img_usage = img.get('usage', '')
                
                sections.append(f"  - {img_name}")
                sections.append(f"    路径: {img_path}")
                sections.append(f"    说明: {img_desc}")
                sections.append(f"    用途: {img_usage}")
                
                # 如果有触发关系，说明
                if 'triggers_select' in img:
                    triggers = img['triggers_select']
                    sections.append(f"    注意: 点击此按钮后会显示以下下拉菜单: {', '.join(triggers)}")
                
                sections.append("")
        
        # 添加使用规则
        usage_rules = kb.get('usage_rules', {})
        if usage_rules:
            sections.append("【重要使用规则】")
            
            # selects需要先点击buttons的规则
            selects_rules = usage_rules.get('selects_require_buttons', {})
            if selects_rules:
                rules_list = selects_rules.get('rules', [])
                if rules_list:
                    sections.append("1. 下拉菜单(selects)必须先点击对应的按钮(buttons)才能显示和使用：")
                    for rule in rules_list:
                        select_name = rule.get('select', '')
                        required_buttons = rule.get('required_button', [])
                        if isinstance(required_buttons, str):
                            required_buttons = [required_buttons]
                        description = rule.get('description', '')
                        sections.append(f"   - {select_name} 需要先点击: {', '.join(required_buttons)}")
                        sections.append(f"     说明: {description}")
                    sections.append("")
            
            # 图片路径格式
            path_format = usage_rules.get('image_path_format', {})
            if path_format:
                sections.append("2. 图片路径格式：")
                sections.append(f"   格式: {path_format.get('format', '')}")
                sections.append(f"   示例: {path_format.get('example', '')}")
                sections.append(f"   注意: {path_format.get('note', '')}")
                sections.append("")
        
        sections.append("【严格要求】")
        sections.append("1. 生成脚本时，必须严格使用上述知识库中的图片，不能使用不存在的图片名称")
        sections.append("2. 使用selects类图片时，必须先点击对应的buttons类图片")
        sections.append("3. 图片路径必须使用知识库中提供的完整路径格式")
        sections.append("4. 如果测试描述中提到的功能没有对应的图片，请在注释中说明，并使用最接近的图片")
        sections.append("")
        
        return "\n".join(sections)
    
    def _build_prompt(
        self,
        test_name: str,
        test_description: str,
        project_info: Dict[str, Any]
    ) -> str:
        """构建AI提示词"""
        project_name = project_info.get('name', '未知项目')
        app_path = project_info.get('source_path', 'C:\\path\\to\\app.exe')
        project_desc = project_info.get('description', '无')
        
        # 处理路径，避免在f-string中使用反斜杠 (Python 3.9兼容性)
        if app_path:
            app_path_clean = app_path.replace('\\', '/')
        else:
            app_path_clean = 'C:/path/to/app.exe'
        
        # 构建图片知识库部分
        image_kb_section = self._build_image_knowledge_section()
        
        prompt = f"""你是一个Robot Framework + SikuliLibrary专家。请根据以下需求生成一个完整的UI自动化测试脚本。

【当前使用的AI模型】
- AI模型: {self.ai_model_name} ({self.ai_model_id})
- 说明: 本系统使用Claude Sonnet 4.5模型生成测试脚本，该模型具有强大的代码生成和理解能力

{image_kb_section}

【测试需求】
测试用例名称：{test_name}
测试描述：{test_description}

【项目信息】
- 项目名称：{project_name}
- 应用程序路径：{app_path_clean}
- 项目描述：{project_desc}

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
${{APP_PATH}}           {app_path_clean}
${{IMAGE_PATH}}         robot_resources
${{TIMEOUT}}            30

*** Test Cases ***
{test_name}
    [Documentation]    {test_description}
    [Tags]    ui-test    auto-generated
    
    # 1. 启动应用程序
    Start Process    ${{APP_PATH}}    alias=app_under_test
    Sleep    8s    # 等待应用启动（增加等待时间确保程序完全加载）
    
    # 2. 设置图像识别参数
    Add Image Path    ${{IMAGE_PATH}}
    Set Min Similarity    0.6    # 降低相似度阈值提高识别成功率
    
    # 3. 执行测试步骤（根据测试描述生成具体步骤）
    # 例如：Wait Until Screen Contain    main_window.png    30    （注意：超时参数必须是数字，不要使用 "30s"）
    # 例如：Click    button.png    （注意：Click会自动找到图像并移动鼠标，不需要单独的Hover步骤）
    # 例如：Input Text    input_field.png    测试文本
    # 例如：Screen Should Contain    success_message.png
    # 例如：Sleep    3s    （Sleep可以使用时间格式，例如 3s 或 3）
    # 注意：不要使用 Hover 关键字，SikuliLibrary中没有这个关键字！
    # 注意：Wait Until Screen Contain 的超时参数必须是纯数字（秒数），例如：30，不要使用 "30s"
    
    # 4. 清理：关闭应用程序
    [Teardown]    Terminate Process    app_under_test    kill=True

【重要说明】
1. 图像文件需要提前准备，放在 robot_resources 目录下（执行时会自动复制到工作目录）
2. 使用 Start Process 而不是 Run 来启动GUI应用
3. 使用 Terminate Process 来确保应用被正确关闭
4. 所有Windows路径使用双反斜杠（\\\\）或正斜杠（/）
5. 添加适当的 Sleep 等待应用启动和响应（建议8秒，确保程序完全加载）
6. 使用 Set Min Similarity 设置图像匹配相似度（建议0.6，提高识别成功率）
7. 在 [Teardown] 中确保应用被关闭，即使测试失败也要执行

【常用SikuliLibrary关键字】
- Wait Until Screen Contain <image> <timeout>: 等待屏幕出现某个图像（timeout必须是数字，单位秒，例如：10 或 30，不要使用 "10s" 或 "30s"）
- Click <image>: 点击图像（会自动找到图像并移动鼠标到该位置，然后点击）
- Double Click <image>: 双击图像
- Right Click <image>: 右键点击图像
- Input Text <image> <text>: 在图像位置输入文本
- Screen Should Contain <image>: 断言屏幕包含某个图像
- Screen Should Not Contain <image>: 断言屏幕不包含某个图像
- Capture Screen: 截取屏幕（自动保存到sikuli_captured目录）
- Sleep <time>: 等待指定时间（time可以是数字秒数，例如：Sleep    3，或者使用时间格式，例如：Sleep    3s）

【重要格式说明】
- Wait Until Screen Contain 的超时参数必须是纯数字（秒数），例如：Wait Until Screen Contain    image.png    10（不要使用 "10s"）
- Sleep 命令可以使用数字或时间格式，例如：Sleep    3 或 Sleep    3s（两种格式都可以）
- 关键字返回值使用 RETURN 语句，不要使用 [Return] 设置（已弃用）

【重要提示】
- SikuliLibrary 中没有 Hover 关键字！不要使用 Hover
- SikuliLibrary 中没有 Find 关键字！不要使用 Find 来获取图像位置
- Click 关键字会自动找到图像并移动鼠标到该位置，然后点击，所以不需要单独的移动鼠标步骤
- 如果测试描述中提到"移动鼠标到XX位置"，直接使用 Click 即可，不需要先移动鼠标再点击
- 如果需要点击图像的偏移位置（例如：点击画布的某个坐标），必须使用 Python 脚本配合 Windows API：
  * 创建一个自定义关键字，使用 Evaluate 执行 Python 代码
  * 使用 ctypes.windll.user32.SetCursorPos(x, y) 移动鼠标到目标坐标
  * 使用 ctypes.windll.user32.mouse_event(0x0002, 0, 0, 0, 0) 按下左键
  * 使用 ctypes.windll.user32.mouse_event(0x0004, 0, 0, 0, 0) 释放左键
  * 或者：使用辅助 Python 脚本文件来点击坐标
- 如果测试涉及符号面板中的图形符号：
  * 遍历所有可见的图形符号，每个图形只创建一次
  * 不使用滚轮，不滚动符号面板，只使用当前可见的图形符号
  * 按照以下顺序遍历所有可见的图形符号（每个图形只创建一次）：
    - robot_resources/symbols/card.png
    - robot_resources/symbols/cycle_boundary.png
    - robot_resources/symbols/data.png
    - robot_resources/symbols/direct_access_memory.png
    - robot_resources/symbols/disk.png
    - robot_resources/symbols/display.png
    - robot_resources/symbols/endpoint_symbol.png
    - robot_resources/symbols/file.png
    - robot_resources/symbols/internal_memory_storage.png
    - robot_resources/symbols/judge.png
    - robot_resources/symbols/manual_input.png
    - robot_resources/symbols/manual_operation.png
    - robot_resources/symbols/parallel_mode.png
    - robot_resources/symbols/perforated_tape.png
    - robot_resources/symbols/prepare.png
    - robot_resources/symbols/sequential_access_memory.png
    - robot_resources/symbols/store_data.png
    - robot_resources/symbols/text.png
  * 如果某个图形符号在当前屏幕不可见（需要滚动才能看到），则跳过该图形，继续下一个
  * 对于每个可见的图形符号，先点击该图形符号，然后在画布上放置图形
- 画布定位策略：
  * 等待画布出现（使用 canvas_empty.png 或 canvas_with_grid.png 来定位画布）
  * 确认画布区域可见且可用
- Click Region 关键字实现（重要）：
  * 必须创建一个自定义关键字 Click Region，接受图像路径和偏移量
  * 实现方式：
    1. 先使用 Click 关键字点击画布图像（canvas_empty.png 或 canvas_with_grid.png），确保画布可见
    2. 使用固定坐标作为画布基准点（例如：画布左上角在 (200, 150)），计算目标坐标 = 基准坐标 + 偏移量
    3. 使用 Python 脚本（通过 Evaluate 关键字）调用 Windows API 来点击目标坐标：
       - 使用 ctypes.windll.user32.SetCursorPos(x, y) 移动鼠标
       - 使用 ctypes.windll.user32.mouse_event(0x0002, 0, 0, 0, 0) 按下左键
       - 使用 ctypes.windll.user32.mouse_event(0x0004, 0, 0, 0, 0) 释放左键
  * 重要：不要使用 Run Process 或 Run 关键字调用外部 Python 脚本文件（如 click_coordinate.py），必须使用 Evaluate 关键字直接执行 Python 代码
- 图形位置计算：
  * 第一个图形从画布左上角开始（起始位置偏移（10, 10）或（20, 20），从左上角出发）
  * 每个图形向右移动60像素，每行10个图形后换行，向下移动60像素
  * 每次点击图形符号后，等待0.3秒再点击画布
  * 每次在画布上点击后，等待0.2秒再继续下一个操作
  * 如果某个图形符号不可见（点击失败或超时），则跳过该图形，继续下一个，不要因为一个图形失败而停止整个测试

【图片使用要求（严格遵守）】
1. 必须使用上述知识库中列出的图片，不能使用知识库中不存在的图片名称
2. 使用selects类图片时，必须先点击对应的buttons类图片（参考知识库中的使用规则）
3. 图片路径格式：在Variables中定义 ${{IMAGE_PATH}} = robot_resources，然后使用 ${{IMAGE_PATH}}/buttons/add_line_button.png 这样的格式（执行器会自动将 robot_resources 替换为绝对路径）
4. 如果测试描述中提到的功能没有对应的图片，请：
   - 在注释中说明缺少的图片
   - 使用知识库中最接近的图片替代
   - 或者使用通用的等待和验证步骤

【生成要求】
请根据测试描述"{test_description}"生成具体的测试步骤。
- 必须严格使用知识库中的图片
- 必须遵守selects和buttons的使用顺序关系
- 只输出Robot Framework脚本内容，不要包含markdown代码块标记或其他说明文字"""
        
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
    
    def validate_script(self, script: str) -> tuple:
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
