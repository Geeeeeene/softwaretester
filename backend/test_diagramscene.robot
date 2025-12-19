*** Settings ***
Library    SikuliLibrary
Library    OperatingSystem
Library    Process
Documentation    Qt DiagramScene 流程图编辑器自动化测试
Test Timeout    2 minutes

*** Variables ***
${APP_PATH}    C:\\Users\\lenovo\\Desktop\\FreeCharts\\diagramscene.exe
${IMAGE_PATH}    C:\\Users\\lenovo\\Desktop\\homemadeTester\\backend\\examples\\robot_resources
${SCREENSHOT_PATH}    C:\\Users\\lenovo\\Desktop\\homemadeTester\\backend\\artifacts\\robot_framework\\screenshots
${MAIN_WINDOW}    C:\\Users\\lenovo\\Desktop\\homemadeTester\\backend\\examples\\robot_resources\\main_window.png

*** Test Cases ***
测试1-验证应用启动
    [Documentation]    测试DiagramScene应用能否正常启动并显示主窗口
    [Tags]    smoke    startup
    
    Log    开始测试Qt DiagramScene应用启动
    
    # 初始化SikuliLibrary
    Add Image Path    ${IMAGE_PATH}
    Start Sikuli Process
    
    # 启动应用程序
    Log    启动应用: ${APP_PATH}
    Start Process    ${APP_PATH}    alias=diagramscene
    Sleep    5s
    
    # 等待主窗口出现（最多等待30秒，使用较低相似度以提高稳定性）
    Log    等待主窗口显示...
    Set Min Similarity    0.7
    Wait Until Screen Contain    ${MAIN_WINDOW}    30
    
    # 截图记录应用启动成功
    ${screenshot}=    Capture Screen
    Log    ✓ 应用启动成功，主窗口已显示，截图: ${screenshot}
    
    # 验证主窗口确实存在
    Set Min Similarity    0.7
    ${exists}=    Exists    ${MAIN_WINDOW}    timeout=5
    Should Be True    ${exists}    主窗口未找到
    Log    ✓ 主窗口验证通过
    
    # 等待2秒观察
    Sleep    2s
    
    # 关闭应用
    Log    关闭应用...
    ${result}=    Run Keyword And Return Status    Terminate Process    diagramscene    kill=True
    Run Keyword If    ${result}    Log    进程已终止
    ...    ELSE    Log    进程已自行关闭
    Sleep    1s
    
    # 清理
    Stop Remote Server
    Log    测试完成！

测试2-简单交互测试
    [Documentation]    测试应用启动后的基本交互
    [Tags]    interaction
    
    Log    开始交互测试
    
    # 初始化
    Add Image Path    ${IMAGE_PATH}
    Start Sikuli Process
    
    # 启动应用
    Start Process    ${APP_PATH}    alias=diagramscene2
    Sleep    5s
    Set Min Similarity    0.7
    Wait Until Screen Contain    ${MAIN_WINDOW}    30
    
    # 截图初始状态
    ${screenshot1}=    Capture Screen
    Log    应用已启动，截图: ${screenshot1}
    
    # 尝试点击窗口（确保窗口激活）
    Set Min Similarity    0.7
    Click    ${MAIN_WINDOW}
    Sleep    1s
    ${screenshot2}=    Capture Screen
    Log    窗口点击完成，截图: ${screenshot2}
    
    # 等待观察
    Sleep    2s
    
    # 关闭应用
    ${result}=    Run Keyword And Return Status    Terminate Process    diagramscene2    kill=True
    Run Keyword If    ${result}    Log    进程已终止
    ...    ELSE    Log    进程已自行关闭
    Sleep    1s
    
    # 清理
    Stop Remote Server
    Log    交互测试完成！

*** Keywords ***
启动DiagramScene应用
    [Documentation]    启动DiagramScene应用并等待主窗口显示
    Add Image Path    ${IMAGE_PATH}
    Start Sikuli Process
    Start Process    ${APP_PATH}    alias=diagramscene_app
    Sleep    5s
    Set Min Similarity    0.7
    Wait Until Screen Contain    ${MAIN_WINDOW}    30
    Log    DiagramScene应用已启动

关闭DiagramScene应用
    [Documentation]    关闭DiagramScene应用
    ${result}=    Run Keyword And Return Status    Terminate Process    diagramscene_app    kill=True
    Run Keyword If    ${result}    Log    进程已终止
    ...    ELSE    Log    进程已自行关闭
    Sleep    1s
    Stop Remote Server
    Log    DiagramScene应用已关闭

