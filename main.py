from __future__ import annotations

import argparse
import difflib
import importlib.util
import json
import logging
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

from utils.logging_utils import configure_logging
from utils.memory import AssistantMemory
from utils.platform import current_platform
from utils.process_control import BackgroundProcessManager


LOGGER = logging.getLogger("voice_assistant")


class FeatureUnavailableError(RuntimeError):
    pass


@dataclass
class AssistantTurn:
    heard_text: str
    intent: dict[str, Any]
    tool_message: str
    success: bool


class VoiceAssistantApp:
    def __init__(self, config_path: Path):
        from llm.engine import LocalLLMEngine
        from stt.whisper_cpp import WhisperCppSTT
        from tools.base import ToolDispatcher, ToolRegistry
        from tools.system_tools import register_builtin_tools
        from utils.config import load_config

        self.config_path = config_path.resolve()
        self.root_dir = self.config_path.parent
        self.config = load_config(config_path)
        configure_logging(
            self.config["assistant"]["log_level"],
            Path(self.config["logging"]["file"]),
        )
        self.registry = ToolRegistry()
        self.memory = AssistantMemory(self.config["memory"])
        register_builtin_tools(self.registry, self.config, self.memory)
        self.registry.load_plugins(Path(self.config["tools"]["plugins_dir"]), self.config)
        self.dispatcher = ToolDispatcher(self.registry)
        self.stt = WhisperCppSTT(self.config["stt"])
        self.llm = LocalLLMEngine(self.config["llm"], self.registry)
        self._tts = None
        self._recorder = None
        self.process_manager = BackgroundProcessManager(
            Path(self.config["runtime"]["pid_file"]),
            Path(self.config["runtime"]["daemon_log"]),
        )

    def close(self) -> None:
        if self._tts is not None:
            self._tts.shutdown()

    @property
    def recorder(self):
        return self._get_recorder()

    @property
    def tts(self):
        if not self.config["assistant"]["tts_enabled"]:
            return None
        return self._get_tts()

    def doctor(self) -> int:
        try:
            from stt.audio import AudioInputError, NoMicrophoneError
        except ModuleNotFoundError:
            AudioInputError = RuntimeError
            NoMicrophoneError = RuntimeError

        missing = []
        runtime_status = self.process_manager.status()
        try:
            recorder = self._get_recorder()
            microphone = {
                "available": recorder.has_input_device(),
                "selected_device": recorder.selected_input_device() if recorder.has_input_device() else None,
            }
        except (FeatureUnavailableError, NoMicrophoneError, AudioInputError) as exc:
            microphone = {"available": False, "selected_device": None, "error": str(exc)}

        tts_ready = False
        tts_error = None
        if self.config["assistant"]["tts_enabled"]:
            try:
                tts = self._get_tts()
                tts_ready = tts.is_available()
            except FeatureUnavailableError as exc:
                tts_error = str(exc)
        checks = {
            "platform": current_platform().value,
            "stt_ready": self.stt.is_available(),
            "llm_ready": self.llm.is_available(),
            "tts_ready": tts_ready,
            "plugin_count": len(self.registry.plugin_modules),
            "tool_count": len(self.registry.tool_names()),
            "background": runtime_status,
            "microphone": microphone,
            "paths": {
                "stt_executable": str(self.stt.executable),
                "stt_model": str(self.stt.model),
                "llm_executable": str(self.llm.executable),
                "llm_model": str(self.llm.model),
                "tts_executable": str(Path(self.config["tts"]["executable"])) if self.config["assistant"]["tts_enabled"] else None,
                "tts_model": str(Path(self.config["tts"]["model"])) if self.config["assistant"]["tts_enabled"] else None,
                "tts_config": str(Path(self.config["tts"]["config"])) if self.config["assistant"]["tts_enabled"] else None,
            },
            "settings": {
                "audio_trigger_mode": str(self.config["audio"]["trigger_mode"]),
                "stt_language": self.stt.language,
                "hotword_enabled": bool(self.config["assistant"]["hotword"]["enabled"]),
                "hotword_phrase": str(self.config["assistant"]["hotword"]["phrase"]),
            },
        }
        if tts_error is not None:
            checks["tts_error"] = tts_error
        if not self.stt.executable.exists():
            missing.append("stt_executable")
        if not self.stt.model.exists():
            missing.append("stt_model")
        if not self.llm.executable.exists():
            missing.append("llm_executable")
        if not self.llm.model.exists():
            missing.append("llm_model")
        if self.config["assistant"]["tts_enabled"]:
            if not Path(self.config["tts"]["executable"]).exists():
                missing.append("tts_executable")
            if not Path(self.config["tts"]["model"]).exists():
                missing.append("tts_model")
            if not Path(self.config["tts"]["config"]).exists():
                missing.append("tts_config")
        checks["missing"] = missing
        print(json.dumps(checks, indent=2))
        if not checks["stt_ready"] or not checks["llm_ready"]:
            print("Missing required local binaries or models. See docs and models/README.md.", file=sys.stderr)
            return 1
        return 0

    def process_text(
        self,
        text: str,
        speak_override: Optional[bool] = None,
        enforce_hotword: bool = False,
    ) -> AssistantTurn:
        normalized_text = text.strip()
        if not normalized_text:
            raise ValueError("Cannot process empty text.")

        hotword_cfg = self.config["assistant"]["hotword"]
        if hotword_cfg["enabled"] and enforce_hotword:
            stripped = self._strip_hotword(normalized_text, hotword_cfg["phrase"])
            if stripped is None:
                LOGGER.info("Ignoring transcript because the hotword was not detected.")
                return AssistantTurn(text, {"action": "respond", "parameters": {}}, "Hotword not detected.", False)
            normalized_text = stripped

        LOGGER.info("User text: %s", normalized_text)
        intent = self.llm.generate_intent(normalized_text, self.memory.recent_items())
        result = self.dispatcher.dispatch(intent)

        self.memory.add_item(
            {
                "text": normalized_text,
                "intent": intent,
                "success": result.success,
                "message": result.message,
            }
        )

        should_speak = self.config["assistant"]["tts_enabled"] if speak_override is None else speak_override
        if should_speak and result.message:
            try:
                tts = self._get_tts()
            except FeatureUnavailableError as exc:
                LOGGER.warning("TTS is unavailable: %s", exc)
            else:
                tts.speak_async(result.message)

        return AssistantTurn(normalized_text, intent, result.message, result.success)

    def process_microphone_once(
        self,
        speak_override: Optional[bool] = None,
        enforce_hotword: bool = True,
        manual_trigger: bool = False,
    ) -> AssistantTurn:
        try:
            from stt.audio import write_wav_file
        except ModuleNotFoundError as exc:
            raise FeatureUnavailableError(
                "Audio input features require the Python dependencies from requirements.txt, including numpy and sounddevice."
            ) from exc

        if manual_trigger:
            self._wait_for_manual_trigger()
        recorder = self._get_recorder()
        with tempfile.TemporaryDirectory(prefix="voice_assistant_") as tmp_dir:
            wav_path = Path(tmp_dir) / "input.wav"
            audio_data = recorder.capture_utterance()
            write_wav_file(wav_path, audio_data, self.config["audio"]["sample_rate"])
            text = self.stt.transcribe_file(wav_path)
        return self.process_text(text, speak_override=speak_override, enforce_hotword=enforce_hotword)

    def run_forever(
        self,
        speak_override: Optional[bool] = None,
        enforce_hotword: bool = True,
        manual_trigger: bool = False,
    ) -> int:
        try:
            from stt.audio import AudioInputError, NoMicrophoneError
        except ModuleNotFoundError:
            AudioInputError = RuntimeError
            NoMicrophoneError = RuntimeError

        LOGGER.info("Assistant started. Press Ctrl+C to stop.")
        try:
            while True:
                try:
                    turn = self.process_microphone_once(
                        speak_override=speak_override,
                        enforce_hotword=enforce_hotword,
                        manual_trigger=manual_trigger,
                    )
                    print(json.dumps({"heard": turn.heard_text, "intent": turn.intent, "message": turn.tool_message}, indent=2))
                except TimeoutError:
                    LOGGER.debug("No speech detected in the configured capture window.")
                except (NoMicrophoneError, AudioInputError) as exc:
                    LOGGER.error("Audio input is unavailable: %s", exc)
                    print(
                        json.dumps(
                            {
                                "status": "no_microphone",
                                "message": str(exc),
                                "hint": "Connect a microphone, choose a device in config.yaml, or use --text mode.",
                            },
                            indent=2,
                        )
                    )
                    return 1
                except FeatureUnavailableError as exc:
                    LOGGER.error("Audio runtime is unavailable: %s", exc)
                    print(
                        json.dumps(
                            {
                                "status": "audio_runtime_unavailable",
                                "message": str(exc),
                                "hint": "Install the Python audio dependencies or use --text mode.",
                            },
                            indent=2,
                        )
                    )
                    return 1
                except Exception as exc:
                    LOGGER.exception("Assistant loop failed: %s", exc)
        except KeyboardInterrupt:
            LOGGER.info("Assistant stopped by user.")
            return 0

    def background_status(self) -> int:
        print(json.dumps(self.process_manager.status(), indent=2))
        return 0

    def start_background(self, speak_override: Optional[bool] = None) -> int:
        if str(self.config["audio"]["trigger_mode"]).strip().lower() == "push_to_talk":
            print(
                json.dumps(
                    {
                        "status": "unsupported_background_mode",
                        "message": "Push-to-talk mode requires an interactive terminal or custom UI trigger.",
                    },
                    indent=2,
                )
            )
            return 1
        command = [
            sys.executable,
            str(Path(__file__).resolve()),
            "--config",
            str(self.config_path),
        ]
        if speak_override is False:
            command.append("--no-tts")
        pid = self.process_manager.start(command, self.root_dir)
        print(
            json.dumps(
                {
                    "status": "started",
                    "pid": pid,
                    "log_file": str(Path(self.config["runtime"]["daemon_log"])),
                },
                indent=2,
            )
        )
        return 0

    def stop_background(self) -> int:
        stopped = self.process_manager.stop()
        print(json.dumps({"status": "stopped" if stopped else "not_running"}, indent=2))
        return 0

    def list_audio_devices(self) -> int:
        try:
            from stt.audio import AudioInputError
        except ModuleNotFoundError:
            AudioInputError = RuntimeError

        try:
            devices = self._list_input_devices()
        except (AudioInputError, FeatureUnavailableError) as exc:
            print(json.dumps({"status": "audio_error", "message": str(exc)}, indent=2))
            return 1
        print(json.dumps({"input_devices": devices}, indent=2))
        return 0

    def _get_recorder(self):
        if self._recorder is not None:
            return self._recorder
        try:
            from stt.audio import MicrophoneRecorder
        except ModuleNotFoundError as exc:
            raise FeatureUnavailableError(
                "Audio input features require the Python dependencies from requirements.txt, including numpy and sounddevice."
            ) from exc
        self._recorder = MicrophoneRecorder(self.config["audio"])
        return self._recorder

    def _get_tts(self):
        if self._tts is not None:
            return self._tts
        if not self.config["assistant"]["tts_enabled"]:
            raise FeatureUnavailableError("TTS is disabled in config.yaml.")
        try:
            from tts.piper import PiperTTS
        except ModuleNotFoundError as exc:
            raise FeatureUnavailableError(
                "TTS playback requires the Python dependencies from requirements.txt, including numpy and sounddevice."
            ) from exc
        self._tts = PiperTTS(self.config["tts"])
        return self._tts

    def _list_input_devices(self) -> list[dict[str, Any]]:
        try:
            from stt.audio import MicrophoneRecorder
        except ModuleNotFoundError as exc:
            raise FeatureUnavailableError(
                "Audio device inspection requires the Python dependencies from requirements.txt, including numpy and sounddevice."
            ) from exc
        return MicrophoneRecorder.list_input_devices()

    def _wait_for_manual_trigger(self) -> None:
        if not sys.stdin or not sys.stdin.isatty():
            raise RuntimeError("Push-to-talk mode requires an interactive terminal or a custom application trigger.")
        print("Press Enter to start listening...")
        input()

    def _strip_hotword(self, transcript: str, hotword: str) -> str | None:
        cleaned = transcript.strip()
        lowered = cleaned.lower().strip(" ,.!?")
        expected = hotword.strip().lower()

        if lowered == "[blank_audio]":
            return None

        if expected in lowered:
            return lowered.split(expected, 1)[1].strip(" ,.!?") or ""

        # Accept direct assistant invocations even when the first word varies.
        if lowered.startswith("assistant "):
            return lowered.split("assistant", 1)[1].strip(" ,.!?")
        if lowered == "assistant":
            return ""

        words = lowered.replace(",", " ").replace(".", " ").split()
        if not words:
            return None

        first_two = " ".join(words[:2])
        first_three = " ".join(words[:3])
        similarity = max(
            difflib.SequenceMatcher(None, expected, first_two).ratio(),
            difflib.SequenceMatcher(None, expected, first_three).ratio(),
        )

        if similarity >= 0.62:
            remainder_words = words[2:] if len(words) >= 2 else []
            if len(words) >= 3 and difflib.SequenceMatcher(None, expected, first_three).ratio() >= similarity:
                remainder_words = words[3:]
            return " ".join(remainder_words).strip(" ,.!?")

        return None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Offline cross-platform voice assistant.")
    parser.add_argument("--config", default="config.yaml", help="Path to the YAML configuration file.")
    parser.add_argument("--text", help="Process a text command instead of microphone input.")
    parser.add_argument("--once", action="store_true", help="Capture one microphone utterance and exit.")
    parser.add_argument("--no-tts", action="store_true", help="Disable text-to-speech for this run.")
    parser.add_argument("--no-hotword", action="store_true", help="Disable hotword enforcement for microphone input.")
    parser.add_argument("--push-to-talk", action="store_true", help="Require pressing Enter before each microphone capture.")
    parser.add_argument("--list-audio-devices", action="store_true", help="List detected microphone input devices.")
    parser.add_argument("--doctor", action="store_true", help="Validate configured executables and models.")
    parser.add_argument(
        "--background",
        choices=["start", "stop", "status"],
        help="Run or control the assistant as a background process.",
    )
    return parser


