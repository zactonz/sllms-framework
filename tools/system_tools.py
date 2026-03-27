from __future__ import annotations

from datetime import datetime
import json
import re
import shlex
import subprocess
import urllib.error
import urllib.parse
import urllib.request
import webbrowser
from pathlib import Path
from urllib.parse import quote_plus

from tools.base import ToolDefinition, ToolRegistry, ToolResult
from tools.content_tools import register_content_tools
from tools.control_tools import register_control_tools
from tools.info_tools import register_info_tools
from utils.platform import build_open_app_command, current_platform, resolve_app_alias, resolve_wifi_command


def register_builtin_tools(registry: ToolRegistry, config: dict, memory=None) -> None:
    registry.register(
        ToolDefinition(
            name="open_app",
            description="Open a desktop application by name.",
            parameters={"name": "Application name or alias, such as notepad or chrome."},
            handler=lambda params: open_app(params.get("name", "")),
        )
    )
    registry.register(
        ToolDefinition(
            name="run_command",
            description="Run a single allowlisted command when explicitly allowed by configuration.",
            parameters={"cmd": "Single shell command string."},
            handler=lambda params: run_command(params.get("cmd", ""), config),
        )
    )
    registry.register(
        ToolDefinition(
            name="control_device",
            description="Control a supported device like wifi by setting a state such as on or off.",
            parameters={"device": "Supported device name.", "state": "Requested state."},
            handler=lambda params: control_device(params.get("device", ""), params.get("state", "")),
        )
    )
    registry.register(
        ToolDefinition(
            name="web_search",
            description="Open the default browser with a Google search.",
            parameters={"query": "Search query string."},
            handler=lambda params: web_search(params.get("query", "")),
        )
    )
    registry.register(
        ToolDefinition(
            name="open_url",
            description="Open an explicit URL in the default browser.",
            parameters={"url": "Absolute http or https URL to open."},
            handler=lambda params: open_url(params.get("url", "")),
        )
    )
    registry.register(
        ToolDefinition(
            name="respond",
            description="Return a plain assistant reply without executing a system action.",
            parameters={"message": "Text to say back to the user."},
            handler=lambda params: respond(params.get("message", "")),
        )
    )
    registry.register(
        ToolDefinition(
            name="get_time",
            description="Return the current local date and time.",
            parameters={},
            handler=lambda params: get_time(),
        )
    )
    registry.register(
        ToolDefinition(
            name="call_api",
            description="Call a configured external HTTP API endpoint from the allowlist.",
            parameters={
                "name": "Configured endpoint name from config.yaml.",
                "query": "Optional query parameters object.",
                "body": "Optional JSON body object.",
            },
            handler=lambda params: call_api(params, config),
        )
    )
    registry.register(
        ToolDefinition(
            name="show_memory",
            description="Show recent assistant interactions stored in short-term memory.",
            parameters={"limit": "Optional number of recent items to show."},
            handler=lambda params: show_memory(params, memory),
        )
    )
    register_info_tools(registry, config)
    register_content_tools(registry, config, memory)
    register_control_tools(registry, config)


def open_app(name: str) -> ToolResult:
    if not name.strip():
        return ToolResult(False, "No application name was provided.")
    os_name = current_platform()
    resolved_name = resolve_app_alias(name.strip(), os_name)
    completed = subprocess.run(build_open_app_command(resolved_name, os_name), capture_output=True, text=True, check=False)
    if completed.returncode != 0:
        stderr = completed.stderr.strip() or completed.stdout.strip()
        return ToolResult(False, f"Failed to open {name}: {stderr}")
    return ToolResult(True, f"Opening {name}.")


def run_command(cmd: str, config: dict) -> ToolResult:
    if not cmd.strip():
        return ToolResult(False, "No command was provided.")
    if not config["tools"]["allow_run_command"]:
        return ToolResult(False, "run_command is disabled in config.yaml.")

    command_args = _parse_command_args(cmd)
    if not command_args:
        return ToolResult(
            False,
            "Only a single command with arguments is allowed. Shell operators, redirection, and command chaining are blocked.",
        )

    first_token = Path(command_args[0]).name.lower()
    allowed = set(config["tools"]["allowed_commands"])
    if first_token not in allowed:
        return ToolResult(False, f"Command '{first_token}' is not in the allowed command list.")

    completed = subprocess.run(
        command_args,
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
        cwd=str(Path(config["tools"]["workspace_root"]).resolve()),
    )
    output = (completed.stdout or completed.stderr).strip()
    if completed.returncode != 0:
        return ToolResult(False, f"Command failed: {output}")
    return ToolResult(True, output or f"Command '{cmd}' completed successfully.")


def control_device(device: str, state: str) -> ToolResult:
    normalized_device = device.strip().lower()
    normalized_state = state.strip().lower()
    if normalized_device != "wifi":
        return ToolResult(False, f"Unsupported device '{device}'. Built-in support currently covers wifi.")
    if normalized_state not in {"on", "off", "enable", "disable"}:
        return ToolResult(False, f"Unsupported state '{state}' for wifi. Use on or off.")

    command = resolve_wifi_command(normalized_state)
    if command is None:
        return ToolResult(False, f"Wi-Fi control is not available on {current_platform().value}.")

    completed = subprocess.run(command, capture_output=True, text=True, check=False)
    if completed.returncode != 0:
        stderr = completed.stderr.strip() or completed.stdout.strip()
        return ToolResult(False, f"Failed to update wifi state: {stderr}")

    desired_state = "on" if normalized_state in {"on", "enable"} else "off"
    return ToolResult(True, f"Wi-Fi turned {desired_state}.")


