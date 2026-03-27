from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from tools.base import ToolDefinition, ToolRegistry, ToolResult
from utils.platform import PlatformName, current_platform


def register_content_tools(registry: ToolRegistry, config: dict, memory=None) -> None:
    workspace_root = Path(config["tools"]["workspace_root"]).resolve()
    notes_dir = Path(config["tools"]["notes_dir"]).resolve()
    notes_dir.mkdir(parents=True, exist_ok=True)
    allow_workspace_writes = bool(config["tools"].get("allow_workspace_writes", False))
    allow_sensitive_actions = bool(config["tools"].get("allow_sensitive_actions", False))

    _register_clipboard_tools(registry)
    _register_note_tools(registry, notes_dir, allow_sensitive_actions)
    _register_file_tools(registry, workspace_root, allow_workspace_writes, allow_sensitive_actions)
    _register_memory_tools(registry, notes_dir, memory, allow_sensitive_actions)


def _register_clipboard_tools(registry: ToolRegistry) -> None:
    registry.register(
        ToolDefinition(
            name="copy_to_clipboard",
            description="Copy plain text to the system clipboard.",
            parameters={"text": "Plain text to copy."},
            handler=lambda params: _copy_to_clipboard(str(params.get("text", ""))),
        )
    )
    _register(registry, "read_clipboard", "Read plain text from the system clipboard.", {}, lambda params: _read_clipboard())
    _register(registry, "clear_clipboard", "Clear the system clipboard.", {}, lambda params: _copy_to_clipboard(""))


def _register_note_tools(registry: ToolRegistry, notes_dir: Path, allow_sensitive_actions: bool) -> None:
    registry.register(
        ToolDefinition(
            name="save_note",
            description="Save or replace a note file inside the configured notes directory.",
            parameters={"name": "Note file name without path separators.", "text": "Note content."},
            handler=lambda params: _save_note(notes_dir, str(params.get("name", "")), str(params.get("text", "")), append=False),
        )
    )
    registry.register(
        ToolDefinition(
            name="append_note",
            description="Append text to a note file inside the configured notes directory.",
            parameters={"name": "Note file name without path separators.", "text": "Text to append."},
            handler=lambda params: _save_note(notes_dir, str(params.get("name", "")), str(params.get("text", "")), append=True),
        )
    )
    registry.register(
        ToolDefinition(
            name="read_note",
            description="Read a note file from the configured notes directory.",
            parameters={"name": "Note file name without path separators."},
            handler=lambda params: _read_note(notes_dir, str(params.get("name", ""))),
        )
    )
    _register(registry, "list_notes", "List note files in the configured notes directory.", {}, lambda params: _list_notes(notes_dir))
    registry.register(
        ToolDefinition(
            name="delete_note",
            description="Delete a note file from the configured notes directory when sensitive actions are enabled.",
            parameters={"name": "Note file name without path separators."},
            handler=lambda params: _delete_note(notes_dir, str(params.get("name", "")), allow_sensitive_actions),
        )
    )
    _register(registry, "clear_notes", "Delete all note files when sensitive actions are enabled.", {}, lambda params: _clear_notes(notes_dir, allow_sensitive_actions))
    registry.register(
        ToolDefinition(
            name="note_exists",
            description="Check whether a note file exists in the configured notes directory.",
            parameters={"name": "Note file name without path separators."},
            handler=lambda params: _note_exists(notes_dir, str(params.get("name", ""))),
        )
    )
    _register(registry, "note_stats", "Return a summary of note files.", {}, lambda params: _note_stats(notes_dir))


