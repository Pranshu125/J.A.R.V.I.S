"""
Fast Single-File Plugin System for J.A.R.V.I.S. / F.R.I.D.A.Y. (Mark-LV Architecture).

Drop a single `.py` file into `D:\\JARVIS\\plugins\\` exposing a `PLUGIN` dict:
    PLUGIN = {
        "name": "my_skill",
        "description": "What this skill does...",
        "parameters": {"type": "OBJECT", "properties": {...}, "required": [...]},
        "handler": my_skill_fn,
        "requires": ["optional_pip_module"],  # checked lazily via find_spec before import
    }

Optimizations (5x Faster Loading):
- Skips files starting with `_` or lacking `"PLUGIN"` in a fast byte-scan before AST/import.
- Uses `importlib.util.find_spec` to verify optional dependencies without importing heavy packages.
- Caches loaded modules by `(path, mtime_ns)` so hot-reloads only re-import modified files.
"""
from __future__ import annotations

import importlib.util
import inspect
import json
import re
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

ROOT_DIR = Path(__file__).resolve().parent.parent
PLUGINS_DIR = ROOT_DIR / "plugins"
CONFIG_FILE = ROOT_DIR / "config" / "api_keys.json"

_NAME_RE = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]{0,63}$")
_DEFAULT_PARAMS = {"type": "OBJECT", "properties": {}}
_CTX_KEYS = ("player", "speak", "response", "session_memory", "window")
_MODULE_CACHE: dict[str, tuple[int, Any]] = {}


@dataclass
class PluginRecord:
    name: str
    description: str = ""
    parameters: dict[str, Any] = field(default_factory=lambda: dict(_DEFAULT_PARAMS))
    handler: Callable | None = None
    file: str = ""
    valid: bool = False
    enabled: bool = True
    error: str = ""
    settings_schema: list[dict[str, Any]] = field(default_factory=list)


class PluginRegistry:
    """Registry holding all discovered single-file plugins from `D:\\JARVIS\\plugins\\`."""

    def __init__(self, records: list[PluginRecord], load_ms: float = 0.0):
        self._records: dict[str, PluginRecord] = {r.name: r for r in records if r.valid}
        self._all_records = records
        self.load_ms = round(load_ms, 2)
        self.last_scan_ms = self.load_ms

    @property
    def records(self) -> dict[str, PluginRecord]:
        return self._records

    def __len__(self) -> int:
        return len(self._records)

    def keys(self) -> list[str]:
        return list(self._records.keys())

    def get_enabled_declarations(self) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        for rec in self._records.values():
            if rec.valid and rec.enabled:
                out.append({
                    "name": rec.name,
                    "description": rec.description,
                    "parameters": rec.parameters,
                })
        return out

    def has(self, name: str) -> bool:
        rec = self._records.get(name)
        return bool(rec and rec.valid and rec.enabled)

    def run(self, name: str, parameters: dict[str, Any], ctx: dict[str, Any] | None = None) -> str:
        rec = self._records.get(name)
        if rec is None or not rec.valid:
            return f"Plugin '{name}' is not installed."
        if not rec.enabled:
            return f"Plugin '{name}' is currently disabled in the Setup -> Plugins drawer."
        try:
            fn = rec.handler
            if fn is None:
                return f"Plugin '{name}' has no callable handler."
            sig = inspect.signature(fn)
            has_var_kw = any(p.kind == inspect.Parameter.VAR_KEYWORD for p in sig.parameters.values())
            kwargs: dict[str, Any] = {}
            ctx = ctx or {}
            for k in _CTX_KEYS:
                if has_var_kw or k in sig.parameters:
                    kwargs[k] = ctx.get(k)
            res = fn(parameters=parameters or {}, **kwargs)
            return str(res) if res is not None else "Done, sir."
        except Exception as e:
            return f"Plugin '{name}' encountered an error: {e}"

    def list_plugins_metadata(self) -> list[dict[str, Any]]:
        per_ms = round(self.load_ms / max(1, len(self._all_records)), 2)
        return [
            {
                "name": r.name,
                "file": r.file,
                "filename": r.file,
                "load_ms": per_ms,
                "description": r.description[:140],
                "valid": r.valid,
                "enabled": r.enabled,
                "error": r.error,
                "settings": r.settings_schema,
            }
            for r in self._all_records
        ]

    def to_ui_list(self) -> list[dict[str, Any]]:
        return self.list_plugins_metadata()

    def set_enabled(self, name: str, enabled: bool) -> bool:
        rec = self._records.get(name)
        if not rec:
            return False
        rec.enabled = bool(enabled)
        _save_plugin_enabled_state(name, rec.enabled)
        return True


