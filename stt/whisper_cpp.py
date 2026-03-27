from __future__ import annotations

import logging
import subprocess
import tempfile
from pathlib import Path

from utils.platform import resolve_executable_path


LOGGER = logging.getLogger("voice_assistant.whisper")


class WhisperCppSTT:
    def __init__(self, config: dict):
        self.executable = resolve_executable_path(config["executable"])
        self.model = Path(config["model"]).resolve()
        self.language = config["language"]
        self.threads = int(config["threads"])

    def is_available(self) -> bool:
        return self.executable.exists() and self.model.exists()

    def transcribe_file(self, wav_path: Path) -> str:
        if not self.is_available():
            raise FileNotFoundError(
                f"whisper.cpp is not ready. Expected executable at '{self.executable}' and model at '{self.model}'."
            )

        with tempfile.TemporaryDirectory(prefix="whisper_cpp_") as tmp_dir:
            output_base = Path(tmp_dir) / "transcript"
            command = [
                str(self.executable),
                "-m",
                str(self.model),
                "-f",
                str(wav_path),
                "-t",
                str(self.threads),
                "-otxt",
                "-nt",
                "-of",
                str(output_base),
            ]
            language = str(self.language).strip().lower()
            if language and language != "auto":
                command[6:6] = ["-l", language]
            LOGGER.debug("Running whisper.cpp command: %s", command)
            completed = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=False,
                cwd=str(self.executable.parent),
            )
            transcript_path = output_base.with_suffix(".txt")
            if transcript_path.exists():
                transcript = transcript_path.read_text(encoding="utf-8").strip()
            else:
                transcript = completed.stdout.strip()
            if completed.returncode != 0:
                error_text = completed.stderr.strip() or completed.stdout.strip()
                raise RuntimeError(
                    f"whisper.cpp failed with exit code {completed.returncode}: {error_text or 'no stderr/stdout output'}"
                )
            if not transcript:
                raise RuntimeError("whisper.cpp returned an empty transcript.")
            LOGGER.info("Transcription: %s", transcript)
            return transcript
