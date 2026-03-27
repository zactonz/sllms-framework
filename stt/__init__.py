from __future__ import annotations

__all__ = ["MicrophoneRecorder", "WhisperCppSTT", "write_wav_file"]


def __getattr__(name: str):
    if name == "WhisperCppSTT":
        from .whisper_cpp import WhisperCppSTT

        return WhisperCppSTT
    if name in {"MicrophoneRecorder", "write_wav_file"}:
        from .audio import MicrophoneRecorder, write_wav_file

        exports = {
            "MicrophoneRecorder": MicrophoneRecorder,
            "write_wav_file": write_wav_file,
        }
        return exports[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
