from __future__ import annotations

import json
from pathlib import Path


class AssistantMemory:
    def __init__(self, config: dict):
        self.enabled = bool(config["enabled"])
        self.path = Path(config["path"]).resolve()
        self.max_items = int(config["max_items"])
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if self.enabled and not self.path.exists():
            self.path.write_text("[]", encoding="utf-8")

    def recent_items(self) -> list[dict]:
        if not self.enabled or not self.path.exists():
            return []
        try:
            return json.loads(self.path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return []

    def add_item(self, item: dict) -> None:
        if not self.enabled:
            return
        items = self.recent_items()
        items.append(item)
        items = items[-self.max_items :]
        self.path.write_text(json.dumps(items, indent=2), encoding="utf-8")
