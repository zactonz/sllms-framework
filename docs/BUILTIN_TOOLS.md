# Built-In Tools

SLLMS now ships with 101 built-in tools across system info, notes, memory, workspace automation, and safe machine control. Optional child repos can add desktop automation, browser helpers, and niche domain actions without bloating the base install.

## Core Agent Tools

- `open_app`
- `run_command`
- `control_device`
- `web_search`
- `open_url`
- `respond`
- `get_time`
- `call_api`
- `show_memory`

## Time And Date

- `get_date`
- `get_day_of_week`
- `get_month`
- `get_year`
- `get_timezone`
- `get_timestamp`

## System Information

- `get_hostname`
- `get_os_name`
- `get_os_release`
- `get_os_version`
- `get_machine_arch`
- `get_cpu_count`
- `get_python_version`
- `get_username`
- `get_home_directory`
- `get_working_directory`
- `get_temp_directory`
- `get_disk_usage`
- `get_environment_summary`
- `get_path_variable`
- `get_environment_variable`
- `get_local_ip`
- `get_platform_summary`
- `list_audio_inputs`
- `get_network_summary`
- `resolve_hostname`
- `ping_host`

## Folder And Project Navigation

- `open_home_folder`
- `open_desktop_folder`
- `open_downloads_folder`
- `open_documents_folder`
- `open_pictures_folder`
- `open_music_folder`
- `open_videos_folder`
- `open_temp_folder`
- `open_workspace_folder`
- `open_notes_folder`
- `open_logs_folder`
- `open_models_folder`
- `open_plugins_folder`
- `open_docs_folder`
- `open_examples_folder`
- `open_scripts_folder`
- `open_readme_file`
- `open_config_file`
- `open_folder`

## Clipboard

- `copy_to_clipboard`
- `read_clipboard`
- `clear_clipboard`

## Notes

- `save_note`
- `append_note`
- `read_note`
- `list_notes`
- `delete_note`
- `clear_notes`
- `note_exists`
- `note_stats`

## Workspace File Tools

- `list_directory`
- `read_text_file`
- `write_text_file`
- `append_text_file`
- `create_directory`
- `delete_file`
- `copy_file`
- `move_file`
- `path_exists`
- `file_info`
- `list_workspace_files`

## Memory Utilities

- `memory_count`
- `export_memory`
- `clear_memory`

## App Shortcuts

- `open_terminal`
- `open_browser`
- `open_notepad`
- `open_calculator`
- `open_settings`
- `open_system_monitor`

## Process Control

- `list_processes`
- `list_top_processes`
- `is_process_running`
- `kill_process`
- `close_app`
- `restart_app`

## Device Control

- `wifi_on`
- `wifi_off`
- `bluetooth_on`
- `bluetooth_off`

## Power Actions

- `lock_screen`
- `sleep_machine`
- `shutdown_machine`
- `restart_machine`
- `log_out_user`

## Optional Child Repos

The core repo does not bundle reusable external tool families.

Examples of separate child repos you can publish or install:

- `sllms-tools-browser`
- `sllms-tools-desktop`
- `sllms-tools-dev`

Those child repos depend on `sllms-framework`, not the other way around.

## Safety Notes

- `run_command` is disabled by default
- when enabled, `run_command` executes a single allowlisted command without shell chaining or redirection
- `kill_process` and `close_app` require `tools.allow_process_control: true`
- `lock_screen`, `sleep_machine`, `shutdown_machine`, `restart_machine`, and `log_out_user` require `tools.allow_power_actions: true`
- workspace write tools require `tools.allow_workspace_writes: true`
- destructive actions such as `delete_file`, `delete_note`, `clear_notes`, and `clear_memory` also require `tools.allow_sensitive_actions: true`