def web_search(query: str) -> ToolResult:
    if not query.strip():
        return ToolResult(False, "No search query was provided.")
    url = f"https://www.google.com/search?q={quote_plus(query.strip())}"
    opened = webbrowser.open_new_tab(url)
    if not opened:
        return ToolResult(False, f"Unable to open a browser for query '{query}'.")
    return ToolResult(True, f"Searching Google for {query}.", {"url": url})


def open_url(url: str) -> ToolResult:
    candidate = url.strip()
    if not candidate:
        return ToolResult(False, "No URL was provided.")
    lowered = candidate.lower()
    if not (lowered.startswith("http://") or lowered.startswith("https://")):
        return ToolResult(False, "Only absolute http or https URLs are allowed.")
    opened = webbrowser.open_new_tab(candidate)
    if not opened:
        return ToolResult(False, f"Unable to open {candidate}.")
    return ToolResult(True, f"Opening {candidate}.", {"url": candidate})


def respond(message: str) -> ToolResult:
    reply = message.strip() or "I am ready."
    return ToolResult(True, reply)


def get_time() -> ToolResult:
    now = datetime.now().astimezone()
    return ToolResult(
        True,
        now.strftime("The local time is %I:%M %p on %A, %B %d, %Y."),
        {
            "iso": now.isoformat(),
            "timezone": str(now.tzinfo),
        },
    )


def call_api(params: dict, config: dict) -> ToolResult:
    endpoint_name = str(params.get("name", "")).strip()
    if not endpoint_name:
        return ToolResult(False, "No API endpoint name was provided.")

    endpoints = config.get("apis", {}).get("endpoints", {})
    endpoint = endpoints.get(endpoint_name)
    if not endpoint:
        return ToolResult(False, f"API endpoint '{endpoint_name}' is not configured in config.yaml.")

    method = str(endpoint.get("method", "GET")).upper()
    base_url = str(endpoint.get("url", "")).strip()
    timeout_seconds = int(endpoint.get("timeout_seconds", 20))
    static_headers = dict(endpoint.get("headers", {}))
    query = params.get("query", {}) or {}
    body = params.get("body", {}) or {}

    if not isinstance(query, dict) or not isinstance(body, dict):
        return ToolResult(False, "API query and body parameters must be JSON objects.")

    allowed_query = set(endpoint.get("allowed_query_params", []))
    allowed_body = set(endpoint.get("allowed_body_fields", []))

    unexpected_query = sorted(set(query.keys()) - allowed_query)
    unexpected_body = sorted(set(body.keys()) - allowed_body)
    if unexpected_query:
        return ToolResult(False, f"Query parameters not allowed for '{endpoint_name}': {', '.join(unexpected_query)}.")
    if unexpected_body:
        return ToolResult(False, f"Body fields not allowed for '{endpoint_name}': {', '.join(unexpected_body)}.")

    url = base_url
    if query:
        encoded_query = urllib.parse.urlencode(query, doseq=True)
        separator = "&" if "?" in base_url else "?"
        url = f"{base_url}{separator}{encoded_query}"

    payload = None
    headers = {"User-Agent": "sllms-framework/1.0", **static_headers}
    if method in {"POST", "PUT", "PATCH"}:
        payload = json.dumps(body).encode("utf-8")
        headers.setdefault("Content-Type", "application/json")

    request = urllib.request.Request(url=url, data=payload, method=method, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            response_text = response.read().decode("utf-8", errors="replace")
            preview = response_text[:500].strip()
            return ToolResult(
                True,
                f"API '{endpoint_name}' returned HTTP {response.status}.",
                {"status": response.status, "body_preview": preview, "url": url},
            )
    except urllib.error.HTTPError as exc:
        body_text = exc.read().decode("utf-8", errors="replace")
        return ToolResult(False, f"API '{endpoint_name}' failed with HTTP {exc.code}: {body_text[:300].strip()}")
    except urllib.error.URLError as exc:
        return ToolResult(False, f"API '{endpoint_name}' request failed: {exc.reason}")


def show_memory(params: dict, memory) -> ToolResult:
    if memory is None:
        return ToolResult(False, "Assistant memory is unavailable.")
    try:
        limit = int(params.get("limit", 5))
    except (TypeError, ValueError):
        limit = 5
    limit = max(1, min(limit, 20))
    items = memory.recent_items()[-limit:]
    if not items:
        return ToolResult(True, "No recent memory items were found.", {"items": []})
    lines = []
    for index, item in enumerate(items, start=1):
        text = str(item.get("text", "")).strip()
        action = str(item.get("intent", {}).get("action", "unknown"))
        success = bool(item.get("success", False))
        lines.append(f"{index}. [{action}] {'ok' if success else 'failed'}: {text}")
    return ToolResult(True, "\n".join(lines), {"items": items})


def _first_command_token(command: str) -> str:
    tokenized = _parse_command_args(command)
    if tokenized:
        return Path(tokenized[0]).name.lower()
    match = re.match(r"^\s*([^\s]+)", command)
    return Path(match.group(1)).name.lower() if match else ""


def _parse_command_args(command: str) -> list[str]:
    stripped = command.strip()
    if not stripped or _contains_shell_syntax(stripped):
        return []
    try:
        return shlex.split(stripped, posix=current_platform().value != "windows")
    except ValueError:
        return []


def _contains_shell_syntax(command: str) -> bool:
    shell_tokens = ("&&", "||", "|", ";", ">", "<", "`", "$(", "\n", "\r")
    return any(token in command for token in shell_tokens)
