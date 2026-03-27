# Using SLLMS

## What SLLMS Is

SLLMS is a cross-platform offline voice assistant framework for developers building local or self-hosted AI applications.

It provides a reusable pipeline:

`microphone -> speech-to-text -> local LLM intent parsing -> tool execution -> optional text-to-speech`

You can use it as:

- a standalone voice assistant
- a dictation or transcription building block
- a talking software foundation
- a Python framework embedded in your own app
- a plugin-based local automation engine
- a private on-device assistant for enterprise workflows

## What Developers Can Build

SLLMS is designed for real applications, including:

- assistant robots
- desktop voice assistants
- dictation and voice typing software
- local copilots for developers
- enterprise workflow assistants
- voice-controlled internal tools
- edge-device operators and kiosk assistants
- smart home or device control systems
- privacy-sensitive offline assistants
- domain-specific agents with custom tools and APIs

## Supported Platforms

Target operating systems:

- Windows
- macOS
- Linux

Supported Python versions:

- Python 3.10+

Recommended shell environments:

- Windows PowerShell
- macOS zsh
- Linux bash

Validation guidance:

- the framework targets all three operating systems
- developers should validate microphone, speaker, and local runtime behavior on their own target hardware
- developers should read [Requirements And Limitations](REQUIREMENTS_AND_LIMITATIONS.md) before committing to a hardware target

## Runtime Backends

SLLMS uses local runtimes instead of cloud APIs by default:

- STT: `whisper.cpp`
- LLM: `llama.cpp`
- TTS: `Piper`

Compatible model types:

- Whisper `.bin` models for `whisper.cpp`
- GGUF language models for `llama.cpp`
- Piper `.onnx` voices with matching `.json` config

Language support notes:

- English-only Whisper models such as `base.en` are fast and lightweight
- multilingual Whisper models let teams support non-English speech
- set `stt.language` to a language code such as `es`, `fr`, or `de`
- set `stt.language` to `auto` to let Whisper detect the spoken language
- choose a matching Piper voice if spoken responses should use that language
- built-in fast-path commands currently cover common actions in English, Spanish, French, German, Italian, and Portuguese
- spoken responses from built-in tools are still mostly English by default unless custom tools or prompts are localized

## Minimum Requirements

Baseline development requirements:

- 64-bit operating system
- Python 3.10 or newer
- microphone input for voice capture
- speaker or headphones for TTS playback
- internet connection during bootstrap for runtime and model download

Baseline device guidance:

- CPU-only system supported
- 4 GB RAM minimum for lightweight usage
- 8 GB RAM recommended for a smoother local LLM experience
- 2 to 4 CPU threads recommended for edge devices

Storage guidance:

- source code is small
- downloaded runtime binaries and models require additional disk space
- actual disk usage depends on the Whisper model, GGUF model, and Piper voice you choose

## Recommended Defaults

For lightweight edge usage:

- Whisper: `tiny.en` or `base.en`
- LLM: 2B to 4B GGUF models in Q4 or Q5
- TTS: one default Piper voice
- threads: start with `4` and profile from there

For faster command assistants:

- rely on built-in fast-path tool intents for common commands
- use the LLM only for unmatched or more flexible requests
- disable TTS if latency matters more than spoken output

## Install Modes

### Clone And Run

Use this when you want to run the framework directly:

Windows PowerShell:

```powershell
git clone https://github.com/zactonz/sllms-framework.git sllms-framework
cd sllms-framework
python -m pip install -e .
python scripts\bootstrap.py --all
python main.py --doctor
python main.py --once
```

macOS / Linux:

```bash
git clone https://github.com/zactonz/sllms-framework.git sllms-framework
cd sllms-framework
python3 -m pip install -e .
python3 scripts/bootstrap.py --all
python3 main.py --doctor
python3 main.py --once
```

### Install As A Framework

Use this when you want to build your own product on top of SLLMS:

Windows PowerShell:

```powershell
git clone https://github.com/zactonz/sllms-framework.git sllms-framework
cd sllms-framework
python -m pip install -e .
python scripts\bootstrap.py --all
sllms --doctor
```

macOS / Linux:

```bash
git clone https://github.com/zactonz/sllms-framework.git sllms-framework
cd sllms-framework
python3 -m pip install -e .
python3 scripts/bootstrap.py --all
sllms --doctor
```

## Ways To Use SLLMS

### 1. Use The CLI

Examples:

```bash
sllms --once
sllms --once --push-to-talk
sllms --text "what time is it"
sllms --text "que hora es"
sllms --text "ouvre notepad"
sllms --background start
sllms --list-audio-devices
```

### 2. Embed It In Your Own App

