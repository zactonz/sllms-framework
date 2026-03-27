from __future__ import annotations

import importlib
import importlib.util
import logging
from dataclasses import dataclass
from importlib import metadata
from pathlib import Path
from types import ModuleType
from typing import Any, Callable


LOGGER = logging.getLogger("voice_assistant.tools")
ToolHandler = Callable[[dict[str, Any]], "ToolResult"]


@dataclass
class ToolDefinition:
    name: str
    description: str
    parameters: dict[str, str]
    handler: ToolHandler


@dataclass
class ToolResult:
    success: bool
    message: str
    data: dict[str, Any] | None = None


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, ToolDefinition] = {}
        self.plugin_modules: list[ModuleType] = []
        self._loaded_plugin_keys: set[str] = set()

    def register(self, tool: ToolDefinition) -> None:
        self._tools[tool.name] = tool

    def get(self, name: str) -> ToolDefinition:
        if name not in self._tools:
            raise KeyError(f"Tool '{name}' is not registered.")
        return self._tools[name]

    def tool_names(self) -> list[str]:
        return sorted(self._tools.keys())

    def describe_tools(self) -> list[dict]:
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.parameters,
            }
            for tool in self._tools.values()
        ]

    def load_plugins(self, plugins_dir: Path, config: dict) -> None:
        self._load_directory_plugins(plugins_dir, config)
        self._load_configured_plugin_modules(config)
        self._load_entrypoint_plugins(config)

    def _load_directory_plugins(self, plugins_dir: Path, config: dict) -> None:
        if not plugins_dir.exists():
            return
        for plugin_path in sorted(plugins_dir.glob("*.py")):
            if plugin_path.name.startswith("_"):
                continue
            plugin_key = f"file:{plugin_path.resolve()}"
            if plugin_key in self._loaded_plugin_keys:
                continue
            spec = importlib.util.spec_from_file_location(plugin_path.stem, plugin_path)
            if spec is None or spec.loader is None:
                continue
            try:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                self._register_plugin_module(module, config, plugin_key, plugin_path.name)
            except Exception as exc:
                LOGGER.warning("Failed to load plugin file '%s': %s", plugin_path.name, exc)

    def _load_configured_plugin_modules(self, config: dict) -> None:
        module_names = config.get("tools", {}).get("plugin_modules", []) or []
        for module_name in module_names:
            normalized_name = str(module_name).strip()
            if not normalized_name:
                continue
            plugin_key = f"module:{normalized_name}"
            if plugin_key in self._loaded_plugin_keys:
                continue
            try:
                module = importlib.import_module(normalized_name)
                self._register_plugin_module(module, config, plugin_key, normalized_name)
            except Exception as exc:
                LOGGER.warning("Failed to load configured plugin module '%s': %s", normalized_name, exc)

    def _load_entrypoint_plugins(self, config: dict) -> None:
        tools_config = config.get("tools", {})
        if not bool(tools_config.get("enable_entrypoint_discovery", True)):
            return
        group = str(tools_config.get("plugin_entrypoint_group", "sllms.plugins")).strip() or "sllms.plugins"
        try:
            entry_points = metadata.entry_points()
            if hasattr(entry_points, "select"):
                selected = entry_points.select(group=group)
            else:
                selected = entry_points.get(group, [])
        except Exception as exc:
            LOGGER.warning("Unable to inspect plugin entry points for group '%s': %s", group, exc)
            return

        for entry_point in selected:
            plugin_key = f"entrypoint:{group}:{entry_point.name}"
            if plugin_key in self._loaded_plugin_keys:
                continue
            try:
                module = entry_point.load()
                # Allow either a module with register() or a register callable directly.
                if callable(module) and not hasattr(module, "register"):
                    register = module
                    register(self, config)
                    self._loaded_plugin_keys.add(plugin_key)
                    LOGGER.info("Loaded plugin entry point: %s", entry_point.name)
                    continue
                self._register_plugin_module(module, config, plugin_key, entry_point.name)
            except Exception as exc:
                LOGGER.warning("Failed to load plugin entry point '%s': %s", entry_point.name, exc)

    def _register_plugin_module(self, module: ModuleType, config: dict, plugin_key: str, display_name: str) -> None:
        register = getattr(module, "register", None)
        if callable(register):
            register(self, config)
            self.plugin_modules.append(module)
            self._loaded_plugin_keys.add(plugin_key)
            LOGGER.info("Loaded plugin: %s", display_name)
            return
        LOGGER.warning("Skipping plugin '%s' because it does not expose a callable register() function.", display_name)


class ToolDispatcher:
    def __init__(self, registry: ToolRegistry):
        self.registry = registry

    def dispatch(self, intent: dict[str, Any]) -> ToolResult:
        # The dispatcher keeps tool execution isolated from intent generation so
        # new tools can be added without changing the agent loop.
        action = intent["action"]
        parameters = intent.get("parameters", {})
        tool = self.registry.get(action)
        return tool.handler(parameters)
