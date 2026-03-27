from __future__ import annotations

import platform
import shutil
import subprocess
from enum import Enum
from pathlib import Path


class PlatformName(str, Enum):
    WINDOWS = "windows"
    MACOS = "macos"
    LINUX = "linux"


def current_platform() -> PlatformName:
    system = platform.system().lower()
    if system == "windows":
        return PlatformName.WINDOWS
    if system == "darwin":
        return PlatformName.MACOS
    return PlatformName.LINUX


def apply_platform_executable_suffix(path: Path, key: str) -> Path:
    if key != "executable":
        return path.resolve()
    if current_platform() == PlatformName.WINDOWS and path.suffix.lower() != ".exe":
        return path.with_suffix(".exe").resolve()
    return path.resolve()


def resolve_executable_path(configured_path: str) -> Path:
    path = Path(configured_path)
    if path.exists():
        return path.resolve()
    discovered = shutil.which(str(path))
    if discovered:
        return Path(discovered).resolve()
    return path.resolve()


def build_shell_command(command: str) -> list[str]:
    os_name = current_platform()
    if os_name == PlatformName.WINDOWS:
        return ["powershell", "-NoProfile", "-Command", command]
    shell = "/bin/zsh" if os_name == PlatformName.MACOS and Path("/bin/zsh").exists() else "/bin/bash"
    return [shell, "-lc", command]


def resolve_app_alias(name: str, os_name: PlatformName) -> str:
    lowered = name.strip().lower()
    aliases = {
        PlatformName.WINDOWS: {
            "notepad": "notepad",
            "nodepad": "notepad",
            "notepad.": "notepad",
            "calculator": "calc",
            "chrome": "chrome",
            "browser": "chrome",
            "terminal": "powershell",
        },
        PlatformName.MACOS: {
            "notepad": "TextEdit",
            "nodepad": "TextEdit",
            "notepad.": "TextEdit",
            "calculator": "Calculator",
            "chrome": "Google Chrome",
            "browser": "Safari",
            "terminal": "Terminal",
        },
        PlatformName.LINUX: {
            "notepad": "gedit",
            "nodepad": "gedit",
            "notepad.": "gedit",
            "calculator": "gnome-calculator",
            "chrome": "google-chrome",
            "browser": "xdg-open",
            "terminal": "x-terminal-emulator",
        },
    }
    return aliases.get(os_name, {}).get(lowered, name)


def build_open_app_command(name: str, os_name: PlatformName) -> list[str]:
    if os_name == PlatformName.WINDOWS:
        return ["powershell", "-NoProfile", "-Command", f"Start-Process '{name}'"]
    if os_name == PlatformName.MACOS:
        return ["open", "-a", name]
    if name == "xdg-open":
        return ["xdg-open", "https://www.google.com"]
    return [name]


def resolve_wifi_command(state: str) -> list[str] | None:
    normalized_state = "on" if state in {"on", "enable"} else "off"
    os_name = current_platform()
    if os_name == PlatformName.WINDOWS:
        admin_state = "ENABLED" if normalized_state == "on" else "DISABLED"
        return ["netsh", "interface", "set", "interface", "name=Wi-Fi", f"admin={admin_state}"]
    if os_name == PlatformName.MACOS:
        device = _detect_macos_wifi_device()
        if not device:
            return None
        return ["networksetup", "-setairportpower", device, normalized_state]
    if shutil.which("nmcli"):
        return ["nmcli", "radio", "wifi", normalized_state]
    return None


def _detect_macos_wifi_device() -> str | None:
    if current_platform() != PlatformName.MACOS:
        return None
    completed = subprocess.run(["networksetup", "-listallhardwareports"], capture_output=True, text=True, check=False)
    if completed.returncode != 0:
        return None
    lines = completed.stdout.splitlines()
    for index, line in enumerate(lines):
        if line.strip() == "Hardware Port: Wi-Fi" and index + 1 < len(lines):
            next_line = lines[index + 1].strip()
            if next_line.startswith("Device: "):
                return next_line.split("Device: ", 1)[1].strip()
    return None
