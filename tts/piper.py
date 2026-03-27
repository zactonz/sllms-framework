from __future__ import annotations

import concurrent.futures
import logging
import subprocess
import tempfile
import wave
from typing import Optional
from pathlib import Path

import numpy as np
import sounddevice as sd

from utils.platform import resolve_executable_path


LOGGER = logging.getLogger("voice_assistant.tts")


class PiperTTS:
    def __init__(self, config: dict):
        self.executable = resolve_executable_path(config["executable"])
        self.model = Path(config["model"]).resolve()
        self.model_config = Path(config["config"]).resolve()
        self.speaker = int(config["speaker"])
        self.length_scale = float(config["length_scale"])
        self.noise_scale = float(config["noise_scale"])
        self.noise_w = float(config["noise_w"])
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=1, thread_name_prefix="piper_tts")
        self._latest_future: Optional[concurrent.futures.Future] = None

    def is_available(self) -> bool:
        return self.executable.exists() and self.model.exists() and self.model_config.exists()

    def shutdown(self) -> None:
        self.wait_for_pending()
        self.executor.shutdown(wait=True, cancel_futures=False)

    def speak_async(self, text: str) -> concurrent.futures.Future:
        self._latest_future = self.executor.submit(self.speak, text)
        return self._latest_future

    def wait_for_pending(self) -> None:
        if self._latest_future is None:
            return
        try:
            self._latest_future.result()
        except Exception as exc:
            LOGGER.error("Pending TTS task failed: %s", exc)
        finally:
            self._latest_future = None

    def speak(self, text: str) -> None:
        if not self.is_available():
            LOGGER.warning("Piper is unavailable; skipping TTS.")
            return
        with tempfile.TemporaryDirectory(prefix="piper_tts_") as tmp_dir:
            output_path = Path(tmp_dir) / "response.wav"
            command = [
                str(self.executable),
                "--model",
                str(self.model),
                "--config",
                str(self.model_config),
                "--speaker",
                str(self.speaker),
                "--length_scale",
                str(self.length_scale),
                "--noise_scale",
                str(self.noise_scale),
                "--noise_w",
                str(self.noise_w),
                "--output_file",
                str(output_path),
            ]
            completed = subprocess.run(
                command,
                input=text,
                text=True,
                capture_output=True,
                check=False,
                cwd=str(self.executable.parent),
            )
            if completed.returncode != 0:
                LOGGER.error("Piper synthesis failed: %s", completed.stderr.strip() or completed.stdout.strip())
                return
            self._play_wav(output_path)

    def _play_wav(self, wav_path: Path) -> None:
        try:
            with wave.open(str(wav_path), "rb") as wav_file:
                frames = wav_file.readframes(wav_file.getnframes())
                channels = wav_file.getnchannels()
                sample_rate = wav_file.getframerate()
            audio = np.frombuffer(frames, dtype=np.int16)
            if channels > 1:
                audio = audio.reshape(-1, channels)
            sd.play(audio, sample_rate, blocking=True)
        except Exception as exc:
            LOGGER.error("Audio playback failed: %s", exc)
