"""
系统测试集成测试脚本
测试完整的系统测试流程：创建项目 -> 生成测试用例 -> 执行测试 -> 查看结果
"""
import requests
import time
import json

# API配置
BASE_URL = "http://localhost:8000/api/v1"

def test_ui_test_workflow():
    """测试完整的系统测试工作流"""
    
    print("=" * 60)
    print("系统测试集成测试")
    print("=" * 60)
    
    # 1. 创建系统测试项目
    print("\n步骤1: 创建系统测试项目")
    project_data = {
        "name": "测试UI项目",
        "description": "这是一个用于测试系统测试功能的项目",
        "project_type": "ui",
        "source_path": "C:\\Users\\lenovo\\Desktop\\FreeCharts\\diagramscene.exe"
    }
    
    response = requests.post(f"{BASE_URL}/projects", json=project_data)
    if response.status_code != 200:
        print(f"❌ 创建项目失败: {response.text}")
        return
    
    project = response.json()
    project_id = project["id"]
    print(f"✓ 项目创建成功，ID: {project_id}")
    print(f"  项目名称: {project['name']}")
    print(f"  项目类型: {project['project_type']}")
    
    # 2. 生成系统测试用例
    print("\n步骤2: 使用AI生成系统测试用例")
    generate_request = {
        "name": "应用启动测试",
        "description": """测试应用程序能否正常启动并显示主窗口。
测试步骤：
1. 启动应用程序
2. 等待5秒让应用完全加载
3. 验证主窗口是否出现（检查main_window.png）
4. 关闭应用程序"""
    }
    
    response = requests.post(
        f"{BASE_URL}/projects/{project_id}/system-test/generate",
        json=generate_request
    )
    
    if response.status_code != 200:
        print(f"❌ 生成测试用例失败: {response.text}")
        return
    
    test_case = response.json()
    print(f"✓ 测试用例生成成功")
    print(f"  测试名称: {test_case['name']}")
    print(f"\n生成的Robot Framework脚本:")
    print("-" * 60)
    print(test_case['robot_script'])
    print("-" * 60)
    
    # 3. 执行系统测试
    print("\n步骤3: 执行系统测试")
    execute_request = {
        "name": test_case['name'],
        "description": test_case['description'],
        "robot_script": test_case['robot_script']
    }
    
    response = requests.post(
        f"{BASE_URL}/projects/{project_id}/system-test/execute",
        json=execute_request
    )
    
    if response.status_code != 200:
        print(f"❌ 执行测试失败: {response.text}")
        return
    
    execution = response.json()
    execution_id = execution["execution_id"]
    print(f"✓ 测试开始执行，执行ID: {execution_id}")
    print(f"  状态: {execution['status']}")
    
    # 4. 轮询测试结果
    print("\n步骤4: 等待测试完成...")
    max_wait = 120  # 最多等待2分钟
    wait_time = 0
    
    while wait_time < max_wait:
        time.sleep(5)
        wait_time += 5
        
        response = requests.get(
            f"{BASE_URL}/projects/{project_id}/system-test/results/{execution_id}"
        )
        
        if response.status_code != 200:
            print(f"❌ 获取测试结果失败: {response.text}")
            return
        
        result = response.json()
        status = result["status"]
        
        print(f"  [{wait_time}s] 当前状态: {status}")
        
        if status != "running":
            # 测试完成
            print("\n" + "=" * 60)
            print("测试执行完成")
            print("=" * 60)
            print(f"执行ID: {result['execution_id']}")
            print(f"状态: {result['status']}")
            print(f"是否通过: {'✓ 通过' if result['passed'] else '✗ 失败'}")
            
            if result.get('duration_seconds'):
                print(f"执行时长: {result['duration_seconds']:.2f} 秒")
            
            if result.get('error_message'):
                print(f"\n错误信息:")
                print(result['error_message'])
            
            if result.get('logs'):
                print(f"\n测试日志:")
                print("-" * 60)
                print(result['logs'])
                print("-" * 60)
            
            if result.get('artifacts'):
                print(f"\n生成的文件:")
                for artifact in result['artifacts']:
                    print(f"  - {artifact['name']} ({artifact['type']})")
                    print(f"    路径: {artifact['path']}")
            
            break
    else:
        print(f"\n❌ 测试超时（等待了{max_wait}秒）")
    
    # 5. 获取执行历史
    print("\n步骤5: 获取执行历史")
    response = requests.get(f"{BASE_URL}/projects/{project_id}/system-test/executions")
    
    if response.status_code != 200:
        print(f"❌ 获取执行历史失败: {response.text}")
        return
    
    history = response.json()
    print(f"✓ 执行历史获取成功")
    print(f"  总执行次数: {history['statistics']['total_executions']}")
    print(f"  完成次数: {history['statistics']['completed_executions']}")
    print(f"  通过次数: {history['statistics']['passed_executions']}")
    print(f"  通过率: {history['statistics']['pass_rate']:.2f}%")
    
    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)


if __name__ == "__main__":
    try:
        test_ui_test_workflow()
    except Exception as e:
        print(f"\n❌ 测试过程中出现异常: {str(e)}")
        import traceback
        traceback.print_exc()

