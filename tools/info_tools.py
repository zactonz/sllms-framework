from __future__ import annotations

import getpass
import os
import platform
import shutil
import socket
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path

from tools.base import ToolDefinition, ToolRegistry, ToolResult
from utils.platform import PlatformName, current_platform


def register_info_tools(registry: ToolRegistry, config: dict) -> None:
    workspace_root = Path(config["tools"]["workspace_root"]).resolve()
    notes_dir = Path(config["tools"]["notes_dir"]).resolve()
    log_dir = Path(config["logging"]["file"]).resolve().parent
    models_dir = Path(config["stt"]["model"]).resolve().parents[1]
    plugins_dir = Path(config["tools"]["plugins_dir"]).resolve()

    _register_time_tools(registry)
    _register_system_info_tools(registry)
    _register_folder_tools(registry, workspace_root, notes_dir, log_dir, models_dir, plugins_dir)
    _register_network_info_tools(registry)


def _register_time_tools(registry: ToolRegistry) -> None:
    _register(registry, "get_date", "Return the current local date.", {}, lambda params: _time_result("%A, %B %d, %Y", "date"))
    _register(registry, "get_day_of_week", "Return the current local day of the week.", {}, lambda params: _time_result("%A", "day_of_week"))
    _register(registry, "get_month", "Return the current local month name.", {}, lambda params: _time_result("%B", "month"))
    _register(registry, "get_year", "Return the current local year.", {}, lambda params: _time_result("%Y", "year"))
    _register(registry, "get_timezone", "Return the current local timezone.", {}, lambda params: _timezone_result())
    _register(registry, "get_timestamp", "Return the current local ISO timestamp.", {}, lambda params: _timestamp_result())


def _register_system_info_tools(registry: ToolRegistry) -> None:
    _register(registry, "get_hostname", "Return the local hostname.", {}, lambda params: _ok(f"Hostname: {socket.gethostname()}", {"hostname": socket.gethostname()}))
    _register(registry, "get_os_name", "Return the operating system name.", {}, lambda params: _ok(f"Operating system: {platform.system()}", {"os_name": platform.system()}))
    _register(registry, "get_os_release", "Return the operating system release.", {}, lambda params: _ok(f"OS release: {platform.release()}", {"os_release": platform.release()}))
    _register(registry, "get_os_version", "Return the operating system version.", {}, lambda params: _ok(f"OS version: {platform.version()}", {"os_version": platform.version()}))
    _register(registry, "get_machine_arch", "Return the machine architecture.", {}, lambda params: _ok(f"Architecture: {platform.machine()}", {"architecture": platform.machine()}))
    _register(registry, "get_cpu_count", "Return the available CPU count.", {}, lambda params: _ok(f"CPU count: {os.cpu_count() or 1}", {"cpu_count": os.cpu_count() or 1}))
    _register(registry, "get_python_version", "Return the current Python version.", {}, lambda params: _ok(f"Python version: {platform.python_version()}", {"python_version": platform.python_version()}))
    _register(registry, "get_username", "Return the current OS username.", {}, lambda params: _ok(f"Current user: {getpass.getuser()}", {"username": getpass.getuser()}))
    _register(registry, "get_home_directory", "Return the current home directory.", {}, lambda params: _path_result("Home directory", Path.home()))
    _register(registry, "get_working_directory", "Return the current working directory.", {}, lambda params: _path_result("Working directory", Path.cwd()))
    _register(registry, "get_temp_directory", "Return the system temp directory.", {}, lambda params: _path_result("Temp directory", Path(tempfile.gettempdir())))
    _register(registry, "get_disk_usage", "Return disk usage for the current working directory.", {}, lambda params: _disk_usage_result(Path.cwd()))
    _register(registry, "get_environment_summary", "Return a short environment summary.", {}, lambda params: _environment_summary_result())
    _register(registry, "get_path_variable", "Return the PATH environment variable.", {}, lambda params: _ok(os.environ.get("PATH", ""), {"path": os.environ.get("PATH", "")}))
    registry.register(
        ToolDefinition(
            name="get_environment_variable",
            description="Return the value of a named environment variable.",
            parameters={"name": "Environment variable name."},
            handler=lambda params: _environment_variable_result(str(params.get("name", "")).strip()),
        )
    )
    _register(registry, "get_local_ip", "Return local IP address information.", {}, lambda params: _local_ip_result())
    _register(registry, "get_platform_summary", "Return a platform summary for the current machine.", {}, lambda params: _platform_summary_result())
    _register(registry, "list_audio_inputs", "List detected audio input devices.", {}, lambda params: _audio_inputs_result())


