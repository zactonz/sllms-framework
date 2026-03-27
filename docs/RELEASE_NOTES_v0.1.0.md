# SLLMS v0.1.0

## Summary

First public release of the SLLMS Voice Assistant Framework.

SLLMS is a cross-platform, offline-first framework for building voice-enabled local AI applications with:

- `whisper.cpp` for speech-to-text
- `llama.cpp` for local intent parsing and tool calling
- `Piper` for optional text-to-speech
- a dispatcher-based tool system
- plugin-driven extensibility

## Highlights

- Windows, macOS, and Linux targeting
- installable `sllms` CLI and embeddable Python API
- offline microphone -> STT -> tool-call -> action -> TTS pipeline
- configurable hotword mode and push-to-talk mode
- graceful no-microphone handling
- background mode for always-on assistants
- short-term memory for recent commands
- multilingual fast-path routing for common commands
- examples and docs for building real applications on top of the framework

## Included Built-In Tools

- `open_app(name)`
- `run_command(cmd)`
- `control_device(device, state)`
- `web_search(query)`
- `open_url(url)`
- `get_time()`
- `call_api(name, query, body)`
- `show_memory(limit)`
- `respond(message)`

## Developer Experience

- `python scripts/bootstrap.py --all`
- `python -m pip install -e .`
- `sllms --doctor`
- `sllms --list-audio-devices`
- `python scripts/smoke_test.py`

## Notes

- runtime binaries and models are downloaded during bootstrap and are not committed to source control
- open-ended local LLM reasoning on CPU may be slower than tool-first commands
- built-in command routing is strongest when used with the fast-path tool patterns

## Recommended Next Steps

- validate bootstrap on macOS and Linux hardware
- localize built-in response text by language
- add more built-in instant command patterns
- package a small desktop UI or tray wrapper
