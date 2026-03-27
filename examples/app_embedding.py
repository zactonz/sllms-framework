from __future__ import annotations

from pathlib import Path

from main import VoiceAssistantApp


class EmbeddedVoiceFeature:
    def __init__(self) -> None:
        self.app = VoiceAssistantApp(Path("config.yaml"))

    def handle_user_text(self, text: str) -> dict:
        result = self.app.process_text(text, speak_override=False)
        return {
            "heard": result.heard_text,
            "intent": result.intent,
            "message": result.tool_message,
            "success": result.success,
        }

    def close(self) -> None:
        self.app.close()


def main() -> int:
    feature = EmbeddedVoiceFeature()
    try:
        payload = feature.handle_user_text("search google for edge voice AI")
        print(payload)
        return 0
    finally:
        feature.close()


if __name__ == "__main__":
    raise SystemExit(main())
