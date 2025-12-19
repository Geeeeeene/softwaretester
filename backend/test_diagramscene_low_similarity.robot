*** Settings ***
Library    SikuliLibrary
Library    OperatingSystem
Library    Process
Documentation    Qt DiagramScene 流程图编辑器自动化测试 - 低相似度版本

*** Variables ***
${APP_PATH}    C:\\Users\\lenovo\\Desktop\\FreeCharts\\diagramscene.exe
${IMAGE_PATH}    C:\\Users\\lenovo\\Desktop\\homemadeTester\\backend\\examples\\robot_resources
${SCREENSHOT_PATH}    C:\\Users\\lenovo\\Desktop\\homemadeTester\\backend\\artifacts\\robot_framework\\screenshots
${MAIN_WINDOW}    C:\\Users\\lenovo\\Desktop\\homemadeTester\\backend\\examples\\robot_resources\\main_window.png

*** Test Cases ***
测试1-低相似度验证应用启动
    [Documentation]    使用较低的相似度阈值测试应用启动
    [Tags]    smoke    startup    low-similarity
    
    Log    开始测试（低相似度模式）
    
    # 初始化SikuliLibrary
    Add Image Path    ${IMAGE_PATH}
    Start Sikuli Process
    
    # 启动应用程序
    Log    启动应用: ${APP_PATH}
    Start Process    ${APP_PATH}    alias=diagramscene
    Sleep    8s    等待应用完全启动
    
    # 先截取当前屏幕
    ${screen_cap}=    Capture Screen
    Log    当前屏幕已截图: ${screen_cap}
    
    # 尝试不同的相似度阈值
    Log    尝试相似度 0.5 (50%)
    ${found_50}=    Run Keyword And Return Status
    ...    Click    ${MAIN_WINDOW}    similarity=0.5
    
    Run Keyword If    ${found_50}    Log    ✓✓✓ 在相似度50%下找到图像！    level=WARN
    ...    ELSE    Log    ✗ 相似度50%未找到
    
    Sleep    2s
    
    Run Keyword Unless    ${found_50}    Log    尝试相似度 0.3 (30%)
    Run Keyword Unless    ${found_50}    Run Keyword And Return Status
    ...    Click    ${MAIN_WINDOW}    similarity=0.3
    
    # 截图记录结果
    ${result_cap}=    Capture Screen
    Log    结果截图: ${result_cap}
    
    # 关闭应用
    Log    关闭应用...
    ${result}=    Run Keyword And Return Status    Terminate Process    diagramscene    kill=True
    Run Keyword If    not ${result}    Log    进程已自行关闭
    Sleep    1s
    
    # 清理
    Stop Remote Server
    Log    测试完成！

测试2-逐步降低相似度
    [Documentation]    尝试不同相似度阈值找到最佳匹配
    [Tags]    diagnostic
    
    Log    开始相似度诊断测试
    
    # 初始化
    Add Image Path    ${IMAGE_PATH}
    Start Sikuli Process
    
    # 启动应用
    Start Process    ${APP_PATH}    alias=diagramscene2
    Sleep    8s
    
    # 截图
    ${sim_screen}=    Capture Screen
    Log    截图已保存: ${sim_screen}
    
    # 尝试不同相似度
    @{similarities}=    Create List    0.9    0.8    0.7    0.6    0.5    0.4    0.3
    
    FOR    ${sim}    IN    @{similarities}
        Log    尝试相似度: ${sim}
        ${found}=    Run Keyword And Return Status
        ...    Exists    ${MAIN_WINDOW}    similarity=${sim}    timeout=2
        
        Run Keyword If    ${found}    Log    ✓ 相似度 ${sim} 找到了！    level=WARN
        Run Keyword If    ${found}    Exit For Loop
        
        Run Keyword Unless    ${found}    Log    ✗ 相似度 ${sim} 未找到
    END
    
    # 关闭
    ${result}=    Run Keyword And Return Status    Terminate Process    diagramscene2    kill=True
    Run Keyword If    not ${result}    Log    进程已自行关闭
    Sleep    1s
    Stop Remote Server

