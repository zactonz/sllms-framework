# Troubleshooting

## Goal

This guide maps common SLLMS errors and symptoms to likely causes and fixes.

## Install And Startup

### `missing_python_dependencies`

Cause:

- required Python packages such as `PyYAML`, `numpy`, or `sounddevice` are not installed

Fix:

- run `python -m pip install -r requirements.txt`
- if you are using a virtual environment, make sure it is activated first

### `stt_ready: false`, `llm_ready: false`, or `tts_ready: false` in `--doctor`

Cause:

- the configured runtime executable or model path does not exist
- bootstrap was not run
- the config file points at the wrong relative path

Fix:

- run `python scripts/bootstrap.py --all`
- inspect the reported paths from `python main.py --doctor`
- confirm your config file points at the correct runtime and model locations

### `audio_runtime_unavailable`

Cause:

- audio-related Python dependencies are missing
- microphone or speaker features were requested in an environment without `numpy` and `sounddevice`

Fix:

- install `requirements.txt`
- use `--text` mode if you want to continue without microphone capture

## Audio And Speech

### `no_microphone`

Cause:

- no input device is available
- the selected device in `config.yaml` does not exist
- the OS blocked microphone access

Fix:

- run `python main.py --list-audio-devices`
- remove or correct `audio.device`
- check microphone permissions in the operating system
- try `--text` mode to validate the rest of the stack

### `timeout`

Cause:

- no speech crossed the configured energy threshold before timeout
- the microphone is too quiet or too far away
- background noise or device gain is misconfigured

Fix:

- speak closer to the microphone
- lower `audio.energy_threshold`
- increase `audio.max_record_seconds`
- try `--push-to-talk` to test capture more deliberately

### Speech captured, but hotword commands are ignored

Cause:

- the transcript did not include the configured hotword phrase
- the current hotword logic checks transcript text after capture rather than a dedicated wake-word model

Fix:

- test with `--no-hotword`
- choose a shorter hotword phrase
- confirm `assistant.hotword.phrase` matches how people actually say it

## Tool And Action Errors

### `run_command is disabled in config.yaml.`

Cause:

- `tools.allow_run_command` is still `false`

Fix:

- enable it only if you truly need it
- then allowlist only the specific commands you want

### `Command '<name>' is not in the allowed command list.`

Cause:

- the command is not listed in `tools.allowed_commands`

Fix:

- add the exact executable name to `allowed_commands`
- avoid allowlisting interpreters or shell entrypoints unless you intentionally want broad execution power

### `Only a single command with arguments is allowed.`

Cause:

- `run_command` rejected shell chaining, redirection, or shell syntax

Fix:

- pass one command with normal arguments only
- move complex workflows into a custom tool instead of trying to chain shell commands

### `Workspace writes are disabled.`

Cause:

- file-writing tools were used while `tools.allow_workspace_writes` is `false`

Fix:

- enable workspace writes only if your product needs them

### `delete_file requires tools.allow_workspace_writes and tools.allow_sensitive_actions.`

Cause:

- a destructive workspace action was attempted without both safety flags enabled

Fix:

- enable both flags only when you intentionally want destructive behavior

### `Path '...' is outside the configured workspace root ...`

Cause:

- a file tool tried to access a path outside `tools.workspace_root`

Fix:

- pass a workspace-relative path inside the configured root
- widen `tools.workspace_root` only if the product truly requires it

## Plugin And Extension Errors

### `Failed to load plugin file ...` or `Failed to load configured plugin module ...`

Cause:

- the plugin raised an exception at import time
- the configured module name is wrong
- the plugin has missing dependencies

Fix:

- run the plugin directly in Python to isolate the import error
- install its dependencies
- keep plugin import code lightweight and move risky logic into handlers

### `Skipping plugin '...' because it does not expose a callable register() function.`

Cause:

- the plugin file or module does not define `register(registry, config)`

Fix:

- add a top-level `register()` function
- make sure it registers one or more `ToolDefinition` objects

## API And Web Errors

### `API endpoint '<name>' is not configured in config.yaml.`

Cause:

- `call_api` was asked to use an endpoint name that is not in `apis.endpoints`

Fix:

- add the endpoint to config
- keep endpoint names stable and descriptive

### `Query parameters not allowed ...` or `Body fields not allowed ...`

Cause:

- the request used fields outside the configured allowlist

Fix:

- add only the fields you truly want to expose
- prefer named API configs over free-form HTTP requests

## Platform-Specific Notes

### Linux desktop tools do nothing or fail

Cause:

- required desktop utilities are missing on the current distro or desktop environment

Fix:

- confirm `xdg-open`, `nmcli`, `bluetoothctl`, and clipboard utilities are installed when you use those features
- extend the platform wrappers if your environment uses different utilities

### macOS audio or automation features fail

Cause:

- system privacy permissions block microphone or automation access

Fix:

- approve the terminal or app in macOS privacy settings
- retry after permission is granted

### Windows control features fail

Cause:

- some actions require local privileges or depend on adapter names and shell environment

Fix:

- verify PowerShell is available
- verify the target app, process, or network adapter names match your machine

## When To Move Beyond Core

If you keep hitting the same limit repeatedly, it usually means the right solution is a custom plugin or child tool pack.

Common examples:

- smart lights and IoT device integrations
- browser automation
- enterprise APIs with authentication
- robot hardware drivers
- multi-step workflows with several actions in sequence
