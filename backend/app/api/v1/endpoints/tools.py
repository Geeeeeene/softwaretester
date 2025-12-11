"""工具状态检查API"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

from app.executors.unit_executor import UnitExecutor
from app.executors.memory_executor import MemoryExecutor
import shutil
import os
from pathlib import Path

router = APIRouter()


class ToolStatus(BaseModel):
    """工具状态响应"""
    available: bool
    path: Optional[str] = None
    message: str
    install_hint: Optional[str] = None
    version: Optional[str] = None


class ToolsStatusResponse(BaseModel):
    """所有工具状态响应"""
    utbot: ToolStatus
    gcov: ToolStatus
    lcov: ToolStatus
    drmemory: ToolStatus
    genhtml: Optional[ToolStatus] = None


def check_tool_executable(path: str) -> tuple[bool, str]:
    """检查工具可执行文件"""
    if not path:
        return False, "未找到（路径为空）"
    
    path_obj = Path(path)
    if not path_obj.exists():
        return False, f"路径不存在: {path}"
    
    if not path_obj.is_file():
        return False, f"路径不是文件: {path}"
    
    if not os.access(path_obj, os.X_OK):
        return False, f"文件不可执行: {path}"
    
    return True, f"已找到: {path}"


def check_system_tool(name: str) -> tuple[bool, str, Optional[str]]:
    """检查系统工具（从PATH查找）"""
    exe_name = f"{name}.exe" if os.name == 'nt' else name
    tool_path = shutil.which(name) or shutil.which(exe_name)
    
    if tool_path:
        return True, f"已找到: {tool_path}", tool_path
    else:
        return False, "未找到", None


@router.get("/status", response_model=ToolsStatusResponse)
def get_tools_status():
    """获取所有工具状态"""
    unit_executor = UnitExecutor()
    memory_executor = MemoryExecutor()
    
    # 检查 UTBotCpp
    utbot_available = False
    utbot_path = ""
    utbot_message = "未找到"
    utbot_hint = "请确保 UTBotCpp 已编译并配置正确路径"
    
    if unit_executor.utbot_executable:
        available, message = check_tool_executable(unit_executor.utbot_executable)
        utbot_available = available
        utbot_path = unit_executor.utbot_executable if available else ""
        utbot_message = message
    else:
        utbot_hint = "请检查 UTBotCpp 是否已编译，配置路径: backend/tools/utbot/UTBotCpp"
    
    # 检查 gcov
    gcov_available = False
    gcov_path = ""
    gcov_message = "未找到"
    gcov_hint = "gcov 通常随 MinGW/GCC 安装"
    
    if unit_executor.gcov_path:
        available, message = check_tool_executable(unit_executor.gcov_path)
        gcov_available = available
        gcov_path = unit_executor.gcov_path if available else ""
        gcov_message = message
    else:
        available, message, path = check_system_tool("gcov")
        gcov_available = available
        gcov_path = path or ""
        gcov_message = message
    
    # 检查 lcov
    lcov_available = False
    lcov_path = ""
    lcov_message = "未找到"
    lcov_hint = "Windows 可以使用 Chocolatey 安装: choco install lcov\n或使用 MSYS2: pacman -S mingw-w64-x86_64-lcov"
    
    if unit_executor.lcov_path:
        available, message = check_tool_executable(unit_executor.lcov_path)
        lcov_available = available
        lcov_path = unit_executor.lcov_path if available else ""
        lcov_message = message
    else:
        available, message, path = check_system_tool("lcov")
        lcov_available = available
        lcov_path = path or ""
        lcov_message = message
    
    # 检查 genhtml（可选）
    genhtml_available = False
    genhtml_path = ""
    genhtml_message = "未找到（可选）"
    
    if unit_executor.genhtml_path:
        available, message = check_tool_executable(unit_executor.genhtml_path)
        genhtml_available = available
        genhtml_path = unit_executor.genhtml_path if available else ""
        genhtml_message = message
    else:
        available, message, path = check_system_tool("genhtml")
        genhtml_available = available
        genhtml_path = path or ""
        genhtml_message = message
    
    # 检查 Dr. Memory
    drmemory_available = False
    drmemory_path = ""
    drmemory_message = "未找到"
    drmemory_hint = "请下载并安装 Dr. Memory\n下载地址: https://github.com/DynamoRIO/drmemory/releases"
    
    if memory_executor.drmemory_executable:
        available, message = check_tool_executable(memory_executor.drmemory_executable)
        drmemory_available = available
        drmemory_path = memory_executor.drmemory_executable if available else ""
        drmemory_message = message
    else:
        drmemory_hint = "请下载并安装 Dr. Memory\n下载地址: https://github.com/DynamoRIO/drmemory/releases\n配置路径: backend/tools/drmemory"
    
    return ToolsStatusResponse(
        utbot=ToolStatus(
            available=utbot_available,
            path=utbot_path if utbot_available else None,
            message=utbot_message,
            install_hint=utbot_hint if not utbot_available else None
        ),
        gcov=ToolStatus(
            available=gcov_available,
            path=gcov_path if gcov_available else None,
            message=gcov_message,
            install_hint=gcov_hint if not gcov_available else None
        ),
        lcov=ToolStatus(
            available=lcov_available,
            path=lcov_path if lcov_available else None,
            message=lcov_message,
            install_hint=lcov_hint if not lcov_available else None
        ),
        drmemory=ToolStatus(
            available=drmemory_available,
            path=drmemory_path if drmemory_available else None,
            message=drmemory_message,
            install_hint=drmemory_hint if not drmemory_available else None
        ),
        genhtml=ToolStatus(
            available=genhtml_available,
            path=genhtml_path if genhtml_available else None,
            message=genhtml_message
        ) if genhtml_available or genhtml_path else None
    )


@router.get("/status/{tool_name}", response_model=ToolStatus)
def get_tool_status(tool_name: str):
    """获取单个工具状态"""
    tool_name_lower = tool_name.lower()
    
    if tool_name_lower == "utbot":
        unit_executor = UnitExecutor()
        if unit_executor.utbot_executable:
            available, message = check_tool_executable(unit_executor.utbot_executable)
            return ToolStatus(
                available=available,
                path=unit_executor.utbot_executable if available else None,
                message=message,
                install_hint="请确保 UTBotCpp 已编译并配置正确路径" if not available else None
            )
        else:
            return ToolStatus(
                available=False,
                message="未找到",
                install_hint="请检查 UTBotCpp 是否已编译"
            )
    
    elif tool_name_lower == "gcov":
        unit_executor = UnitExecutor()
        if unit_executor.gcov_path:
            available, message = check_tool_executable(unit_executor.gcov_path)
            return ToolStatus(
                available=available,
                path=unit_executor.gcov_path if available else None,
                message=message
            )
        else:
            available, message, path = check_system_tool("gcov")
            return ToolStatus(
                available=available,
                path=path,
                message=message,
                install_hint="gcov 通常随 MinGW/GCC 安装" if not available else None
            )
    
    elif tool_name_lower == "lcov":
        unit_executor = UnitExecutor()
        if unit_executor.lcov_path:
            available, message = check_tool_executable(unit_executor.lcov_path)
            return ToolStatus(
                available=available,
                path=unit_executor.lcov_path if available else None,
                message=message
            )
        else:
            available, message, path = check_system_tool("lcov")
            return ToolStatus(
                available=available,
                path=path,
                message=message,
                install_hint="Windows 可以使用 Chocolatey 安装: choco install lcov\n或使用 MSYS2: pacman -S mingw-w64-x86_64-lcov" if not available else None
            )
    
    elif tool_name_lower == "drmemory":
        memory_executor = MemoryExecutor()
        if memory_executor.drmemory_executable:
            available, message = check_tool_executable(memory_executor.drmemory_executable)
            return ToolStatus(
                available=available,
                path=memory_executor.drmemory_executable if available else None,
                message=message,
                install_hint="请下载并安装 Dr. Memory\n下载地址: https://github.com/DynamoRIO/drmemory/releases" if not available else None
            )
        else:
            return ToolStatus(
                available=False,
                message="未找到",
                install_hint="请下载并安装 Dr. Memory\n下载地址: https://github.com/DynamoRIO/drmemory/releases"
            )
    
    elif tool_name_lower == "genhtml":
        unit_executor = UnitExecutor()
        if unit_executor.genhtml_path:
            available, message = check_tool_executable(unit_executor.genhtml_path)
            return ToolStatus(
                available=available,
                path=unit_executor.genhtml_path if available else None,
                message=message
            )
        else:
            available, message, path = check_system_tool("genhtml")
            return ToolStatus(
                available=available,
                path=path,
                message=message,
                install_hint="genhtml 通常与 lcov 一起安装" if not available else None
            )
    
    else:
        return ToolStatus(
            available=False,
            message=f"未知工具: {tool_name}"
        )



