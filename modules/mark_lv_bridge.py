"""
Unified Action, Memory, Agent, Radar, and Vision Bridge for J.A.R.V.I.S. & F.R.I.D.A.Y.
Integrates all 17 Mark-LV action modules, Mark-XXXIX-OR multi-step Agent Planner/Executor,
Mark-LV structured Memory Manager & Undo Stack, AI-Assistant-1.1 OpenSky Aircraft Radar,
and Gemini 3.8 Flash Vision (screen + camera) into D:\\JARVIS.
"""
from __future__ import annotations

import io
import json
import math
import os
import sys
import threading
import time
import webbrowser
from pathlib import Path
from typing import Any, Callable

import requests

# Ensure Windows stdout/stderr never fail on Unicode/emoji logs from Mark-LV / Mark-XXXIX modules
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        try:
            _stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

ROOT_DIR = Path(__file__).resolve().parent.parent
MARK_LV_DIR = ROOT_DIR / "Repos" / "Mark-LV"
MARK_XXXIX_DIR = ROOT_DIR / "Repos" / "Mark-XXXIX-OR"

# Ensure Mark-LV takes priority over Mark-XXXIX-OR in sys.path (Mark-LV has the newest actions & memory_manager)
for repo_path in (MARK_XXXIX_DIR, MARK_LV_DIR):
    p_str = str(repo_path)
    if repo_path.exists():
        if p_str in sys.path:
            sys.path.remove(p_str)
        sys.path.insert(0, p_str)


def sync_api_keys_config() -> str:
    """Populate config/api_keys.json across workspace and reference repos from GEMINI_API_KEY env var."""
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY") or ""
    payload = {
        "gemini_api_key": api_key,
        "os_system": "windows",
        "camera_index": 0,
    }
    for base in (ROOT_DIR, MARK_LV_DIR, MARK_XXXIX_DIR):
        if base.exists():
            try:
                cfg_dir = base / "config"
                cfg_dir.mkdir(parents=True, exist_ok=True)
                cfg_file = cfg_dir / "api_keys.json"
                existing = {}
                if cfg_file.exists():
                    try:
                        existing = json.loads(cfg_file.read_text(encoding="utf-8"))
                    except Exception:
                        existing = {}
                existing.update({k: v for k, v in payload.items() if v != "" or k not in existing})
                if api_key:
                    existing["gemini_api_key"] = api_key
                cfg_file.write_text(json.dumps(existing, indent=2), encoding="utf-8")
            except Exception as e:
                print(f"[Bridge] Config sync warning for {base}: {e}")
    return api_key


def patch_gemini_models() -> None:
    """
    Patch Mark-LV core.gemini ladders and google.generativeai GenerativeModel
    so any legacy 'gemini-2.5-flash' or 'live' one-shot calls use 'gemini-3.8-flash'.
    """
    try:
        from core import gemini as lv_gemini
        lv_gemini._KEY_FILE = ROOT_DIR / "config" / "api_keys.json"
        lv_gemini._cached_key = None
        fast_ladder = (
            "gemini-3.8-flash",
            "gemini-flash-latest",
            "gemini-3.5-flash",
            "gemini-3.5-flash-lite",
        )
        lv_gemini._LADDERS[lv_gemini.FAST] = fast_ladder
        lv_gemini._LADDERS[lv_gemini.SMART] = fast_ladder
        lv_gemini._LADDERS[lv_gemini.SEARCH] = fast_ladder
    except Exception as e:
        print(f"[Bridge] core.gemini patch warning: {e}")

    try:
        import google.generativeai as genai
        _OrigGenModel = genai.GenerativeModel

        class _PatchedGenModel(_OrigGenModel):
            def __init__(self, model_name="gemini-3.8-flash", *args, **kwargs):
                if isinstance(model_name, str) and ("2.5-flash" in model_name or "1.5-flash" in model_name):
                    model_name = "gemini-3.8-flash"
                super().__init__(model_name, *args, **kwargs)

        genai.GenerativeModel = _PatchedGenModel
    except Exception as e:
        print(f"[Bridge] genai model redirect warning: {e}")


