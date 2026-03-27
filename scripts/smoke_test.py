from __future__ import annotations

import logging
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from main import VoiceAssistantApp


def main() -> int:
    app = VoiceAssistantApp(ROOT / "config.yaml")
    try:
        logging.getLogger("voice_assistant").setLevel(logging.WARNING)
        logging.getLogger("voice_assistant.llm").setLevel(logging.WARNING)
        doctor_code = app.doctor()
        checks = {
            "doctor_exit_code": doctor_code,
            "tests": [],
        }

        for text in ("hello assistant", "show recent memory", "que hora es"):
            turn = app.process_text(text, speak_override=False)
            checks["tests"].append(
                {
                    "input": text,
                    "intent": turn.intent,
                    "message": turn.tool_message,
                    "success": turn.success,
                }
            )

        time_turn = app.process_text("what time is it", speak_override=False)
        checks["tests"].append(
            {
                "input": "what time is it",
                "intent": time_turn.intent,
                "message": time_turn.tool_message,
                "success": time_turn.success,
            }
        )

        checks["all_tests_passed"] = all(item["success"] for item in checks["tests"])
        print(json.dumps(checks, indent=2))
        return 0 if checks["all_tests_passed"] else 1
    finally:
        app.close()


if __name__ == "__main__":
    raise SystemExit(main())
