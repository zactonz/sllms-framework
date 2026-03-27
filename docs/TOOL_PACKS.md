# Tool Packs

SLLMS is now designed to support a framework-plus-ecosystem model:

- `sllms-framework` stays focused on the core voice pipeline and a general starter tool set
- niche or domain-specific tools live in separate child repos as installable tool packs

This keeps the core framework smaller, safer, and easier to maintain.

## Recommended Repo Structure

Core repo:

- `sllms-framework`

Optional tool-pack repos:

- `sllms-tools-desktop`
- `sllms-tools-dev`
- `sllms-tools-browser`
- `sllms-tools-enterprise`
- `sllms-tools-home-automation`
- `sllms-tools-operators`
- `sllms-tools-research`

## How Tool Packs Load

SLLMS supports three plugin sources:

1. Local plugin files in `plugins/`
2. Explicit Python modules listed in `config.yaml`
3. Installed Python packages that expose the `sllms.plugins` entry point group

That means users can:

- drop in a single local plugin file for quick experiments
- install a reusable tool-pack package with `pip`
- keep niche tools in a dedicated GitHub repo

## Option 1: Local Plugin File

Place a file in `plugins/` with a `register(registry, config)` function.

This is best for:

- quick local testing
- project-specific private tools
- early development

## Option 2: Explicit Module Import

Add installed module names to `config.yaml`:

```yaml
tools:
  plugin_modules:
    - "sllms_tools_notifications.plugin"
    - "sllms_tools_browser.plugin"
```

This is best when:

- you want explicit control over which installed tool packs load
- you want different environments to enable different tool packs

## Option 3: Entry Point Discovery

Installed packages can expose this entry point group:

```toml
[project.entry-points."sllms.plugins"]
notifications = "sllms_tools_notifications.plugin"
```

When `tools.enable_entrypoint_discovery: true`, SLLMS auto-loads those packages.

This is best when:

- you want a clean plugin ecosystem
- users should only need `pip install ...`
- multiple niche tool packs may be installed side by side

## Recommended Tool-Pack Contract

Each external pack should provide:

- one package, for example `sllms_tools_notifications`
- one module with a `register(registry, config)` function
- one or more `ToolDefinition` registrations
- clear README instructions
- any config examples needed by the pack

## Install Flow For Users

Example:

```bash
pip install sllms-framework
pip install sllms-tools-desktop
pip install sllms-tools-notifications
```

Then either:

- rely on entry point auto-discovery

or:

```yaml
tools:
  plugin_modules:
    - "sllms_tools_desktop.plugin"
    - "sllms_tools_notifications.plugin"
```

## What Should Stay In Core

Good core candidates:

- basic app launch/open tools
- time/date/system info
- safe folder navigation
- memory and notes basics
- allowlisted API and shell wrappers
- a small, broadly useful local automation starter set

## What Should Move To Tool Packs

Good external-pack candidates:

- browser automation
- developer tooling
- enterprise integrations
- home automation
- operator console workflows
- hardware or vendor-specific integrations
- industry-specific tools

## Tool-Pack Template

See the template package in:

- `templates/sllms_tool_pack_template/`

That template shows:

- package structure
- `pyproject.toml`
- entry point registration
- example `register()` function

Use that template to create separate repos such as:

- `sllms-tools-browser`
- `sllms-tools-desktop`
- `sllms-tools-dev`

## Security Guidance

Tool packs should:

- validate parameters strictly
- document any sensitive actions clearly
- keep destructive actions behind config flags
- avoid silently enabling risky behavior
- follow the same safety model as the core framework