class JarvisUIAdapter:
    """
    Adapter passed as `player` to Mark-LV and Mark-XXXIX actions.
    Bridges `.write_log()`, `.show_content()`, `.show_video()`, and `.current_file`
    directly to our pywebview `hud.html` interface.
    """
    def __init__(self, pipeline):
        self.pipeline = pipeline
        self.current_file: str | None = None

    def write_log(self, text: str) -> None:
        if not text:
            return
        try:
            safe = json.dumps(str(text))
            self.pipeline.window.evaluate_js(f"addLog('SYSTEM', {safe})")
        except Exception:
            print(f"[HUD Log] {text}")

    def show_content(self, title: str, content: str, content_type: str = "text") -> None:
        snippet = str(content or "")[:600]
        self.write_log(f"[{title}] {snippet}")

    def show_video(self, source: str, title: str = "Video") -> None:
        self.write_log(f"Playing media: {title} ({source})")
        if str(source).startswith("http"):
            webbrowser.open(str(source))


# ==============================================================================
# OPENSKY AIRCRAFT RADAR (Ported from AI-Assistant-1.1 / Mark-X.1)
# ==============================================================================
OPENSKY_STATES = "https://opensky-network.org/api/states/all"
OPENSKY_FLIGHTS = "https://opensky-network.org/api/flights/aircraft"


