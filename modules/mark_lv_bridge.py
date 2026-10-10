"""
Unified Action, Memory, Agent, Radar, and Vision Bridge for J.A.R.V.I.S. & F.R.I.D.A.Y.
Integrates all 17 Mark-LV action modules, Mark-XXXIX-OR multi-step Agent Planner/Executor,
Mark-LV structured Memory Manager & Undo Stack, AI-Assistant-1.1 OpenSky Aircraft Radar,
and Gemini 3.8 Flash Vision (screen + camera) into D:\\JARVIS.
"""
from __future__ import annotations

import base64
import io
import json
import logging
import math
import os
import sys
import threading
import time
import warnings
import webbrowser
from pathlib import Path
from typing import Any, Callable

import requests

warnings.filterwarnings("ignore", category=FutureWarning)
logging.getLogger("google_genai.models").setLevel(logging.ERROR)
logging.getLogger("httpx").setLevel(logging.WARNING)

# Ensure Windows stdout/stderr never fail on Unicode/symbol logs from Mark-LV / Mark-XXXIX modules
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
for _repo_path in (MARK_XXXIX_DIR, MARK_LV_DIR):
    _p_str = str(_repo_path)
    if _repo_path.exists():
        if _p_str in sys.path:
            sys.path.remove(_p_str)
        sys.path.insert(0, _p_str)


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
                existing: dict[str, Any] = {}
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


GEMINI_MODEL_LADDER: tuple[str, ...] = (
    "gemini-3.5-flash-lite",
    "gemini-3.1-flash-lite",
    "gemini-flash-lite-latest",
    "gemini-3.5-flash",
    "gemini-3.6-flash",
    "gemini-3.7-flash",
)
_EXHAUSTED_MODELS: set[str] = set()


def get_active_gemini_ladder() -> list[str]:
    active = [m for m in GEMINI_MODEL_LADDER if m not in _EXHAUSTED_MODELS]
    return active if active else list(GEMINI_MODEL_LADDER)


def mark_model_exhausted(model_name: str) -> None:
    _EXHAUSTED_MODELS.add(model_name)


def patch_gemini_models() -> None:
    """
    Patch Mark-LV core.gemini ladders and google.generativeai GenerativeModel
    so any legacy 'gemini-2.5-flash' or rate-limited model automatically rotates
    across GEMINI_MODEL_LADDER without 429 crashes.
    """
    try:
        from core import gemini as lv_gemini
        lv_gemini._KEY_FILE = ROOT_DIR / "config" / "api_keys.json"
        lv_gemini._cached_key = None
        lv_gemini._LADDERS[lv_gemini.FAST] = (*GEMINI_MODEL_LADDER, lv_gemini.LIVE)
        lv_gemini._LADDERS[lv_gemini.SMART] = (*GEMINI_MODEL_LADDER, lv_gemini.LIVE)
        lv_gemini._LADDERS[lv_gemini.SEARCH] = ("gemini-3.5-flash-lite",)
    except Exception as e:
        print(f"[Bridge] core.gemini patch warning: {e}")

    try:
        import google.generativeai as genai
        from google.api_core import retry as g_retry
        _OrigGenModel = genai.GenerativeModel
        _NO_RETRY = g_retry.Retry(predicate=lambda exc: False)

        class _PatchedGenModel(_OrigGenModel):
            def __init__(self, model_name: str = "gemini-3.5-flash-lite", *args: Any, **kwargs: Any):
                self._init_args = args
                self._init_kwargs = kwargs
                ladder = get_active_gemini_ladder()
                if isinstance(model_name, str) and (
                    "2.5-flash" in model_name
                    or "1.5-flash" in model_name
                    or model_name in _EXHAUSTED_MODELS
                ):
                    model_name = ladder[0]
                self._current_model_name = model_name
                super().__init__(model_name, *args, **kwargs)

            def generate_content(self, contents: Any, *args: Any, **kwargs: Any):
                kwargs.setdefault("request_options", {"retry": _NO_RETRY})
                try:
                    return super().generate_content(contents, *args, **kwargs)
                except Exception as first_err:
                    err_str = str(first_err)
                    if any(code in err_str for code in ("429", "RESOURCE_EXHAUSTED", "Quota exceeded", "404")):
                        mark_model_exhausted(self._current_model_name)
                        for fallback_name in get_active_gemini_ladder():
                            if fallback_name == self._current_model_name:
                                continue
                            try:
                                alt = _OrigGenModel(fallback_name, *self._init_args, **self._init_kwargs)
                                return alt.generate_content(contents, *args, **kwargs)
                            except Exception as sub_err:
                                s_str = str(sub_err)
                                if any(code in s_str for code in ("429", "RESOURCE_EXHAUSTED", "404")):
                                    mark_model_exhausted(fallback_name)
                                continue
                    raise first_err

        genai.GenerativeModel = _PatchedGenModel
    except Exception as e:
        print(f"[Bridge] genai model redirect warning: {e}")


