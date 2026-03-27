# Use Cases

## Goal

This document explains the kinds of products SLLMS is designed to help developers build.

## 1. Hotword Assistant Robot

Target:

- a robot or embedded assistant that listens for a phrase such as `hey robot`
- hears a command
- performs a tool action
- answers back in speech or text

What SLLMS gives you:

- microphone capture
- transcript-based hotword gating
- local intent parsing
- tool registry and dispatcher
- optional spoken replies through Piper

What you usually add:

- robot hardware drivers
- motor or sensor tools
- smart-home or relay integrations
- a custom UI or enclosure-specific runtime wrapper

Relevant files:

- `config.yaml`
- `examples/configs/home_robot.example.yaml`
- `examples/home_robot_assistant.py`
- `examples/plugins/light_control_plugin.py`

## 2. Dictation Software

Target:

- a voice typing or transcription tool that turns spoken audio into text

What SLLMS gives you:

- microphone capture
- WAV generation
- local Whisper transcription

What you usually add:

- editor integration
- transcript post-processing
- formatting rules
- save/export workflows

Relevant files:

- `stt/audio.py`
- `stt/whisper_cpp.py`
- `examples/dictation_once.py`

## 3. Talking Desktop Assistant

Target:

- a desktop app that can hear requests, open software, call local tools, and answer back

What SLLMS gives you:

- app launch helpers
- process inspection
- optional TTS
- Python embedding API

What you usually add:

- application-specific tools
- UI, tray app, or packaging layer
- organization-specific workflows

Relevant files:

- `examples/text_assistant.py`
- `examples/app_embedding.py`
- `examples/machine_control_demo.py`

## 4. Listen -> Act -> Speak Automation

Target:

- a system that hears a request, triggers one or more business or device actions, and confirms the result

What SLLMS gives you:

- speech pipeline
- tool registration and dispatch
- safe config-driven API access
- custom plugin support

Current core limitation:

- the core intent schema selects one tool action per turn

Practical pattern today:

- wrap multi-step logic inside a custom tool or child repo tool pack
- let that tool perform the whole workflow and return one final result message

## 5. Smart Home Or Device Control

Target:

- a voice assistant that controls lights, relays, switches, or other devices

What SLLMS gives you:

- the speech and action orchestration foundation
- a place to register safe device-control tools

What you usually add:

- device drivers
- vendor APIs
- local network discovery
- authentication and safety checks

Important note:

- the core repo intentionally does not ship production smart-home connectors
- those belong in custom plugins or future child repos such as a dedicated smart-home tool pack

## 6. Enterprise And Operator Workflows

Target:

- a private assistant for internal systems, dashboards, approvals, ticketing, or operations

What SLLMS gives you:

- local-first deployment model
- API allowlists
- plugin architecture
- embeddable Python app object

What you usually add:

- authenticated API clients
- role-aware tools
- audit logging
- organization-specific policies
