from __future__ import annotations

import copy
import os
from pathlib import Path

from utils.platform import apply_platform_executable_suffix


DEFAULT_CONFIG = {
    "assistant": {
        "name": "EdgeVoice",
        "hotword": {"enabled": True, "phrase": "hey assistant"},
        "tts_enabled": True,
        "log_level": "INFO",
    },
    "audio": {
        "sample_rate": 16000,
        "channels": 1,
        "block_duration_ms": 30,
        "silence_duration_s": 1.1,
        "max_record_seconds": 12,
        "energy_threshold": 450.0,
        "device": None,
        "trigger_mode": "voice",
    },
    "stt": {
        "executable": "models/whisper-runtime/whisper-cli",
        "model": "models/whisper/ggml-base.en.bin",
        "language": "en",
        "threads": 4,
    },
    "llm": {
        "executable": "models/llama-runtime/llama-cli",
        "model": "models/llm/Phi-3-mini-4k-instruct-q4.gguf",
        "ctx_size": 2048,
        "max_tokens": 96,
        "temperature": 0.0,
        "top_p": 0.1,
        "repeat_penalty": 1.05,
        "threads": 4,
        "timeout_seconds": 12,
    },
    "tts": {
        "executable": "models/piper-runtime/piper/piper",
        "model": "models/piper/en_US-lessac-medium.onnx",
        "config": "models/piper/en_US-lessac-medium.onnx.json",
        "speaker": 0,
        "length_scale": 1.0,
        "noise_scale": 0.667,
        "noise_w": 0.8,
    },
    "browser": {
        "engine": "chromium",
        "channel": None,
        "headless": False,
        "timeout_ms": 10000,
        "slow_mo_ms": 0,
        "viewport_width": 1440,
        "viewport_height": 900,
        "downloads_dir": "browser-downloads",
    },
    "tools": {
        "allow_run_command": False,
        "allow_workspace_writes": False,
        "allow_process_control": False,
        "allow_power_actions": False,
        "allow_sensitive_actions": False,
        "allowed_commands": ["echo", "dir", "ls", "pwd", "whoami"],
        "plugins_dir": "plugins",
        "plugin_modules": [],
        "enable_entrypoint_discovery": True,
        "plugin_entrypoint_group": "sllms.plugins",
        "workspace_root": ".",
        "notes_dir": "notes",
        "screenshots_dir": "screenshots",
    },
    "apis": {"endpoints": {}},
    "memory": {"enabled": True, "path": ".assistant_memory.json", "max_items": 12},
    "logging": {"file": "assistant.log"},
    "runtime": {"pid_file": ".assistant.pid", "daemon_log": "assistant-daemon.log"},
}


def load_config(config_path: Path) -> dict:
    import yaml

    config = copy.deepcopy(DEFAULT_CONFIG)
    with config_path.open("r", encoding="utf-8") as handle:
        user_config = yaml.safe_load(handle) or {}
    _deep_update(config, user_config)
    _resolve_paths(config, config_path.parent.resolve())
    return config


def _deep_update(target: dict, source: dict) -> None:
    for key, value in source.items():
        if isinstance(value, dict) and isinstance(target.get(key), dict):
            _deep_update(target[key], value)
        else:
            target[key] = value


def _resolve_paths(config: dict, root_dir: Path) -> None:
    for section, key in (
        ("stt", "executable"),
        ("stt", "model"),
        ("llm", "executable"),
        ("llm", "model"),
        ("tts", "executable"),
        ("tts", "model"),
        ("tts", "config"),
        ("browser", "downloads_dir"),
        ("tools", "plugins_dir"),
        ("tools", "workspace_root"),
        ("tools", "notes_dir"),
        ("tools", "screenshots_dir"),
        ("memory", "path"),
        ("logging", "file"),
        ("runtime", "pid_file"),
        ("runtime", "daemon_log"),
    ):
        raw_value = os.path.expandvars(str(config[section][key]))
        resolved = Path(raw_value)
        if not resolved.is_absolute():
            resolved = root_dir / resolved
        config[section][key] = str(apply_platform_executable_suffix(resolved, key))
