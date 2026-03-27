# Requirements And Limitations

## Goal

This document explains the minimum requirements, practical deployment limits, and platform-specific caveats for SLLMS.

## Baseline Requirements

Minimum baseline:

- 64-bit Windows, macOS, or Linux
- Python 3.10 or newer
- internet access during bootstrap if you want the helper scripts to download runtimes and models
- a microphone for voice capture workflows
- speakers or headphones for spoken reply workflows

Recommended baseline:

- 4 GB RAM minimum for lightweight local use
- 8 GB RAM or more for smoother local LLM usage
- 2 to 4 CPU threads for small models on edge devices
- SSD storage for faster model loading

Disk expectations:

- the source repo is small
- the downloaded native runtimes and models can range from hundreds of MB to multiple GB depending on the Whisper model, GGUF model, and Piper voice you choose

## Runtime Requirements

SLLMS relies on three local backends:

- `whisper.cpp` for speech-to-text
- `llama.cpp` for local intent parsing
- `Piper` for optional text-to-speech

The bootstrap script can install defaults, but teams may also point `config.yaml` at their own local runtime and model paths.

## Audio Requirements

For microphone workflows:

- the OS must expose at least one input device
- the Python `sounddevice` package must be installed
- the machine must allow microphone access for the terminal or app that runs SLLMS

For TTS playback:

- the Python `sounddevice` package must be installed
- the machine must allow speaker playback from the running app
- Piper runtime files and a compatible voice model must be present if TTS is enabled

## Platform Notes

### Windows

Best-supported shell and runtime environment:

- PowerShell
- Python installed and available on `PATH`

Built-in integrations rely on Windows commands such as:

- `powershell`
- `tasklist`
- `taskkill`
- `netsh`
- `shutdown`

Platform caveats:

- Wi-Fi control depends on the expected adapter naming and local privileges
- app launch aliases are intentionally simple and may need extension for enterprise images or kiosk environments
- desktop automation beyond the starter tool set belongs in child repos or custom plugins

### macOS

Best-supported shell and runtime environment:

- `zsh`
- Python 3.10+

Built-in integrations rely on macOS commands such as:

- `open`
- `osascript`
- `networksetup`
- `pmset`

Platform caveats:

- macOS privacy permissions can block microphone access until the host app or terminal is approved
- Bluetooth power control requires `blueutil` for the built-in Bluetooth tools
- app names are resolved through `open -a`, so custom app names may need custom aliases

### Linux

Best-supported shell and runtime environment:

- `bash`
- Python 3.10+

Built-in integrations depend more heavily on distro and desktop environment:

- folder opening uses `xdg-open`
- Wi-Fi control uses `nmcli`
- Bluetooth control uses `bluetoothctl`
- clipboard support expects Wayland or X11 clipboard tools such as `wl-copy`, `wl-paste`, `xclip`, or `xsel`
- settings and system monitor launch depend on commands like `gnome-control-center`, `systemsettings`, `xfce4-settings-manager`, `gnome-system-monitor`, `mate-system-monitor`, or `ksysguard`

Platform caveats:

- some desktop-control tools may be unavailable on minimal servers or unusual desktop environments
- app aliases such as browser, calculator, or terminal may need adjustment for your distro

## Hardware Guidance

For lightweight assistants:

- small Whisper models such as `tiny.en` or `base.en`
- small GGUF instruction models in the 2B to 4B range
- one Piper voice

For robots, kiosks, and embedded operator terminals:

- use a stable microphone with predictable gain
- calibrate `audio.energy_threshold`
- validate speaker feedback and echo conditions
- disable TTS if command latency matters more than spoken confirmation

## Functional Limitations

Current core limitations include:

- one tool action per turn in the core intent schema
- no built-in multi-step planning or multi-tool orchestration loop in the core
- hotword detection is transcript-based after speech capture, not a dedicated wake-word engine
- no built-in vendor-specific smart-home integrations in the core repo
- no bundled browser automation pack in the core repo
- no bundled GPU-specific optimization workflow; the project is CPU-first by design

What this means in practice:

- if you want multi-step workflows today, implement them inside a custom tool or child tool pack
- if you want “turn on the light, then announce success, then log it” in one logical step, a custom tool is the cleanest current pattern
- if you want a production-grade wake word engine, you will likely add or swap a dedicated keyword spotting component in a child repo

## Configuration Limits And Safety

Safety defaults:

- `run_command` is off by default
- workspace writes are off by default
- process control is off by default
- power actions are off by default
- destructive actions require explicit opt-in

Recommended constraints:

- do not allowlist shell interpreters unless you intentionally want broad local execution power
- do not expose unrestricted free-form external URLs
- keep smart-device credentials and API keys outside the repo

## Example Config Caveat

Config paths are resolved relative to the config file location.

That means example configs stored under `examples/configs/` must include explicit relative paths back to the repo root. The shipped example configs in this repo already do that.
