# Adding Custom Tools

SLLMS is designed to be extended.

The easiest way to add your own features is to create a plugin in `plugins/` and register one or more tools.

## Plugin Shape

Each plugin is a normal Python file with a `register(registry, config)` function.

Example:

```python
from tools.base import ToolDefinition, ToolResult


def register(registry, config) -> None:
    registry.register(
        ToolDefinition(
            name="say_hello_to_team",
            description="Return a demo message for the team.",
            parameters={"name": "Team member name."},
            handler=_say_hello_to_team,
        )
    )


def _say_hello_to_team(params: dict) -> ToolResult:
    name = str(params.get("name", "")).strip()
    if not name:
        return ToolResult(False, "A name is required.")
    return ToolResult(True, f"Hello, {name}.")
```

After saving the file in `plugins/`, restart the assistant and the tool will be loaded automatically.

## Recommended Workflow

1. Create a new plugin file in `plugins/`.
2. Register one or more `ToolDefinition` objects.
3. Validate all parameters inside the handler.
4. Return a `ToolResult`.
5. Test the tool directly from Python or with a text prompt.

## Testing A Custom Tool Directly

```python
from pathlib import Path
from main import VoiceAssistantApp

app = VoiceAssistantApp(Path("config.yaml"))
result = app.dispatcher.dispatch(
    {"action": "say_hello_to_team", "parameters": {"name": "Zactonz"}}
)
print(result.message)
app.close()
```

## Where To Put Custom Logic

Good plugin candidates:

- internal APIs
- CRM and ERP integrations
- desktop automation for a specific company workflow
- project-specific build or deployment steps
- hardware/device integrations
- note-taking or operator workflows

## Safety Guidance

Treat plugin handlers like production code:

- validate input strictly
- avoid arbitrary shell execution unless you really need it
- keep destructive actions behind config flags
- log important actions
- make error messages clear and actionable

## Going Beyond Plugins

If you want deeper integration, you can also:

- point SLLMS at different models in `config.yaml`
- add new built-in tool modules under `tools/`
- add fast-path command routing in `llm/engine.py`
- embed `VoiceAssistantApp` inside your own desktop app, web service, kiosk app, or operator console

If you want a reusable niche package rather than a single local plugin, see [Tool Packs](TOOL_PACKS.md). The core repo ships a template for external child repos in `templates/sllms_tool_pack_template/`, while reusable tool families should live outside the core repo.

## Useful Files To Study

- `plugins/README.md`
- `examples/plugins/todo_plugin.py`
- `tools/base.py`
- `tools/system_tools.py`
- `docs/EXTENDING.md`