def _haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0
    d_lat = math.radians(lat2 - lat1)
    d_lon = math.radians(lon2 - lon1)
    a = (
        math.sin(d_lat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(d_lon / 2) ** 2
    )
    return 2 * r * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _get_user_coords() -> tuple[float, float, str]:
    try:
        loc = requests.get("http://ip-api.com/json/", timeout=4).json()
        return float(loc.get("lat", 22.7196)), float(loc.get("lon", 75.8577)), loc.get("city", "Indore")
    except Exception:
        return 22.7196, 75.8577, "Indore"


def run_aircraft_radar(action: str = "report", radius_km: float = 200.0) -> str:
    """Scan nearby airspace within radius_km using OpenSky Network API or open FlightRadar24 map."""
    lat, lon, city = _get_user_coords()
    act = (action or "report").lower().strip()

    if act in ("map", "open", "radar"):
        url = f"https://www.flightradar24.com/{lat:.4f},{lon:.4f}/9"
        webbrowser.open(url)
        return f"Opening live FlightRadar24 airspace display over {city}, sir."

    deg_pad = max(1.0, radius_km / 100.0)
    lamin, lamax = lat - deg_pad, lat + deg_pad
    lomin, lomax = lon - deg_pad, lon + deg_pad

    try:
        resp = requests.get(
            f"{OPENSKY_STATES}?lamin={lamin:.4f}&lamax={lamax:.4f}&lomin={lomin:.4f}&lomax={lomax:.4f}",
            timeout=8,
        )
        data = resp.json() if resp.status_code == 200 else {}
    except Exception as e:
        return f"Airspace radar sweep encountered interference: {e}"

    planes = []
    for s in data.get("states") or []:
        p_lat, p_lon = s[6], s[5]
        if p_lat is None or p_lon is None:
            continue
        dist = _haversine(lat, lon, float(p_lat), float(p_lon))
        if dist <= radius_km:
            planes.append({
                "icao24": s[0],
                "callsign": (s[1] or "Unknown").strip() or "Unidentified",
                "country": s[2] or "Unknown",
                "distance": dist,
                "velocity_kmh": (s[9] or 0) * 3.6,
                "heading": s[10] or 0,
                "altitude_m": s[7] or 0,
            })

    if not planes:
        return f"Sir, radar scan complete over {city}. No active transponders detected within {int(radius_km)} kilometers."

    planes.sort(key=lambda x: x["distance"])
    closest = planes[0]
    total = len(planes)
    dist = closest["distance"]
    speed = closest["velocity_kmh"]
    heading = closest["heading"]

    if dist < 50:
        situation = "approaching your sector"
    elif dist < 120:
        situation = "transiting nearby airspace"
    else:
        situation = "operating at a safe distance"

    return (
        f"Sir, radar scan complete over {city}. I have detected {total} aircraft within {int(radius_km)} kilometers. "
        f"The nearest is callsign {closest['callsign']}, registered in {closest['country']}, "
        f"approximately {dist:.1f} kilometers away, traveling at {speed:.0f} kilometers per hour, "
        f"heading {heading:.0f} degrees, currently {situation}."
    )


# ==============================================================================
# SCREEN & WEBCAM GEMINI VISION (Ported from Mark-LV screen_processor.py)
# ==============================================================================
def run_screen_or_camera_vision(angle: str = "screen", text: str = "Describe what you see clearly and concisely.") -> str:
    """Capture screen or webcam frame and analyze with Gemini 3.8 Flash Vision."""
    try:
        from actions.screen_processor import _capture_screen, _capture_camera
        if (angle or "screen").lower().strip() in ("camera", "webcam", "cam", "face"):
            img_bytes, mime = _capture_camera()
            source_label = "webcam"
        else:
            img_bytes, mime = _capture_screen()
            source_label = "display"
    except Exception as e:
        return f"Visual sensor capture failed: {e}"

    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if api_key:
        try:
            from google import genai
            from google.genai import types as gtypes

            client = genai.Client(api_key=api_key)
            part = gtypes.Part.from_bytes(data=img_bytes, mime_type=mime)
            prompt = (
                f"You are analyzing the user's {source_label}. "
                f"Answer directly in 2-3 spoken sentences without markdown bullets: {text}"
            )
            resp = client.models.generate_content(
                model="gemini-3.8-flash",
                contents=[part, prompt],
            )
            if resp and getattr(resp, "text", None):
                return resp.text.strip()
        except Exception as e:
            print(f"[Vision] Gemini vision error: {e}")

    return f"Captured {source_label} frame ({len(img_bytes)} bytes), sir, but vision model did not return a description."


# ==============================================================================
# UNIFIED REGISTRY BUILDER & TOOL DISPATCHER
# ==============================================================================
class UnifiedToolSuite:
    """Holds Mark-LV ActionRegistry + 12 Core/Agent/Memory/Radar/World tools."""

    def __init__(self, pipeline):
        self.pipeline = pipeline
        self.ui = JarvisUIAdapter(pipeline)
        sync_api_keys_config()
        patch_gemini_models()

        # Bind Mark-LV confirmation gate
        try:
            from core import confirm
            confirm.bind(
                show=lambda title, detail: self.ui.write_log(f"CONFIRMATION REQUIRED: {title} — {detail}"),
                hide=lambda: None,
                log=self.ui.write_log,
            )
        except Exception as e:
            print(f"[Bridge] confirm.bind warning: {e}")

        # Load all 17 Mark-LV actions
        self.registry = None
        try:
            from core.action_loader import discover_actions
            actions_dir = MARK_LV_DIR / "actions"
            if actions_dir.exists():
                self.registry = discover_actions(actions_dir, logger=lambda m: print(f"[Mark-LV] {m}"))
        except Exception as e:
            print(f"[Bridge] Action discovery error: {e}")

        # Initialize SystemMonitor & ProactiveEngine
        self.sys_monitor = None
        self.proactive_engine = None
        try:
            from actions.system_monitor import SystemMonitor
            from actions.proactive import ProactiveEngine
            self.sys_monitor = SystemMonitor()
            self.proactive_engine = ProactiveEngine()
        except Exception as e:
            print(f"[Bridge] Monitor init warning: {e}")

    def speak(self, text: str) -> None:
        if text and hasattr(self.pipeline, "response_queue"):
            self.pipeline.response_queue.put(str(text))

    def get_ollama_tools(self) -> list[dict]:
        """Return OpenAI/Ollama-formatted tool declarations for all 29+ tools."""
        tools: list[dict] = []

        # 1. All 17 auto-discovered Mark-LV actions
        if self.registry:
            for decl in self.registry.get_tool_declarations():
                params = self._normalize_schema(decl.get("parameters", {"type": "object", "properties": {}}))
                tools.append({
                    "type": "function",
                    "function": {
                        "name": decl["name"],
                        "description": decl["description"][:300],
                        "parameters": params,
                    },
                })

        # 2. Core / Inline / Agent / Memory / Radar / World tools
        extra_tools = [
            {
                "name": "screen_process",
                "description": "Capture the user's screen or webcam camera and analyze it with Gemini Vision.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "angle": {"type": "string", "description": "'screen' or 'camera'"},
                        "text": {"type": "string", "description": "Question or instruction about what is visible"},
                    },
                    "required": ["text"],
                },
            },
            {
                "name": "aircraft_report",
                "description": "Scan live airspace radar within 200km for nearby aircraft (callsign, country, distance, speed, heading) or open the live FlightRadar24 map.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "action": {"type": "string", "description": "'report' for radar scan or 'map' to open FlightRadar24"},
                        "radius_km": {"type": "number", "description": "Radar scan radius in kilometers (default 200)"},
                    },
                },
            },
            {
                "name": "agent_task",
                "description": "Execute a complex multi-step autonomous goal using the Mark-XXXIX Agent Planner and Executor (chains web research, file creation, code execution, and app control).",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "goal": {"type": "string", "description": "Full natural-language description of the multi-step goal to accomplish"},
                    },
                    "required": ["goal"],
                },
            },
            {
                "name": "save_memory",
                "description": "Save a fact about the user to permanent structured long-term memory (identity, preferences, projects, relationships, wishes, notes).",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "category": {"type": "string", "description": "identity | preferences | projects | relationships | wishes | notes"},
                        "key": {"type": "string", "description": "Short snake_case key (e.g. name, favorite_language, current_project)"},
                        "value": {"type": "string", "description": "Value to remember"},
                    },
                    "required": ["category", "key", "value"],
                },
            },
            {
                "name": "recall_memory",
                "description": "Search permanent long-term memory for stored facts about the user, their projects, preferences, or notes.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Keyword to search in memory (or empty string to list all)"},
                    },
                },
            },
            {
                "name": "manage_monitor",
                "description": "Add, remove, list, or check background news/topic monitors.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "action": {"type": "string", "description": "add | remove | list | check"},
                        "topic": {"type": "string", "description": "Topic to monitor or remove"},
                    },
                    "required": ["action"],
                },
            },
            {
                "name": "system_status",
                "description": "Get a detailed hardware diagnostic report: CPU %, RAM GB, GPU %, CPU temperature, uptime, and active process count.",
                "parameters": {"type": "object", "properties": {}},
            },
            {
                "name": "undo",
                "description": "Undo the most recent file, desktop, or setting change made by JARVIS/FRIDAY, or list undo history.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "action": {"type": "string", "description": "'undo' (default) or 'list'"},
                    },
                },
            },
            {
                "name": "split_workspace",
                "description": "Tile two applications side-by-side on screen (snaps left_app to left half and right_app to right half).",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "left_app": {"type": "string", "description": "Left application name"},
                        "right_app": {"type": "string", "description": "Right application name"},
                    },
                    "required": ["left_app", "right_app"],
                },
            },
            {
                "name": "get_world_news",
                "description": "Fetch live breaking global news headlines and open the interactive World Monitor satellite dashboard.",
                "parameters": {"type": "object", "properties": {}},
            },
            {
                "name": "get_finance_news",
                "description": "Fetch live financial & market news headlines and open the interactive Finance Monitor dashboard.",
                "parameters": {"type": "object", "properties": {}},
            },
            {
                "name": "execute_terminal",
                "description": "Execute a shell or PowerShell command on the Windows machine and return its output.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "command": {"type": "string", "description": "Command line string to run"},
                    },
                    "required": ["command"],
                },
            },
        ]

        existing_names = {t["function"]["name"] for t in tools}
        for et in extra_tools:
            if et["name"] not in existing_names:
                tools.append({"type": "function", "function": et})

        return tools

    def _normalize_schema(self, schema: dict) -> dict:
        """Convert uppercase Gemini schema types ('OBJECT', 'STRING') to lowercase JSON Schema."""
        if not isinstance(schema, dict):
            return {"type": "object", "properties": {}}
        out = {}
        for k, v in schema.items():
            if k == "type" and isinstance(v, str):
                out[k] = v.lower()
            elif k == "properties" and isinstance(v, dict):
                out[k] = {pk: self._normalize_schema(pv) for pk, pv in v.items()}
            elif k == "items" and isinstance(v, dict):
                out[k] = self._normalize_schema(v)
            else:
                out[k] = v
        return out

    def execute(self, name: str, args: dict) -> str:
        """Execute any of the 29+ registered tools and return a spoken/logged result string."""
        args = args or {}
        self.ui.write_log(f"Executing tool: {name}")

        # 1. Check auto-discovered Mark-LV action registry first
        if self.registry and self.registry.has(name):
            ctx = {
                "player": self.ui,
                "speak": self.speak,
                "response": "",
                "session_memory": None,
            }
            return self.registry.run(name, args, ctx)

        # 2. Inline & Core tools
        if name in ("screen_process", "analyze_screen"):
            angle = args.get("angle", "screen")
            query = args.get("text") or args.get("query") or "Describe what is on screen."
            return run_screen_or_camera_vision(angle=angle, text=query)

        if name == "aircraft_report":
            return run_aircraft_radar(
                action=args.get("action", "report"),
                radius_km=float(args.get("radius_km", 200)),
            )

        if name == "agent_task":
            goal = args.get("goal", "")
            if not goal:
                return "Please specify a goal for the autonomous agent, sir."
            try:
                from agent.executor import AgentExecutor
                executor = AgentExecutor()
                threading.Thread(
                    target=lambda: executor.execute(goal=goal, speak=self.speak),
                    daemon=True,
                ).start()
                return f"Autonomous agent deployed for goal: {goal}. I will brief you as each step completes, sir."
            except Exception as e:
                return f"Agent task initialization failed: {e}"

        if name == "save_memory":
            try:
                from memory.memory_manager import remember
                cat = args.get("category", "notes")
                key = args.get("key", "note")
                val = args.get("value", "")
                return remember(key=key, value=val, category=cat)
            except Exception as e:
                return f"Memory save failed: {e}"

        if name == "recall_memory":
            try:
                from memory.memory_manager import search_memory
                q = str(args.get("query", "") or "").replace("_", " ")
                return search_memory(q)
            except Exception as e:
                return f"Memory recall failed: {e}"

        if name == "manage_monitor":
            try:
                from actions.background_monitor import add_monitor, remove_monitor, list_monitors, check_all
                act = (args.get("action") or "list").lower()
                topic = args.get("topic", "")
                if act == "add":
                    return add_monitor(topic)
                if act == "remove":
                    return remove_monitor(topic)
                if act == "check":
                    alerts = check_all()
                    return "\n".join(alerts) if alerts else "Checked all monitored topics; no new headlines today, sir."
                topics = list_monitors()
                return f"Currently monitoring: {', '.join(topics)}" if topics else "No active background topic monitors."
            except Exception as e:
                return f"Monitor management failed: {e}"

        if name == "system_status":
            try:
                from actions.system_monitor import get_system_status
                st = get_system_status()
                parts = [
                    f"CPU is at {st['cpu_percent']}%",
                    f"RAM is at {st['ram_percent']}% ({st['ram_used_gb']} of {st['ram_total_gb']} GB)",
                ]
                if st.get("gpu_percent") is not None:
                    parts.append(f"GPU load is {st['gpu_percent']}%")
                if st.get("cpu_temp_c") is not None:
                    parts.append(f"CPU temperature is {st['cpu_temp_c']}°C")
                parts.append(f"system uptime is {st['uptime']} across {st['process_count']} active processes")
                return "Sir, " + ", ".join(parts) + "."
            except Exception as e:
                return f"System status check failed: {e}"

        if name == "undo":
            try:
                from core.undo import undo_last, history
                if (args.get("action") or "undo").lower() == "list":
                    items = history()
                    return "Undo stack: " + ", ".join(items) if items else "Undo history is empty."
                return undo_last()
            except Exception as e:
                return f"Undo failed: {e}"

        return f"Tool '{name}' is not recognized."
