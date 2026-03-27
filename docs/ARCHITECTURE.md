# Architecture

## Pipeline

```text
microphone -> stt/audio.py -> whisper.cpp -> llm/engine.py -> tools/base.py -> tools/system_tools.py -> optional Piper TTS
```

## Core Modules

- `main.py`
  - CLI entrypoint
  - runtime loop
  - background process control
- `stt/`
  - microphone capture
  - WAV export
  - `whisper.cpp` wrapper
- `llm/`
  - prompt construction
  - strict JSON intent generation
  - fallback parser
- `tools/`
  - tool registry
  - dispatcher
  - built-in tools
  - plugin loading
- `tts/`
  - Piper synthesis
  - async playback
- `utils/`
  - config
  - logging
  - memory
  - platform helpers
  - background process management

## Design Principles

- Local-first and CPU-first
- Cross-platform by default
- Safe configuration for shell commands and external APIs
- Extend without changing the agent loop
- Keep install flow simple for framework adopters

## Tool Calling Model

The LLM returns strict JSON:

```json
{
  "action": "open_app",
  "parameters": {
    "name": "notepad"
  }
}
```

The dispatcher resolves `action` against the registry and executes the handler.

## Security Model

- `run_command` is allowlisted and executes a single argv command
- external APIs are config allowlisted
- tools are explicit and discoverable
- local state is separated from source
