from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from main import VoiceAssistantApp


def main() -> int:
    app = VoiceAssistantApp(ROOT / "config.yaml")
    try:
        tool_names = app.registry.tool_names()
        print(f"SLLMS built-in and plugin tools: {len(tool_names)}")
        for name in tool_names:
            print(f"- {name}")
        return 0
    finally:
        app.close()


if __name__ == "__main__":
    raise SystemExit(main())
