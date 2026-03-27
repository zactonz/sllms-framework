# Repo Structure

This document defines the intended repository model for SLLMS.

## Core Repo

The main repo is:

- `sllms-framework`

It contains:

- the core voice pipeline
- the CLI and Python API
- built-in core tools
- config, setup scripts, docs, and examples
- the template for external child repos

The core repo must remain independently usable.

That means:

- it must not require any child repo to install
- it must not bundle reusable child repos inside the core repo
- it must stay functional with only `pip install -e .` plus runtime/model bootstrap

## Child Repos

Each reusable tool family should live in its own repo.

Examples:

- `sllms-tools-browser`
- `sllms-tools-desktop`
- `sllms-tools-dev`
- `sllms-tools-enterprise`

Each child repo:

- depends on `sllms-framework`
- exposes tools through `sllms.plugins` entry points or explicit plugin modules
- may bring its own optional dependencies
- can be versioned and released independently

## Dependency Direction

The dependency direction is one-way:

- `sllms-framework` does not depend on child repos
- child repos depend on `sllms-framework`

## Extension Paths

Users extend the core in three ways:

1. local plugins in `plugins/`
2. installed modules listed in `tools.plugin_modules`
3. installed child repos discovered through `tools.enable_entrypoint_discovery`

## What Belongs In Core

Keep these in the core repo:

- voice capture, STT, LLM, TTS, memory, and orchestration
- safe broadly useful built-in tools
- examples that work with the core repo alone
- templates and docs for external child repos

## What Belongs In Child Repos

Move these into child repos:

- niche tool families
- heavy optional dependencies
- browser automation
- enterprise connectors
- vendor-specific hardware integrations
- developer workflow packs
- domain-specific automation bundles

## Publishing Order

Publish `sllms-framework` first as a standalone repo.

Publish child repos after that as optional add-ons.
