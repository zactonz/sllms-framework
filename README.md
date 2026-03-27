# SLLMS Voice Assistant Framework

SLLMS is a cross-platform, offline-first voice assistant framework for developers building real applications on Windows, macOS, and Linux.

It provides a modular local pipeline:

`microphone -> whisper.cpp -> local LLM intent parsing -> tool execution -> optional Piper TTS`

SLLMS is intended to be a starting kit for programmers who want to build:

- voice assistants with AI
- dictation software with AI
- talking software with AI
- listen -> act -> speak systems that hear a request, call tools, and respond in text and speech

SLLMS is designed to be:

- easy to clone and bootstrap
- installable as a reusable Python framework
- extendable with custom tools, plugins, models, and APIs
- ready to grow into a multi-repo ecosystem where child tool repos stay separate from the core
- suitable for edge devices and self-hosted deployments

## Why SLLMS

SLLMS gives developers a practical starting point for building:

- voice-enabled desktop apps
- dictation and transcription software
- offline assistants for edge devices
- private enterprise copilots
- local automation agents
- domain-specific assistants with custom tools
- complete products built on top of a reusable voice AI core

## Intended Usage

SLLMS is a good fit when you want a prebuilt framework that already handles speech I/O, intent routing, tool registration, and extension patterns so your team can focus on domain logic.

Common targets include:

- a hotword-enabled assistant robot that listens and answers immediately
- a smart-home or device-control assistant that can hear, act, and speak back
- a dictation app that captures audio and turns it into text
- a talking desktop assistant that opens apps, calls APIs, or runs approved commands
- a custom voice-enabled product that needs a reusable Python foundation

## Core Capabilities

- Offline STT with `whisper.cpp`
- Local LLM tool calling with `llama.cpp`
- Optional offline TTS with `Piper`
- Structured JSON intent pipeline
- Tool registry and dispatcher pattern
- Plugin-based extension model
- Multilingual fast-path commands for common actions
- Background mode for always-on assistants
- Push-to-talk mode for manual triggering
- Short-term memory for recent interactions
- Allowlisted shell commands and HTTP APIs
- Installable `sllms` CLI and embeddable Python API

## Supported Platforms

- Windows
- macOS
- Linux

Supported Python:

- Python 3.10+

Recommended environment:

- 64-bit CPU
- 4 GB RAM minimum for lightweight usage
- 8 GB RAM recommended for smoother local LLM performance
- microphone input for voice capture
- speaker or headphones for TTS output

Detailed operating-system, hardware, and feature limitations are documented in [Requirements And Limitations](docs/REQUIREMENTS_AND_LIMITATIONS.md).

## Runtime Stack

- STT: `whisper.cpp`
- LLM: `llama.cpp`
- TTS: `Piper`

Recommended edge-friendly defaults:

- Whisper `tiny.en` or `base.en`
- 2B to 4B GGUF model in Q4 or Q5
- one Piper voice

## Quick Start

### Windows PowerShell

Direct bootstrap:

```powershell
git clone https://github.com/zactonz/sllms-framework.git sllms-framework
cd sllms-framework
python -m pip install -e .
python scripts\bootstrap.py --all
python main.py --doctor
python main.py --text "what time is it" --no-tts
python main.py --once
```

Helper script:

```powershell
git clone https://github.com/zactonz/sllms-framework.git sllms-framework
cd sllms-framework
powershell -ExecutionPolicy Bypass -File .\scripts\setup.ps1 -BootstrapAll
.\.venv\Scripts\python.exe main.py --doctor
.\.venv\Scripts\python.exe main.py --text "what time is it" --no-tts
.\.venv\Scripts\python.exe main.py --once
```

### macOS

Direct bootstrap:

```bash
git clone https://github.com/zactonz/sllms-framework.git sllms-framework
cd sllms-framework
python3 -m pip install -e .
python3 scripts/bootstrap.py --all
python3 main.py --doctor
python3 main.py --text "what time is it" --no-tts
python3 main.py --once
```

Helper script:

```bash
git clone https://github.com/zactonz/sllms-framework.git sllms-framework
cd sllms-framework
bash ./scripts/setup.sh --bootstrap-all
source .venv/bin/activate
python main.py --doctor
python main.py --text "what time is it" --no-tts
python main.py --once
```

### Linux

Direct bootstrap:

```bash
git clone https://github.com/zactonz/sllms-framework.git sllms-framework
cd sllms-framework
python3 -m pip install -e .
python3 scripts/bootstrap.py --all
python3 main.py --doctor
python3 main.py --text "what time is it" --no-tts
python3 main.py --once
```

Helper script:

```bash
git clone https://github.com/zactonz/sllms-framework.git sllms-framework
cd sllms-framework
bash ./scripts/setup.sh --bootstrap-all
source .venv/bin/activate
python main.py --doctor
python main.py --text "what time is it" --no-tts
python main.py --once
```

## Main Commands

Cross-platform installed CLI:

```bash
sllms --once
sllms --once --push-to-talk
sllms --text "what time is it"
sllms --text "search google for cats"
sllms --doctor
sllms --list-audio-devices
sllms --background start
sllms --background status
sllms --background stop
```

Direct Python entrypoints are shown in the OS-specific quick start sections above.

## How Developers Use SLLMS

Developers can use SLLMS in four common ways:

- run it as a standalone voice assistant
- embed it in a Python application
- extend it with custom plugins and tools
- deploy it on their own workstation, edge box, VM, or private server

