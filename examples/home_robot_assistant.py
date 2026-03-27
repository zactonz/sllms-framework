from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from main import VoiceAssistantApp


def main() -> int:
    app = VoiceAssistantApp(ROOT / "examples/configs/home_robot.example.yaml")
    try:
        if app.llm.is_available():
            commands = [
                "turn on the kitchen light",
                "what time is it",
                "turn off the kitchen light",
            ]
            for command in commands:
                turn = app.process_text(command, speak_override=False)
                print(json.dumps({"input": command, "intent": turn.intent, "message": turn.tool_message}, indent=2))
        else:
            intents = [
                {"action": "set_light_state", "parameters": {"name": "kitchen", "state": "on"}},
                {"action": "get_light_state", "parameters": {"name": "kitchen"}},
                {"action": "get_time", "parameters": {}},
                {"action": "set_light_state", "parameters": {"name": "kitchen", "state": "off"}},
            ]
            for intent in intents:
                result = app.dispatcher.dispatch(intent)
                print(json.dumps({"intent": intent, "result": result.__dict__}, indent=2))
        return 0
    finally:
        app.close()


if __name__ == "__main__":
    raise SystemExit(main())