def _register_file_tools(
    registry: ToolRegistry,
    workspace_root: Path,
    allow_workspace_writes: bool,
    allow_sensitive_actions: bool,
) -> None:
    registry.register(
        ToolDefinition(
            name="list_directory",
            description="List files inside a workspace-relative directory.",
            parameters={"path": "Workspace-relative path. Defaults to '.'", "limit": "Optional maximum items."},
            handler=lambda params: _list_directory(
                _resolve_workspace_path(workspace_root, str(params.get("path", "") or ".")),
                _int_param(params.get("limit"), 50, 1, 500),
            ),
        )
    )
    registry.register(
        ToolDefinition(
            name="read_text_file",
            description="Read a text file inside the configured workspace root.",
            parameters={"path": "Workspace-relative file path."},
            handler=lambda params: _read_text_file(_resolve_workspace_path(workspace_root, str(params.get("path", "")))),
        )
    )
    registry.register(
        ToolDefinition(
            name="write_text_file",
            description="Write a text file inside the configured workspace root when workspace writes are enabled.",
            parameters={"path": "Workspace-relative file path.", "text": "Text content to write."},
            handler=lambda params: _write_text_file(workspace_root, str(params.get("path", "")), str(params.get("text", "")), append=False, allow_workspace_writes=allow_workspace_writes),
        )
    )
    registry.register(
        ToolDefinition(
            name="append_text_file",
            description="Append text to a file inside the configured workspace root when workspace writes are enabled.",
            parameters={"path": "Workspace-relative file path.", "text": "Text content to append."},
            handler=lambda params: _write_text_file(workspace_root, str(params.get("path", "")), str(params.get("text", "")), append=True, allow_workspace_writes=allow_workspace_writes),
        )
    )
    registry.register(
        ToolDefinition(
            name="create_directory",
            description="Create a directory inside the configured workspace root when workspace writes are enabled.",
            parameters={"path": "Workspace-relative directory path."},
            handler=lambda params: _create_directory(workspace_root, str(params.get("path", "")), allow_workspace_writes),
        )
    )
    registry.register(
        ToolDefinition(
            name="delete_file",
            description="Delete a file inside the configured workspace root when workspace writes and sensitive actions are enabled.",
            parameters={"path": "Workspace-relative file or directory path."},
            handler=lambda params: _delete_file(workspace_root, str(params.get("path", "")), allow_workspace_writes, allow_sensitive_actions),
        )
    )
    registry.register(
        ToolDefinition(
            name="copy_file",
            description="Copy a file inside the configured workspace root when workspace writes are enabled.",
            parameters={"source": "Workspace-relative source path.", "destination": "Workspace-relative destination path."},
            handler=lambda params: _copy_file(workspace_root, str(params.get("source", "")), str(params.get("destination", "")), allow_workspace_writes),
        )
    )
    registry.register(
        ToolDefinition(
            name="move_file",
            description="Move a file inside the configured workspace root when workspace writes are enabled.",
            parameters={"source": "Workspace-relative source path.", "destination": "Workspace-relative destination path."},
            handler=lambda params: _move_file(workspace_root, str(params.get("source", "")), str(params.get("destination", "")), allow_workspace_writes),
        )
    )
    registry.register(
        ToolDefinition(
            name="path_exists",
            description="Check if a path exists inside the configured workspace root.",
            parameters={"path": "Workspace-relative path."},
            handler=lambda params: _path_exists(_resolve_workspace_path(workspace_root, str(params.get("path", "")))),
        )
    )
    registry.register(
        ToolDefinition(
            name="file_info",
            description="Return file metadata for a workspace-relative path.",
            parameters={"path": "Workspace-relative file or directory path."},
            handler=lambda params: _file_info(_resolve_workspace_path(workspace_root, str(params.get("path", "")))),
        )
    )
    _register(registry, "list_workspace_files", "List the top-level workspace files.", {}, lambda params: _list_directory(workspace_root, 200))


def _register_memory_tools(registry: ToolRegistry, notes_dir: Path, memory, allow_sensitive_actions: bool) -> None:
    _register(registry, "memory_count", "Return the number of stored memory items.", {}, lambda params: _memory_count(memory))
    _register(registry, "export_memory", "Export short-term memory to a JSON file in the notes directory.", {}, lambda params: _export_memory(memory, notes_dir))
    _register(registry, "clear_memory", "Clear short-term memory when sensitive actions are enabled.", {}, lambda params: _clear_memory(memory, allow_sensitive_actions))


def _register(registry: ToolRegistry, name: str, description: str, parameters: dict[str, str], handler) -> None:
    registry.register(ToolDefinition(name=name, description=description, parameters=parameters, handler=handler))


