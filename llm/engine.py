from __future__ import annotations

import json
import logging
import re
import subprocess
import tempfile
import unicodedata
from pathlib import Path

from llm.prompts import build_tool_prompt, build_user_prompt
from tools.base import ToolRegistry
from utils.json_utils import extract_first_json_object
from utils.platform import current_platform, resolve_app_alias, resolve_executable_path


LOGGER = logging.getLogger("voice_assistant.llm")


class LocalLLMEngine:
    DIRECT_APP_ALIASES = {
        "notepad",
        "nodepad",
        "calculator",
        "calc",
        "chrome",
        "browser",
        "terminal",
        "powershell",
    }
    GREETING_PHRASES = {
        "hello",
        "hi",
        "hey",
        "hello assistant",
        "hi assistant",
        "hey assistant",
        "hola",
        "hola asistente",
        "buenas",
        "bonjour",
        "salut",
        "bonjour assistant",
        "hallo",
        "guten tag",
        "ciao",
        "ciao assistente",
        "ola",
        "ola assistente",
    }
    TIME_PHRASES = {
        "what time is it",
        "current time",
        "tell me the time",
        "whats the time",
        "que hora es",
        "dime la hora",
        "hora actual",
        "quelle heure est il",
        "donne moi lheure",
        "heure actuelle",
        "wie spat ist es",
        "wie viel uhr ist es",
        "aktuelle uhrzeit",
        "che ore sono",
        "dimmi lora",
        "que horas sao",
        "me diga as horas",
        "hora atual",
    }
    DATE_PHRASES = {
        "what date is it",
        "todays date",
        "current date",
        "what day is it",
        "que fecha es hoy",
        "que dia es hoy",
        "fecha actual",
        "quelle date sommes nous",
        "quel jour sommes nous",
        "date actuelle",
        "welches datum ist heute",
        "welcher tag ist heute",
        "aktuelles datum",
        "che data e oggi",
        "che giorno e oggi",
        "qual e la data di oggi",
        "que data e hoje",
        "que dia e hoje",
        "data atual",
    }
    MEMORY_PHRASES = {
        "show memory",
        "show recent memory",
        "list memory",
        "list recent memory",
        "muestra memoria",
        "muestra la memoria",
        "muestra memoria reciente",
        "mostrar memoria",
        "mostrar memoria reciente",
        "montre memoire",
        "affiche memoire",
        "affiche la memoire",
        "zeige speicher",
        "zeige den speicher",
        "zeige erinnerungen",
        "mostra memoria",
        "mostra la memoria",
        "mostrar memoria",
        "mostre a memoria",
        "mostra a memoria",
    }
    OPEN_PREFIXES = [
        "open",
        "launch",
        "start",
        "abre",
        "abrir",
        "inicia",
        "iniciar",
        "lanza",
        "lanzar",
        "ouvre",
        "ouvrir",
        "lance",
        "offne",
        "starte",
        "starten",
        "apri",
        "avvia",
        "abra",
        "abrir o",
        "abre o",
        "abra o",
    ]
    SEARCH_PREFIXES = [
        "search google for",
        "search for",
        "search",
        "google",
        "busca en google",
        "busca google",
        "busca",
        "buscar",
        "googlea",
        "cherche sur google",
        "recherche sur google",
        "cherche",
        "recherche",
        "suche bei google",
        "suche",
        "cerca su google",
        "cerca",
        "pesquise no google",
        "pesquise",
        "procure no google",
        "procure",
        "busque no google",
        "busque",
    ]
    RUN_PREFIXES = [
        "run",
        "execute",
        "ejecuta",
        "ejecutar",
        "executa",
        "executar",
        "execute la commande",
        "execute le programme",
        "fuhre aus",
        "ausfuhren",
        "esegui",
    ]
    OPEN_URL_PREFIXES = [
        "open url",
        "open website",
        "open site",
        "abre url",
        "abre sitio",
        "abre sitio web",
        "ouvre url",
        "ouvre site",
        "offne url",
        "offne webseite",
        "apri url",
        "apri sito",
        "abrir url",
        "abrir site",
        "abra url",
        "abra site",
    ]
    WIFI_STATE_PHRASES = {
        "turn wifi on": "on",
        "set wifi on": "on",
        "turn wifi off": "off",
        "set wifi off": "off",
        "enciende wifi": "on",
        "activa wifi": "on",
        "prende wifi": "on",
        "apaga wifi": "off",
        "desactiva wifi": "off",
        "apague wifi": "off",
        "allume le wifi": "on",
        "active le wifi": "on",
        "eteins le wifi": "off",
        "desactive le wifi": "off",
        "schalte wlan ein": "on",
        "aktiviere wlan": "on",
        "schalte wlan aus": "off",
        "deaktiviere wlan": "off",
        "attiva wifi": "on",
        "disattiva wifi": "off",
        "ligue o wifi": "on",
        "ative o wifi": "on",
        "desligue o wifi": "off",
        "desative o wifi": "off",
    }
    SPECIAL_TOOL_PHRASES = {
        "open settings": ("open_settings", {}),
        "open system settings": ("open_settings", {}),
        "open task manager": ("open_system_monitor", {}),
        "open system monitor": ("open_system_monitor", {}),
        "lock screen": ("lock_screen", {}),
        "sleep machine": ("sleep_machine", {}),
        "shutdown machine": ("shutdown_machine", {}),
        "restart machine": ("restart_machine", {}),
        "log out": ("log_out_user", {}),
        "logout": ("log_out_user", {}),
        "open desktop folder": ("open_desktop_folder", {}),
        "open downloads folder": ("open_downloads_folder", {}),
        "open documents folder": ("open_documents_folder", {}),
        "open home folder": ("open_home_folder", {}),
        "open workspace folder": ("open_workspace_folder", {}),
        "open notes folder": ("open_notes_folder", {}),
        "list processes": ("list_processes", {}),
        "show processes": ("list_processes", {}),
        "wifi on": ("wifi_on", {}),
        "wifi off": ("wifi_off", {}),
        "abre configuracion": ("open_settings", {}),
        "abre ajustes": ("open_settings", {}),
        "bloquea la pantalla": ("lock_screen", {}),
        "abre la carpeta descargas": ("open_downloads_folder", {}),
        "ouvre les parametres": ("open_settings", {}),
        "verrouille lecran": ("lock_screen", {}),
        "ouvre le dossier telechargements": ("open_downloads_folder", {}),
        "offne einstellungen": ("open_settings", {}),
        "bildschirm sperren": ("lock_screen", {}),
        "apri impostazioni": ("open_settings", {}),
        "blocca schermo": ("lock_screen", {}),
        "abrir configuracoes": ("open_settings", {}),
        "bloquear tela": ("lock_screen", {}),
    }
    CLOSE_PREFIXES = [
        "close",
        "quit",
        "stop",
        "cerrar",
        "cierra",
        "ferme",
        "schliesse",
        "chiudi",
        "fechar",
        "fecha",
    ]

    def __init__(self, config: dict, registry: ToolRegistry):
        self.executable = resolve_executable_path(config["executable"])
        self.runtime_executable = self._resolve_runtime_executable(self.executable)
        self.model = Path(config["model"]).resolve()
        self.ctx_size = int(config["ctx_size"])
        self.max_tokens = int(config["max_tokens"])
        self.temperature = float(config["temperature"])
        self.top_p = float(config["top_p"])
        self.repeat_penalty = float(config["repeat_penalty"])
        self.threads = int(config["threads"])
        self.timeout_seconds = int(config["timeout_seconds"])
        self.registry = registry
        self.intent_schema = {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": self.registry.tool_names(),
                },
                "parameters": {
                    "type": "object",
                    "additionalProperties": True,
                },
            },
            "required": ["action", "parameters"],
            "additionalProperties": False,
        }

    def is_available(self) -> bool:
        return self.runtime_executable.exists() and self.model.exists()

    def generate_intent(self, text: str, recent_items: list[dict]) -> dict:
        fast_path = self._fast_path_intent(text)
        if fast_path is not None:
            LOGGER.info("Fast-path intent: %s", fast_path)
            return fast_path
        if self.is_available():
            try:
                return self._generate_intent_with_llama(text, recent_items)
            except Exception as exc:
                LOGGER.warning("Falling back to rule-based parser after llama.cpp failure: %s", exc)
        return self._fallback_intent(text)

    def _generate_intent_with_llama(self, text: str, recent_items: list[dict]) -> dict:
        tool_prompt = build_tool_prompt(self.registry.describe_tools())
        user_prompt = build_user_prompt(text, recent_items)
        with tempfile.TemporaryDirectory(prefix="llama_intent_") as tmp_dir:
            tmp_path = Path(tmp_dir)
            system_prompt_path = tmp_path / "system_prompt.txt"
            user_prompt_path = tmp_path / "user_prompt.txt"
            schema_path = tmp_path / "intent_schema.json"

            system_prompt_path.write_text(tool_prompt, encoding="utf-8")
            user_prompt_path.write_text(user_prompt, encoding="utf-8")
            schema_path.write_text(json.dumps(self.intent_schema), encoding="utf-8")

            command = [
                str(self.runtime_executable),
                "-m",
                str(self.model),
                "--simple-io",
                "--no-display-prompt",
                "--log-disable",
                "--ctx-size",
                str(self.ctx_size),
                "-n",
                str(self.max_tokens),
                "--temp",
                str(self.temperature),
                "--top-p",
                str(self.top_p),
                "--repeat-penalty",
                str(self.repeat_penalty),
                "-t",
                str(self.threads),
                "--system-prompt-file",
                str(system_prompt_path),
                "--file",
                str(user_prompt_path),
                "--json-schema-file",
                str(schema_path),
            ]
            LOGGER.debug("Running llama.cpp command: %s", command)
            completed = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=False,
                timeout=self.timeout_seconds,
                cwd=str(self.runtime_executable.parent),
            )

        if completed.returncode != 0:
            error_text = completed.stderr.strip() or completed.stdout.strip()
            raise RuntimeError(error_text or f"llama.cpp failed with exit code {completed.returncode}")

        raw_output = completed.stdout.strip()
        if not raw_output and completed.stderr.strip():
            raw_output = completed.stderr.strip()
        if not raw_output:
            raise RuntimeError("llama.cpp returned no output.")

        intent = self._parse_llama_output(raw_output)
        self._validate_intent(intent)
        LOGGER.info("LLM intent: %s", intent)
        return intent

    def _resolve_runtime_executable(self, configured_executable: Path) -> Path:
        sibling_dir = configured_executable.parent
        preferred_names = [
            "llama-completion.exe",
            "llama-completion",
            configured_executable.name,
        ]
        for name in preferred_names:
            candidate = sibling_dir / name
            if candidate.exists():
                if candidate != configured_executable:
                    LOGGER.info("Using llama runtime executable: %s", candidate)
                return candidate.resolve()
        return configured_executable.resolve()

    def _parse_llama_output(self, raw_output: str) -> dict:
        candidates = [raw_output]
        try:
            candidates.append(extract_first_json_object(raw_output))
        except Exception:
            pass

        for candidate in candidates:
            try:
                return json.loads(candidate)
            except json.JSONDecodeError:
                repaired = self._repair_json(candidate)
                if repaired is not None:
                    try:
                        return json.loads(repaired)
                    except json.JSONDecodeError:
                        continue

        raise ValueError(f"Unable to parse llama.cpp JSON output: {raw_output[:500]}")

    def _repair_json(self, candidate: str) -> str | None:
        repaired = re.sub(r",(\s*[}\]])", r"\1", candidate)
        return repaired if repaired != candidate else None

    def _fast_path_intent(self, text: str) -> dict | None:
        normalized = self._normalize_command_text(text)
        return self._intent_from_normalized_text(normalized)

    def _fallback_intent(self, text: str) -> dict:
        normalized = self._normalize_command_text(text)
        intent = self._intent_from_normalized_text(normalized)
        if intent is not None:
            return intent
        return {"action": "respond", "parameters": {"message": f'I heard: "{text}"'}}

    def _intent_from_normalized_text(self, normalized: str) -> dict | None:
        if normalized in self.GREETING_PHRASES:
            return {"action": "respond", "parameters": {"message": "Hello. How can I help?"}}
        if normalized in self.TIME_PHRASES or normalized in self.DATE_PHRASES:
            return {"action": "get_time", "parameters": {}}
        special_action = self.SPECIAL_TOOL_PHRASES.get(normalized)
        if special_action is not None:
            action, parameters = special_action
            return {"action": action, "parameters": parameters}
        if self._looks_like_direct_app_request(normalized):
            return {"action": "open_app", "parameters": {"name": normalized}}

        close_target = self._match_prefixed_value(normalized, self.CLOSE_PREFIXES)
        if close_target:
            return {"action": "close_app", "parameters": {"name": close_target}}

        open_target = self._match_prefixed_value(normalized, self.OPEN_PREFIXES)
        if open_target:
            return {"action": "open_app", "parameters": {"name": open_target}}

        search_query = self._match_prefixed_value(normalized, self.SEARCH_PREFIXES)
        if search_query:
            return {"action": "web_search", "parameters": {"query": search_query}}

        command = self._match_prefixed_value(normalized, self.RUN_PREFIXES)
        if command:
            return {"action": "run_command", "parameters": {"cmd": command}}

        if normalized in self.MEMORY_PHRASES:
            return {"action": "show_memory", "parameters": {"limit": 5}}

        url = self._match_prefixed_value(normalized, self.OPEN_URL_PREFIXES)
        if url:
            return {"action": "open_url", "parameters": {"url": url}}

        wifi_state = self.WIFI_STATE_PHRASES.get(normalized)
        if wifi_state:
            return {"action": "control_device", "parameters": {"device": "wifi", "state": wifi_state}}

        return None

    def _validate_intent(self, intent: dict) -> None:
        if not isinstance(intent, dict):
            raise ValueError("Intent must be a JSON object.")
        if "action" not in intent or "parameters" not in intent:
            raise ValueError("Intent JSON must contain 'action' and 'parameters'.")
        if intent["action"] not in self.registry.tool_names():
            raise ValueError(f"Unknown tool '{intent['action']}'.")
        if not isinstance(intent["parameters"], dict):
            raise ValueError("Intent parameters must be a JSON object.")

    def _normalize_command_text(self, text: str) -> str:
        normalized = text.strip().lower()
        normalized = unicodedata.normalize("NFKD", normalized)
        normalized = normalized.encode("ascii", "ignore").decode("ascii")
        normalized = re.sub(r"[\"'`]+", "", normalized)
        normalized = re.sub(r"[?!.,;:]+$", "", normalized)
        normalized = re.sub(r"\s+", " ", normalized)
        return normalized

    def _looks_like_direct_app_request(self, normalized: str) -> bool:
        if " " in normalized or not normalized:
            return False
        resolved = resolve_app_alias(normalized, current_platform()).strip().lower()
        return normalized in self.DIRECT_APP_ALIASES or resolved != normalized

    def _match_prefixed_value(self, normalized: str, prefixes: list[str]) -> str | None:
        for prefix in sorted(prefixes, key=len, reverse=True):
            if normalized.startswith(prefix + " "):
                return normalized[len(prefix) :].strip()
        return None
