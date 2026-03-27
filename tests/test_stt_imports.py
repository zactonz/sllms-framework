from __future__ import annotations

import importlib
import unittest


class STTImportTests(unittest.TestCase):
    def test_whisper_import_does_not_require_audio_runtime(self) -> None:
        module = importlib.import_module("stt.whisper_cpp")
        self.assertEqual(module.WhisperCppSTT.__name__, "WhisperCppSTT")


if __name__ == "__main__":
    unittest.main()