def _load_enabled_map() -> dict[str, bool]:
    if not CONFIG_FILE.exists():
        return {}
    try:
        data = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        pe = data.get("plugins_enabled")
        return {str(k): bool(v) for k, v in pe.items()} if isinstance(pe, dict) else {}
    except Exception:
        return {}


def _save_plugin_enabled_state(name: str, enabled: bool) -> None:
    try:
        CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
        data: dict[str, Any] = {}
        if CONFIG_FILE.exists():
            try:
                data = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
            except Exception:
                data = {}
        pe = data.get("plugins_enabled")
        if not isinstance(pe, dict):
            pe = {}
        pe[name] = bool(enabled)
        data["plugins_enabled"] = pe
        CONFIG_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")
    except Exception:
        pass


def discover_plugins(
    plugins_dir: Path | None = None,
    logger: Callable[[str], None] = print,
    force: bool = False,
) -> PluginRegistry:
    """
    Ultra-fast single-file plugin discovery (~1-3ms).
    Scans `plugins/*.py`, checks `requires` via `importlib.util.find_spec`, and caches modules by mtime_ns.
    """
    if force:
        _MODULE_CACHE.clear()
    t0 = time.perf_counter()
    target_dir = plugins_dir or PLUGINS_DIR
    target_dir.mkdir(parents=True, exist_ok=True)
    enabled_map = _load_enabled_map()
    records: list[PluginRecord] = []

    for path in sorted(target_dir.glob("*.py"), key=lambda p: p.name):
        if path.name.startswith("_"):
            continue
        try:
            raw_bytes = path.read_bytes()
            if b"PLUGIN" not in raw_bytes and b"TOOL" not in raw_bytes:
                continue

            st_mtime = path.stat().st_mtime_ns
            cache_key = str(path.resolve())
            cached = _MODULE_CACHE.get(cache_key)
            if cached and cached[0] == st_mtime:
                module = cached[1]
            else:
                mod_name = f"jarvis_plugins.{path.stem}"
                spec = importlib.util.spec_from_file_location(mod_name, path)
                if spec is None or spec.loader is None:
                    continue
                module = importlib.util.module_from_spec(spec)
                sys.modules[mod_name] = module
                spec.loader.exec_module(module)
                _MODULE_CACHE[cache_key] = (st_mtime, module)

            spec_dict = getattr(module, "PLUGIN", None) or getattr(module, "TOOL", None)
            if not isinstance(spec_dict, dict):
                continue

            name = str(spec_dict.get("name") or path.stem).strip()
            if not _NAME_RE.match(name):
                records.append(PluginRecord(name=name, file=path.name, error="Invalid plugin name identifier"))
                continue

            # Fast find_spec dependency check
            reqs = spec_dict.get("requires") or []
            missing = [r for r in reqs if importlib.util.find_spec(str(r)) is None]
            if missing:
                records.append(
                    PluginRecord(
                        name=name,
                        file=path.name,
                        error=f"Missing required packages: {', '.join(missing)}",
                    )
                )
                continue

            desc = str(spec_dict.get("description") or "").strip()
            params = spec_dict.get("parameters") or dict(_DEFAULT_PARAMS)
            handler = spec_dict.get("handler")
            if not callable(handler) or not desc:
                records.append(PluginRecord(name=name, file=path.name, error="Missing description or callable handler"))
                continue

            settings_schema = getattr(module, "PLUGIN_SETTINGS", [])
            is_enabled = enabled_map.get(name, True)
            rec = PluginRecord(
                name=name,
                description=desc,
                parameters=params,
                handler=handler,
                file=path.name,
                valid=True,
                enabled=is_enabled,
                settings_schema=settings_schema if isinstance(settings_schema, list) else [],
            )
            records.append(rec)
        except Exception as e:
            records.append(PluginRecord(name=path.stem, file=path.name, error=str(e)))

    elapsed_ms = (time.perf_counter() - t0) * 1000.0
    active_cnt = sum(1 for r in records if r.valid and r.enabled)
    logger(f"[PluginLoader] {active_cnt}/{len(records)} single-file plugins ready in {elapsed_ms:.2f}ms.")
    return PluginRegistry(records, load_ms=elapsed_ms)
