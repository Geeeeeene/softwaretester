"""Test IR Schema定义

统一的测试中间表示格式，支持多种测试类型
"""
from typing import List, Dict, Any, Optional, Literal, Union
from pydantic import BaseModel, Field


# ============ UI测试IR ============

class UIAction(BaseModel):
    """UI操作"""
    type: Literal["click", "input", "select", "wait", "assert", "custom"]
    target: str = Field(..., description="目标元素选择器或描述")
    value: Optional[Any] = Field(None, description="操作值（输入文本、选择项等）")
    timeout: Optional[int] = Field(5000, description="超时时间（毫秒）")
    description: Optional[str] = None


class UITestIR(BaseModel):
    """UI测试IR"""
    type: Literal["ui"] = "ui"
    name: str = Field(..., description="测试用例名称")
    description: Optional[str] = None
    
    # 前置条件
    preconditions: List[str] = Field(default_factory=list)
    
    # 测试步骤
    steps: List[UIAction] = Field(..., description="测试步骤序列")
    
    # 期望结果
    expected_results: List[str] = Field(default_factory=list)
    
    # 元数据
    tags: List[str] = Field(default_factory=list)
    priority: Literal["low", "medium", "high", "critical"] = "medium"
    estimated_duration: Optional[int] = Field(None, description="预计执行时间（秒）")


# ============ 单元测试IR ============

class FunctionUnderTest(BaseModel):
    """被测函数"""
    name: str
    file_path: str
    line_number: Optional[int] = None
    signature: Optional[str] = None


class TestInput(BaseModel):
    """测试输入"""
    parameters: Dict[str, Any] = Field(default_factory=dict)
    mock_objects: Dict[str, Any] = Field(default_factory=dict)


class TestAssertion(BaseModel):
    """测试断言"""
    type: Literal["equals", "not_equals", "contains", "throws", "custom"]
    expected: Any
    actual: Optional[str] = Field(None, description="实际值表达式")
    message: Optional[str] = None


class UnitTestIR(BaseModel):
    """单元测试IR"""
    type: Literal["unit"] = "unit"
    name: str
    description: Optional[str] = None
    
    # 被测函数
    function_under_test: FunctionUnderTest
    
    # 测试输入
    inputs: TestInput
    
    # 断言
    assertions: List[TestAssertion]
    
    # 覆盖率目标
    coverage_target: Optional[float] = Field(None, ge=0.0, le=1.0)
    
    # 元数据
    tags: List[str] = Field(default_factory=list)
    priority: Literal["low", "medium", "high", "critical"] = "medium"


# ============ 集成测试IR ============

class ServiceEndpoint(BaseModel):
    """服务端点"""
    name: str
    url: str
    method: Literal["GET", "POST", "PUT", "DELETE", "PATCH"]
    headers: Dict[str, str] = Field(default_factory=dict)
    body: Optional[Dict[str, Any]] = None


class IntegrationTestIR(BaseModel):
    """集成测试IR"""
    type: Literal["integration"] = "integration"
    name: str
    description: Optional[str] = None
    
    # 测试流程
    flow: List[ServiceEndpoint]
    
    # 验证点
    validations: List[TestAssertion]
    
    # 环境要求
    required_services: List[str] = Field(default_factory=list)
    
    # 元数据
    tags: List[str] = Field(default_factory=list)
    priority: Literal["low", "medium", "high", "critical"] = "medium"


# ============ 静态分析IR ============

class StaticAnalysisRule(BaseModel):
    """静态分析规则"""
    rule_id: str
    severity: Literal["info", "warning", "error", "critical"]
    category: str
    enabled: bool = True


class StaticAnalysisIR(BaseModel):
    """静态分析IR"""
    type: Literal["static"] = "static"
    name: str
    description: Optional[str] = None
    
    # 分析工具（clazy 或 cppcheck）
    tool: Literal["clazy", "cppcheck"] = Field("cppcheck", description="使用的静态分析工具")
    
    # 分析目标
    target_files: List[str] = Field(default_factory=list)
    target_directories: List[str] = Field(default_factory=list)
    
    # 分析规则
    rules: List[StaticAnalysisRule] = Field(default_factory=list)
    
    # 工具特定配置
    checks: Optional[List[str]] = Field(None, description="Clazy 检查项（如 ['level1', 'level2']）")
    enable: Optional[str] = Field(None, description="Cppcheck 启用的检查类型（如 'all', 'error', 'warning'）")
    suppress: Optional[List[str]] = Field(None, description="Cppcheck 抑制的警告列表")
    
    # 排除项
    exclude_patterns: List[str] = Field(default_factory=list)
    
    # 元数据
    tags: List[str] = Field(default_factory=list)


# ============ 统一Test IR ============

class TestIR(BaseModel):
    """统一Test IR（联合类型）"""
    ir_version: str = "1.0"
    test: Union[UITestIR, UnitTestIR, IntegrationTestIR, StaticAnalysisIR] = Field(
        ..., discriminator="type"
    )
    
    # 通用元数据
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


# ============ 批量Test IR ============

class BatchTestIR(BaseModel):
    """批量Test IR"""
    batch_name: str
    description: Optional[str] = None
    tests: List[TestIR]
    parallel_execution: bool = False
    max_workers: int = Field(1, ge=1, le=10)