def _copy_to_clipboard(text: str) -> ToolResult:
    try:
        completed = _clipboard_write(text)
    except RuntimeError as exc:
        return ToolResult(False, str(exc))
    if completed.returncode != 0:
        return ToolResult(False, completed.stderr.strip() or completed.stdout.strip() or "Clipboard write failed.")
    return ToolResult(True, "Clipboard updated.", {"text": text})


def _read_clipboard() -> ToolResult:
    try:
        completed = _clipboard_read()
    except RuntimeError as exc:
        return ToolResult(False, str(exc))
    if completed.returncode != 0:
        return ToolResult(False, completed.stderr.strip() or completed.stdout.strip() or "Clipboard read failed.")
    text = completed.stdout.strip()
    return ToolResult(True, text or "Clipboard is empty.", {"text": text})


def _clipboard_write(text: str) -> subprocess.CompletedProcess:
    os_name = current_platform()
    if os_name == PlatformName.WINDOWS:
        return subprocess.run(["powershell", "-NoProfile", "-Command", "Set-Clipboard"], input=text, text=True, capture_output=True, check=False)
    if os_name == PlatformName.MACOS:
        return subprocess.run(["pbcopy"], input=text, text=True, capture_output=True, check=False)
    if shutil.which("wl-copy"):
        return subprocess.run(["wl-copy"], input=text, text=True, capture_output=True, check=False)
    if shutil.which("xclip"):
        return subprocess.run(["xclip", "-selection", "clipboard"], input=text, text=True, capture_output=True, check=False)
    if shutil.which("xsel"):
        return subprocess.run(["xsel", "--clipboard", "--input"], input=text, text=True, capture_output=True, check=False)
    raise RuntimeError("Clipboard tools are unavailable on this machine.")


def _clipboard_read() -> subprocess.CompletedProcess:
    os_name = current_platform()
    if os_name == PlatformName.WINDOWS:
        return subprocess.run(["powershell", "-NoProfile", "-Command", "Get-Clipboard"], capture_output=True, text=True, check=False)
    if os_name == PlatformName.MACOS:
        return subprocess.run(["pbpaste"], capture_output=True, text=True, check=False)
    if shutil.which("wl-paste"):
        return subprocess.run(["wl-paste"], capture_output=True, text=True, check=False)
    if shutil.which("xclip"):
        return subprocess.run(["xclip", "-selection", "clipboard", "-o"], capture_output=True, text=True, check=False)
    if shutil.which("xsel"):
        return subprocess.run(["xsel", "--clipboard", "--output"], capture_output=True, text=True, check=False)
    raise RuntimeError("Clipboard tools are unavailable on this machine.")


def _sanitize_note_name(name: str) -> Path:
    cleaned = name.strip().replace("\\", "_").replace("/", "_")
    if not cleaned:
        raise ValueError("A note name is required.")
    if not cleaned.endswith(".txt"):
        cleaned += ".txt"
    return Path(cleaned)


def _save_note(notes_dir: Path, name: str, text: str, append: bool) -> ToolResult:
    try:
        note_path = (notes_dir / _sanitize_note_name(name)).resolve()
    except ValueError as exc:
        return ToolResult(False, str(exc))
    mode = "a" if append else "w"
    with note_path.open(mode, encoding="utf-8") as handle:
        handle.write(text)
        if append and text and not text.endswith("\n"):
            handle.write("\n")
    return ToolResult(True, f"{'Appended to' if append else 'Saved'} note {note_path.name}.", {"path": str(note_path)})


def _read_note(notes_dir: Path, name: str) -> ToolResult:
    try:
        note_path = (notes_dir / _sanitize_note_name(name)).resolve()
    except ValueError as exc:
        return ToolResult(False, str(exc))
    if not note_path.exists():
        return ToolResult(False, f"Note not found: {note_path.name}")
    text = note_path.read_text(encoding="utf-8")
    return ToolResult(True, text or "(empty note)", {"path": str(note_path), "text": text})


def _list_notes(notes_dir: Path) -> ToolResult:
    notes = sorted(path.name for path in notes_dir.glob("*.txt"))
    return ToolResult(True, "\n".join(notes) if notes else "No notes found.", {"notes": notes})


