from __future__ import annotations

import tempfile
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from stt.audio import MicrophoneRecorder, write_wav_file
from stt.whisper_cpp import WhisperCppSTT
from utils.config import load_config


def main() -> int:
    config = load_config(ROOT / "config.yaml")
    recorder = MicrophoneRecorder(config["audio"])
    stt = WhisperCppSTT(config["stt"])

    with tempfile.TemporaryDirectory(prefix="sllms_dictation_") as tmp_dir:
        wav_path = Path(tmp_dir) / "dictation.wav"
        audio_data = recorder.capture_utterance()
        write_wav_file(wav_path, audio_data, config["audio"]["sample_rate"])
        transcript = stt.transcribe_file(wav_path)

    print("DICTATION:")
    print(transcript)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
