from __future__ import annotations

import getpass
import shutil
import subprocess

from tools.base import ToolDefinition, ToolRegistry, ToolResult
from utils.platform import (
    PlatformName,
    build_open_app_command,
    current_platform,
    resolve_app_alias,
    resolve_wifi_command,
)


def register_control_tools(registry: ToolRegistry, config: dict) -> None:
    allow_process_control = bool(config["tools"].get("allow_process_control", False))
    allow_power_actions = bool(config["tools"].get("allow_power_actions", False))

    _register_app_shortcuts(registry)
    _register_process_tools(registry, allow_process_control)
    _register_device_tools(registry)
    _register_power_tools(registry, allow_power_actions)


def _register_app_shortcuts(registry: ToolRegistry) -> None:
    shortcuts = {
        "open_terminal": "terminal",
        "open_browser": "browser",
        "open_notepad": "notepad",
        "open_calculator": "calculator",
    }
    for tool_name, app_name in shortcuts.items():
        _register(registry, tool_name, f"Open {app_name}.", {}, lambda params, name=app_name: _open_app(name))

    _register(registry, "open_settings", "Open the system settings application if available.", {}, lambda params: _open_special_app("settings"))
    _register(registry, "open_system_monitor", "Open the task manager or system monitor if available.", {}, lambda params: _open_special_app("system_monitor"))


def _register_process_tools(registry: ToolRegistry, allow_process_control: bool) -> None:
    _register(registry, "list_processes", "List running processes.", {}, lambda params: _list_processes(50))
    registry.register(
        ToolDefinition(
            name="list_top_processes",
            description="List the top running processes by the current platform command output.",
            parameters={"limit": "Maximum number of processes to include."},
            handler=lambda params: _list_processes(_int_param(params.get("limit"), 10, 1, 50)),
        )
    )
    registry.register(
        ToolDefinition(
            name="is_process_running",
            description="Check if a process is running by name.",
            parameters={"name": "Process name to check."},
            handler=lambda params: _is_process_running(str(params.get("name", ""))),
        )
    )
    registry.register(
        ToolDefinition(
            name="kill_process",
            description="Terminate a process by name when process control is enabled.",
            parameters={"name": "Process name to stop."},
            handler=lambda params: _kill_process(str(params.get("name", "")), allow_process_control),
        )
    )
    registry.register(
        ToolDefinition(
            name="close_app",
            description="Close an app by name when process control is enabled.",
            parameters={"name": "Application or process name."},
            handler=lambda params: _kill_process(str(params.get("name", "")), allow_process_control),
        )
    )
    registry.register(
        ToolDefinition(
            name="restart_app",
            description="Restart an app by name when process control is enabled.",
            parameters={"name": "Application or process name."},
            handler=lambda params: _restart_app(str(params.get("name", "")), allow_process_control),
        )
    )


def _register_device_tools(registry: ToolRegistry) -> None:
    _register(registry, "wifi_on", "Turn Wi-Fi on if supported.", {}, lambda params: _wifi_state("on"))
    _register(registry, "wifi_off", "Turn Wi-Fi off if supported.", {}, lambda params: _wifi_state("off"))
    _register(registry, "bluetooth_on", "Turn Bluetooth on if supported.", {}, lambda params: _bluetooth_state("on"))
    _register(registry, "bluetooth_off", "Turn Bluetooth off if supported.", {}, lambda params: _bluetooth_state("off"))


def _register_power_tools(registry: ToolRegistry, allow_power_actions: bool) -> None:
    _register(registry, "lock_screen", "Lock the current machine when power actions are enabled.", {}, lambda params: _power_action("lock", allow_power_actions))
    _register(registry, "sleep_machine", "Sleep the current machine when power actions are enabled.", {}, lambda params: _power_action("sleep", allow_power_actions))
    _register(registry, "shutdown_machine", "Shut down the current machine when power actions are enabled.", {}, lambda params: _power_action("shutdown", allow_power_actions))
    _register(registry, "restart_machine", "Restart the current machine when power actions are enabled.", {}, lambda params: _power_action("restart", allow_power_actions))
    _register(registry, "log_out_user", "Log out the current user when power actions are enabled.", {}, lambda params: _power_action("logout", allow_power_actions))


