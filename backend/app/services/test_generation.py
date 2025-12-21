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

    async def generate_catch2_test(self, file_content: str, file_name: str, doc_summary: Optional[str] = None) -> str:
        """为给定的 C++ 代码生成 Catch2 测试用例"""
        # 为避免 format/f-string 与源代码中的花括号冲突，使用占位符再手动替换
        prompt_template = """你是一个专业的 C++ 测试工程师。请为以下 C++ 代码生成使用 Catch2 框架的单元测试用例。

<<DOC_SUMMARY>>

**源代码文件名**: <<FILE_NAME>>
**代码内容**:
```cpp
<<FILE_CONTENT>>
```

**要求**:
1. 使用 Catch2 框架 (混合版 v3)。**必须使用 `#include "catch_amalgamated.hpp"`** 而不是 `<catch2/...>`。
2. **访问权限（极其重要）**：**只能使用 `public` 接口，严禁访问任何 `private` 或 `protected` 成员**：
   - **禁止调用 `protected` 方法**：如 `paint()`, `mousePressEvent()`, `mouseMoveEvent()`, `hoverMoveEvent()`, `contextMenuEvent()` 等所有 protected 事件处理函数。
   - **禁止调用 `private` 方法**：如 `rectWhere()` 等任何 private 函数。
   - **禁止访问 `private` 成员变量**：如 `arrows`, `isHover`, `isChange` 等。
   - **禁止访问 `private` 枚举值**：如 `TF_TopL`, `TF_Top`, `TF_TopR`, `TF_Right`, `TF_BottomR`, `TF_Bottom`, `TF_BottomL`, `TF_Left` 等任何 private 枚举成员。
   - **只能测试 `public` 接口**：构造函数（如果 public）、public 方法、public 属性。如果某个功能只能通过 protected/private 接口访问，请跳过该测试用例。
   - **示例 - 禁止的操作**：
     * ❌ `item.paint(&painter, &option, nullptr)` - paint 是 protected
     * ❌ `group.hoverMoveEvent(&event)` - hoverMoveEvent 是 protected
     * ❌ `group.mouseMoveEvent(&event)` - mouseMoveEvent 是 protected
     * ❌ `auto map = group.rectWhere()` - rectWhere 是 private
     * ❌ `CHECK(item->arrows.size() == 1)` - arrows 是 private
     * ❌ `CHECK(item->isHover == true)` - isHover 是 private
     * ❌ `CHECK(map.contains(DiagramItemGroup::TF_TopL))` - TF_TopL 是 private 枚举
   - **示例 - 允许的操作**：
     * ✅ `DiagramItem item(DiagramItem::Step, nullptr, nullptr)` - 如果构造函数是 public
     * ✅ `CHECK(item.diagramType() == DiagramItem::Step)` - 如果 diagramType() 是 public 方法
     * ✅ `item.setPos(10, 20)` - 如果 setPos 是 public（Qt 的 public 方法）
3. **头文件与类型完整性**：
   - 若某类型在头文件中只有前向声明（如 `class Arrow;`），测试代码必须补充包含实际定义的头文件（如 `#include "arrow.h"`），否则不能实例化或删除该类型。
   - 使用到的 Qt/自定义类型都要包含对应头文件，例如 `#include <QMenu>`, `#include <QGraphicsSceneContextMenuEvent>`, `#include "diagramitem.h"` 等。
4. **严格匹配函数签名 / 若不确定则不要调用**：
   - 构造/函数需要的所有非默认参数必须提供（如 `DiagramItem(Type, QMenu*, ...)` 需传 `nullptr`/对象占位）。
   - 对于指针参数，如果没有合适对象，请传 `nullptr`，不要省略参数。
   - **不要伪造不存在的构造函数**。例：`DiagramPath` 的构造函数需要 5 个参数 (`DiagramItem*, DiagramItem*, DiagramItem::TransformState, DiagramItem::TransformState, QGraphicsItem*`)，如果无法提供合法参数，请跳过这类测试，不要编译一个错误签名。
   - 如果某个类型的正确用法不清楚，宁可跳过该用例，也不要写出不能编译的代码。
5. **Catch2 语法**：在 `CHECK` / `REQUIRE` 中出现逻辑运算（`||`, `&&`）必须加外层双括号，如 `CHECK((a == b || c == d))`。
6. **代码格式与可编译性（必须保证可直接编译）**：
   - 所有构造/函数调用必须写全，行尾有分号，不能留下悬空的括号或未完成的语句。
   - `TEST_CASE` / `SECTION` 的花括号必须成对匹配，文件末尾必须补齐所有右括号。
   - 如果不确定某个构造函数参数或用法，请跳过该用例，**不要**输出无法编译的代码。
   - **重要：确保生成的代码完整，不要中途截断。每个语句、每个函数调用、每个括号都必须完整。**
7. 生成覆盖正常、边界、异常的用例。
8. **只返回 C++ 测试代码**，不写解释或 Markdown。代码必须完整，不能截断。
9. 测试宏使用 `TEST_CASE` 和 `SECTION`。

**最后提醒**：在生成代码前，请仔细检查源代码中的访问修饰符（`public:`, `protected:`, `private:`）。**绝对不要**生成任何访问 protected 或 private 成员的代码。如果某个测试需要访问非 public 成员，请直接跳过该测试用例。

请生成测试代码："""

        # 构建文档要点部分
        doc_summary_section = ""
        if doc_summary:
            doc_summary_section = f"""**项目设计文档要点**:
{doc_summary}

这些要点可以帮助你更好地理解代码的设计意图和功能要求。请在生成测试用例时参考这些要点。

---
"""
        
        prompt = (
            prompt_template
            .replace("<<DOC_SUMMARY>>", doc_summary_section)
            .replace("<<FILE_NAME>>", file_name)
            .replace("<<FILE_CONTENT>>", file_content or "")
        )

        try:
            if self.base_url:
                client = anthropic.Anthropic(api_key=self.api_key, base_url=self.base_url)
            else:
                client = anthropic.Anthropic(api_key=self.api_key)
            
            print(f"📤 正在发送请求到 Claude API 生成测试用例...", file=sys.stderr, flush=True)
            
            message = client.messages.create(
                model=self.model,
                max_tokens=8000,  # 增加到 8000，避免代码被截断
                temperature=0.2,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            # 检查是否因为 token 限制被截断
            stop_reason = getattr(message, 'stop_reason', None)
            if stop_reason == 'max_tokens':
                print(f"⚠️ 警告: 生成的代码可能因 token 限制被截断！", file=sys.stderr, flush=True)
            
            test_code = message.content[0].text
            original_length = len(test_code)
            
            # 清理 Markdown 代码块包裹（如果 AI 还是加了的话）
            # 改进：如果找不到结束标记，保留所有内容
            if "```cpp" in test_code:
                parts = test_code.split("```cpp", 1)
                if len(parts) > 1:
                    remaining = parts[1]
                    if "```" in remaining:
                        test_code = remaining.split("```", 1)[0]
                    else:
                        # 没有结束标记，保留所有内容
                        test_code = remaining
                        print(f"⚠️ 警告: 未找到代码块结束标记，保留所有内容", file=sys.stderr, flush=True)
            elif "```" in test_code:
                parts = test_code.split("```", 1)
                if len(parts) > 1:
                    remaining = parts[1]
                    if "```" in remaining:
                        test_code = remaining.split("```", 1)[0]
                    else:
                        # 没有结束标记，保留所有内容
                        test_code = remaining
                        print(f"⚠️ 警告: 未找到代码块结束标记，保留所有内容", file=sys.stderr, flush=True)
            
            test_code = test_code.strip()
            
            # 基本完整性检查：检查括号是否匹配
            open_braces = test_code.count('{')
            close_braces = test_code.count('}')
            if open_braces != close_braces:
                print(f"⚠️ 警告: 花括号不匹配！开括号: {open_braces}, 闭括号: {close_braces}", file=sys.stderr, flush=True)
            
            # 检查代码是否以不完整的语句结尾
            last_line = test_code.split('\n')[-1].strip() if test_code else ""
            if last_line and not last_line.endswith((';', '}', '{', ')')):
                # 检查是否是未完成的构造/函数调用
                if '::' in last_line or '(' in last_line:
                    print(f"⚠️ 警告: 代码可能不完整，最后一行: {last_line[:50]}...", file=sys.stderr, flush=True)
            
            print(f"✅ AI 测试生成成功！原始长度: {original_length}, 清理后长度: {len(test_code)}", file=sys.stderr, flush=True)
            return test_code
            
        except Exception as e:
            logger.error(f"AI 生成测试失败: {str(e)}")
            print(f"❌ AI 生成测试失败: {str(e)}", file=sys.stderr, flush=True)
            raise Exception(f"AI 生成测试失败: {str(e)}")

