from __future__ import annotations

import subprocess

from tools.base import ToolDefinition, ToolResult
from utils.platform import PlatformName, current_platform


def register(registry, config) -> None:
    registry.register(
        ToolDefinition(
            name="notify_user",
            description="Show a desktop notification with a title and message.",
            parameters={
                "title": "Notification title.",
                "message": "Notification message body.",
            },
            handler=_notify_user,
        )
    )


def _notify_user(params: dict) -> ToolResult:
    title = str(params.get("title", "")).strip() or "SLLMS"
    message = str(params.get("message", "")).strip()
    if not message:
        return ToolResult(False, "A notification message is required.")

    os_name = current_platform()
    if os_name == PlatformName.WINDOWS:
        command = [
            "powershell",
            "-NoProfile",
            "-Command",
            (
                "Add-Type -AssemblyName System.Windows.Forms; "
                "$notify = New-Object System.Windows.Forms.NotifyIcon; "
                "$notify.Icon = [System.Drawing.SystemIcons]::Information; "
                f"$notify.BalloonTipTitle = '{title}'; "
                f"$notify.BalloonTipText = '{message}'; "
                "$notify.Visible = $true; "
                "$notify.ShowBalloonTip(5000)"
            ),
        ]
    elif os_name == PlatformName.MACOS:
        command = ["osascript", "-e", f'display notification "{message}" with title "{title}"']
    else:
        command = ["notify-send", title, message]

    completed = subprocess.run(command, capture_output=True, text=True, check=False)
    if completed.returncode != 0:
        return ToolResult(False, completed.stderr.strip() or completed.stdout.strip() or "Notification failed.")
    return ToolResult(True, f"Notification sent: {title}")
