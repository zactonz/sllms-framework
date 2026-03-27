# Examples

These examples show how to use the framework as a reusable kit, not just a standalone app.

## Files

- `text_assistant.py`
  - embed the assistant and process text commands
- `app_embedding.py`
  - wrap the assistant inside another Python feature or product
- `voice_once.py`
  - run a single microphone capture from code
- `dictation_once.py`
  - capture audio and transcribe it without tool calling
- `tool_catalog.py`
  - print the full built-in and plugin tool list
- `machine_control_demo.py`
  - dispatch several desktop and machine-control tools from Python
- `home_robot_assistant.py`
  - robot-style assistant example with a light-control plugin and home-robot config
- `configs/api_weather.example.yaml`
  - runnable external API allowlist config
- `configs/home_robot.example.yaml`
  - runnable hotword-enabled home robot config
- `configs/multilingual_spanish.example.yaml`
  - runnable multilingual config for Spanish speech and TTS
- `plugins/todo_plugin.py`
  - example plugin tool
- `plugins/desktop_notification_plugin.py`
  - example custom desktop notification plugin
- `plugins/light_control_plugin.py`
  - example smart-light control plugin for assistant robot style projects

External child-repo template:

- `../templates/sllms_tool_pack_template/`
  - reference template for building a separate reusable tool repo

## Run

```bash
python examples/text_assistant.py
python examples/app_embedding.py
python examples/voice_once.py
python examples/dictation_once.py
python examples/tool_catalog.py
python examples/machine_control_demo.py
python examples/home_robot_assistant.py
```

More guided recipes live in `../docs/EXAMPLE_RECIPES.md`.
