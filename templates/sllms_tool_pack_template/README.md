# SLLMS Tool Pack Template

This template shows how to build a niche tool-pack repo for SLLMS.

## Package Layout

```text
sllms-tool-pack-template/
├── pyproject.toml
└── src/
    └── sllms_tool_pack_template/
        ├── __init__.py
        └── plugin.py
```

## Install Locally

```bash
pip install -e .
```

If entry point discovery is enabled in SLLMS, the tool pack will auto-load.

Otherwise add the module explicitly in `config.yaml`:

```yaml
tools:
  plugin_modules:
    - "sllms_tool_pack_template.plugin"
```