# ==============================================================================
# PRE-DECLARED GEMINI FUNCTION SIGNATURES (O(1) Reuse — Zero Per-Turn Reallocation)
# ==============================================================================
def _t_open_app(app_name: str, action: str = "open"):
    """Open, close, minimize, maximize, or switch to any installed desktop application (action: open | close | minimize | maximize | switch)."""

def _t_web_search(query: str, mode: str = "search", items: str = "", aspect: str = ""):
    """Search the web via DuckDuckGo (mode='search'), search breaking news (mode='news'), or compare products (mode='compare' with comma-separated items)."""

def _t_weather_report(city: str, time: str = "today"):
    """Get detailed weather report and open live Windy radar for any city (time: today | tomorrow | week)."""

def _t_send_message(platform: str, contact: str, message: str):
    """Send a message on WhatsApp, Telegram, Instagram, or Discord to a contact."""

def _t_reminder(date: str, time: str, message: str):
    """Schedule a desktop reminder via Windows Task Scheduler (date: YYYY-MM-DD, time: HH:MM)."""

def _t_youtube_video(action: str, query: str = "", url: str = "", save: bool = False):
    """Control YouTube: play a video (action='play', query='...'), summarize a video transcript (action='summarize', url='...'), get video info (action='info'), or show trending (action='trending')."""

def _t_computer_settings(action: str, value: str = ""):
    """Control computer settings: volume_up, volume_down, volume_set, mute, unmute, brightness_up, brightness_down, brightness_set, dark_mode, wifi_toggle, bluetooth_toggle, lock_screen, sleep, restart, shutdown, reload_page, close_tab, new_tab, zoom_in, zoom_out, scroll_up, scroll_down."""

def _t_browser_control(action: str, url: str = "", query: str = "", text: str = "", selector: str = "", direction: str = "down"):
    """Automate web browser via Playwright/CDP: go_to, search, click, type, scroll, fill_form, smart_click, smart_type, get_text, press, close."""

def _t_file_controller(action: str, path: str = "", name: str = "", destination: str = "", content: str = "", extension: str = ""):
    """Manage files and folders: list, create_file, create_folder, delete, move, copy, rename, read, write, find, largest, disk_usage, organize, info."""

def _t_desktop_control(action: str, path: str = "", url: str = "", mode: str = "by_type"):
    """Manage Windows Desktop: wallpaper (from file path), wallpaper_url (from image URL), organize (by_type or by_date), clean, list, stats."""

def _t_code_helper(action: str, description: str = "", language: str = "python", file_path: str = "", code: str = "", save_path: str = ""):
    """Write, edit, explain, run, or fix code files in any programming language and open in VS Code (action: write | edit | explain | run | auto | build)."""

def _t_dev_agent(description: str, project_name: str = "", language: str = "python", open_vscode: bool = True, run_project: bool = False):
    """Autonomous multi-file software engineer: plans architecture, writes all project files, installs dependencies, opens VS Code, and auto-fixes bugs."""

def _t_computer_control(action: str, text: str = "", x: int = 0, y: int = 0, key: str = "", description: str = "", window_title: str = ""):
    """Direct GUI mouse/keyboard automation: type, smart_type, click, double_click, right_click, hotkey, press, scroll, move, drag, copy, paste, screenshot, wait, clear_field, focus_window, screen_find, random_data."""

