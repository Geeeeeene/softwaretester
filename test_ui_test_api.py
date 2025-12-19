"""
UI测试API验证脚本
用于快速验证UI测试相关的API端点是否正确注册
"""
import sys
import os

# 添加backend到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

def test_imports():
    """测试导入是否正常"""
    print("测试导入...")
    try:
        from app.api.v1.endpoints import ui_test
        print("✓ ui_test模块导入成功")
        
        from app.api.v1 import api_router
        print("✓ api_router导入成功")
        
        from app.executors.robot_framework_executor import RobotFrameworkExecutor
        print("✓ RobotFrameworkExecutor导入成功")
        
        return True
    except Exception as e:
        print(f"✗ 导入失败: {e}")
        return False

def test_router_registration():
    """测试路由是否正确注册"""
    print("\n测试路由注册...")
    try:
        from app.api.v1 import api_router
        
        # 检查路由
        routes = []
        for route in api_router.routes:
            if hasattr(route, 'path'):
                routes.append(route.path)
        
        # 检查UI测试相关路由
        ui_test_patterns = [
            'ui-test/generate',
            'ui-test/execute',
            'ui-test/results',
            'ui-test/executions'
        ]
        
        found_routes = []
        for pattern in ui_test_patterns:
            matching = [r for r in routes if pattern in r]
            if matching:
                found_routes.extend(matching)
                print(f"✓ 找到路由包含: {pattern}")
            else:
                print(f"✗ 未找到路由: {pattern}")
        
        print(f"\n找到的UI测试相关路由:")
        for route in found_routes:
            print(f"  - {route}")
        
        return len(found_routes) > 0
    except Exception as e:
        print(f"✗ 路由检查失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_pydantic_models():
    """测试Pydantic模型是否正确定义"""
    print("\n测试Pydantic模型...")
    try:
        from app.api.v1.endpoints.ui_test import (
            UITestCaseGenerateRequest,
            UITestCaseGenerateResponse,
            UITestExecuteRequest,
            UITestExecuteResponse,
            UITestResult
        )
        
        print("✓ UITestCaseGenerateRequest")
        print("✓ UITestCaseGenerateResponse")
        print("✓ UITestExecuteRequest")
        print("✓ UITestExecuteResponse")
        print("✓ UITestResult")
        
        # 测试创建实例
        req = UITestCaseGenerateRequest(name="测试", description="描述")
        print(f"✓ 创建测试请求实例成功: {req.name}")
        
        return True
    except Exception as e:
        print(f"✗ 模型测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_config():
    """测试配置"""
    print("\n测试配置...")
    try:
        from app.core.config import settings
        
        print(f"✓ CLAUDE_API_KEY 已配置: {'是' if settings.CLAUDE_API_KEY else '否'}")
        print(f"✓ CLAUDE_MODEL: {settings.CLAUDE_MODEL}")
        print(f"✓ CLAUDE_BASE_URL: {settings.CLAUDE_BASE_URL}")
        
        if not settings.CLAUDE_API_KEY:
            print("⚠ 警告: CLAUDE_API_KEY 未配置，AI生成功能将无法使用")
        
        return True
    except Exception as e:
        print(f"✗ 配置测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("="*60)
    print("UI测试功能API验证")
    print("="*60)
    
    results = []
    
    # 运行测试
    results.append(("导入测试", test_imports()))
    results.append(("路由注册", test_router_registration()))
    results.append(("Pydantic模型", test_pydantic_models()))
    results.append(("配置检查", test_config()))
    
    # 输出结果
    print("\n" + "="*60)
    print("测试结果汇总")
    print("="*60)
    
    all_passed = True
    for name, passed in results:
        status = "✓ 通过" if passed else "✗ 失败"
        print(f"{name}: {status}")
        if not passed:
            all_passed = False
    
    print("="*60)
    
    if all_passed:
        print("\n✓ 所有测试通过！UI测试功能API已正确配置。")
        print("\n后续步骤:")
        print("1. 启动后端服务: cd backend && python -m app.main")
        print("2. 启动前端服务: cd frontend && npm run dev")
        print("3. 访问 http://localhost:5173")
        print("4. 创建UI测试项目并测试功能")
        return 0
    else:
        print("\n✗ 部分测试失败，请检查上述错误信息")
        return 1

if __name__ == '__main__':
    exit(main())

