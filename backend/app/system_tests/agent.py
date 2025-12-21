"""系统测试（Robot Framework + SikuliLibrary）脚本生成 Agent（集成 Claude / 通义千问）"""

import os
import re
import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

from app.core.config import settings


def _strip_code_fences(text: str) -> str:
    """尽量把模型输出中的 ```robot / ``` 等代码围栏去掉。"""
    if not text:
        return text
    # 去掉首尾围栏
    text = re.sub(r"^\s*```[a-zA-Z0-9_-]*\s*\n", "", text)
    text = re.sub(r"\n\s*```\s*$", "", text)
    return text.strip()


class SystemTestAgent:
    """用大模型生成 Robot Framework 测试脚本（配合 SikuliLibrary 做 GUI 自动化）。"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        use_claude: bool = True,
        base_url: Optional[str] = None,
    ):
        self.use_claude = use_claude
        if use_claude:
            self.api_key = api_key or settings.CLAUDE_API_KEY or os.getenv("CLAUDE_API_KEY", "")
            self.model = model or settings.CLAUDE_MODEL or os.getenv("CLAUDE_MODEL", "claude-sonnet-4-5-20250929")
            self.base_url = base_url or settings.CLAUDE_BASE_URL or os.getenv("CLAUDE_BASE_URL")
        else:
            self.api_key = api_key or settings.DASHSCOPE_API_KEY or os.getenv("DASHSCOPE_API_KEY", "")
            self.model = model or "qwen-plus"
            self.base_url = None

        if not self.api_key:
            logger.warning("系统测试脚本生成：API Key 未配置（CLAUDE_API_KEY 或 DASHSCOPE_API_KEY）")

    def _build_prompt(
        self,
        app_name: str,
        app_desc: str,
        requirements: str,
        image_files: Optional[List[str]] = None,
    ) -> str:
        image_files = image_files or []
        images_text = "\n".join([f"- {x}" for x in image_files]) if image_files else "（暂无；请生成可替换的占位图片名）"

        # 目标：输出“可执行的 .robot 内容”，尽量不夹杂解释文字。
        return f"""你是资深的 GUI 系统测试工程师。请为一个 Ubuntu 上运行的 Qt 流程图编辑器生成 Robot Framework 测试套件，使用 SikuliLibrary 通过图片识别来操作界面。

被测应用：
- 名称：{app_name}
- 描述：{app_desc or "（无）"}

用户需求/测试点（非常重要）：
{requirements}

可用图片资源文件名（这些图片会放在 suite 目录的 images/ 下，可用相对路径引用）：
{images_text}

输出要求（严格遵守）：
1) 只输出一个 Robot Framework .robot 文件的纯文本内容（不要 Markdown，不要解释，不要三引号围栏）。
2) 必须包含以下结构段落：*** Settings ***、*** Variables ***、*** Keywords ***、*** Test Cases ***。
3) Settings 中必须导入：Library    SikuliLibrary
4) Variables 中定义图片目录变量：${{IMG_DIR}}    images
   并为每个图片文件名定义变量（如果提供了图片列表），例如：${{BTN_OPEN}}    ${{IMG_DIR}}/open.png
5) Keywords 中封装 GUI 操作步骤（Wait/Click/Type 等），优先使用 Wait For/Wait Until Screen Contain/Click 等 SikuliLibrary 关键字。
6) Test Cases 中至少生成 3 条覆盖核心流程的用例：启动/新建流程图、保存、打开/导出（如果需求里提到）。
7) 如果某些图片缺失，请使用占位变量名（例如 ${{BTN_NEW}}、${{ICON_SAVE}}），并在用例里引用这些变量。
8) 所有超时要可配置（例如 ${{TIMEOUT}}），默认 10 秒；对关键步骤使用 Wait 再 Click。
9) 用例尽量健壮：关键步骤失败时，截图并记录日志（可用 SikuliLibrary 的 Capture Screen / Capture Region 等）。
"""

    def generate_robot_suite(
        self,
        app_name: str,
        app_desc: str,
        requirements: str,
        image_files: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        if not self.api_key:
            return {"success": False, "error": "未配置大模型 API Key（CLAUDE_API_KEY 或 DASHSCOPE_API_KEY）"}

        prompt = self._build_prompt(app_name, app_desc, requirements, image_files)
        if self.use_claude:
            result = self._call_claude(prompt)
        else:
            result = self._call_dashscope(prompt)

        if not result.get("success"):
            return result

        content = _strip_code_fences(result.get("content") or "")
        if "*** Settings ***" not in content or "*** Test Cases ***" not in content:
            # 尽量兜底：返回原文方便排查
            return {
                "success": False,
                "error": "模型输出不是有效的 .robot 内容（缺少关键段落）。请调整需求或重试。",
                "raw": result.get("content"),
            }

        return {
            "success": True,
            "content": content,
            "model": result.get("model"),
        }

    def _call_claude(self, prompt: str) -> Dict[str, Any]:
        try:
            import anthropic

            client = (
                anthropic.Anthropic(api_key=self.api_key, base_url=self.base_url)
                if self.base_url
                else anthropic.Anthropic(api_key=self.api_key)
            )
            msg = client.messages.create(
                model=self.model,
                max_tokens=2500,
                temperature=0.2,
                messages=[{"role": "user", "content": prompt}],
            )
            text = msg.content[0].text if msg and msg.content else ""
            return {"success": True, "content": text, "model": self.model}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _call_dashscope(self, prompt: str) -> Dict[str, Any]:
        try:
            import dashscope

            dashscope.api_key = self.api_key
            resp = dashscope.Generation.call(
                model=self.model,
                prompt=prompt,
                max_tokens=2500,
                temperature=0.2,
            )
            if getattr(resp, "status_code", None) == 200:
                text = resp.output.choices[0].message.content
                return {"success": True, "content": text, "model": self.model}
            return {"success": False, "error": f"DashScope 调用失败: {getattr(resp, 'message', 'unknown')}"}
        except Exception as e:
            return {"success": False, "error": str(e)}