def _t_game_updater(action: str, game: str = "", platform: str = "all", schedule_time: str = "03:00"):
    """Manage PC games across Steam, Epic, Riot, Xbox, GOG, Ubisoft, EA, Battle.net: launch, list_installed, update, update_all, install, status, schedule, cancel_schedule."""

def _t_flight_finder(origin: str, destination: str, departure_date: str, return_date: str = "", passengers: int = 1, cabin: str = "economy", save: bool = False):
    """Search Google Flights for live flight routes, airlines, durations, and prices."""

def _t_file_processor(action: str, file_path: str = "", question: str = "", target_language: str = "en", output_format: str = "png"):
    """Process uploaded or local files (PDF, image, DOCX, Excel/CSV, audio/video, ZIP): analyze, summarize, ocr, describe, extract_text, to_word, translate, fix_writing, resize, compress, convert, filter, chart."""

def _t_video_player(action: str, source: str = "", timestamp: str = "", question: str = ""):
    """Play, stop, summarize, or analyze local or online video streams (action: play | stop | Summary | analyze | timestamp | mute | unmute)."""

def _t_screen_process(text: str, angle: str = "screen"):
    """Capture the user's screen (angle='screen') or webcam camera (angle='camera') and analyze what is visible using Gemini Vision."""

def _t_aircraft_report(action: str = "report", radius_km: int = 200):
    """Scan live OpenSky airspace radar within 200km for nearby aircraft (callsign, country, distance, speed, heading) or open the FlightRadar24 map (action: report | map)."""

def _t_agent_task(goal: str):
    """Deploy the Mark-XXXIX autonomous multi-step Agent Planner and Executor for complex multi-step goals."""

def _t_save_memory(category: str, key: str, value: str):
    """Save a permanent fact about the user to structured long-term memory (category: identity | preferences | projects | relationships | wishes | notes)."""

def _t_recall_memory(query: str = ""):
    """Search structured long-term memory for stored facts about the user."""

def _t_manage_monitor(action: str, topic: str = ""):
    """Manage background daily news/topic monitors (action: add | remove | list | check)."""

def _t_system_status():
    """Get a full hardware diagnostic report: CPU %, RAM GB, GPU %, CPU temperature, uptime, and process count."""

def _t_undo(action: str = "undo"):
    """Undo the last reversible file, desktop, or setting change made by the assistant (action: undo | list)."""

def _t_split_workspace(left_app: str, right_app: str):
    """Tile two applications side-by-side on screen (e.g. WhatsApp left, Chrome right)."""

def _t_launch_application(app_name: str):
    """Launch or open an installed desktop application (e.g. whatsapp, chrome, spotify, vscode, notepad, calculator)."""

def _t_system_hardware_control(action: str, app_name: str = ""):
    """Control volume (volume_up, volume_down, mute), brightness (brightness_up, brightness_down), or launch an application (launch_app with app_name)."""

def _t_window_management(action: str):
    """Manage desktop windows (minimize, maximize, snap_left, snap_right, show_desktop, lock_screen, screenshot, task_manager)."""

def _t_open_website(url: str):
    """Open any website URL, YouTube song or video search in the default web browser."""

def _t_get_world_news():
    """Fetch live breaking global news headlines and open the interactive satellite World Monitor dashboard."""

def _t_get_finance_news():
    """Fetch current market and financial news headlines and open the interactive Finance Monitor dashboard."""

def _t_open_world_monitor():
    """Open the live interactive satellite World Monitor dashboard on screen."""

def _t_open_finance_monitor():
    """Open the live financial markets dashboard on screen."""

def _t_execute_terminal(command: str):
    """Execute a shell or PowerShell command on the machine."""