def _register(registry: ToolRegistry, name: str, description: str, parameters: dict[str, str], handler) -> None:
    registry.register(ToolDefinition(name=name, description=description, parameters=parameters, handler=handler))


def _open_app(name: str) -> ToolResult:
    if not name.strip():
        return ToolResult(False, "No application name was provided.")
    os_name = current_platform()
    resolved_name = resolve_app_alias(name.strip(), os_name)
    completed = subprocess.run(build_open_app_command(resolved_name, os_name), capture_output=True, text=True, check=False)
    if completed.returncode != 0:
        return ToolResult(False, completed.stderr.strip() or completed.stdout.strip() or f"Failed to open {name}.")
    return ToolResult(True, f"Opening {name}.", {"name": resolved_name})


def _open_special_app(kind: str) -> ToolResult:
    os_name = current_platform()
    commands = {
        PlatformName.WINDOWS: {
            "settings": [["powershell", "-NoProfile", "-Command", "Start-Process 'ms-settings:'"]],
            "system_monitor": [["powershell", "-NoProfile", "-Command", "Start-Process 'taskmgr'"]],
        },
        PlatformName.MACOS: {
            "settings": [["open", "-a", "System Settings"], ["open", "-a", "System Preferences"]],
            "system_monitor": [["open", "-a", "Activity Monitor"]],
        },
        PlatformName.LINUX: {
            "settings": [["gnome-control-center"], ["systemsettings"], ["xfce4-settings-manager"]],
            "system_monitor": [["gnome-system-monitor"], ["mate-system-monitor"], ["ksysguard"]],
        },
    }
    for command in commands.get(os_name, {}).get(kind, []):
        completed = subprocess.run(command, capture_output=True, text=True, check=False)
        if completed.returncode == 0:
            return ToolResult(True, f"Opened {kind.replace('_', ' ')}.", {"command": command})
    return ToolResult(False, f"Unable to open {kind.replace('_', ' ')} on {os_name.value}.")


def _list_processes(limit: int) -> ToolResult:
    os_name = current_platform()
    command = ["tasklist"] if os_name == PlatformName.WINDOWS else ["ps", "-eo", "pid,comm,%cpu,%mem"]
    completed = subprocess.run(command, capture_output=True, text=True, check=False)
    if completed.returncode != 0:
        return ToolResult(False, completed.stderr.strip() or completed.stdout.strip() or "Failed to list processes.")
    lines = [line for line in completed.stdout.splitlines() if line.strip()]
    preview = "\n".join(lines[: max(limit + 1, 2)])
    return ToolResult(True, preview, {"lines": lines[: limit + 1]})


def _is_process_running(name: str) -> ToolResult:
    if not name.strip():
        return ToolResult(False, "A process name is required.")
    os_name = current_platform()
    if os_name == PlatformName.WINDOWS:
        command = ["tasklist", "/FI", f"IMAGENAME eq {name}*"]
    else:
        command = ["pgrep", "-fl", name]
    completed = subprocess.run(command, capture_output=True, text=True, check=False)
    output = (completed.stdout or "").strip()
    running = bool(output and "No tasks are running" not in output)
    return ToolResult(True, f"Process '{name}' {'is' if running else 'is not'} running.", {"name": name, "running": running, "output": output})


def _kill_process(name: str, allow_process_control: bool) -> ToolResult:
    if not allow_process_control:
        return ToolResult(False, "Process control is disabled. Enable tools.allow_process_control in config.yaml.")
    if not name.strip():
        return ToolResult(False, "A process name is required.")
    os_name = current_platform()
    command = ["taskkill", "/IM", f"{name}*", "/F"] if os_name == PlatformName.WINDOWS else ["pkill", "-f", name]
    completed = subprocess.run(command, capture_output=True, text=True, check=False)
    if completed.returncode != 0:
        return ToolResult(False, completed.stderr.strip() or completed.stdout.strip() or f"Failed to stop {name}.")
    return ToolResult(True, f"Stopped {name}.", {"name": name})


