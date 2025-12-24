import os
import sys
import logging
import re
from typing import Dict, Any, List, Optional
from pathlib import Path
import json
import anthropic  # pyright: ignore[reportMissingImports]

from app.core.config import settings
from app.test_ir.schemas import IntegrationTestIR

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
5. **Catch2 语法（极其重要）**：在 `CHECK` / `REQUIRE` 中出现逻辑运算（`||`, `&&`）**必须**加外层双括号！
   - ❌ **错误示例**：`CHECK(a == b || c == d)` - 这会导致编译错误！
   - ❌ **错误示例**：`CHECK(value > 0 && value < 100)` - 这会导致编译错误！
   - ✅ **正确示例**：`CHECK((a == b || c == d))` - 注意双括号！
   - ✅ **正确示例**：`CHECK((value > 0 && value < 100))` - 注意双括号！
   - **规则**：如果断言表达式中包含 `||` 或 `&&`，整个表达式必须用双括号包裹：`CHECK((表达式))` 或 `REQUIRE((表达式))`
   - **检查清单**：生成代码后，检查每一行包含 `||` 或 `&&` 的 `CHECK`/`REQUIRE` 语句，确保它们都有双括号！
6. **代码格式与可编译性（必须保证可直接编译）**：
   - 所有构造/函数调用必须写全，行尾有分号，不能留下悬空的括号或未完成的语句。
   - `TEST_CASE` / `SECTION` 的花括号必须成对匹配，文件末尾必须补齐所有右括号。
   - 如果不确定某个构造函数参数或用法，请跳过该用例，**不要**输出无法编译的代码。
   - **重要：确保生成的代码完整，不要中途截断。每个语句、每个函数调用、每个括号都必须完整。**
7. 生成覆盖正常、边界、异常的用例。
8. **只返回 C++ 测试代码**，不写解释或 Markdown。代码必须完整，不能截断。
9. 测试宏使用 `TEST_CASE` 和 `SECTION`。

**最后提醒**：
1. 在生成代码前，请仔细检查源代码中的访问修饰符（`public:`, `protected:`, `private:`）。**绝对不要**生成任何访问 protected 或 private 成员的代码。
2. **必须检查**：生成代码后，逐行检查所有包含 `||` 或 `&&` 的 `CHECK`/`REQUIRE` 语句，确保它们都使用双括号格式：`CHECK((表达式))` 或 `REQUIRE((表达式))`。这是编译通过的必要条件！
3. 如果某个测试需要访问非 public 成员，请直接跳过该测试用例。