_RAW_GEMINI_TOOLS = (
    (_t_open_app, "open_app"),
    (_t_web_search, "web_search"),
    (_t_weather_report, "weather_report"),
    (_t_send_message, "send_message"),
    (_t_reminder, "reminder"),
    (_t_youtube_video, "youtube_video"),
    (_t_computer_settings, "computer_settings"),
    (_t_browser_control, "browser_control"),
    (_t_file_controller, "file_controller"),
    (_t_desktop_control, "desktop_control"),
    (_t_code_helper, "code_helper"),
    (_t_dev_agent, "dev_agent"),
    (_t_computer_control, "computer_control"),
    (_t_game_updater, "game_updater"),
    (_t_flight_finder, "flight_finder"),
    (_t_file_processor, "file_processor"),
    (_t_video_player, "video_player"),
    (_t_screen_process, "screen_process"),
    (_t_aircraft_report, "aircraft_report"),
    (_t_agent_task, "agent_task"),
    (_t_save_memory, "save_memory"),
    (_t_recall_memory, "recall_memory"),
    (_t_manage_monitor, "manage_monitor"),
    (_t_system_status, "system_status"),
    (_t_undo, "undo"),
    (_t_split_workspace, "split_workspace"),
    (_t_launch_application, "launch_application"),
    (_t_system_hardware_control, "system_hardware_control"),
    (_t_window_management, "window_management"),
    (_t_open_website, "open_website"),
    (_t_get_world_news, "get_world_news"),
    (_t_get_finance_news, "get_finance_news"),
    (_t_open_world_monitor, "open_world_monitor"),
    (_t_open_finance_monitor, "open_finance_monitor"),
    (_t_execute_terminal, "execute_terminal"),
)
for _fn, _public_name in _RAW_GEMINI_TOOLS:
    _fn.__name__ = _public_name

GEMINI_TOOL_FUNCTIONS: list[Callable] = [fn for fn, _ in _RAW_GEMINI_TOOLS]


class JarvisUIAdapter:
    """
    Adapter passed as `player` to Mark-LV and Mark-XXXIX actions.
    Bridges `.write_log()`, `.show_content()`, `.show_video()`, and `.current_file`
    directly to our pywebview `hud.html` interface.
    """
    def __init__(self, pipeline: Any):
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
# SHARED GEOLOCATION & OPENSKY AIRCRAFT RADAR (Ported from AI-Assistant-1.1 / Mark-X.1)
# ==============================================================================
OPENSKY_STATES = "https://opensky-network.org/api/states/all"
_LOCATION_CACHE: dict[str, Any] | None = None


def get_user_location(force_refresh: bool = False) -> dict[str, Any]:
    """Return cached user geolocation (lat, lon, city, country, ip, isp) with dual-API fallback."""
    global _LOCATION_CACHE
    now = time.time()
    if not force_refresh and _LOCATION_CACHE and (now - _LOCATION_CACHE.get("ts", 0) < 900):
        return _LOCATION_CACHE

    data: dict[str, Any] = {
        "lat": 22.7196,
        "lon": 75.8577,
        "city": "Indore",
        "country": "IN",
        "ip": "Unknown",
        "isp": "Unknown ISP",
        "ts": now,
    }
    try:
        loc = requests.get("http://ip-api.com/json/", timeout=4).json()
        data.update({
            "lat": float(loc.get("lat", 22.7196)),
            "lon": float(loc.get("lon", 75.8577)),
            "city": str(loc.get("city") or "Indore"),
            "country": str(loc.get("countryCode") or ""),
            "ip": str(loc.get("query") or "Unknown"),
            "isp": str(loc.get("isp") or "Unknown ISP"),
        })
    except Exception:
        try:
            loc = requests.get("https://ipapi.co/json/", timeout=4).json()
            data.update({
                "lat": float(loc.get("latitude", 22.7196)),
                "lon": float(loc.get("longitude", 75.8577)),
                "city": str(loc.get("city") or "Indore"),
                "country": str(loc.get("country_code") or ""),
                "ip": str(loc.get("ip") or "Unknown"),
                "isp": str(loc.get("org") or "Unknown ISP"),
            })
        except Exception:
            pass

    _LOCATION_CACHE = data
    return data


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


def run_aircraft_radar(action: str = "report", radius_km: float = 200.0) -> str:
    """Scan nearby airspace within radius_km using OpenSky Network API or open FlightRadar24 map."""
    loc = get_user_location()
    lat, lon, city = loc["lat"], loc["lon"], loc["city"]
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
# SCREEN & WEBCAM GEMINI VISION (Ported from Mark-LV & Mark-XXXIX-OR)
# ==============================================================================
_VISION_CLIENT = None