### Embed In A Project

```python
from pathlib import Path
from sllms_framework import VoiceAssistantApp

app = VoiceAssistantApp(Path("config.yaml"))
turn = app.process_text("what time is it", speak_override=False)
print(turn.intent)
print(turn.tool_message)
app.close()
```

## How Developers Extend SLLMS

Developers can:

- add their own tools
- add their own plugins
- point to their own Whisper models
- choose a microphone device or push-to-talk trigger mode
- point to their own GGUF local LLMs
- point to their own Piper voices
- define allowlisted external APIs
- define allowlisted local shell commands
- build their own UI, service, or product around the assistant engine
- install optional child repos from separate GitHub repos or Python packages

The core repo includes the external-tool template only:

- `templates/sllms_tool_pack_template/`

Typical extension ideas:

- internal ticketing tools
- CRM and ERP integrations
- database queries
- smart-device controls
- local app workflows
- alerting and operations dashboards
- browser automation flows that open sites, navigate, click, and fill data

## Important Limits

SLLMS is already useful as a starter kit, but a few design limits should be understood up front:

- the core intent engine currently selects one tool action per turn
- hotword handling is transcript-based after capture, not a dedicated always-listening keyword spotting engine
- smart-home and robot integrations are intended to come from custom tools or future child repos rather than the core repo
- platform support is broad, but some desktop-control features depend on OS-specific commands or utilities

## Built-In Tools

- `open_app(name)`
- `run_command(cmd)`
- `control_device(device, state)`
- `web_search(query)`
- `open_url(url)`
- `get_time()`
- `call_api(name, query, body)`
- `show_memory(limit)`
- `respond(message)`

## Framework Layout

- `sllms_framework/`
  Public Python API and CLI entrypoint
- `stt/`, `llm/`, `tts/`, `tools/`, `utils/`
  Framework internals
- `scripts/bootstrap.py`
  Downloads platform-specific runtimes and models
- `models/`
  Local runtime assets and model files
- `docs/`, `examples/`, `plugins/`
  Developer documentation, examples, and extensions

The source code stays in the repo like a normal professional library, while large native runtimes and AI models are downloaded only when developers choose to bootstrap.

## Security Defaults

- shell execution is disabled by default
- command execution uses an allowlist and runs a single argv command without shell chaining when enabled
- external API access uses named allowlists
- tools are centrally registered and dispatch-controlled
- large runtime assets and models stay outside the source package

## Performance Notes

SLLMS is optimized for practical local workflows rather than maximum benchmark throughput.

Fast on most edge-friendly setups:

- microphone capture
- Whisper transcription with small models
- built-in tool-first commands
- local app launch and browser actions
- deterministic commands like time, search, and memory

Potentially slower on CPU-only devices:

- open-ended local reasoning
- larger GGUF models
- long prompt-driven intent parsing

Best production pattern:

- fast-path common actions
- use the local LLM as a fallback for more flexible requests

Current fast-path command coverage includes common actions in:

- English
- Spanish
- French
- German
- Italian
- Portuguese

## Audio And Language Notes

- if no microphone is detected, the CLI returns a friendly `no_microphone` status and suggests `--text` mode
- developers can inspect microphones with `sllms --list-audio-devices`
- `--push-to-talk` supports manual capture in the CLI, and embedded apps can call `process_microphone_once()` from their own UI button
- multilingual support is available by using a multilingual Whisper model, setting `stt.language` to a language code or `auto`, and choosing a matching Piper voice

## Documentation

- [Quickstart](docs/QUICKSTART.md)
- [Using SLLMS](docs/USING_SLLMS.md)
- [Requirements And Limitations](docs/REQUIREMENTS_AND_LIMITATIONS.md)
- [Troubleshooting](docs/TROUBLESHOOTING.md)
- [Use Cases](docs/USE_CASES.md)
- [Example Recipes](docs/EXAMPLE_RECIPES.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Extending](docs/EXTENDING.md)
- [Adding Custom Tools](docs/ADDING_CUSTOM_TOOLS.md)
- [Tool Packs](docs/TOOL_PACKS.md)
- [Repo Structure](docs/REPO_STRUCTURE.md)
- [Production Notes](docs/PRODUCTION.md)
- [Built-In Tools](docs/BUILTIN_TOOLS.md)
- [Release Checklist](docs/RELEASE_CHECKLIST.md)
- [Release Notes Draft](docs/RELEASE_NOTES_v0.1.0.md)
- [Examples](examples/README.md)
- [Model Setup](models/README.md)
- [Contributing](CONTRIBUTING.md)

## License

SLLMS is released under the MIT License in [LICENSE](LICENSE).

That means developers can use, modify, extend, and distribute it freely, including in commercial projects, with the standard MIT no-warranty and no-liability terms.

## Release And Repo Expectations

- downloaded models are not committed
- runtime artifacts and logs are ignored
- backend runtimes are isolated per engine to avoid DLL conflicts
- source code is installable through `pip install -e .`
- GitHub Actions validates Windows, macOS, and Linux package installs
- examples show embedding, plugins, and config patterns

## Good Fit Use Cases

- desktop voice assistants
- local developer copilots
- enterprise on-prem assistants
- voice-controlled operator consoles
- privacy-first AI tools
- custom applications built on top of a reusable voice pipeline

SLLMS ships with a lean core tool set, and can load optional child repos such as `sllms-tools-browser` or `sllms-tools-desktop` only when users install them separately.
