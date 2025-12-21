"""Robot Framework + SikuliLibrary 系统(UI)测试执行器"""

import os
import time
import uuid
import shutil
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional

from app.core.config import settings
from app.executors.base import BaseExecutor


class RobotExecutor(BaseExecutor):
    """Robot Framework 执行器（可配合 SikuliLibrary 做 GUI 自动化）"""

    def __init__(self):
        self.name = "RobotFramework"

    def validate_ir(self, test_ir: Dict[str, Any]) -> bool:
        if not isinstance(test_ir, dict):
            return False
        if test_ir.get("type") not in ("system", "robot", "ui_system"):
            return False
        # suite_path：解压后的目录（包含 .robot 文件/目录）
        if not test_ir.get("suite_path"):
            return False
        return True

    def _which(self, name: str) -> Optional[str]:
        return shutil.which(name)

    def execute(self, test_ir: Dict[str, Any]) -> Dict[str, Any]:
        start = time.time()

        if not self.validate_ir(test_ir):
            return {
                "status": "error",
                "error_message": "Invalid Robot(Test IR) format: missing type/suite_path",
                "duration": 0,
            }

        robot_bin = test_ir.get("robot_bin") or "robot"
        if self._which(robot_bin) is None:
            return {
                "status": "error",
                "error_message": f"Robot Framework 未安装或不可用（找不到可执行文件: {robot_bin}）。请在后端环境安装 robotframework。",
                "duration": 0,
            }

        suite_path = Path(str(test_ir["suite_path"])).expanduser()
        if not suite_path.is_absolute():
            # 允许相对路径：相对项目 artifacts 根目录
            suite_path = Path(settings.ARTIFACT_STORAGE_PATH) / suite_path
        if not suite_path.exists():
            return {
                "status": "error",
                "error_message": f"suite_path 不存在: {suite_path}",
                "duration": 0,
            }

        entry = test_ir.get("entry")  # 可以是具体 .robot 或子目录
        target = suite_path / entry if entry else suite_path
        if not target.exists():
            return {
                "status": "error",
                "error_message": f"Robot 入口不存在: {target}",
                "duration": 0,
            }

        # 输出目录：/app/artifacts/system_runs/<run_id>/
        run_id = f"rf_{int(time.time())}_{uuid.uuid4().hex[:8]}"
        out_dir = Path(settings.ARTIFACT_STORAGE_PATH) / "system_runs" / run_id
        out_dir.mkdir(parents=True, exist_ok=True)

        # Robot 输出文件名
        output_xml = out_dir / "output.xml"
        log_html = out_dir / "log.html"
        report_html = out_dir / "report.html"

        # 可选：在无头环境下启用 Xvfb
        use_xvfb = bool(test_ir.get("use_xvfb", True))
        xvfb_bin = test_ir.get("xvfb_bin") or "xvfb-run"
        xvfb_screen = test_ir.get("xvfb_screen") or "1920x1080x24"

        # Robot 参数
        robot_args: List[str] = []
        extra_args = test_ir.get("robot_args")
        if isinstance(extra_args, list):
            robot_args.extend([str(x) for x in extra_args])

        # 标签选择（可选）
        if test_ir.get("include"):
            robot_args += ["--include", str(test_ir["include"])]
        if test_ir.get("exclude"):
            robot_args += ["--exclude", str(test_ir["exclude"])]

        # 超时（秒）
        timeout_seconds = test_ir.get("timeout_seconds")
        timeout_seconds = int(timeout_seconds) if timeout_seconds else None

        cmd: List[str] = [
            robot_bin,
            "--outputdir",
            str(out_dir),
            "--output",
            str(output_xml.name),
            "--log",
            str(log_html.name),
            "--report",
            str(report_html.name),
        ] + robot_args + [str(target)]

        if use_xvfb:
            if self._which(xvfb_bin) is None:
                return {
                    "status": "error",
                    "error_message": f"需要无头执行但找不到 {xvfb_bin}。请在后端环境安装 xvfb。",
                    "duration": 0,
                }
            cmd = [xvfb_bin, "-a", "-s", f"-screen 0 {xvfb_screen}"] + cmd

        env = os.environ.copy()
        extra_env = test_ir.get("env")
        if isinstance(extra_env, dict):
            for k, v in extra_env.items():
                if v is None:
                    continue
                env[str(k)] = str(v)

        # 关键：在 suite_path 作为工作目录运行，方便相对资源引用（图片、resource、library 等）
        cwd = str(suite_path)

        try:
            proc = subprocess.run(
                cmd,
                cwd=cwd,
                env=env,
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
            )
            stdout = proc.stdout or ""
            stderr = proc.stderr or ""
            rc = proc.returncode
        except subprocess.TimeoutExpired as e:
            duration = time.time() - start
            logs = (e.stdout or "") + "\n" + (e.stderr or "")
            return {
                "status": "error",
                "error_message": f"Robot 执行超时（>{timeout_seconds}s）",
                "duration": duration,
                "logs": logs,
                "artifacts": [],
            }
        except Exception as e:
            duration = time.time() - start
            return {
                "status": "error",
                "error_message": f"Robot 执行异常: {e}",
                "duration": duration,
                "logs": "",
                "artifacts": [],
            }

        duration = time.time() - start

        # Robot 返回码：0=全部通过，1=有失败用例，>=2=执行错误
        if rc == 0:
            status = "passed"
            passed = True
        elif rc == 1:
            status = "failed"
            passed = False
        else:
            status = "error"
            passed = False

        # 将 stdout/stderr 写入 artifacts，便于前端查看
        console_log = out_dir / "console.log"
        try:
            console_log.write_text((stdout or "") + "\n" + (stderr or ""), encoding="utf-8", errors="replace")
        except Exception:
            pass

        # 产物路径（通过 /artifacts 静态挂载可直接访问）
        artifacts: List[Dict[str, str]] = [
            {"type": "rf_report", "path": f"/artifacts/system_runs/{run_id}/report.html"},
            {"type": "rf_log", "path": f"/artifacts/system_runs/{run_id}/log.html"},
            {"type": "rf_output", "path": f"/artifacts/system_runs/{run_id}/output.xml"},
            {"type": "rf_console", "path": f"/artifacts/system_runs/{run_id}/console.log"},
        ]

        # logs 字段用于页面直接展示（截断避免过大）
        merged = (stdout or "") + ("\n" + stderr if stderr else "")
        merged = merged[-20000:] if len(merged) > 20000 else merged

        return {
            "status": status,
            "passed": passed,
            "duration": duration,
            "logs": merged,
            "error_message": None if status != "error" else "Robot 执行发生错误（详见 console.log / output.xml）",
            "metadata": {
                "returncode": rc,
                "run_id": run_id,
                "out_dir": str(out_dir),
                "cmd": cmd,
            },
            "artifacts": artifacts,
            "log_path": str(artifacts[-1]["path"]),
        }


