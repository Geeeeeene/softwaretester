"""
Test IR (Intermediate Representation) Schema
统一的测试中间表示层，用于解耦不同测试类型和执行器
"""
from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field
from enum import Enum


class TestType(str, Enum):
    """测试类型"""
    UI = "ui"
    UNIT = "unit"
    INTEGRATION = "integration"
    STATIC = "static"
    PERFORMANCE = "performance"


class AssertionType(str, Enum):
    """断言类型"""
    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    CONTAINS = "contains"
    NOT_CONTAINS = "not_contains"
    GREATER_THAN = "greater_than"
    LESS_THAN = "less_than"
    EXISTS = "exists"
    NOT_EXISTS = "not_exists"
    VISIBLE = "visible"
    NOT_VISIBLE = "not_visible"


class UIActionType(str, Enum):
    """UI操作类型"""
    CLICK = "click"
    INPUT = "input"
    SELECT = "select"
    HOVER = "hover"
    DRAG = "drag"
    WAIT = "wait"
    NAVIGATE = "navigate"
    SCREENSHOT = "screenshot"


# ========== UI Test IR ==========
class UILocator(BaseModel):
    """UI元素定位器"""
    type: str = Field(..., description="定位器类型: id, xpath, css, text等")
    value: str = Field(..., description="定位器值")
    timeout: Optional[int] = Field(5000, description="超时时间(ms)")


class UIAction(BaseModel):
    """UI操作"""
    action: UIActionType = Field(..., description="操作类型")
    locator: Optional[UILocator] = Field(None, description="目标元素定位器")
    value: Optional[str] = Field(None, description="输入值或参数")
    description: Optional[str] = Field(None, description="操作描述")
    wait_after: Optional[int] = Field(None, description="操作后等待时间(ms)")


class UIAssertion(BaseModel):
    """UI断言"""
    type: AssertionType = Field(..., description="断言类型")
    locator: Optional[UILocator] = Field(None, description="目标元素")
    expected: Any = Field(None, description="期望值")
    actual: Optional[str] = Field(None, description="实际值表达式")
    message: Optional[str] = Field(None, description="断言失败消息")


class UITestStep(BaseModel):
    """UI测试步骤"""
    step_id: str = Field(..., description="步骤ID")
    description: str = Field(..., description="步骤描述")
    actions: List[UIAction] = Field(default_factory=list, description="操作列表")
    assertions: List[UIAssertion] = Field(default_factory=list, description="断言列表")


class UITestIR(BaseModel):
    """UI测试IR"""
    test_type: TestType = TestType.UI
    name: str = Field(..., description="测试名称")
    description: Optional[str] = Field(None, description="测试描述")
    
    # 前置条件
    setup: Optional[List[UITestStep]] = Field(default_factory=list, description="前置步骤")
    
    # 测试步骤
    steps: List[UITestStep] = Field(..., description="测试步骤")
    
    # 后置清理
    teardown: Optional[List[UITestStep]] = Field(default_factory=list, description="清理步骤")
    
    # 配置
    config: Optional[Dict[str, Any]] = Field(default_factory=dict, description="测试配置")


# ========== Unit Test IR ==========
class UnitTestParameter(BaseModel):
    """单元测试参数"""
    name: str = Field(..., description="参数名")
    type: str = Field(..., description="参数类型")
    value: Any = Field(..., description="参数值")


class UnitTestAssertion(BaseModel):
    """单元测试断言"""
    type: AssertionType = Field(..., description="断言类型")
    expected: Any = Field(..., description="期望值")
    actual: Optional[str] = Field(None, description="实际值表达式")
    message: Optional[str] = Field(None, description="断言消息")


class UnitTestIR(BaseModel):
    """单元测试IR"""
    test_type: TestType = TestType.UNIT
    name: str = Field(..., description="测试名称")
    description: Optional[str] = Field(None, description="测试描述")
    
    # 目标函数/方法
    target_function: str = Field(..., description="目标函数名")
    target_class: Optional[str] = Field(None, description="目标类名")
    target_module: str = Field(..., description="目标模块路径")
    
    # 测试数据
    parameters: List[UnitTestParameter] = Field(default_factory=list, description="输入参数")
    assertions: List[UnitTestAssertion] = Field(..., description="断言列表")
    
    # Mock配置
    mocks: Optional[List[Dict[str, Any]]] = Field(default_factory=list, description="Mock配置")
    
    # 配置
    config: Optional[Dict[str, Any]] = Field(default_factory=dict, description="测试配置")


# ========== Static Analysis IR ==========
class StaticAnalysisRule(BaseModel):
    """静态分析规则"""
    rule_id: str = Field(..., description="规则ID")
    severity: str = Field(..., description="严重程度: error, warning, info")
    enabled: bool = Field(True, description="是否启用")
    config: Optional[Dict[str, Any]] = Field(default_factory=dict, description="规则配置")


class StaticAnalysisIR(BaseModel):
    """静态分析IR"""
    test_type: TestType = TestType.STATIC
    name: str = Field(..., description="分析任务名称")
    description: Optional[str] = Field(None, description="任务描述")
    
    # 分析目标
    target_paths: List[str] = Field(..., description="目标文件/目录路径")
    exclude_paths: Optional[List[str]] = Field(default_factory=list, description="排除路径")
    
    # 分析规则
    rules: List[StaticAnalysisRule] = Field(..., description="分析规则")
    
    # 配置
    config: Optional[Dict[str, Any]] = Field(default_factory=dict, description="分析配置")


# ========== Integration Test IR ==========
class IntegrationTestIR(BaseModel):
    """集成测试IR"""
    test_type: TestType = TestType.INTEGRATION
    name: str = Field(..., description="测试名称")
    description: Optional[str] = Field(None, description="测试描述")
    
    # 组件列表
    components: List[str] = Field(..., description="参与集成的组件列表")
    
    # 测试场景
    scenario: Dict[str, Any] = Field(..., description="测试场景描述")
    
    # 配置
    config: Optional[Dict[str, Any]] = Field(default_factory=dict, description="测试配置")


# ========== 统一Test IR ==========
TestIR = Union[UITestIR, UnitTestIR, StaticAnalysisIR, IntegrationTestIR]


class TestIRWrapper(BaseModel):
    """Test IR包装器，用于API传输"""
    test_ir: Dict[str, Any] = Field(..., description="Test IR内容")
    version: str = Field("1.0", description="IR版本")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="元数据")


# ========== 执行结果IR ==========
class ExecutionResultIR(BaseModel):
    """测试执行结果IR"""
    test_case_id: Optional[int] = Field(None, description="测试用例ID")
    status: str = Field(..., description="执行状态")
    
    # 时间信息
    started_at: str = Field(..., description="开始时间")
    completed_at: str = Field(..., description="完成时间")
    duration: float = Field(..., description="持续时间(秒)")
    
    # 结果详情
    passed: bool = Field(..., description="是否通过")
    error_message: Optional[str] = Field(None, description="错误信息")
    logs: Optional[str] = Field(None, description="执行日志")
    
    # 覆盖率
    coverage: Optional[Dict[str, Any]] = Field(None, description="覆盖率数据")
    
    # Artifacts
    artifacts: List[Dict[str, str]] = Field(default_factory=list, description="生成的文件")
    
    # 详细结果
    details: Optional[Dict[str, Any]] = Field(default_factory=dict, description="详细结果数据")

