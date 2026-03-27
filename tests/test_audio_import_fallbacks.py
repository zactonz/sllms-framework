from __future__ import annotations

import builtins
import unittest
from pathlib import Path
from unittest.mock import patch

from main import FeatureUnavailableError, VoiceAssistantApp


class AudioImportFallbackTests(unittest.TestCase):
    def setUp(self) -> None:
        self.app = VoiceAssistantApp(Path("config.yaml"))

    def tearDown(self) -> None:
        self.app.close()

    def test_doctor_handles_portaudio_import_error(self) -> None:
        original_import = builtins.__import__

        def raising_import(name, globals=None, locals=None, fromlist=(), level=0):
            if name == "stt.audio":
                raise OSError("PortAudio library not found")
            return original_import(name, globals, locals, fromlist, level)

        with patch("builtins.__import__", side_effect=raising_import):
            code = self.app.doctor()

        self.assertEqual(code, 1)

    def test_get_recorder_maps_portaudio_import_error_to_feature_unavailable(self) -> None:
        original_import = builtins.__import__

        def raising_import(name, globals=None, locals=None, fromlist=(), level=0):
            if name == "stt.audio":
                raise OSError("PortAudio library not found")
            return original_import(name, globals, locals, fromlist, level)

        with patch("builtins.__import__", side_effect=raising_import):
            with self.assertRaises(FeatureUnavailableError):
                self.app._get_recorder()


if __name__ == "__main__":
    unittest.main()
