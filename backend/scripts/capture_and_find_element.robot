*** Settings ***
Library    SikuliLibrary
Library    Process
Library    OperatingSystem

*** Variables ***
${APP_PATH}           C:/Users/lenovo/Desktop/FreeCharts/diagramscene.exe
${SCREENSHOT_DIR}     ${CURDIR}/screenshots
${IMAGE_DIR}          ${CURDIR}/robot_resources

*** Test Cases ***
截图并定位元素坐标
    [Documentation]    启动应用，截图，并帮助定位元素坐标
    
    # 1. 创建截图目录
    Create Directory    ${SCREENSHOT_DIR}
    Create Directory    ${IMAGE_DIR}
    
    # 2. 启动Sikuli进程
    Add Image Path    ${IMAGE_DIR}
    Start Sikuli Process
    
    # 3. 启动应用
    Log    启动应用: ${APP_PATH}
    Start Process    ${APP_PATH}    alias=app
    
    # 4. 等待应用启动
    Sleep    5s
    
    # 5. 截图整个屏幕
    ${full_screen} =    Capture Screen
    Log    完整屏幕截图已保存: ${full_screen}
    
    # 6. 等待用户操作（可以手动点击图元等）
    Log    请手动操作应用（例如：点击左侧图元集的一个图元）
    Log    操作完成后，按任意键继续...
    Sleep    10s
    
    # 7. 再次截图（操作后的状态）
    ${after_action} =    Capture Screen
    Log    操作后截图已保存: ${after_action}
    
    # 8. 使用鼠标位置获取坐标（需要手动将鼠标移动到目标位置）
    Log    请将鼠标移动到目标元素上，然后等待5秒...
    Sleep    5s
    
    # 9. 获取鼠标当前位置（通过截图分析）
    ${current_screen} =    Capture Screen
    Log    当前屏幕截图已保存: ${current_screen}
    Log    请查看截图文件，找到目标元素的坐标
    
    # 10. 关闭应用
    Terminate Process    app    kill=True
    
    # 11. 停止Sikuli进程
    Stop Remote Server
    
    Log    截图完成！请查看 ${SCREENSHOT_DIR} 目录中的截图文件
    Log    使用图像编辑工具（如画图、Photoshop）打开截图，找到目标元素的位置和大小
    Log    然后使用 create_target_image.py 脚本裁剪出目标区域

