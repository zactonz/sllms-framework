from __future__ import annotations

import unittest
from pathlib import Path

from utils.config import load_config


ROOT = Path(__file__).resolve().parent.parent


class ExampleConfigTests(unittest.TestCase):
    def test_api_weather_example_resolves_repo_root_paths(self) -> None:
        config = load_config(ROOT / "examples/configs/api_weather.example.yaml")

        self.assertEqual(Path(config["stt"]["model"]), ROOT / "models/whisper/ggml-base.en.bin")
        self.assertEqual(Path(config["llm"]["model"]), ROOT / "models/llm/Phi-3-mini-4k-instruct-q4.gguf")
        self.assertEqual(Path(config["tools"]["plugins_dir"]), ROOT / "examples/plugins")
        self.assertEqual(Path(config["tools"]["workspace_root"]), ROOT)

    def test_home_robot_example_resolves_repo_root_paths(self) -> None:
        config = load_config(ROOT / "examples/configs/home_robot.example.yaml")

        self.assertEqual(str(config["assistant"]["name"]), "HomeRobot")
        self.assertEqual(Path(config["stt"]["model"]), ROOT / "models/whisper/ggml-base.en.bin")
        self.assertEqual(Path(config["tools"]["plugins_dir"]), ROOT / "examples/plugins")
        self.assertEqual(Path(config["memory"]["path"]), ROOT / ".assistant_memory.json")

    def test_multilingual_example_uses_repo_relative_models(self) -> None:
        config = load_config(ROOT / "examples/configs/multilingual_spanish.example.yaml")

        self.assertEqual(Path(config["stt"]["model"]), ROOT / "models/whisper/ggml-base.bin")
        self.assertEqual(Path(config["tts"]["model"]), ROOT / "models/piper/es_ES-sharvard-medium.onnx")
        self.assertEqual(Path(config["runtime"]["daemon_log"]), ROOT / "assistant-daemon.log")


if __name__ == "__main__":
    unittest.main()