def _get_active_window_title() -> str:
    """Return the title of the currently focused Windows application."""
    try:
        import ctypes
        user32 = ctypes.windll.user32
        hwnd = user32.GetForegroundWindow()
        length = user32.GetWindowTextLengthW(hwnd)
        if length > 0:
            buf = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, buf, length + 1)
            return buf.value.strip()
    except Exception:
        pass
    return "Desktop"


def _fast_capture_screen() -> tuple[bytes, str]:
    """Ultra-fast (~15ms) direct RGB-to-JPEG screen capture with 3-stage Windows GDI fallback."""
    import PIL.Image
    img = None
    try:
        import mss
        with mss.mss() as sct:
            monitors = sct.monitors
            target = monitors[1] if len(monitors) > 1 else monitors[0]
            shot = sct.grab(target)
            img = PIL.Image.frombytes("RGB", shot.size, shot.rgb)
    except Exception:
        try:
            import PIL.ImageGrab
            img = PIL.ImageGrab.grab(include_layered_windows=False).convert("RGB")
        except Exception:
            import pyautogui
            img = pyautogui.screenshot().convert("RGB")

    img.thumbnail((1152, 648), PIL.Image.BILINEAR)
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=76, optimize=False)
    return buf.getvalue(), "image/jpeg"


def run_screen_or_camera_vision(
    angle: str = "screen",
    text: str = "Analyze what is on my screen and help me with what I am looking at.",
    raw_image_bytes: bytes | None = None,
    window: Any = None,
) -> str:
    """Capture screen or webcam frame in ~2-15ms and analyze in a single pass with Gemini Vision."""
    global _VISION_CLIENT
    try:
        if raw_image_bytes:
            img_bytes, mime = raw_image_bytes, "image/jpeg"
            source_label = "webcam" if (angle or "").lower() in ("camera", "webcam", "cam", "face") else "display"
            src_tag = "[IMAGE SOURCE: LIVE HUD WEBCAM]" if source_label == "webcam" else "[IMAGE SOURCE: SCREEN CAPTURE]"
        elif (angle or "screen").lower().strip() in ("camera", "webcam", "cam", "face"):
            img_bytes, mime = None, "image/jpeg"
            if window is not None:
                try:
                    b64_data = window.evaluate_js("typeof captureCameraFrameBase64 === 'function' ? captureCameraFrameBase64() : ''")
                    if b64_data and isinstance(b64_data, str) and "," in b64_data:
                        img_bytes = base64.b64decode(b64_data.split(",", 1)[1])
                except Exception:
                    pass
            if not img_bytes:
                from actions.screen_processor import _capture_camera
                img_bytes, mime = _capture_camera()
            source_label = "webcam"
            src_tag = "[IMAGE SOURCE: WEBCAM]"
        else:
            img_bytes, mime = _fast_capture_screen()
            source_label = "display"
            win_title = _get_active_window_title()
            src_tag = f"[IMAGE SOURCE: SCREEN CAPTURE | ACTIVE WINDOW: {win_title}]"
    except Exception as e:
        return f"Visual sensor capture failed: {e}"

    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    prompt = (
        f"{src_tag}\n"
        "You are JARVIS from Iron Man. Analyze this image with technical precision and intelligence. "
        "Be specific about the exact person, object, gesture, application, text, code, or content visible, and help the user directly. "
        "Respond in maximum 2 to 3 short spoken sentences without markdown bullets or symbols. Speed and clarity are priority.\n"
        f"User request: {text}"
    )
    if api_key:
        try:
            from google import genai
            from google.genai import types as gtypes

            if _VISION_CLIENT is None:
                _VISION_CLIENT = genai.Client(api_key=api_key)
            part = gtypes.Part.from_bytes(data=img_bytes, mime_type=mime)
            for model_name in get_active_gemini_ladder():
                try:
                    resp = _VISION_CLIENT.models.generate_content(
                        model=model_name,
                        contents=[part, prompt],
                    )
                    if resp and getattr(resp, "text", None):
                        return resp.text.strip().replace("*", "")
                except Exception as m_err:
                    err_s = str(m_err)
                    if any(code in err_s for code in ("429", "RESOURCE_EXHAUSTED", "404")):
                        mark_model_exhausted(model_name)
                    continue
        except Exception as e:
            print(f"[Vision] Gemini vision error: {e}")

    # Offline / Local Vision Fallback via Ollama moondream:latest
    try:
        b64_img = base64.b64encode(img_bytes).decode("utf-8")
        r = requests.post(
            "http://localhost:11434/api/generate",
            json={"model": "moondream:latest", "prompt": prompt, "images": [b64_img], "stream": False},
            timeout=35,
        )
        if r.status_code == 200:
            ans = (r.json().get("response") or "").strip()
            if ans:
                return ans
    except Exception as e:
        print(f"[Vision] Local moondream fallback warning: {e}")

    return f"Captured {source_label} frame ({len(img_bytes)} bytes), sir, but vision model did not return a description."


