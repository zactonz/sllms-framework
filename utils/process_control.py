from __future__ import annotations

import os
import signal
import subprocess
import sys
import time
from pathlib import Path

from utils.platform import PlatformName, current_platform


class BackgroundProcessManager:
    def __init__(self, pid_file: Path, log_file: Path):
        self.pid_file = pid_file
        self.log_file = log_file

    def start(self, command: list[str], cwd: Path) -> int:
        status = self.status()
        if status["running"]:
            return status["pid"]

        self.pid_file.parent.mkdir(parents=True, exist_ok=True)
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        with self.log_file.open("a", encoding="utf-8") as handle:
            handle.write(f"\n[{time.strftime('%Y-%m-%d %H:%M:%S')}] Starting background assistant\n")
            kwargs = {
                "cwd": str(cwd),
                "stdin": subprocess.DEVNULL,
                "stdout": handle,
                "stderr": subprocess.STDOUT,
                "close_fds": True,
            }
            if current_platform() == PlatformName.WINDOWS:
                kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS
            else:
                kwargs["start_new_session"] = True
            process = subprocess.Popen(command, **kwargs)
        self.pid_file.write_text(str(process.pid), encoding="utf-8")
        return process.pid

    def stop(self) -> bool:
        pid = self._read_pid()
        if pid is None:
            return False
        if current_platform() == PlatformName.WINDOWS:
            subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"], capture_output=True, text=True, check=False)
        else:
            os.kill(pid, signal.SIGTERM)
        self.pid_file.unlink(missing_ok=True)
        return True

    def status(self) -> dict[str, object]:
        pid = self._read_pid()
        if pid is None:
            return {"running": False, "pid": None, "log_file": str(self.log_file)}
        running = _is_process_running(pid)
        if not running:
            self.pid_file.unlink(missing_ok=True)
            return {"running": False, "pid": None, "log_file": str(self.log_file)}
        return {"running": True, "pid": pid, "log_file": str(self.log_file)}

    def _read_pid(self) -> int | None:
        if not self.pid_file.exists():
            return None
        try:
            return int(self.pid_file.read_text(encoding="utf-8").strip())
        except ValueError:
            self.pid_file.unlink(missing_ok=True)
            return None


def _is_process_running(pid: int) -> bool:
    if current_platform() == PlatformName.WINDOWS:
        completed = subprocess.run(
            ["tasklist", "/FI", f"PID eq {pid}"],
            capture_output=True,
            text=True,
            check=False,
        )
        return str(pid) in completed.stdout
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False
