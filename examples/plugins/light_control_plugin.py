from __future__ import annotations

import json
from pathlib import Path

from tools.base import ToolDefinition, ToolResult


def register(registry, config) -> None:
    registry.register(
        ToolDefinition(
            name="set_light_state",
            description="Turn a named smart light on or off. Example requests: turn on the kitchen light, switch off bedroom light.",
            parameters={
                "name": "Light name such as kitchen, hallway, or bedroom.",
                "state": "Requested state: on or off.",
            },
            handler=lambda params: _set_light_state(config, params),
        )
    )
    registry.register(
        ToolDefinition(
            name="get_light_state",
            description="Read the current stored state for a named smart light.",
            parameters={"name": "Light name such as kitchen or hallway."},
            handler=lambda params: _get_light_state(config, params),
        )
    )


def _set_light_state(config: dict, params: dict) -> ToolResult:
    name = str(params.get("name", "")).strip().lower()
    state = str(params.get("state", "")).strip().lower()
    if not name:
        return ToolResult(False, "A light name is required.")
    if state not in {"on", "off"}:
        return ToolResult(False, "Light state must be 'on' or 'off'.")

    light_state = _load_state(config)
    light_state[name] = state
    _save_state(config, light_state)
    return ToolResult(True, f"The {name} light is now {state}.", {"name": name, "state": state})


def _get_light_state(config: dict, params: dict) -> ToolResult:
    name = str(params.get("name", "")).strip().lower()
    if not name:
        return ToolResult(False, "A light name is required.")

    light_state = _load_state(config)
    state = light_state.get(name, "unknown")
    if state == "unknown":
        return ToolResult(True, f"No stored state was found for the {name} light.", {"name": name, "state": state})
    return ToolResult(True, f"The {name} light is currently {state}.", {"name": name, "state": state})


def _state_path(config: dict) -> Path:
    notes_dir = Path(config["tools"]["notes_dir"]).resolve()
    notes_dir.mkdir(parents=True, exist_ok=True)
    return notes_dir / "light-state.json"


def _load_state(config: dict) -> dict[str, str]:
    path = _state_path(config)
    if not path.exists():
        return {}
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return {str(key): str(value) for key, value in raw.items()}


def _save_state(config: dict, state: dict[str, str]) -> None:
    path = _state_path(config)
    path.write_text(json.dumps(state, indent=2, sort_keys=True), encoding="utf-8")