# ==============================================================================
# UNIFIED REGISTRY BUILDER & TOOL DISPATCHER
# ==============================================================================
class UnifiedToolSuite:
    """Holds Mark-LV ActionRegistry + 12 Core/Agent/Memory/Radar/World tools."""

    def __init__(self, pipeline: Any):
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
        self.agent_executor = None
        self._cached_ollama_tools: list[dict[str, Any]] | None = None
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

    def get_ollama_tools(self) -> list[dict[str, Any]]:
        """Return OpenAI/Ollama-formatted tool declarations for all 29+ tools (cached after first build)."""
        if self._cached_ollama_tools is not None:
            return self._cached_ollama_tools

        tools: list[dict[str, Any]] = []

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
        extra_tools = (
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
        )

        existing_names = {t["function"]["name"] for t in tools}
        for et in extra_tools:
            if et["name"] not in existing_names:
                tools.append({"type": "function", "function": et})

        self._cached_ollama_tools = tools
        return tools

    def _normalize_schema(self, schema: dict[str, Any]) -> dict[str, Any]:
        """Convert uppercase Gemini schema types ('OBJECT', 'STRING') to lowercase JSON Schema."""
        if not isinstance(schema, dict):
            return {"type": "object", "properties": {}}
        out: dict[str, Any] = {}
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

    def execute(self, name: str, args: dict[str, Any]) -> str:
        """Execute any of the 29+ registered tools and return a spoken/logged result string."""
        args = args or {}
        self.ui.write_log(f"Executing tool: {name}")

        orb_only_tools = {
            "screen_process", "analyze_screen", "open_app", "browser_control",
            "youtube_video", "weather_report", "flight_finder", "code_helper",
            "dev_agent", "video_player", "game_updater", "send_message"
        }
        if name in orb_only_tools or (name == "aircraft_report" and str(args.get("action", "")).lower() == "map"):
            if hasattr(self.pipeline, "enter_orb_only_mode"):
                self.pipeline.enter_orb_only_mode(sleep_mode=False)
                if name in ("screen_process", "analyze_screen"):
                    time.sleep(0.35)

        # 1. Fast-path Screen & Camera Vision (bypasses legacy PNG/OpenCV locks)
        if name in ("screen_process", "analyze_screen"):
            angle = args.get("angle", "screen")
            query = args.get("text") or args.get("query") or "Describe what is visible."
            return run_screen_or_camera_vision(
                angle=angle,
                text=query,
                window=getattr(self.pipeline, "window", None),
            )

        # 2. Check auto-discovered Mark-LV action registry
        if self.registry and self.registry.has(name):
            ctx = {
                "player": self.ui,
                "speak": self.speak,
                "response": "",
                "session_memory": None,
            }
            return self.registry.run(name, args, ctx)

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
                self.agent_executor = executor
                cancel_evt = getattr(self.pipeline, "abort_event", None)
                threading.Thread(
                    target=lambda: executor.execute(goal=goal, speak=self.speak, cancel_flag=cancel_evt),
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