```python
from pathlib import Path
from sllms_framework import VoiceAssistantApp

app = VoiceAssistantApp(Path("config.yaml"))
turn = app.process_text("open notepad", speak_override=False)
print(turn.intent)
print(turn.tool_message)
app.close()
```

### 3. Extend It With Plugins

Add Python files in `plugins/` to register your own tools.

You can also install optional child repos, for example:

```bash
pip install sllms-tools-desktop
pip install sllms-tools-browser
python -m playwright install chromium
```

Typical custom tool ideas:

- internal company APIs
- CRM and ERP actions
- database lookups
- document workflows
- smart-device controls
- local app automation
- custom notifications

## What Users Can Customize

Developers can customize:

- their own tools
- their own plugins
- their own Whisper models
- their own GGUF local LLMs
- their own Piper voices
- their chosen microphone device
- their trigger mode such as voice activation or push-to-talk
- their own API allowlists
- their own command allowlists
- microphone thresholds and hotword behavior
- memory, logging, and background runtime settings

The framework ships with a large core catalog of system, notes, memory, workspace, and machine-control tools.
Browser-specific shortcuts and Playwright-powered browser automation can live in an optional child repo such as `sllms-tools-browser`.
See [Built-In Tools](BUILTIN_TOOLS.md).

## Current Design Limits

Important current limits:

- the core intent format chooses one tool action per turn
- hotword handling is transcript-based after capture, not a dedicated wake-word engine
- complex smart-home, robot, and browser integrations are expected to live in plugins or child repos

For many products this is still a strong starting point, but it is worth planning around those boundaries early.

## Can A Team Self-Host It

Yes.

SLLMS is built for self-hosted and edge deployments. A team can run it on:

- a developer workstation
- an on-prem server
- a private VM
- a lab machine
- an edge gateway
- a kiosk or dedicated operator terminal

The project is local-first. Teams control:

- runtime binaries
- models
- config
- plugins
- logs
- deployment method

## Security Model

Safe defaults are part of the framework:

- `run_command` is disabled by default
- shell commands use an allowlist and run as a single command without shell chaining when enabled
- external APIs use named allowlists
- tools are centrally registered and dispatched
- large models and local runtime assets stay outside the source package

Recommended production practices:

- keep `run_command` disabled unless required
- allow only a narrow set of shell commands
- avoid allowlisting interpreters or shell entrypoints unless you intentionally want broad execution power
- use named API configs instead of arbitrary URLs
- keep model downloads out of git
- review every custom tool handler like production code

## Where To Go Next

- read [Use Cases](USE_CASES.md) to map SLLMS to your product idea
- read [Example Recipes](EXAMPLE_RECIPES.md) for runnable examples
- read [Troubleshooting](TROUBLESHOOTING.md) when setup or runtime behavior is unclear
- read [Tool Packs](TOOL_PACKS.md) if you plan to split large tool families into separate repos

## Performance Expectations

SLLMS is optimized for practical local workflows, not maximum benchmark throughput.

What is typically fast:

- microphone capture
- Whisper transcription with small models
- built-in tool-first voice commands
- local app launch and browser actions
- deterministic commands like time, search, and memory

What may be slower on CPU-only devices:

- open-ended local LLM reasoning
- large GGUF models
- very long context windows
- complex multi-step prompt-based intent parsing

Best practice:

- use fast-path tools for common actions
- keep local LLM fallback for flexible or advanced requests

## Real-World Use Cases

Examples of strong fits for SLLMS:

- `Open my coding tools`
- `Search Google for the latest Rust release notes`
- `Show recent memory`
- `Query our internal weather demo API`
- `Launch our operator dashboard`
- `Call our internal ticketing system tool`
- `Run a voice-enabled kiosk workflow`

## Project Structure

Core source:

- `main.py`
- `stt/`
- `llm/`
- `tts/`
- `tools/`
- `utils/`
- `sllms_framework/`

Developer assets:

- `docs/`
- `examples/`
- `plugins/`
- `scripts/`

Downloaded runtime assets:

- `models/`
- `third_party/`

## Validation Checklist

After install, confirm:

- `sllms --doctor` succeeds
- `sllms --list-audio-devices` shows a usable microphone when voice mode is needed
- text commands work
- `--once` captures microphone input
- STT transcribes speech
- at least one tool action succeeds
- TTS audio plays if enabled

## Best Starting Path For New Developers

1. Clone the repo.
2. Run `python -m pip install -e .`
3. Run `python scripts/bootstrap.py --all`
4. Run `sllms --doctor`
5. Test text commands.
6. Test microphone commands.
7. Add one custom tool in `plugins/`.
8. Embed `VoiceAssistantApp` in your own app.
