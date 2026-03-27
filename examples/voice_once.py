from __future__ import annotations

from pathlib import Path

from main import VoiceAssistantApp


def main() -> int:
    app = VoiceAssistantApp(Path("config.yaml"))
    try:
        result = app.process_microphone_once(speak_override=False)
        print("HEARD:", result.heard_text)
        print("INTENT:", result.intent)
        print("MESSAGE:", result.tool_message)
        return 0
    finally:
        app.close()


if __name__ == "__main__":
    raise SystemExit(main())
