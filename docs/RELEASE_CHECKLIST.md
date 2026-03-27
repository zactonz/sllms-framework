# Release Checklist

## Repo Cleanup

- confirm docs point to `https://github.com/zactonz/sllms-framework`
- confirm the core repo does not bundle child tool repos
- confirm `.gitignore` excludes models, runtime assets, logs, caches, and local memory
- remove local files before commit:
  - `.assistant_memory.json`
  - `assistant.log`
  - `assistant-daemon.log`
  - `__pycache__/`
- make sure no downloaded runtime assets are staged:
  - `models/whisper-runtime/`
  - `models/llama-runtime/`
  - `models/piper-runtime/`
  - `models/whisper/`
  - `models/llm/`
  - `models/piper/`
  - `third_party/`

## Validation

- run `python -m pip install -e .`
- run `PYTHONPYCACHEPREFIX=.pycache_local python -m compileall main.py llm stt tts tools utils sllms_framework tests`
- run `python main.py --doctor`
- run `python scripts/smoke_test.py`
- run `python -m unittest discover -s tests -v`
- run at least one text command:
  - `python main.py --text "what time is it" --no-tts`
- run at least one microphone command:
  - `python main.py --once --no-hotword`
- run `python main.py --list-audio-devices`

## Cross-Platform Checks

- verify bootstrap on Windows
- verify bootstrap on macOS
- verify bootstrap on Linux
- verify at least one app-launch alias on each OS
- verify microphone input and TTS playback on each OS

## Docs Review

- confirm README quick-start commands are correct
- confirm the core-vs-child-repo boundary is clearly documented
- confirm installable `sllms` CLI flow is documented
- confirm multilingual config example is linked
- confirm extension/plugin docs match the current API

## Release Packaging

- confirm the real GitHub repo URL is present in:
  - `README.md`
  - `docs/QUICKSTART.md`
  - `docs/USING_SLLMS.md`
  - `CONTRIBUTING.md`
- choose a first release tag, for example `v0.1.0`
- prepare GitHub release notes
- publish the first tagged release

## Recommended First Tag Scope

`v0.1.0` is a good fit for:

- Windows-validated runtime flow
- package install support
- plugin system
- background mode
- multilingual fast-path command routing
- docs and examples for extension
