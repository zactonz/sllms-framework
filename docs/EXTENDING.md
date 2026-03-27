# Extending The Framework

## Add a Plugin Tool

Create a file in `plugins/`, for example `plugins/my_tool.py`:

```python
from tools.base import ToolDefinition, ToolResult


def register(registry, config) -> None:
    registry.register(
        ToolDefinition(
            name="ping_team",
            description="Send a simple message to the team system.",
            parameters={"message": "Message to send."},
            handler=_ping_team,
        )
    )


def _ping_team(params: dict) -> ToolResult:
    message = params.get("message", "").strip()
    if not message:
        return ToolResult(False, "No message provided.")
    return ToolResult(True, f"Would send: {message}")
```

Restart the app and the tool will be loaded automatically.

## Use Installed Child Repos

SLLMS can also load installed Python packages from separate child repos.

Option 1, explicit module loading in `config.yaml`:

```yaml
tools:
  plugin_modules:
    - "sllms_tools_notifications.plugin"
    - "sllms_tools_browser.plugin"
```

Option 2, entry point auto-discovery:

- install a package that exposes the `sllms.plugins` entry point group
- keep `tools.enable_entrypoint_discovery: true`
- restart SLLMS

See [Tool Packs](TOOL_PACKS.md) and [Repo Structure](REPO_STRUCTURE.md) for the full pattern.

## Add an Allowlisted API

Update `config.yaml`:

```yaml
apis:
  endpoints:
    weather_demo:
      url: "https://api.open-meteo.com/v1/forecast"
      method: "GET"
      timeout_seconds: 15
      allowed_query_params: ["latitude", "longitude", "current_weather"]
      allowed_body_fields: []
      headers: {}
```

The LLM can now target `call_api` safely through a named endpoint.

## Enable Local Commands

By default, shell execution is off.

```yaml
tools:
  allow_run_command: true
  allowed_commands:
    - "echo"
    - "git"
    - "make"
```

Only enable the commands you want available. Avoid allowlisting interpreter or shell entrypoints such as `python`, `bash`, `sh`, `cmd`, or `powershell` unless you explicitly want to grant that level of control.

## Swap Models

Change model paths in `config.yaml`:

- `stt.model`
- `llm.model`
- `tts.model`
- `tts.config`

To support another spoken language:

- use a multilingual Whisper model instead of an English-only `.en` model
- set `stt.language` to a code such as `es`, `fr`, `de`, or `auto`
- change the hotword phrase if your assistant should wake in another language
- select a Piper voice for that language if you want spoken replies
- extend the fast-path patterns in `llm/engine.py` if you want instant tool routing for additional languages or domain-specific phrases

To control microphone behavior:

- use `audio.device` to pin a specific input device
- use `audio.trigger_mode: push_to_talk` for manual capture workflows
- use `python main.py --list-audio-devices` to inspect available microphones

## Embed In Your App

You can import the assistant directly:

```python
from pathlib import Path
from sllms_framework import VoiceAssistantApp

app = VoiceAssistantApp(Path("config.yaml"))
result = app.process_text("open notepad", speak_override=False)
print(result.intent)
app.close()
```

## What Can Be Extended

Teams can extend SLLMS by adding:

- plugin tools
- custom shell allowlists
- allowlisted HTTP APIs
- different local models
- custom voices
- custom app wrappers or UIs
- background services around the assistant engine

This makes SLLMS suitable as a reusable foundation for complete products, not only as a demo CLI.
