from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from main import VoiceAssistantApp


def main() -> int:
    app = VoiceAssistantApp(ROOT / "config.yaml")
    try:
        intents = [
            {"action": "get_platform_summary", "parameters": {}},
            {"action": "list_processes", "parameters": {}},
            {"action": "open_docs_folder", "parameters": {}},
            {"action": "close_app", "parameters": {"name": "notepad"}},
        ]
        for intent in intents:
            result = app.dispatcher.dispatch(intent)
            print(json.dumps({"intent": intent, "result": result.__dict__}, indent=2))
        return 0
    finally:
        app.close()


if __name__ == "__main__":
    raise SystemExit(main())
