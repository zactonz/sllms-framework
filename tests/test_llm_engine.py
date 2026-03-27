from __future__ import annotations

import unittest

from llm.engine import LocalLLMEngine
from tools.base import ToolDefinition, ToolRegistry, ToolResult


class LlmEngineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.registry = ToolRegistry()
        for tool_name in (
            "respond",
            "get_time",
            "open_app",
            "close_app",
            "web_search",
            "run_command",
            "show_memory",
            "open_url",
            "control_device",
            "open_settings",
            "open_downloads_folder",
            "list_processes",
            "wifi_on",
            "wifi_off",
        ):
            self.registry.register(
                ToolDefinition(
                    name=tool_name,
                    description="test",
                    parameters={},
                    handler=lambda params: ToolResult(True, "ok"),
                )
            )
        self.engine = LocalLLMEngine(
            {
                "executable": "missing-llama-cli",
                "model": "missing-model.gguf",
                "ctx_size": 2048,
                "max_tokens": 32,
                "temperature": 0.0,
                "top_p": 0.1,
                "repeat_penalty": 1.05,
                "threads": 1,
                "timeout_seconds": 5,
            },
            self.registry,
        )

    def test_multilingual_time_phrase_uses_fast_path(self) -> None:
        intent = self.engine.generate_intent("que hora es", [])
        self.assertEqual(intent["action"], "get_time")

    def test_search_phrase_routes_to_web_search(self) -> None:
        intent = self.engine.generate_intent("search google for cats", [])
        self.assertEqual(intent["action"], "web_search")
        self.assertEqual(intent["parameters"]["query"], "cats")


if __name__ == "__main__":
    unittest.main()