**生成代码后自检清单**：
- [ ] 所有包含 `||` 的 `CHECK`/`REQUIRE` 都使用了双括号？
- [ ] 所有包含 `&&` 的 `CHECK`/`REQUIRE` 都使用了双括号？
- [ ] 没有访问任何 protected 或 private 成员？
- [ ] 所有括号都正确匹配？

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
            
            message = client.messages.create(
                model=self.model,
                max_tokens=4000,
                temperature=0.2,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            test_code = message.content[0].text
            
            # 清理 Markdown 代码块包裹
            if "```cpp" in test_code:
                test_code = test_code.split("```cpp")[1].split("```")[0]
            elif "```" in test_code:
                test_code = test_code.split("```")[1].split("```")[0]
            
            return test_code.strip()
            
        except Exception as e:
            logger.error(f"AI 生成测试失败: {str(e)}")
            raise Exception(f"AI 生成测试失败: {str(e)}")

    async def generate_integration_test_from_code(
        self,
        file_content: str,
        file_name: str,
        project_info: Dict[str, Any],
        additional_info: Optional[str] = None
    ) -> str:
        """分析C++代码并生成集成测试用例（Catch2格式）"""
        
        # 推断可能的头文件名
        header_hints = []
        if file_name.endswith('.cpp'):
            base_name = file_name[:-4]
            header_hints.append(f'{base_name}.h')
            header_hints.append(f'{base_name}.hpp')
        elif file_name.endswith('.cc') or file_name.endswith('.cxx'):
            base_name = file_name.rsplit('.', 1)[0]
            header_hints.append(f'{base_name}.h')
            header_hints.append(f'{base_name}.hpp')
        
        header_hint_text = ""
        if header_hints:
            header_hint_text = f"\n   **提示**：源代码文件是 `{file_name}`，通常对应的头文件是 `{header_hints[0]}` 或 `{header_hints[1] if len(header_hints) > 1 else header_hints[0]}`。如果测试代码需要调用源代码中的类或函数，请包含相应的头文件。"
        
        prompt = f"""你是一个专业的 C++ 集成测试工程师。请分析以下 C++ 代码，识别其中的类、函数、模块之间的交互，然后生成使用 Catch2 框架的集成测试用例。

**源代码文件名**: {file_name}
**项目信息**:
- 项目名称: {project_info.get('name', 'Unknown')}
- 编程语言: {project_info.get('language', 'cpp')}

**代码内容**:
```cpp
{file_content}
```

**重要约束**:
1. **绝对禁止包含 main 函数**：执行环境已经提供了 main 函数和 QApplication 初始化，你只需要生成测试用例代码。
2. **禁止使用外部 HTTP 客户端库**：不要使用 curl、httpx、libcurl 等 HTTP 客户端库，这些库在编译环境中不可用。
3. **只使用标准库和 Qt**：只能使用 C++ 标准库（<string>, <vector>, <iostream>, <fstream>, <memory> 等）和 Qt 库（如果代码使用了 Qt）。
4. **专注于代码内部集成**：测试代码中类之间、模块之间、函数之间的交互，而不是外部 HTTP API。
5. **访问权限检查**：**严禁调用受保护 (protected) 或私有 (private) 的成员函数**。只能测试公共 (public) 接口。如果函数是 protected（如 `paint()`, `mousePressEvent()`），请通过公共接口间接测试或跳过。
6. **严格分析函数签名**：生成的测试代码必须完全匹配函数参数。
   - **检查构造函数**：如果构造函数有多个参数（如 `DiagramItem(Type, QMenu*, ...)`），你**必须**提供所有非默认参数。
   - **对于指针参数**：如果你没有合适的资源对象（如 `QMenu*`），请传递 `nullptr`。**严禁遗漏参数**导致 "no matching function" 错误。

**要求**:
1. **代码分析**：
   - 仔细分析代码，识别类、函数、模块之间的交互关系
   - 识别代码中的函数调用流程、数据流、对象创建和销毁
   - 识别代码中的文件操作、Qt 组件交互等集成点
   - 分析代码的执行流程和依赖关系

2. **测试用例生成**：
   - 使用 Catch2 框架 (混合版 v3)。**必须使用 `#include "catch_amalgamated.hpp"`** 而不是 `<catch2/...>`。
   - **绝对不要包含 main 函数**，执行环境已经提供了。
   - 生成集成测试用例，测试代码内部不同组件之间的交互：
     * 测试多个类之间的协作
     * 测试函数调用链
     * 测试数据在不同模块之间的传递
     * 测试 Qt 组件之间的交互（如果代码使用了 Qt）
     * 测试文件操作（使用标准库的 <fstream>）
   - **禁止使用 HTTP 客户端库**（如 curl、httpx），这些库在编译环境中不可用。

3. **测试组织**：
   - 使用 `TEST_CASE` 定义测试用例
   - 使用 `SECTION` 组织不同的测试步骤
   - 每个测试用例应该覆盖一个完整的集成流程

4. **验证和断言**：
   - 使用 Catch2 的断言宏（CHECK、REQUIRE等）验证结果
   - 验证函数返回值、对象状态、数据内容等
   - 验证文件操作的结果（如果涉及文件操作）

5. **Catch2 语法规范**：
   - 在 `CHECK` 或 `REQUIRE` 中进行逻辑运算（如 `||`, `&&`）时，**必须在外层加双括号**，例如 `CHECK((a == b || c == d))`。

6. **依赖处理**：
   - **必须包含被测试代码的头文件**：如果测试代码需要调用源代码中的类或函数，必须包含相应的头文件。
     * 如果源代码文件是 `mainwindow.cpp`，需要包含 `#include "mainwindow.h"` 或 `#include "mainwindow.hpp"`
     * 如果源代码文件是 `diagramitem.cpp`，需要包含 `#include "diagramitem.h"`
     * **这是最重要的，缺少头文件会导致编译失败**{header_hint_text}
   - 如果代码使用 Qt，需要包含相应的头文件（如 `#include <QWidget>`, `#include <QString>` 等）
   - **不要初始化 QApplication**，执行环境已经初始化了
   - 只能使用标准库和 Qt 库，不要使用其他第三方库

7. **代码生成最佳实践**：
   - **先检查代码结构**：分析代码中有哪些公共接口可以测试
   - **使用简单的测试用例**：优先测试简单的函数调用和返回值验证
   - **避免复杂的依赖**：如果代码依赖外部资源，使用模拟或简化处理
   - **使用 nullptr 处理指针**：如果无法创建真实对象，使用 nullptr 并测试空指针情况
   - **确保至少生成一个 TEST_CASE**：必须包含至少一个有效的 `TEST_CASE("测试名称")` 定义

8. **只返回生成的 C++ 测试代码内容**，不要包含任何解释性文字或 Markdown 代码块外的内容。
9. **绝对不要包含 main 函数**。
10. **必须生成可编译的代码**：确保生成的代码语法正确，包含所有必要的头文件，函数调用参数匹配。

**示例结构**:
```cpp
#include "catch_amalgamated.hpp"
#include <string>
#include <vector>
#include <fstream>
// 如果代码使用 Qt，包含相应的 Qt 头文件
// #include <QWidget>
// #include <QString>

// 包含被测试代码的头文件（如果需要）
// #include "your_header.hpp"

TEST_CASE("集成测试: 类之间的交互") {{
    SECTION("测试类A和类B的协作") {{
        // 创建对象
        // 调用函数
        // 验证结果
        CHECK(/* 验证条件 */);
    }}
    
    SECTION("测试函数调用链") {{
        // 调用函数1
        // 调用函数2
        // 验证最终结果
        REQUIRE(/* 验证条件 */);
    }}
    
    SECTION("测试文件操作") {{
        // 使用标准库进行文件操作
        std::ofstream file("test.txt");
        // 执行操作
        // 验证结果
        CHECK(/* 验证条件 */);
    }}
}}
```

{f"**额外信息**: {additional_info}" if additional_info else ""}

请分析代码并生成集成测试用例："""

        try:
            if self.base_url:
                client = anthropic.Anthropic(api_key=self.api_key, base_url=self.base_url)
            else:
                client = anthropic.Anthropic(api_key=self.api_key)
            
            print(f"📤 正在发送请求到 Claude API 分析代码并生成集成测试用例...", file=sys.stderr, flush=True)
            
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
            
<<<<<<< HEAD
            test_code = test_code.strip()
            
            # 自动修复 Catch2 断言中的逻辑运算符问题
            # 使用更简单直接的方法：正则表达式替换
            def fix_logical_operators_in_assertions(code: str) -> str:
                """修复 Catch2 断言中的逻辑运算符问题"""
                original_code = code
                fixes_count = 0
                
                # 首先，找到所有包含逻辑运算符的 CHECK/REQUIRE 语句
                # 使用多行模式，逐行处理
                lines = code.split('\n')
                fixed_lines = []
                
                for line_num, line in enumerate(lines, 1):
                    original_line = line
                    stripped = line.strip()
                    
                    # 跳过注释和空行
                    if not stripped or stripped.startswith('//') or stripped.startswith('/*'):
                        fixed_lines.append(line)
                        continue
                    
                    # 检查是否包含 CHECK 或 REQUIRE，并且包含 || 或 &&
                    if ('CHECK' in stripped or 'REQUIRE' in stripped) and ('||' in stripped or '&&' in stripped):
                        # 检查是否已经用双括号包裹
                        if re.search(r'(CHECK|REQUIRE)\s*\(\([^)]*(?:\|\||&&)', stripped):
                            # 已经正确包裹，跳过
                            fixed_lines.append(line)
                            continue
                        
                        # 使用更直接的方法：找到 CHECK/REQUIRE 后的第一个 ( 和匹配的 )
                        # 然后检查内容是否包含逻辑运算符，如果是则添加括号
                        new_line = line
                        pos = 0
                        
                        while pos < len(new_line):
                            # 查找 CHECK 或 REQUIRE
                            check_idx = new_line.find('CHECK', pos)
                            require_idx = new_line.find('REQUIRE', pos)
                            
                            if check_idx == -1 and require_idx == -1:
                                break
                            
                            # 找到最近的宏
                            if check_idx != -1 and (require_idx == -1 or check_idx < require_idx):
                                macro_start = check_idx
                                macro_end = check_idx + 5
                                macro = 'CHECK'
                            else:
                                macro_start = require_idx
                                macro_end = require_idx + 7
                                macro = 'REQUIRE'
                            
                            # 跳过空格，找到左括号
                            paren_start = macro_end
                            while paren_start < len(new_line) and new_line[paren_start] in ' \t':
                                paren_start += 1
                            
                            if paren_start >= len(new_line) or new_line[paren_start] != '(':
                                pos = macro_end
                                continue
                            
                            # 使用栈找到匹配的右括号
                            stack = 0
                            paren_end = -1
                            for i in range(paren_start, len(new_line)):
                                if new_line[i] == '(':
                                    stack += 1
                                elif new_line[i] == ')':
                                    stack -= 1
                                    if stack == 0:
                                        paren_end = i
                                        break
                            
                            if paren_end > paren_start:
                                content = new_line[paren_start + 1:paren_end]
                                
                                # 检查内容中是否包含 || 或 &&
                                if ('||' in content or '&&' in content):
                                    # 检查是否已经有双括号包裹
                                    content_stripped = content.strip()
                                    if not (content_stripped.startswith('(') and content_stripped.endswith(')')):
                                        # 需要修复：在内容外添加括号
                                        before = new_line[:paren_start + 1]
                                        after = new_line[paren_end:]
                                        new_line = before + '(' + content + ')' + after
                                        
                                        fixes_count += 1
                                        print(f"🔧 修复逻辑运算符 (行 {line_num}): {original_line.strip()[:70]}...", file=sys.stderr, flush=True)
                                        print(f"   -> {new_line.strip()[:70]}...", file=sys.stderr, flush=True)
                                        # 修复后重新开始扫描（因为位置改变了）
                                        break
                            
                            pos = macro_end
                        
                        if new_line != line:
                            print(f"   -> {new_line.strip()[:70]}...", file=sys.stderr, flush=True)
                        
                        fixed_lines.append(new_line)
                    else:
                        fixed_lines.append(line)
                
                if fixes_count > 0:
                    print(f"✅ 自动修复了 {fixes_count} 处逻辑运算符问题", file=sys.stderr, flush=True)
                else:
                    # 即使没有修复，也检查一下是否有遗漏
                    if '||' in code or '&&' in code:
                        print(f"⚠️ 检测到逻辑运算符，但可能未完全修复，请检查代码", file=sys.stderr, flush=True)
                
                return '\n'.join(fixed_lines)
            
            # 执行自动修复
            test_code = fix_logical_operators_in_assertions(test_code)
            
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
=======
            # 移除可能的 main 函数（双重保险）
            lines = test_code.split('\n')
            filtered_lines = []
            skip_main = False
            brace_count = 0
            for line in lines:
                # 检测 main 函数开始
                if 'int main(' in line or 'void main(' in line:
                    skip_main = True
                    brace_count = line.count('{') - line.count('}')
                    continue
                
                if skip_main:
                    brace_count += line.count('{') - line.count('}')
                    if brace_count <= 0:
                        skip_main = False
                    continue
                
                filtered_lines.append(line)
            
            test_code = '\n'.join(filtered_lines)
            
            print(f"✅ AI 集成测试生成成功！长度: {len(test_code)}", file=sys.stderr, flush=True)
            return test_code.strip()
>>>>>>> origin/tzf
            
        except Exception as e:
            logger.error(f"AI 生成集成测试失败: {str(e)}")
            print(f"❌ AI 生成集成测试失败: {str(e)}", file=sys.stderr, flush=True)
            raise Exception(f"AI 生成集成测试失败: {str(e)}")

    async def execute_tests_with_ai(
        self,
        test_code: str,
        source_code: str,
        source_file_name: str,
        project_info: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """使用 AI 分析并模拟执行测试用例，返回执行结果"""
        
        prompt = f"""你是一个专业的测试执行分析专家。请分析以下测试用例，模拟执行它们，并返回详细的执行结果。

**源代码文件**: {source_file_name}
**源代码内容**:
```cpp
{source_code[:3000]}
```

**测试用例代码**:
```cpp
{test_code[:3000]}
```

{f"**项目信息**: {project_info}" if project_info else ""}

请执行以下任务：

1. **分析测试用例**：
   - 识别所有 TEST_CASE 和 SECTION
   - 理解每个测试用例的目的
   - 分析测试用例的逻辑

2. **模拟执行**：
   - 根据源代码和测试用例，推断每个测试用例的执行结果
   - 判断测试是否会通过或失败
   - 如果失败，分析失败原因

3. **返回结果**（请严格按照以下JSON格式返回，不要添加任何其他文字）：
```json
{{
  "success": true/false,
  "summary": {{
    "total": 测试用例总数,
    "passed": 通过的用例数,
    "failed": 失败的用例数,
    "assertions": {{
      "successes": 成功的断言数,
      "failures": 失败的断言数
    }},
    "cases": [
      {{
        "name": "测试用例名称",
        "tags": "标签",
        "successes": 通过的断言数,
        "failures": 失败的断言数,
        "sections": [
          {{
            "name": "Section名称",
            "successes": 通过的断言数,
            "failures": 失败的断言数
          }}
        ]
      }}
    ]
  }},
  "logs": "详细的执行日志，包括每个测试用例的执行过程和结果",
  "analysis": "对测试结果的深度分析，包括：测试覆盖情况、发现的问题、改进建议等"
}}
```

**重要**：
- 请仔细分析源代码，确保测试结果符合代码的实际行为
- 如果测试用例调用了不存在的函数或访问了私有成员，标记为失败
- 如果测试用例逻辑有误，也要标记为失败
- 请用中文编写日志和分析内容
- 只返回JSON格式的结果，不要添加Markdown代码块标记"""

        try:
            if self.base_url:
                client = anthropic.Anthropic(api_key=self.api_key, base_url=self.base_url)
            else:
                client = anthropic.Anthropic(api_key=self.api_key)
            
            print(f"🤖 正在使用 AI 执行测试用例...", file=sys.stderr, flush=True)
            
            message = client.messages.create(
                model=self.model,
                max_tokens=4000,
                temperature=0.2,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            response_text = message.content[0].text.strip()
            
            # 尝试提取JSON（可能被Markdown代码块包裹）
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()
            
            # 解析JSON
            try:
                result = json.loads(response_text)
                print(f"✅ AI 执行完成", file=sys.stderr, flush=True)
                
                # 确保返回格式符合预期
                if "summary" not in result:
                    result["summary"] = {
                        "total": 0,
                        "passed": 0,
                        "failed": 0,
                        "assertions": {"successes": 0, "failures": 0},
                        "cases": []
                    }
                
                return result
                
            except json.JSONDecodeError as e:
                logger.error(f"AI 返回的JSON格式无效: {str(e)}")
                logger.error(f"响应内容: {response_text[:500]}")
                # 如果JSON解析失败，返回一个错误结果
                return {
                    "success": False,
                    "summary": {
                        "total": 0,
                        "passed": 0,
                        "failed": 0,
                        "assertions": {"successes": 0, "failures": 0},
                        "cases": []
                    },
                    "logs": f"AI 执行失败: JSON解析错误\n\nAI返回内容:\n{response_text}",
                    "analysis": "AI 返回的结果格式不正确，无法解析。请检查AI配置或重试。"
                }
            
        except Exception as e:
            logger.error(f"AI 执行测试失败: {str(e)}")
            print(f"❌ AI 执行测试失败: {str(e)}", file=sys.stderr, flush=True)
            return {
                "success": False,
                "summary": {
                    "total": 0,
                    "passed": 0,
                    "failed": 0,
                    "assertions": {"successes": 0, "failures": 0},
                    "cases": []
                },
                "logs": f"AI 执行失败: {str(e)}",
                "analysis": f"AI 执行测试时发生错误: {str(e)}"
            }

    async def generate_integration_test_from_project(
        self,
        project_files: Dict[str, str],
        project_info: Dict[str, Any],
        additional_info: Optional[str] = None
    ) -> str:
        """分析整个项目的代码并生成集成测试用例"""
        
        # 构建项目代码概览
        files_summary = []
        total_lines = 0
        for file_path, content in list(project_files.items())[:30]:  # 限制文件数量
            lines = content.split('\n')
            total_lines += len(lines)
            files_summary.append(f"- {file_path}: {len(lines)} 行")
        
        project_overview = f"""
**项目包含 {len(project_files)} 个源代码文件，共约 {total_lines} 行代码**

**主要文件列表**:
{chr(10).join(files_summary[:20])}
{f'... 还有 {len(project_files) - 20} 个文件' if len(project_files) > 20 else ''}
"""
        
        # 构建所有源代码内容（限制长度）
        all_code_content = ""
        for file_path, content in list(project_files.items())[:15]:  # 限制文件数量
            all_code_content += f"\n\n// ========== {file_path} ==========\n{content[:1000]}\n"  # 每个文件限制1000字符
        
        prompt = f"""你是一个专业的 C++ 集成测试工程师。请分析以下整个项目的代码，识别其中的类、函数、模块之间的交互，然后生成使用 Catch2 框架的集成测试用例。

**项目信息**:
- 项目名称: {project_info.get('name', 'Unknown')}
- 编程语言: {project_info.get('language', 'cpp')}
- 源代码路径: {project_info.get('source_path', 'Unknown')}

{project_overview}

**项目源代码内容**:
```cpp
{all_code_content[:8000]}  # 限制总长度
```

**重要约束**:
1. **绝对禁止包含 main 函数**：执行环境已经提供了 main 函数和 QApplication 初始化，你只需要生成测试用例代码。
2. **禁止使用外部 HTTP 客户端库**：不要使用 curl、httpx、libcurl 等 HTTP 客户端库。
3. **只使用标准库和 Qt**：只能使用 C++ 标准库和 Qt 库。
4. **专注于项目级别的集成测试**：
   - 测试不同类之间的协作
   - 测试模块之间的交互
   - 测试数据流和函数调用链
   - 测试整个系统的集成点
5. **访问权限检查**：**严禁调用受保护 (protected) 或私有 (private) 的成员函数**。只能测试公共 (public) 接口。
6. **严格分析函数签名**：生成的测试代码必须完全匹配函数参数。

**要求**:
1. **项目分析**：
   - 分析项目的整体架构
   - 识别主要的类和模块
   - 理解类之间的依赖关系
   - 识别关键的集成点

2. **测试用例生成**：
   - 使用 Catch2 框架 (混合版 v3)。**必须使用 `#include "catch_amalgamated.hpp"`**。
   - **绝对不要包含 main 函数**。
   - 生成项目级别的集成测试用例：
     * 测试多个类之间的协作
     * 测试跨模块的函数调用
     * 测试数据在不同模块之间的传递
     * 测试 Qt 组件之间的交互（如果项目使用了 Qt）
   - 确保测试覆盖项目的关键集成点

3. **测试组织**：
   - 使用 `TEST_CASE` 定义测试用例
   - 使用 `SECTION` 组织不同的测试步骤
   - 每个测试用例应该覆盖一个完整的集成流程

4. **依赖处理**：
   - 包含必要的头文件
   - 如果项目使用 Qt，包含相应的 Qt 头文件
   - **不要初始化 QApplication**，执行环境已经初始化了

5. **代码生成最佳实践**：
   - 优先测试项目的核心功能和关键集成点
   - 使用简单的测试用例，避免复杂的依赖
   - 使用 nullptr 处理指针参数
   - **确保至少生成一个 TEST_CASE**

8. **只返回生成的 C++ 测试代码内容**，不要包含任何解释性文字或 Markdown 代码块外的内容。
9. **绝对不要包含 main 函数**。
10. **必须生成可编译的代码**：确保生成的代码语法正确，包含所有必要的头文件。

{f"**额外信息**: {additional_info}" if additional_info else ""}

请分析整个项目并生成集成测试用例："""

        try:
            if self.base_url:
                client = anthropic.Anthropic(api_key=self.api_key, base_url=self.base_url)
            else:
                client = anthropic.Anthropic(api_key=self.api_key)
            
            print(f"📤 正在发送请求到 Claude API 分析整个项目并生成集成测试用例...", file=sys.stderr, flush=True)
            
            message = client.messages.create(
                model=self.model,
                max_tokens=4000,
                temperature=0.2,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            test_code = message.content[0].text
            
            # 清理 Markdown 代码块包裹
            if "```cpp" in test_code:
                test_code = test_code.split("```cpp")[1].split("```")[0]
            elif "```" in test_code:
                test_code = test_code.split("```")[1].split("```")[0]
            
            # 移除可能的 main 函数
            lines = test_code.split('\n')
            filtered_lines = []
            skip_main = False
            brace_count = 0
            for line in lines:
                if 'int main(' in line or 'void main(' in line:
                    skip_main = True
                    brace_count = line.count('{') - line.count('}')
                    continue
                
                if skip_main:
                    brace_count += line.count('{') - line.count('}')
                    if brace_count <= 0:
                        skip_main = False
                    continue
                
                filtered_lines.append(line)
            
            test_code = '\n'.join(filtered_lines)
            
            print(f"✅ AI 项目级别集成测试生成成功！长度: {len(test_code)}", file=sys.stderr, flush=True)
            return test_code.strip()
            
        except Exception as e:
            logger.error(f"AI 生成项目级别集成测试失败: {str(e)}")
            print(f"❌ AI 生成项目级别集成测试失败: {str(e)}", file=sys.stderr, flush=True)
            raise Exception(f"AI 生成项目级别集成测试失败: {str(e)}")
