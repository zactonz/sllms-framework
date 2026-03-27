from __future__ import annotations

from tools.base import ToolDefinition, ToolResult


def register(registry, config) -> None:
    registry.register(
        ToolDefinition(
            name="template_tool",
            description="Example external tool-pack action.",
            parameters={"name": "Example parameter."},
            handler=_template_tool,
        )
    )


def _template_tool(params: dict) -> ToolResult:
    name = str(params.get("name", "")).strip() or "world"
    return ToolResult(True, f"Hello from the external tool pack, {name}.")