def _register_folder_tools(
    registry: ToolRegistry,
    workspace_root: Path,
    notes_dir: Path,
    log_dir: Path,
    models_dir: Path,
    plugins_dir: Path,
) -> None:
    folders = {
        "open_home_folder": ("Open the user's home folder.", Path.home()),
        "open_desktop_folder": ("Open the Desktop folder.", Path.home() / "Desktop"),
        "open_downloads_folder": ("Open the Downloads folder.", Path.home() / "Downloads"),
        "open_documents_folder": ("Open the Documents folder.", Path.home() / "Documents"),
        "open_pictures_folder": ("Open the Pictures folder.", Path.home() / "Pictures"),
        "open_music_folder": ("Open the Music folder.", Path.home() / "Music"),
        "open_videos_folder": ("Open the Videos folder.", Path.home() / "Videos"),
        "open_temp_folder": ("Open the system temp folder.", Path(tempfile.gettempdir())),
        "open_workspace_folder": ("Open the configured workspace root.", workspace_root),
        "open_notes_folder": ("Open the configured notes directory.", notes_dir),
        "open_logs_folder": ("Open the log directory.", log_dir),
        "open_models_folder": ("Open the models directory.", models_dir),
        "open_plugins_folder": ("Open the plugins directory.", plugins_dir),
        "open_docs_folder": ("Open the docs directory.", workspace_root / "docs"),
        "open_examples_folder": ("Open the examples directory.", workspace_root / "examples"),
        "open_scripts_folder": ("Open the scripts directory.", workspace_root / "scripts"),
    }
    for tool_name, (description, folder_path) in folders.items():
        _register(registry, tool_name, description, {}, lambda params, path=folder_path: _open_path(path))
    registry.register(
        ToolDefinition(
            name="open_folder",
            description="Open a workspace-relative folder path in the default app.",
            parameters={"path": "Workspace-relative folder path. Defaults to '.'."},
            handler=lambda params: _open_workspace_folder(workspace_root, str(params.get("path", "") or ".")),
        )
    )
    _register(registry, "open_readme_file", "Open README.md in the default app.", {}, lambda params, path=workspace_root / "README.md": _open_path(path))
    _register(registry, "open_config_file", "Open config.yaml in the default app.", {}, lambda params, path=workspace_root / "config.yaml": _open_path(path))


def _register_network_info_tools(registry: ToolRegistry) -> None:
    registry.register(
        ToolDefinition(
            name="resolve_hostname",
            description="Resolve a hostname to IP addresses.",
            parameters={"host": "Hostname to resolve."},
            handler=lambda params: _resolve_hostname(str(params.get("host", "")).strip()),
        )
    )
    registry.register(
        ToolDefinition(
            name="ping_host",
            description="Ping a host or IP address.",
            parameters={"host": "Hostname or IP address to ping."},
            handler=lambda params: _ping_host(str(params.get("host", "")).strip()),
        )
    )
    _register(registry, "get_network_summary", "Return a simple local network summary.", {}, lambda params: _network_summary_result())


def _register(registry: ToolRegistry, name: str, description: str, parameters: dict[str, str], handler) -> None:
    registry.register(ToolDefinition(name=name, description=description, parameters=parameters, handler=handler))


def _time_result(fmt: str, label: str) -> ToolResult:
    now = datetime.now().astimezone()
    value = now.strftime(fmt)
    return _ok(value, {label: value, "iso": now.isoformat()})


def _timezone_result() -> ToolResult:
    now = datetime.now().astimezone()
    zone = str(now.tzinfo)
    return _ok(f"Timezone: {zone}", {"timezone": zone, "iso": now.isoformat()})


def _timestamp_result() -> ToolResult:
    timestamp = datetime.now().astimezone().isoformat()
    return _ok(timestamp, {"timestamp": timestamp})


def _path_result(label: str, path: Path) -> ToolResult:
    resolved = path.resolve()
    return _ok(f"{label}: {resolved}", {"path": str(resolved)})


def _disk_usage_result(path: Path) -> ToolResult:
    usage = shutil.disk_usage(path)
    data = {
        "path": str(path.resolve()),
        "total_gb": round(usage.total / (1024**3), 2),
        "used_gb": round((usage.total - usage.free) / (1024**3), 2),
        "free_gb": round(usage.free / (1024**3), 2),
    }
    return _ok(
        f"Disk usage: total {data['total_gb']} GB, used {data['used_gb']} GB, free {data['free_gb']} GB.",
        data,
    )


