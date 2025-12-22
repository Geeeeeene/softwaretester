import os
import sys
import logging
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

    async def generate_integration_test(
        self, 
        test_ir: IntegrationTestIR,
        project_info: Dict[str, Any],
        additional_info: Optional[str] = None
    ) -> str:
        """为集成测试IR生成Catch2格式的测试用例"""
        
        # 构建测试IR的JSON描述
        test_ir_json = {
            "name": test_ir.name,
            "description": test_ir.description,
            "flow": [
                {
                    "name": endpoint.name,
                    "url": endpoint.url,
                    "method": endpoint.method,
                    "headers": endpoint.headers,
                    "body": endpoint.body
                }
                for endpoint in test_ir.flow
            ],
            "validations": [
                {
                    "type": v.type,
                    "expected": v.expected,
                    "actual": v.actual,
                    "message": v.message
                }
                for v in test_ir.validations
            ],
            "required_services": test_ir.required_services,
            "tags": test_ir.tags,
            "priority": test_ir.priority
        }
        
        prompt = f"""你是一个专业的 C++ 集成测试工程师。请根据以下集成测试需求，生成使用 Catch2 框架的集成测试用例。

**项目信息**:
- 项目名称: {project_info.get('name', 'Unknown')}
- 编程语言: {project_info.get('language', 'cpp')}

**集成测试需求**:
```json
{json.dumps(test_ir_json, indent=2, ensure_ascii=False)}
```

**要求**:
1. 使用 Catch2 框架 (混合版 v3)。**必须使用 `#include "catch_amalgamated.hpp"`** 而不是 `<catch2/...>`。
2. 使用 HTTP 客户端库发送请求。推荐使用 `httpx` 的 C++ 版本或 `curl` 库，如果没有，可以使用 `std::filesystem` 和系统调用。
3. 对于每个服务端点（flow中的每个端点）：
   - 发送对应的 HTTP 请求（GET/POST/PUT/DELETE/PATCH）
   - 设置请求头（headers）
   - 发送请求体（body，如果是POST/PUT/PATCH）
   - 接收响应
4. 对于每个验证点（validations中的每个验证）：
   - 使用 Catch2 的断言宏（CHECK、REQUIRE等）验证响应
   - 根据验证类型（equals、not_equals、contains等）进行相应的断言
   - 如果验证失败，输出有意义的错误消息
5. **Catch2 语法规范**：在 `CHECK` 或 `REQUIRE` 中进行逻辑运算（如 `||`, `&&`）时，**必须在外层加双括号**，例如 `CHECK((a == b || c == d))`。
6. 测试用例应该组织为：
   - 使用 `TEST_CASE` 定义测试用例
   - 使用 `SECTION` 组织不同的测试步骤
7. 如果项目使用 Qt，需要包含相应的头文件并初始化 QApplication（如果需要）。
8. **只返回生成的 C++ 测试代码内容**，不要包含任何解释性文字或 Markdown 代码块外的内容。

**示例结构**:
```cpp
#include "catch_amalgamated.hpp"
#include <string>
#include <vector>
// 根据需要包含HTTP客户端库

TEST_CASE("测试用例名称") {{
    // 初始化（如果需要）
    
    SECTION("步骤1: 调用端点1") {{
        // 发送HTTP请求
        // 验证响应
    }}
    
    SECTION("步骤2: 调用端点2") {{
        // 发送HTTP请求
        // 验证响应
    }}
}}
```

{f"**额外信息**: {additional_info}" if additional_info else ""}

请生成测试代码："""

        try:
            if self.base_url:
                client = anthropic.Anthropic(api_key=self.api_key, base_url=self.base_url)
            else:
                client = anthropic.Anthropic(api_key=self.api_key)
            
            print(f"📤 正在发送请求到 Claude API 生成集成测试用例...", file=sys.stderr, flush=True)
            
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
            
            print(f"✅ AI 集成测试生成成功！长度: {len(test_code)}", file=sys.stderr, flush=True)
            return test_code.strip()
            
        except Exception as e:
            logger.error(f"AI 生成集成测试失败: {str(e)}")
            print(f"❌ AI 生成集成测试失败: {str(e)}", file=sys.stderr, flush=True)
            raise Exception(f"AI 生成集成测试失败: {str(e)}")

    async def generate_integration_test_from_code(
        self,
        file_content: str,
        file_name: str,
        project_info: Dict[str, Any],
        additional_info: Optional[str] = None
    ) -> str:
        """分析C++代码并生成集成测试用例（Catch2格式）"""
        
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
   - 如果代码使用 Qt，需要包含相应的头文件（如 `#include <QWidget>`, `#include <QString>` 等）
   - **不要初始化 QApplication**，执行环境已经初始化了
   - 只能使用标准库和 Qt 库，不要使用其他第三方库

7. **只返回生成的 C++ 测试代码内容**，不要包含任何解释性文字或 Markdown 代码块外的内容。
8. **绝对不要包含 main 函数**。

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
            
        except Exception as e:
            logger.error(f"AI 生成集成测试失败: {str(e)}")
            print(f"❌ AI 生成集成测试失败: {str(e)}", file=sys.stderr, flush=True)
            raise Exception(f"AI 生成集成测试失败: {str(e)}")