def _delete_note(notes_dir: Path, name: str, allow_sensitive_actions: bool) -> ToolResult:
    if not allow_sensitive_actions:
        return ToolResult(False, "delete_note is disabled. Enable tools.allow_sensitive_actions in config.yaml.")
    try:
        note_path = (notes_dir / _sanitize_note_name(name)).resolve()
    except ValueError as exc:
        return ToolResult(False, str(exc))
    if not note_path.exists():
        return ToolResult(False, f"Note not found: {note_path.name}")
    note_path.unlink()
    return ToolResult(True, f"Deleted note {note_path.name}.", {"path": str(note_path)})


def _clear_notes(notes_dir: Path, allow_sensitive_actions: bool) -> ToolResult:
    if not allow_sensitive_actions:
        return ToolResult(False, "clear_notes is disabled. Enable tools.allow_sensitive_actions in config.yaml.")
    removed = 0
    for path in notes_dir.glob("*.txt"):
        path.unlink(missing_ok=True)
        removed += 1
    return ToolResult(True, f"Removed {removed} note files.", {"removed": removed})


def _note_exists(notes_dir: Path, name: str) -> ToolResult:
    try:
        note_path = (notes_dir / _sanitize_note_name(name)).resolve()
    except ValueError as exc:
        return ToolResult(False, str(exc))
    exists = note_path.exists()
    return ToolResult(True, f"Note {note_path.name} {'exists' if exists else 'does not exist'}.", {"path": str(note_path), "exists": exists})


def _note_stats(notes_dir: Path) -> ToolResult:
    notes = list(notes_dir.glob("*.txt"))
    total_bytes = sum(path.stat().st_size for path in notes if path.exists())
    return ToolResult(True, f"{len(notes)} notes using {total_bytes} bytes.", {"count": len(notes), "bytes": total_bytes})


def _resolve_workspace_path(workspace_root: Path, raw_path: str) -> Path:
    candidate = Path(raw_path.strip() or ".")
    if not candidate.is_absolute():
        candidate = workspace_root / candidate
    candidate = candidate.resolve()
    try:
        candidate.relative_to(workspace_root)
    except ValueError as exc:
        raise ValueError(f"Path '{candidate}' is outside the configured workspace root {workspace_root}.") from exc
    return candidate


def _list_directory(path: Path, limit: int) -> ToolResult:
    if not path.exists():
        return ToolResult(False, f"Directory not found: {path}")
    if not path.is_dir():
        return ToolResult(False, f"Path is not a directory: {path}")
    entries = sorted(path.iterdir(), key=lambda item: item.name.lower())
    lines = [entry.name + ("/" if entry.is_dir() else "") for entry in entries[:limit]]
    return ToolResult(True, "\n".join(lines) if lines else "(empty directory)", {"entries": lines, "path": str(path)})


def _read_text_file(path: Path) -> ToolResult:
    if not path.exists():
        return ToolResult(False, f"File not found: {path}")
    if not path.is_file():
        return ToolResult(False, f"Path is not a file: {path}")
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return ToolResult(False, f"File is not valid UTF-8 text: {path}")
    return ToolResult(True, text, {"path": str(path), "text": text})