def _environment_summary_result() -> ToolResult:
    data = {
        "username": getpass.getuser(),
        "cwd": str(Path.cwd()),
        "home": str(Path.home()),
        "temp": tempfile.gettempdir(),
        "python": sys.executable,
    }
    return _ok(
        f"User {data['username']} in {data['cwd']} using Python {data['python']}.",
        data,
    )


def _environment_variable_result(name: str) -> ToolResult:
    if not name:
        return ToolResult(False, "An environment variable name is required.")
    value = os.environ.get(name)
    if value is None:
        return ToolResult(False, f"Environment variable '{name}' was not found.")
    return _ok(value, {"name": name, "value": value})


def _local_ip_result() -> ToolResult:
    hostname = socket.gethostname()
    addresses = sorted({item[4][0] for item in socket.getaddrinfo(hostname, None) if item[4]})
    return _ok(f"Local addresses: {', '.join(addresses) if addresses else 'none found'}", {"hostname": hostname, "addresses": addresses})


def _platform_summary_result() -> ToolResult:
    data = {
        "platform": platform.system(),
        "release": platform.release(),
        "version": platform.version(),
        "machine": platform.machine(),
        "python": platform.python_version(),
    }
    return _ok(
        f"{data['platform']} {data['release']} on {data['machine']} using Python {data['python']}.",
        data,
    )


def _audio_inputs_result() -> ToolResult:
    from stt.audio import AudioInputError, MicrophoneRecorder

    try:
        devices = MicrophoneRecorder.list_input_devices()
    except AudioInputError as exc:
        return ToolResult(False, str(exc))
    if not devices:
        return _ok("No audio input devices were found.", {"devices": []})
    names = [device["name"] for device in devices]
    return _ok(f"Audio inputs: {', '.join(names)}", {"devices": devices})


def _open_path(path: Path) -> ToolResult:
    target = path.resolve()
    if not target.exists():
        return ToolResult(False, f"Path does not exist: {target}")
    os_name = current_platform()
    if os_name == PlatformName.WINDOWS:
        command = ["powershell", "-NoProfile", "-Command", f"Start-Process '{target}'"]
    elif os_name == PlatformName.MACOS:
        command = ["open", str(target)]
    else:
        command = ["xdg-open", str(target)]
    completed = subprocess.run(command, capture_output=True, text=True, check=False)
    if completed.returncode != 0:
        return ToolResult(False, completed.stderr.strip() or completed.stdout.strip() or f"Failed to open {target}.")
    return _ok(f"Opened {target}.", {"path": str(target)})


def _resolve_hostname(host: str) -> ToolResult:
    if not host:
        return ToolResult(False, "A host is required.")
    try:
        addresses = sorted({item[4][0] for item in socket.getaddrinfo(host, None)})
    except socket.gaierror as exc:
        return ToolResult(False, f"Unable to resolve {host}: {exc}")
    return _ok(f"{host}: {', '.join(addresses)}", {"host": host, "addresses": addresses})


def _ping_host(host: str) -> ToolResult:
    if not host:
        return ToolResult(False, "A host is required.")
    count_flag = "-n" if current_platform() == PlatformName.WINDOWS else "-c"
    completed = subprocess.run(["ping", count_flag, "2", host], capture_output=True, text=True, check=False, timeout=20)
    output = (completed.stdout or completed.stderr).strip()
    if completed.returncode != 0:
        return ToolResult(False, output or f"Ping failed for {host}.")
    return _ok(output, {"host": host})


def _network_summary_result() -> ToolResult:
    return _local_ip_result()


def _ok(message: str, data: dict | None = None) -> ToolResult:
    return ToolResult(True, message, data)


def _open_workspace_folder(workspace_root: Path, raw_path: str) -> ToolResult:
    try:
        path = _resolve_workspace_relative_path(workspace_root, raw_path)
    except ValueError as exc:
        return ToolResult(False, str(exc))
    if not path.is_dir():
        return ToolResult(False, f"Path is not a directory: {path}")
    return _open_path(path)


def _resolve_workspace_relative_path(workspace_root: Path, raw_path: str) -> Path:
    candidate = Path(raw_path.strip() or ".")
    if not candidate.is_absolute():
        candidate = workspace_root / candidate
    candidate = candidate.resolve()
    try:
        candidate.relative_to(workspace_root)
    except ValueError as exc:
        raise ValueError(f"Path '{candidate}' is outside the configured workspace root {workspace_root}.") from exc
    return candidate