def _restart_app(name: str, allow_process_control: bool) -> ToolResult:
    stopped = _kill_process(name, allow_process_control)
    if not stopped.success and "not found" not in stopped.message.lower():
        return stopped
    opened = _open_app(name)
    if not opened.success:
        return opened
    return ToolResult(True, f"Restarted {name}.", {"name": name})


def _wifi_state(state: str) -> ToolResult:
    command = resolve_wifi_command(state)
    if command is None:
        return ToolResult(False, f"Wi-Fi control is not available on {current_platform().value}.")
    completed = subprocess.run(command, capture_output=True, text=True, check=False)
    if completed.returncode != 0:
        return ToolResult(False, completed.stderr.strip() or completed.stdout.strip() or "Failed to update Wi-Fi state.")
    return ToolResult(True, f"Wi-Fi turned {state}.", {"state": state})


def _bluetooth_state(state: str) -> ToolResult:
    os_name = current_platform()
    if os_name == PlatformName.MACOS and shutil.which("blueutil"):
        command = ["blueutil", "--power", "1" if state == "on" else "0"]
    elif os_name == PlatformName.LINUX and shutil.which("bluetoothctl"):
        command = ["bluetoothctl", "power", state]
    else:
        command = None
    if command is None:
        return ToolResult(False, f"Bluetooth control is not available on {os_name.value}.")
    completed = subprocess.run(command, capture_output=True, text=True, check=False)
    if completed.returncode != 0:
        return ToolResult(False, completed.stderr.strip() or completed.stdout.strip() or "Failed to update Bluetooth state.")
    return ToolResult(True, f"Bluetooth turned {state}.", {"state": state})


def _power_action(action: str, allow_power_actions: bool) -> ToolResult:
    if not allow_power_actions:
        return ToolResult(False, "Power actions are disabled. Enable tools.allow_power_actions in config.yaml.")
    os_name = current_platform()
    commands = {
        PlatformName.WINDOWS: {
            "lock": ["rundll32.exe", "user32.dll,LockWorkStation"],
            "sleep": ["rundll32.exe", "powrprof.dll,SetSuspendState", "0,1,0"],
            "shutdown": ["shutdown", "/s", "/t", "0"],
            "restart": ["shutdown", "/r", "/t", "0"],
            "logout": ["shutdown", "/l"],
        },
        PlatformName.MACOS: {
            "lock": ["/System/Library/CoreServices/Menu Extras/User.menu/Contents/Resources/CGSession", "-suspend"],
            "sleep": ["pmset", "sleepnow"],
            "shutdown": ["osascript", "-e", 'tell app "System Events" to shut down'],
            "restart": ["osascript", "-e", 'tell app "System Events" to restart'],
            "logout": ["osascript", "-e", 'tell app "System Events" to log out'],
        },
        PlatformName.LINUX: {
            "lock": ["loginctl", "lock-session"],
            "sleep": ["systemctl", "suspend"],
            "shutdown": ["systemctl", "poweroff"],
            "restart": ["systemctl", "reboot"],
            "logout": ["loginctl", "terminate-user", getpass.getuser()],
        },
    }
    command = commands.get(os_name, {}).get(action)
    if command is None:
        return ToolResult(False, f"Action '{action}' is not supported on {os_name.value}.")
    completed = subprocess.run(command, capture_output=True, text=True, check=False)
    if completed.returncode != 0:
        return ToolResult(False, completed.stderr.strip() or completed.stdout.strip() or f"Failed to {action}.")
    return ToolResult(True, f"Requested system action: {action}.", {"action": action})


def _int_param(raw_value, default: int, minimum: int, maximum: int) -> int:
    try:
        value = int(raw_value)
    except (TypeError, ValueError):
        value = default
    return max(minimum, min(maximum, value))