def _write_text_file(workspace_root: Path, raw_path: str, text: str, append: bool, allow_workspace_writes: bool) -> ToolResult:
    if not allow_workspace_writes:
        return ToolResult(False, "Workspace writes are disabled. Enable tools.allow_workspace_writes in config.yaml.")
    path = _resolve_workspace_path(workspace_root, raw_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a" if append else "w", encoding="utf-8") as handle:
        handle.write(text)
    return ToolResult(True, f"{'Appended to' if append else 'Wrote'} {path}.", {"path": str(path)})


def _create_directory(workspace_root: Path, raw_path: str, allow_workspace_writes: bool) -> ToolResult:
    if not allow_workspace_writes:
        return ToolResult(False, "Workspace writes are disabled. Enable tools.allow_workspace_writes in config.yaml.")
    path = _resolve_workspace_path(workspace_root, raw_path)
    path.mkdir(parents=True, exist_ok=True)
    return ToolResult(True, f"Created directory {path}.", {"path": str(path)})


def _delete_file(workspace_root: Path, raw_path: str, allow_workspace_writes: bool, allow_sensitive_actions: bool) -> ToolResult:
    if not allow_workspace_writes or not allow_sensitive_actions:
        return ToolResult(False, "delete_file requires tools.allow_workspace_writes and tools.allow_sensitive_actions.")
    path = _resolve_workspace_path(workspace_root, raw_path)
    if not path.exists():
        return ToolResult(False, f"Path not found: {path}")
    if path.is_dir():
        shutil.rmtree(path)
    else:
        path.unlink()
    return ToolResult(True, f"Deleted {path}.", {"path": str(path)})


def _copy_file(workspace_root: Path, source_raw: str, destination_raw: str, allow_workspace_writes: bool) -> ToolResult:
    if not allow_workspace_writes:
        return ToolResult(False, "Workspace writes are disabled. Enable tools.allow_workspace_writes in config.yaml.")
    source = _resolve_workspace_path(workspace_root, source_raw)
    destination = _resolve_workspace_path(workspace_root, destination_raw)
    if not source.exists():
        return ToolResult(False, f"Source not found: {source}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    if source.is_dir():
        shutil.copytree(source, destination, dirs_exist_ok=True)
    else:
        shutil.copy2(source, destination)
    return ToolResult(True, f"Copied {source} to {destination}.", {"source": str(source), "destination": str(destination)})


def _move_file(workspace_root: Path, source_raw: str, destination_raw: str, allow_workspace_writes: bool) -> ToolResult:
    if not allow_workspace_writes:
        return ToolResult(False, "Workspace writes are disabled. Enable tools.allow_workspace_writes in config.yaml.")
    source = _resolve_workspace_path(workspace_root, source_raw)
    destination = _resolve_workspace_path(workspace_root, destination_raw)
    if not source.exists():
        return ToolResult(False, f"Source not found: {source}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(source), str(destination))
    return ToolResult(True, f"Moved {source} to {destination}.", {"source": str(source), "destination": str(destination)})


def _path_exists(path: Path) -> ToolResult:
    exists = path.exists()
    return ToolResult(True, f"{path} {'exists' if exists else 'does not exist'}.", {"path": str(path), "exists": exists})


def _file_info(path: Path) -> ToolResult:
    if not path.exists():
        return ToolResult(False, f"Path not found: {path}")
    stat = path.stat()
    data = {
        "path": str(path),
        "is_file": path.is_file(),
        "is_dir": path.is_dir(),
        "size": stat.st_size,
    }
    return ToolResult(True, f"{path.name}: {data['size']} bytes.", data)


def _memory_count(memory) -> ToolResult:
    if memory is None:
        return ToolResult(False, "Assistant memory is unavailable.")
    count = len(memory.recent_items())
    return ToolResult(True, f"Memory contains {count} items.", {"count": count})


def _export_memory(memory, notes_dir: Path) -> ToolResult:
    if memory is None:
        return ToolResult(False, "Assistant memory is unavailable.")
    export_path = notes_dir / "assistant_memory_export.json"
    source_path = memory.path
    export_path.write_text(source_path.read_text(encoding="utf-8") if source_path.exists() else "[]", encoding="utf-8")
    return ToolResult(True, f"Exported memory to {export_path}.", {"path": str(export_path)})


def _clear_memory(memory, allow_sensitive_actions: bool) -> ToolResult:
    if memory is None:
        return ToolResult(False, "Assistant memory is unavailable.")
    if not allow_sensitive_actions:
        return ToolResult(False, "clear_memory is disabled. Enable tools.allow_sensitive_actions in config.yaml.")
    memory.path.write_text("[]", encoding="utf-8")
    return ToolResult(True, "Cleared assistant memory.", {"path": str(memory.path)})


def _int_param(raw_value, default: int, minimum: int, maximum: int) -> int:
    try:
        value = int(raw_value)
    except (TypeError, ValueError):
        value = default
    return max(minimum, min(maximum, value))
