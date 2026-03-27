from __future__ import annotations

from pathlib import Path

from main import VoiceAssistantApp


def main() -> int:
    app = VoiceAssistantApp(Path("config.yaml"))
    try:
        commands = [
            "open notepad",
            "search google for cats",
            "show recent memory",
        ]
        for command in commands:
            result = app.process_text(command, speak_override=False)
            print("INPUT:", command)
            print("INTENT:", result.intent)
            print("MESSAGE:", result.tool_message)
            print("-" * 40)
        return 0
    finally:
        app.close()


if __name__ == "__main__":
    raise SystemExit(main())