def missing_python_packages() -> list[str]:
    required_modules = {
        "yaml": "PyYAML",
    }
    missing = []
    for module_name, package_name in required_modules.items():
        if importlib.util.find_spec(module_name) is None:
            missing.append(package_name)
    return missing


def main() -> int:
    try:
        from stt.audio import AudioInputError, NoMicrophoneError
    except ModuleNotFoundError:
        AudioInputError = RuntimeError
        NoMicrophoneError = RuntimeError

    parser = build_parser()
    args = parser.parse_args()
    missing = missing_python_packages()
    if missing:
        print(
            json.dumps(
                {
                    "status": "missing_python_dependencies",
                    "packages": missing,
                    "hint": "Install them with: python -m pip install -r requirements.txt",
                },
                indent=2,
            ),
            file=sys.stderr,
        )
        return 1
    config_path = Path(args.config).resolve()
    app = VoiceAssistantApp(config_path)
    try:
        manual_trigger = args.push_to_talk or str(app.config["audio"]["trigger_mode"]).strip().lower() == "push_to_talk"
        if args.doctor:
            return app.doctor()
        if args.list_audio_devices:
            return app.list_audio_devices()
        if args.background == "status":
            return app.background_status()
        if args.background == "start":
            return app.start_background(speak_override=not args.no_tts)
        if args.background == "stop":
            return app.stop_background()
        if args.text:
            turn = app.process_text(args.text, speak_override=not args.no_tts)
            print(json.dumps({"heard": turn.heard_text, "intent": turn.intent, "message": turn.tool_message}, indent=2))
            return 0 if turn.success else 1
        if args.once:
            try:
                turn = app.process_microphone_once(
                    speak_override=not args.no_tts,
                    enforce_hotword=not args.no_hotword,
                    manual_trigger=manual_trigger,
                )
                print(json.dumps({"heard": turn.heard_text, "intent": turn.intent, "message": turn.tool_message}, indent=2))
                return 0 if turn.success else 1
            except TimeoutError as exc:
                print(json.dumps({"status": "timeout", "message": str(exc)}, indent=2))
                return 1
            except (NoMicrophoneError, AudioInputError) as exc:
                print(
                    json.dumps(
                        {
                            "status": "no_microphone",
                            "message": str(exc),
                            "hint": "Connect a microphone, use --list-audio-devices, or run in --text mode.",
                        },
                        indent=2,
                    )
                )
                return 1
            except FeatureUnavailableError as exc:
                print(
                    json.dumps(
                        {
                            "status": "audio_runtime_unavailable",
                            "message": str(exc),
                            "hint": "Install the Python audio dependencies or run in --text mode.",
                        },
                        indent=2,
                    )
                )
                return 1
        return app.run_forever(
            speak_override=not args.no_tts,
            enforce_hotword=not args.no_hotword,
            manual_trigger=manual_trigger,
        )
    finally:
        app.close()


if __name__ == "__main__":
    raise SystemExit(main())
