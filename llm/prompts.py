from __future__ import annotations

import json


def build_tool_prompt(tool_specs: list[dict]) -> str:
    tools_json = json.dumps(tool_specs, indent=2)
    return (
        "You are an intent parser for a local voice assistant.\n"
        "Choose exactly one tool action.\n"
        "Return exactly one JSON object and nothing else.\n"
        "The JSON schema is:\n"
        '{\n  "action": "<tool_name>",\n  "parameters": { ... }\n}\n'
        "Only use tools from the list below.\n"
        "If the user is asking to search the web, use web_search.\n"
        "If the user only wants a spoken/text reply, use respond.\n"
        "Never wrap the JSON in markdown fences.\n"
        "Available tools:\n"
        f"{tools_json}\n"
    )


def build_user_prompt(text: str, recent_items: list[dict]) -> str:
    history = json.dumps(recent_items[-4:], indent=2) if recent_items else "[]"
    return (
        f"Conversation memory:\n{history}\n\n"
        f'User request: "{text}"\n'
        "Return the JSON intent now."
    )
