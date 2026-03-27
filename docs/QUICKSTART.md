# Quickstart

## Goal

Clone the framework, install local runtimes and models, then start building voice-enabled edge apps.

For operating-system limits, hardware guidance, and known functional boundaries, also read [Requirements And Limitations](REQUIREMENTS_AND_LIMITATIONS.md).

## 1. Clone

Windows PowerShell:

```powershell
git clone https://github.com/zactonz/sllms-framework.git sllms-framework
cd sllms-framework
```

macOS / Linux:

```bash
git clone https://github.com/zactonz/sllms-framework.git sllms-framework
cd sllms-framework
```

## 2. Bootstrap

### Windows PowerShell

Direct bootstrap:

```powershell
python -m pip install -e .
python scripts\bootstrap.py --all
```

Helper script:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\setup.ps1 -BootstrapAll
```

### macOS

Direct bootstrap:

```bash
python3 -m pip install -e .
python3 scripts/bootstrap.py --all
```

Helper script:

```bash
bash ./scripts/setup.sh --bootstrap-all
```

### Linux

Direct bootstrap:

```bash
python3 -m pip install -e .
python3 scripts/bootstrap.py --all
```

Helper script:

```bash
bash ./scripts/setup.sh --bootstrap-all
```

This installs:

- Python dependencies
- `whisper.cpp`
- `llama.cpp`
- Piper runtime
- Whisper model
- LLM model
- Piper voice

After bootstrap you can use either `python main.py ...` or the installed `sllms ...` command.

## 3. Validate

Windows PowerShell:

```powershell
python main.py --doctor
sllms --doctor
```

macOS / Linux:

```bash
python3 main.py --doctor
sllms --doctor
```

Expected result:

- `stt_ready: true`
- `llm_ready: true`
- `tts_ready: true`

Optional audio inspection:

```bash
sllms --list-audio-devices
```

## 4. Run

Windows PowerShell text tests:

```powershell
python main.py --text "what time is it" --no-tts
python main.py --text "search google for cats" --no-tts
```

macOS / Linux text tests:

```bash
python3 main.py --text "what time is it" --no-tts
python3 main.py --text "search google for cats" --no-tts
```

Windows PowerShell microphone tests:

```powershell
python main.py --once
python main.py --once --push-to-talk
python main.py
```

macOS / Linux microphone tests:

```bash
python3 main.py --once
python3 main.py --once --push-to-talk
python3 main.py
```

If no microphone is available, the CLI returns a `no_microphone` status and you can still use:

Windows PowerShell:

```powershell
python main.py --text "what time is it"
```

macOS / Linux:

```bash
python3 main.py --text "what time is it"
```

Background mode:

```bash
sllms --background start
sllms --background status
sllms --background stop
```

## 5. Start Extending

- Add tools in `plugins/`
- Add API allowlists in `config.yaml`
- Change `audio.device` or `audio.trigger_mode` in `config.yaml`
- Switch `stt.language` and model paths for multilingual deployments
- Install optional child repos later if your application needs them.
  See `docs/TOOL_PACKS.md` for the extension model.
- Use the sample apps in `examples/`
- See `docs/EXAMPLE_RECIPES.md` for guided basic and advanced recipes
- See `docs/TROUBLESHOOTING.md` for common setup and runtime problems
