#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
集成测试脚本 - 对指定项目进行集成测试
"""
import requests
import json
import sys
import os
from pathlib import Path

# 设置输出编码为UTF-8
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# API基础URL
BASE_URL = "http://localhost:8000/api/v1"

def print_step(step, message):
    """打印步骤信息"""
    print(f"\n{'='*60}")
    print(f"步骤 {step}: {message}")
    print('='*60)

def check_backend():
    """检查后端是否运行"""
    try:
        response = requests.get(f"{BASE_URL.replace('/api/v1', '')}/health", timeout=5)
        if response.status_code == 200:
            print("[OK] 后端服务运行正常")
            return True
    except Exception as e:
        print(f"[ERROR] 后端服务未运行: {e}")
        print("\n请先启动后端服务:")
        print("  1. 打开新的终端窗口")
        print("  2. cd backend")
        print("  3. python -m uvicorn app.main:app --reload --port 8000")
        print("\n或者使用启动脚本: .\\启动项目.ps1")
        return False
    return False

def create_project(project_name, zip_file_path):
    """创建项目并上传源代码"""
    print_step(1, "创建集成测试项目")
    
    # 检查文件是否存在
    if not os.path.exists(zip_file_path):
        print(f"❌ 文件不存在: {zip_file_path}")
        return None
    
    print(f"📁 文件路径: {zip_file_path}")
    print(f"📦 文件大小: {os.path.getsize(zip_file_path) / 1024 / 1024:.2f} MB")
    
    # 创建项目（使用FormData上传文件）
    with open(zip_file_path, 'rb') as f:
        files = {
            'source_file': (os.path.basename(zip_file_path), f, 'application/zip')
        }
        data = {
            'name': project_name,
            'description': '集成测试项目 - diagramscene_ultima',
            'project_type': 'integration',
            'language': 'cpp',
            'framework': 'Qt'
        }
        
        try:
            response = requests.post(
                f"{BASE_URL}/projects",
                files=files,
                data=data,
                timeout=60
            )
            response.raise_for_status()
            project = response.json()
            print(f"[OK] 项目创建成功!")
            print(f"   项目ID: {project['id']}")
            print(f"   项目名称: {project['name']}")
            return project
        except Exception as e:
            print(f"[ERROR] 创建项目失败: {e}")
            if hasattr(e, 'response'):
                print(f"   响应内容: {e.response.text}")
            return None

def generate_test_case(project_id):
    """生成集成测试用例"""
    print_step(2, "AI生成集成测试用例")
    
    # 定义集成测试需求
    # 注意：由于这是一个Qt图形应用，我们测试一些基本的HTTP端点
    # 如果应用没有HTTP API，我们可以测试应用启动等基本功能
    test_ir = {
        "type": "integration",
        "name": "DiagramScene应用集成测试",
        "description": "测试DiagramScene应用的基本功能和API端点",
        "flow": [
            {
                "name": "健康检查",
                "url": "http://localhost:8000/health",
                "method": "GET",
                "headers": {},
                "body": None
            },
            {
                "name": "API文档端点",
                "url": "http://localhost:8000/docs",
                "method": "GET",
                "headers": {},
                "body": None
            }
        ],
        "validations": [
            {
                "type": "equals",
                "expected": 200,
                "actual": "response.status_code",
                "message": "健康检查应返回200状态码"
            },
            {
                "type": "contains",
                "expected": "healthy",
                "actual": "response.body",
                "message": "响应应包含healthy"
            }
        ],
        "required_services": [],
        "tags": ["integration", "api"],
        "priority": "high"
    }
    
    request_data = {
        "test_ir": test_ir,
        "additional_info": "这是一个Qt图形应用项目，请生成测试应用启动和基本功能的集成测试用例。如果应用有HTTP API，请测试API端点。"
    }
    
    try:
        print("📤 发送生成请求到AI...")
        response = requests.post(
            f"{BASE_URL}/integration-tests/{project_id}/generate",
            json=request_data,
            timeout=120  # AI生成可能需要较长时间
        )
        response.raise_for_status()
        result = response.json()
        print("[OK] 测试用例生成成功!")
        print(f"   测试名称: {result.get('test_name', 'N/A')}")
        print(f"   代码长度: {len(result.get('test_code', ''))} 字符")
        return result
    except Exception as e:
        print(f"[ERROR] 生成测试用例失败: {e}")
        if hasattr(e, 'response'):
            print(f"   响应内容: {e.response.text}")
        return None

def execute_test(project_id, test_code):
    """执行集成测试"""
    print_step(3, "执行集成测试")
    
    request_data = {
        "test_code": test_code
    }
    
    try:
        print("🚀 开始执行测试...")
        print("   (这可能需要几分钟时间，请耐心等待...)")
        response = requests.post(
            f"{BASE_URL}/integration-tests/{project_id}/execute",
            json=request_data,
            timeout=300  # 编译和执行可能需要较长时间
        )
        response.raise_for_status()
        result = response.json()
        return result
    except Exception as e:
        print(f"[ERROR] 执行测试失败: {e}")
        if hasattr(e, 'response'):
            print(f"   响应内容: {e.response.text}")
        return None

def print_results(result):
    """打印测试结果"""
    print_step(4, "测试结果")
    
    if not result:
        print("❌ 未获取到测试结果")
        return
    
    success = result.get('success', False)
    summary = result.get('summary', {})
    logs = result.get('logs', '')
    
    print(f"\n{'[OK] 测试成功' if success else '[ERROR] 测试失败'}")
    print(f"\n📊 测试统计:")
    print(f"   总用例数: {summary.get('total', 0)}")
    print(f"   通过: {summary.get('passed', 0)}")
    print(f"   失败: {summary.get('failed', 0)}")
    
    assertions = summary.get('assertions', {})
    if assertions:
        print(f"   断言通过: {assertions.get('successes', 0)}")
        print(f"   断言失败: {assertions.get('failures', 0)}")
    
    # 显示用例详情
    cases = summary.get('cases', [])
    if cases:
        print(f"\n📋 用例详情:")
        for i, case in enumerate(cases, 1):
            status = "[OK]" if case.get('success', False) else "[FAIL]"
            print(f"   {status} {i}. {case.get('name', 'Unknown')}")
            if case.get('sections'):
                for section in case['sections']:
                    sec_status = "[OK]" if section.get('success', False) else "[FAIL]"
                    print(f"      {sec_status} - {section.get('name', 'Unknown')}")
    
    # 显示日志（最后1000字符）
    if logs:
        print(f"\n📝 执行日志 (最后部分):")
        print("-" * 60)
        log_lines = logs.split('\n')
        # 只显示最后50行
        for line in log_lines[-50:]:
            print(line)
        print("-" * 60)

def main():
    """主函数"""
    print("\n" + "="*60)
    print("集成测试脚本 - DiagramScene项目")
    print("="*60)
    
    # 检查后端
    if not check_backend():
        sys.exit(1)
    
    # 文件路径
    zip_file_path = r"C:\Users\汤\Desktop\项目测试资料\资料包\程序\utnubu组_源代码\utnubu组_source\diagramscene_ultima.zip"
    
    # 如果文件不存在，尝试其他可能的路径
    if not os.path.exists(zip_file_path):
        print(f"\n[WARNING] 文件不存在: {zip_file_path}")
        print("请检查文件路径是否正确")
        # 尝试查找文件
        possible_paths = [
            zip_file_path,
            os.path.join(os.path.expanduser("~"), "Desktop", "diagramscene_ultima.zip"),
            "diagramscene_ultima.zip"
        ]
        for path in possible_paths:
            if os.path.exists(path):
                zip_file_path = path
                print(f"[OK] 找到文件: {zip_file_path}")
                break
        else:
            print("[ERROR] 未找到文件，请手动指定文件路径")
            sys.exit(1)
    
    # 1. 创建项目
    project = create_project("DiagramScene集成测试", zip_file_path)
    if not project:
        sys.exit(1)
    
    project_id = project['id']
    
    # 2. 生成测试用例
    test_result = generate_test_case(project_id)
    if not test_result:
        print("\n⚠️  测试用例生成失败，但可以继续尝试执行")
        sys.exit(1)
    
    test_code = test_result.get('test_code', '')
    
    # 显示生成的代码片段（前500字符）
    if test_code:
        print(f"\n📄 生成的测试代码预览 (前500字符):")
        print("-" * 60)
        print(test_code[:500])
        if len(test_code) > 500:
            print("...")
        print("-" * 60)
    
    # 3. 执行测试
    execution_result = execute_test(project_id, test_code)
    
    # 4. 显示结果
    print_results(execution_result)
    
    print("\n" + "="*60)
    print("测试完成!")
    print("="*60)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n[WARNING] 用户中断测试")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] 发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

