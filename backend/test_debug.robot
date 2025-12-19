*** Settings ***
Library    SikuliLibrary
Library    OperatingSystem
Library    Process
Documentation    调试版本 - 帮助诊断图像识别问题

*** Variables ***
${APP_PATH}    C:\\Users\\lenovo\\Desktop\\FreeCharts\\diagramscene.exe
${MAIN_WINDOW}    C:\\Users\\lenovo\\Desktop\\homemadeTester\\backend\\examples\\robot_resources\\main_window.png
${SCREENSHOT_PATH}    C:\\Users\\lenovo\\Desktop\\homemadeTester\\backend\\artifacts\\robot_framework\\screenshots

*** Test Cases ***
调试测试-手动启动应用
    [Documentation]    需要您手动启动应用，然后测试图像识别
    [Tags]    debug    manual
    
    Log    ========================================
    Log    调试测试开始
    Log    ========================================
    
    # 初始化SikuliLibrary
    Log    1. 初始化SikuliLibrary...
    Start Sikuli Process
    Log    ✓ SikuliLibrary已初始化
    
    # 等待用户手动启动应用
    Log    ========================================
    Log    请按以下步骤操作：
    Log    1. 手动启动应用: ${APP_PATH}
    Log    2. 等待应用完全加载
    Log    3. 确保应用窗口在屏幕最前面
    Log    ========================================
    
    # 等待用户操作
    Sleep    15s    等待用户手动启动应用
    
    # 先截取当前屏幕
    Log    2. 截取当前屏幕状态...
    ${screenshot_file}=    Capture Screen
    Log    ✓ 屏幕截图已保存: ${screenshot_file}
    Log    请查看 sikuli_captured 目录中的截图
    
    # 尝试查找图像（短超时）
    Log    3. 尝试查找目标图像...
    Log    目标图像: ${MAIN_WINDOW}
    
    ${found}=    Run Keyword And Return Status    
    ...    Wait Until Screen Contain    ${MAIN_WINDOW}    5
    
    Run Keyword If    ${found}    Log    ✓✓✓ 成功找到图像！✓✓✓    level=WARN
    ...    ELSE    Log    ✗✗✗ 未找到图像 ✗✗✗    level=ERROR
    
    # 再次截图
    ${screenshot_file2}=    Capture Screen
    Log    截图已保存: ${screenshot_file2}
    
    # 清理
    Stop Remote Server
    
    Log    ========================================
    Log    调试测试完成
    Log    请检查 sikuli_captured 目录中的截图
    Log    比较截图和 ${MAIN_WINDOW}
    Log    看看有什么不同
    Log    ========================================

调试测试-自动启动应用
    [Documentation]    自动启动应用并诊断
    [Tags]    debug    auto
    
    Log    ========================================
    Log    自动启动调试测试
    Log    ========================================
    
    # 初始化
    Start Sikuli Process
    
    # 启动应用
    Log    启动应用: ${APP_PATH}
    Start Process    ${APP_PATH}    alias=debug_app
    
    # 等待不同时间并截图
    Log    等待3秒...
    Sleep    3s
    ${cap1}=    Capture Screen
    Log    截图1: ${cap1}
    
    Log    等待5秒...
    Sleep    2s
    ${cap2}=    Capture Screen
    Log    截图2: ${cap2}
    
    Log    等待8秒...
    Sleep    3s
    ${cap3}=    Capture Screen
    Log    截图3: ${cap3}
    
    # 尝试查找
    Log    尝试查找图像...
    ${found}=    Run Keyword And Return Status    
    ...    Wait Until Screen Contain    ${MAIN_WINDOW}    10
    
    Run Keyword If    ${found}    Log    ✓ 找到图像！
    ...    ELSE    Log    ✗ 未找到图像
    
    # 关闭应用
    ${result}=    Run Keyword And Return Status    Terminate Process    debug_app    kill=True
    Run Keyword If    not ${result}    Log    进程已自行关闭
    Sleep    1s
    
    Stop Remote Server
    
    Log    ========================================
    Log    请查看 sikuli_captured 目录中的截图
    Log    查看最新的3张截图（应用启动的不同时间点）
    Log    这些截图显示了应用的启动过程
    Log    ========================================

*** Keywords ***
等待用户确认
    [Arguments]    ${message}    ${wait_time}=10
    Log    ${message}
    Sleep    ${wait_time}s

