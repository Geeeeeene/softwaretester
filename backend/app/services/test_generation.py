import os
import sys
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path
import anthropic

from app.core.config import settings

logger = logging.getLogger(__name__)

class TestGenerationService:
    """使用 AI 生成测试用例的服务"""
    
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None, base_url: Optional[str] = None):
        self.api_key = api_key or settings.CLAUDE_API_KEY
        self.model = model or settings.CLAUDE_MODEL
        self.base_url = base_url or settings.CLAUDE_BASE_URL
        
        if not self.api_key:
            logger.warning("CLAUDE_API_KEY 未设置，AI 测试生成功能将不可用")

    async def generate_catch2_test(self, file_content: str, file_name: str) -> str:
        """为给定的 C++ 代码生成 Catch2 测试用例"""
        prompt = f"""你是一个专业的 C++ 测试工程师。请为以下 C++ 代码生成使用 Catch2 框架的单元测试用例。

**源代码文件名**: {file_name}
**代码内容**:
```cpp
{file_content}
```

**要求**:
1. 使用 Catch2 框架 (混合版 v3)。**必须使用 `#include "catch_amalgamated.hpp"`** 而不是 `<catch2/...>`。
2. **重要：访问权限检查**。生成的测试代码**严禁调用受保护 (protected) 或私有 (private) 的成员函数**。如果 `paint()`、`mousePressEvent()` 等函数被声明为 protected，请不要直接调用它们。
3. **重要：严格分析函数签名**。生成的测试代码必须完全匹配函数参数。
   - **检查构造函数**：如果构造函数有多个参数（如 `DiagramItem(Type, QMenu*, ...)`），你**必须**提供所有非默认参数。
   - **对于指针参数**：如果你没有合适的资源对象（如 `QMenu*`），请传递 `nullptr`。**严禁遗漏参数**导致 "no matching function" 错误。
4. 如果代码使用 Qt 类，必须包含相应的头文件（如 `#include <QPainter>`, `#include <QMenu>`）。
5. **Catch2 语法规范**：在 `CHECK` 或 `REQUIRE` 中进行逻辑运算（如 `||`, `&&`）时，**必须在外层加双括号**，例如 `CHECK((a == b || c == d))`。
5. 生成全面的测试用例，覆盖正常情况、边界情况和异常情况。
6. **只返回生成的 C++ 测试代码内容**，不要包含任何解释性文字或 Markdown 代码块块外的内容。
7. 测试宏使用 `TEST_CASE` 和 `SECTION`。

请生成测试代码："""

        try:
            if self.base_url:
                client = anthropic.Anthropic(api_key=self.api_key, base_url=self.base_url)
            else:
                client = anthropic.Anthropic(api_key=self.api_key)
            
            print(f"📤 正在发送请求到 Claude API 生成测试用例...", file=sys.stderr, flush=True)
            
            message = client.messages.create(
                model=self.model,
                max_tokens=4000,
                temperature=0.2,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            test_code = message.content[0].text
            
            # 清理 Markdown 代码块包裹（如果 AI 还是加了的话）
            if "```cpp" in test_code:
                test_code = test_code.split("```cpp")[1].split("```")[0]
            elif "```" in test_code:
                test_code = test_code.split("```")[1].split("```")[0]
            
            print(f"✅ AI 测试生成成功！长度: {len(test_code)}", file=sys.stderr, flush=True)
            return test_code.strip()
            
        except Exception as e:
            logger.error(f"AI 生成测试失败: {str(e)}")
            print(f"❌ AI 生成测试失败: {str(e)}", file=sys.stderr, flush=True)
            raise Exception(f"AI 生成测试失败: {str(e)}")

