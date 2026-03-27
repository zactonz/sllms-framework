# Model And Runtime Layout

This directory is intentionally mostly empty in source control.

SLLMS expects local runtime binaries and model files to be placed under `models/`
after bootstrap, but those large assets should not be committed to the repo.

## Expected Layout

- `models/whisper-runtime/`
  Native `whisper.cpp` runtime bundle
- `models/whisper/`
  Whisper `.bin` model files
- `models/llama-runtime/`
  Native `llama.cpp` runtime bundle
- `models/llm/`
  GGUF language models
- `models/piper-runtime/`
  Native Piper runtime bundle
- `models/piper/`
  Piper voice `.onnx` files and matching `.json` configs

## Recommended Setup

From the repo root, run:

```bash
python scripts/bootstrap.py --all
```

That bootstrap flow installs Python dependencies, downloads or builds the local
runtimes, and fetches the default Whisper, LLM, and Piper assets configured for
the framework.

## Notes

- Do not commit downloaded models or native runtime bundles.
- The default paths are configured in `config.yaml`.
- Teams can point `config.yaml` at their own local model locations if they want
  to manage assets outside the repo.
