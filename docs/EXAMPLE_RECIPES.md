# Example Recipes

## Goal

This document organizes the example scripts and configs by developer goal.

## Basic Examples

### Text-only assistant flow

Use when you want to validate tool routing without microphone input.

Files:

- `examples/text_assistant.py`
- `examples/app_embedding.py`

Run:

```bash
python examples/text_assistant.py
python examples/app_embedding.py
```

### Voice capture once

Use when you want to test microphone capture and a single assistant turn.

Files:

- `examples/voice_once.py`

Run:

```bash
python examples/voice_once.py
```

### Dictation only

Use when you want transcription without the tool-calling assistant loop.

Files:

- `examples/dictation_once.py`

Run:

```bash
python examples/dictation_once.py
```

## Intermediate Examples

### Built-in tool catalog

Use when you want to inspect the current built-in and plugin tool surface.

Files:

- `examples/tool_catalog.py`

Run:

```bash
python examples/tool_catalog.py
```

### Direct machine-control dispatch

Use when you want to call tools directly from Python instead of going through text intent parsing.

Files:

- `examples/machine_control_demo.py`

Run:

```bash
python examples/machine_control_demo.py
```

## Advanced Examples

### Hotword home robot style config

Use when you want a robot-like voice assistant profile with hotword, TTS, and example light-control tools.

Files:

- `examples/configs/home_robot.example.yaml`
- `examples/home_robot_assistant.py`
- `examples/plugins/light_control_plugin.py`

Run:

```bash
python examples/home_robot_assistant.py
python main.py --config examples/configs/home_robot.example.yaml --once
```

### API allowlist example

Use when you want the assistant to call a named external HTTP API safely.

Files:

- `examples/configs/api_weather.example.yaml`

Run:

```bash
python main.py --config examples/configs/api_weather.example.yaml --text "call weather demo"
```

### Multilingual example

Use when you want to adapt the assistant to Spanish speech and TTS.

Files:

- `examples/configs/multilingual_spanish.example.yaml`

Run:

```bash
python main.py --config examples/configs/multilingual_spanish.example.yaml --text "que hora es"
```

## Plugin Recipes

Local plugin examples included in the repo:

- `examples/plugins/todo_plugin.py`
- `examples/plugins/desktop_notification_plugin.py`
- `examples/plugins/light_control_plugin.py`

Typical workflow:

1. study one of the example plugins
2. copy it into `plugins/` or package it as a child repo
3. rename the tool(s) and replace the handler logic with your own integration

## Child Repo Pattern

Large or reusable tool families should eventually move into their own repos.

Examples:

- browser automation packs
- desktop automation packs
- enterprise integration packs
- home automation packs
- robot hardware packs

See [Tool Packs](TOOL_PACKS.md) for the extension model.
