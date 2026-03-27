# Production Notes

## Recommended Practices

- Keep `run_command` disabled unless required
- Scope `allowed_commands` narrowly
- Avoid allowlisting interpreters or shell entrypoints unless you intentionally want broad execution power
- Use named API allowlists instead of free-form URLs
- Store custom voices and models outside the repo for managed deployments
- Route logs to your own collection pipeline if needed

## Edge Device Guidance

- Prefer `tiny.en` or `base.en` for STT
- Use 2B to 4B GGUF models in Q4 or Q5
- Start with 4 threads and adjust after profiling
- Disable TTS for command-only devices if latency matters

## Background Operation

Use:

```bash
python main.py --background start
```

The runtime writes:

- PID file from `runtime.pid_file`
- daemon log from `runtime.daemon_log`

## Packaging Suggestions

- Publish this repo with models excluded
- Let adopters run `scripts/bootstrap.py --all`
- Provide pinned release tags for tested model/runtime combinations

## Validation Checklist

- `python main.py --doctor`
- mic capture works
- STT produces text
- LLM emits tool JSON
- at least one built-in tool succeeds
- TTS playback succeeds if enabled
