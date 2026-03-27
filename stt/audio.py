from __future__ import annotations

import logging
import queue
import time
import wave
from pathlib import Path
from typing import Any

import numpy as np
import sounddevice as sd


LOGGER = logging.getLogger("voice_assistant.audio")


class AudioInputError(RuntimeError):
    pass


class NoMicrophoneError(AudioInputError):
    pass


class MicrophoneRecorder:
    def __init__(self, config: dict):
        self.sample_rate = int(config["sample_rate"])
        self.channels = int(config["channels"])
        self.block_duration_ms = int(config["block_duration_ms"])
        self.silence_duration_s = float(config["silence_duration_s"])
        self.max_record_seconds = float(config["max_record_seconds"])
        self.energy_threshold = float(config["energy_threshold"])
        self.device = config.get("device")
        self.trigger_mode = str(config.get("trigger_mode", "voice")).strip().lower()

    @staticmethod
    def list_input_devices() -> list[dict[str, Any]]:
        try:
            devices = sd.query_devices()
        except Exception as exc:
            raise AudioInputError(f"Unable to query audio devices: {exc}") from exc

        default_input_index = _default_input_index()
        results = []
        for index, device in enumerate(devices):
            if int(device.get("max_input_channels", 0)) <= 0:
                continue
            results.append(
                {
                    "index": index,
                    "name": str(device.get("name", f"input-{index}")),
                    "default_samplerate": float(device.get("default_samplerate", 0.0)),
                    "channels": int(device.get("max_input_channels", 0)),
                    "is_default": index == default_input_index,
                }
            )
        return results

    def has_input_device(self) -> bool:
        return bool(self.list_input_devices())

    def selected_input_device(self) -> dict[str, Any]:
        devices = self.list_input_devices()
        if not devices:
            raise NoMicrophoneError("No microphone input device detected.")

        if self.device not in (None, "", "default"):
            configured = str(self.device).strip()
            for device in devices:
                if configured == str(device["index"]) or configured.lower() == str(device["name"]).lower():
                    return device
            raise NoMicrophoneError(
                f"Configured microphone '{configured}' was not found. Use --list-audio-devices to inspect inputs."
            )

        default_input_index = _default_input_index()
        for device in devices:
            if device["index"] == default_input_index:
                return device
        return devices[0]

    def capture_utterance(self) -> np.ndarray:
        blocksize = int(self.sample_rate * (self.block_duration_ms / 1000.0))
        audio_queue: queue.Queue[np.ndarray] = queue.Queue()
        collected: list[np.ndarray] = []
        speech_started = False
        last_voice_at = 0.0
        started_at = time.monotonic()
        selected_device = self.selected_input_device()

        def callback(indata, frames, time_info, status) -> None:
            if status:
                LOGGER.debug("Audio callback status: %s", status)
            audio_queue.put(indata.copy())

        try:
            with sd.InputStream(
                samplerate=self.sample_rate,
                channels=self.channels,
                dtype="int16",
                blocksize=blocksize,
                callback=callback,
                device=selected_device["index"],
            ):
                LOGGER.info("Listening for speech on '%s'...", selected_device["name"])
                while time.monotonic() - started_at < self.max_record_seconds:
                    try:
                        chunk = audio_queue.get(timeout=0.5)
                    except queue.Empty:
                        continue

                    energy = float(np.sqrt(np.mean(chunk.astype(np.float32) ** 2)))
                    is_voice = energy >= self.energy_threshold

                    if is_voice and not speech_started:
                        speech_started = True
                        LOGGER.info("Speech detected.")

                    if speech_started:
                        # Buffer only the active utterance, then stop after a configurable
                        # period of silence so whisper.cpp gets a clean chunk of speech.
                        collected.append(chunk)
                        if is_voice:
                            last_voice_at = time.monotonic()
                        elif last_voice_at and (time.monotonic() - last_voice_at) >= self.silence_duration_s:
                            break
        except sd.PortAudioError as exc:
            raise AudioInputError(
                f"Unable to open microphone '{selected_device['name']}': {exc}. Use --list-audio-devices to inspect inputs."
            ) from exc

        if not collected:
            raise TimeoutError("No speech detected before timeout.")

        return np.concatenate(collected, axis=0)


def write_wav_file(path: Path, audio_data: np.ndarray, sample_rate: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pcm = np.asarray(audio_data, dtype=np.int16)
    channels = pcm.shape[1] if pcm.ndim > 1 else 1
    with wave.open(str(path), "wb") as wav_file:
        wav_file.setnchannels(channels)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(pcm.tobytes())


def _default_input_index() -> int | None:
    default_device = sd.default.device
    if isinstance(default_device, (list, tuple)) and len(default_device) >= 1:
        return int(default_device[0]) if default_device[0] is not None and int(default_device[0]) >= 0 else None
    if default_device is None:
        return None
    try:
        index = int(default_device)
    except (TypeError, ValueError):
        return None
    return index if index >= 0 else None
