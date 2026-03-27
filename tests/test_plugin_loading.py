from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tools.base import ToolRegistry


class PluginLoadingTests(unittest.TestCase):
    def test_bad_local_plugin_does_not_break_good_plugin_loading(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            plugins_dir = Path(tmp_dir)
            (plugins_dir / "good_plugin.py").write_text(
                """
from tools.base import ToolDefinition, ToolResult


def register(registry, config):
    registry.register(
        ToolDefinition(
            name="good_tool",
            description="test",
            parameters={},
            handler=lambda params: ToolResult(True, "ok"),
        )
    )
""".strip()
                + "\n",
                encoding="utf-8",
            )
            (plugins_dir / "broken_plugin.py").write_text("raise RuntimeError('boom')\n", encoding="utf-8")

            registry = ToolRegistry()
            registry.load_plugins(
                plugins_dir,
                {
                    "tools": {
                        "plugin_modules": [],
                        "enable_entrypoint_discovery": False,
                    }
                },
            )

            self.assertIn("good_tool", registry.tool_names())
            self.assertEqual(len(registry.plugin_modules), 1)


if __name__ == "__main__":
    unittest.main()
