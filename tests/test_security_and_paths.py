from __future__ import annotations

import os
import shlex
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tools.content_tools import _resolve_workspace_path
from tools.system_tools import _parse_command_args, run_command


def _join_command(args: list[str]) -> str:
    if os.name == "nt":
        return subprocess.list2cmdline(args)
    return shlex.join(args)


class SecurityAndPathTests(unittest.TestCase):
    def test_run_command_executes_single_allowlisted_command(self) -> None:
        command = _join_command([sys.executable, "-c", "print('safe-run')"])
        result = run_command(
            command,
            {
                "tools": {
                    "allow_run_command": True,
                    "allowed_commands": [Path(sys.executable).name.lower()],
                    "workspace_root": ".",
                }
            },
        )

        self.assertTrue(result.success)
        self.assertIn("safe-run", result.message)

    def test_run_command_rejects_shell_chaining(self) -> None:
        result = run_command(
            "echo hello && whoami",
            {
                "tools": {
                    "allow_run_command": True,
                    "allowed_commands": ["echo"],
                    "workspace_root": ".",
                }
            },
        )

        self.assertFalse(result.success)
        self.assertIn("Only a single command", result.message)

    def test_parse_command_args_rejects_redirection(self) -> None:
        self.assertEqual(_parse_command_args("echo hi > out.txt"), [])

    def test_workspace_path_cannot_escape_root(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            workspace_root = Path(tmp_dir).resolve()
            with self.assertRaises(ValueError):
                _resolve_workspace_path(workspace_root, "../outside.txt")


if __name__ == "__main__":
    unittest.main()
