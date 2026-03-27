from __future__ import annotations

from pathlib import Path

from tools.base import ToolDefinition, ToolResult


TODO_PATH = Path("todo-items.txt")


def register(registry, config) -> None:
    registry.register(
        ToolDefinition(
            name="add_todo",
            description="Add a todo item to a local text file.",
            parameters={"item": "Todo item text."},
            handler=_add_todo,
        )
    )


def _add_todo(params: dict) -> ToolResult:
    item = str(params.get("item", "")).strip()
    if not item:
        return ToolResult(False, "No todo item was provided.")
    with TODO_PATH.open("a", encoding="utf-8") as handle:
        handle.write(f"- {item}\n")
    return ToolResult(True, f"Added todo: {item}")
