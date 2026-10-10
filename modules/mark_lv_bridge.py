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


# 8 REST models + 1 LIVE model = 9-Model Fallback Ladder (saves up to 11s per failed call, zero hangs)
GEMINI_MODEL_LADDER: tuple[str, ...] = (
    "gemini-3.5-flash-lite",
    "gemini-3.1-flash-lite",
    "gemini-flash-lite-latest",
    "gemini-3.5-flash",
    "gemini-3.6-flash",
    "gemini-3.7-flash",
    "gemini-2.5-flash-lite",
    "gemini-2.5-flash",
)
_EXHAUSTED_MODELS: set[str] = set()


def get_active_gemini_ladder() -> list[str]:
    active = [m for m in GEMINI_MODEL_LADDER if m not in _EXHAUSTED_MODELS]
    return active if active else list(GEMINI_MODEL_LADDER)


def mark_model_exhausted(model_name: str) -> None:
    _EXHAUSTED_MODELS.add(model_name)


def patch_gemini_models() -> None:
    """
    Configure the 9-Model Fallback Ladder (8 REST models + 1 LIVE model) across
    Mark-LV core.gemini and google.generativeai GenerativeModel with strict timeouts.
    """
    try:
        from core import gemini as lv_gemini
        lv_gemini._KEY_FILE = ROOT_DIR / "config" / "api_keys.json"
        lv_gemini._cached_key = None
        # 9-Model Ladder: 8 fast REST models + LIVE throwaway session
        nine_model_ladder = (*GEMINI_MODEL_LADDER, lv_gemini.LIVE)
        lv_gemini._LADDERS[lv_gemini.FAST] = nine_model_ladder
        lv_gemini._LADDERS[lv_gemini.SMART] = nine_model_ladder
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
                kwargs.setdefault("request_options", {"retry": _NO_RETRY, "timeout": 12.0})
                try:
                    return super().generate_content(contents, *args, **kwargs)
                except Exception as first_err:
                    err_str = str(first_err)
                    if any(code in err_str for code in ("429", "RESOURCE_EXHAUSTED", "Quota exceeded", "404", "503", "504", "DEADLINE_EXCEEDED")):
                        mark_model_exhausted(self._current_model_name)
                        for fallback_name in get_active_gemini_ladder():
                            if fallback_name == self._current_model_name:
                                continue
                            try:
                                alt = _OrigGenModel(fallback_name, *self._init_args, **self._init_kwargs)
                                return alt.generate_content(contents, *args, **kwargs)
                            except Exception as sub_err:
                                s_str = str(sub_err)
                                if any(code in s_str for code in ("429", "RESOURCE_EXHAUSTED", "404", "503", "504")):
                                    mark_model_exhausted(fallback_name)
                                continue
                    raise first_err

        genai.GenerativeModel = _PatchedGenModel
    except Exception as e:
        print(f"[Bridge] genai model redirect warning: {e}")


# ==============================================================================
# 12 FOCUSED CORE OS-DRIVING SKILLS (~1,000 FEWER TOKENS PER SESSION)
# + DYNAMIC SINGLE-FILE PLUGINS (`plugins/*.py`)
# ==============================================================================
def _t_video_player(action: str = "play", source: str = ""):
    """Play a YouTube link, local video file, or spoken description ('play the new Dune trailer') right inside the HUD in original language (action: play | stop | mute | unmute)."""

def _t_open_app(app_name: str, action: str = "open"):
    """Open, close, minimize, maximize, or switch to any desktop application (action: open | close | minimize | maximize | switch)."""

def _t_computer_settings(action: str, value: str = ""):
    """Control OS settings: volume_up, volume_down, volume_set, mute, unmute, brightness_up, brightness_down, brightness_set, dark_mode, wifi_toggle, bluetooth_toggle, lock_screen, sleep, restart, shutdown, snap_left, snap_right."""

def _t_web_search(query: str, mode: str = "search", items: str = "", aspect: str = ""):
    """Multi-mode web search: mode='search' (facts), 'news' (headlines), 'research' (deep dive), 'price' (cost lookup), or 'compare' (side-by-side comparison)."""

def _t_weather_report(city: str, time: str = "today"):
    """Get live weather forecast and radar for any city (time: today | tomorrow | week)."""

def _t_screen_process(text: str, angle: str = "screen"):
    """Visual awareness: analyze live screen capture (angle='screen') or webcam vision (angle='camera')."""

def _t_file_controller(action: str, path: str = "", name: str = "", destination: str = "", content: str = ""):
    """Manage files & folders with undo support: list, create_file, create_folder, delete, move, copy, rename, read, write, find, largest, disk_usage, organize."""

def _t_desktop_control(action: str, path: str = "", url: str = "", mode: str = "by_type"):
    """Control desktop wallpaper (wallpaper, wallpaper_url), organize desktop icons (by_type/by_date), or clean desktop."""

def _t_computer_control(action: str, text: str = "", x: int = 0, y: int = 0, key: str = "", window_title: str = ""):
    """GUI mouse & keyboard automation: click, double_click, right_click, type, hotkey, press, scroll, move, drag, focus_window, screenshot."""

def _t_reminder(date: str, time: str, message: str):
    """Schedule a native OS desktop reminder (date: YYYY-MM-DD, time: HH:MM)."""

def _t_save_memory(category: str, key: str, value: str):
    """Save or update a persistent user fact across sessions (category: identity | preferences | projects | relationships | wishes | notes)."""

def _t_aircraft_report(action: str = "report", radius_km: int = 200):
    """Scan live 200km OpenSky airspace radar for overhead aircraft or open FlightRadar24 map (action: report | map)."""

# Optional / Plugin-callable signatures (auto-mounted when corresponding single-file plugin is enabled)
def _t_pomodoro_timer(action: str = "start", minutes: int = 40, task: str = "Deep Focus Session"):
    """Start or stop a Pomodoro focus timer card inside the HUD (action: start | stop)."""

def _t_network_radar(action: str = "scan"):
    """Scan LAN devices, gateway ping latency, and open the live NETWORK RADAR card inside the HUD."""

def _t_disk_analyzer(drive: str = "C:\\"):
    """Analyze what is taking up disk space and display the interactive DISK MAP treemap card inside the HUD."""

def _t_earth_globe(mode: str = "vector", earthquakes: bool = False):
    """Show the interactive 3D Earth Globe inside the HUD (mode: vector | satellite | earthquakes)."""

def _t_hardware_schematic(part_a: str = "", part_b: str = ""):
    """Identify electronic components on camera or by name and render an interactive pinout wiring schematic inside the HUD."""

_RAW_GEMINI_TOOLS = (
    # 12 Focused Core OS-Driving Skills
    (_t_video_player, "video_player"),
    (_t_open_app, "open_app"),
    (_t_computer_settings, "computer_settings"),
    (_t_web_search, "web_search"),
    (_t_weather_report, "weather_report"),
    (_t_screen_process, "screen_process"),
    (_t_file_controller, "file_controller"),
    (_t_desktop_control, "desktop_control"),
    (_t_computer_control, "computer_control"),
    (_t_reminder, "reminder"),
    (_t_save_memory, "save_memory"),
    (_t_aircraft_report, "aircraft_report"),
    # 5 Fast Single-File HUD Plugins
    (_t_pomodoro_timer, "pomodoro_timer"),
    (_t_network_radar, "network_radar"),
    (_t_disk_analyzer, "disk_analyzer"),
    (_t_earth_globe, "earth_globe"),
    (_t_hardware_schematic, "hardware_schematic"),
)
for _fn, _public_name in _RAW_GEMINI_TOOLS:
    _fn.__name__ = _public_name

GEMINI_TOOL_FUNCTIONS: list[Callable] = [fn for fn, _ in _RAW_GEMINI_TOOLS]


class JarvisUIAdapter:
    """
    Adapter passed as `player` to Mark-LV actions and single-file plugins.
    Bridges `.write_log()`, `.show_content()`, `.show_video()`, `.stop_video()`,
    `.set_video_muted()`, `.video_is_playing()`, and `.request_say()` directly
    to our `hud.html` interface with Smart Mic Mute coupling.
    """
    def __init__(self, pipeline: Any):
        self.pipeline = pipeline
        self.current_file: str | None = None
        self._video_playing: bool = False
        self._video_muted: bool = True

    def write_log(self, text: str) -> None:
        if not text:
            return
        try:
            safe = json.dumps(str(text))
            self.pipeline.window.evaluate_js(f"addLog('SYSTEM', {safe})")
            if hasattr(self.pipeline, "remote_dashboard") and self.pipeline.remote_dashboard:
                self.pipeline.remote_dashboard.record_log("SYSTEM", str(text))
        except Exception:
            print(f"[HUD Log] {text}")

    def show_content(self, title: str, content: str, content_type: str = "text") -> None:
        snippet = str(content or "")[:600]
        self.write_log(f"[{title}] {snippet}")
        try:
            self.pipeline.window.evaluate_js("glanceAvatarDown && glanceAvatarDown()")
        except Exception:
            pass

    def video_is_playing(self) -> bool:
        return self._video_playing

    def show_video(
        self,
        source: str,
        title: str = "Video",
        muted: bool = True,
        audio_source: str = "",
    ) -> None:
        """Play video directly inside the HUD center stage (local file, direct stream, or dual-stream yt-dlp)."""
        src_str = str(source or "").strip()
        aud_str = str(audio_source or "").strip()
        if os.path.isfile(src_str) and hasattr(self.pipeline, "remote_dashboard") and self.pipeline.remote_dashboard:
            src_str = self.pipeline.remote_dashboard.get_local_media_url(src_str)

        self._video_playing = True
        self._video_muted = bool(muted)
        self.pipeline.video_sound_active = not bool(muted)

        if hasattr(self.pipeline, "exit_orb_only_mode"):
            self.pipeline.exit_orb_only_mode()

        self.write_log(f"Playing on HUD display: {title} ({'Muted' if muted else 'Sound ON — Mic Auto-Muted'})")
        try:
            js_call = (
                f"playHudVideo({json.dumps(src_str)}, {json.dumps(aud_str)}, "
                f"{json.dumps(str(title or 'HUD Media'))}, {'true' if muted else 'false'})"
            )
            self.pipeline.window.evaluate_js(js_call)
        except Exception as e:
            print(f"[HUD Video] show_video error: {e}")

    def stop_video(self) -> None:
        """Stop HUD video playback and cancel any in-flight yt-dlp background resolution."""
        try:
            from actions.video_player import _begin_open
            _begin_open()
        except Exception:
            pass
        self._video_playing = False
        self._video_muted = True
        self.pipeline.video_sound_active = False
        try:
            self.pipeline.window.evaluate_js("stopHudVideo && stopHudVideo()")
        except Exception:
            pass

    def set_video_muted(self, muted: bool) -> None:
        """Toggle HUD video sound and enforce Smart Mic Mute when video audio is active."""
        self._video_muted = bool(muted)
        self.pipeline.video_sound_active = self._video_playing and (not bool(muted))
        if self.pipeline.video_sound_active:
            self.write_log("Smart Mic Mute active: Microphone muted while video audio plays.")
        else:
            self.write_log("Video audio muted: Microphone restored.")
        try:
            self.pipeline.window.evaluate_js(f"setHudVideoMuted && setHudVideoMuted({'true' if muted else 'false'})")
        except Exception:
            pass

    def request_say(self, instruction: str) -> None:
        """Speak asynchronous updates from background threads (e.g. video fallback or mid-task notes)."""
        if not instruction:
            return
        msg = str(instruction)
        if ":" in msg and msg.lower().startswith("tell the user"):
            msg = msg.split(":", 1)[1].strip()
        if hasattr(self.pipeline, "response_queue"):
            self.pipeline.response_queue.put(msg)


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
    """Holds Mark-LV ActionRegistry + Fast Single-File PluginRegistry + 12 Core OS Skills."""

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

        # Load all Mark-LV actions
        self.registry = None
        try:
            from core.action_loader import discover_actions
            actions_dir = MARK_LV_DIR / "actions"
            if actions_dir.exists():
                self.registry = discover_actions(actions_dir, logger=lambda m: print(f"[Mark-LV] {m}"))
        except Exception as e:
            print(f"[Bridge] Action discovery error: {e}")

        # Load single-file drop-in plugins (~1-3ms)
        self.plugin_registry = None
        try:
            from modules.plugin_loader import discover_plugins
            self.plugin_registry = discover_plugins()
        except Exception as e:
            print(f"[Bridge] Plugin discovery warning: {e}")

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

    def reload_plugins(self) -> dict[str, Any]:
        try:
            from modules.plugin_loader import discover_plugins
            self.plugin_registry = discover_plugins(force=True)
            self._cached_ollama_tools = None
            items = self.plugin_registry.list_plugins_metadata()
            return {
                "count": len(items),
                "load_ms": self.plugin_registry.load_ms,
                "plugins": items,
            }
        except Exception:
            return {"count": 0, "load_ms": 0.0, "plugins": []}

    def get_gemini_tools(self) -> list[Callable]:
        """Return Gemini tool callables for the 12 core skills + single-file plugins."""
        return GEMINI_TOOL_FUNCTIONS

    def speak(self, text: str) -> None:
        if text and hasattr(self.pipeline, "response_queue"):
            self.pipeline.response_queue.put(str(text))

    def get_ollama_tools(self) -> list[dict[str, Any]]:
        """Return OpenAI/Ollama-formatted declarations for the 12 focused core skills + enabled single-file plugins."""
        if self._cached_ollama_tools is not None:
            return self._cached_ollama_tools

        core_12_names = {
            "video_player", "open_app", "computer_settings", "web_search",
            "weather_report", "screen_process", "file_controller", "desktop_control",
            "computer_control", "reminder", "save_memory", "aircraft_report",
        }
        tools: list[dict[str, Any]] = []

        # 1. Focused core actions from Mark-LV registry
        if self.registry:
            for decl in self.registry.get_tool_declarations():
                if decl["name"] in core_12_names:
                    params = self._normalize_schema(decl.get("parameters", {"type": "object", "properties": {}}))
                    tools.append({
                        "type": "function",
                        "function": {
                            "name": decl["name"],
                            "description": decl["description"][:220],
                            "parameters": params,
                        },
                    })

        # 2. Inline core declarations (screen_process, aircraft_report, save_memory)
        extra_core = (
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
                "description": "Scan live airspace radar within 200km for nearby aircraft or open FlightRadar24 map.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "action": {"type": "string", "description": "'report' or 'map'"},
                        "radius_km": {"type": "number", "description": "Scan radius in km (default 200)"},
                    },
                },
            },
            {
                "name": "save_memory",
                "description": "Save a fact about the user to permanent long-term memory.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "category": {"type": "string", "description": "identity | preferences | projects | relationships | wishes | notes"},
                        "key": {"type": "string", "description": "Short snake_case key"},
                        "value": {"type": "string", "description": "Value to remember"},
                    },
                    "required": ["category", "key", "value"],
                },
            },
        )
        existing_names = {t["function"]["name"] for t in tools}
        for et in extra_core:
            if et["name"] not in existing_names:
                tools.append({"type": "function", "function": et})
                existing_names.add(et["name"])

        # 3. Single-file drop-in plugins (`plugins/*.py`)
        if self.plugin_registry:
            for p_decl in self.plugin_registry.get_enabled_declarations():
                if p_decl["name"] not in existing_names:
                    tools.append({
                        "type": "function",
                        "function": {
                            "name": p_decl["name"],
                            "description": p_decl["description"][:220],
                            "parameters": self._normalize_schema(p_decl.get("parameters", {"type": "object", "properties": {}})),
                        },
                    })
                    existing_names.add(p_decl["name"])

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
        """Execute any core skill, single-file plugin, or Mark-LV action and return a spoken/logged result."""
        args = args or {}
        self.ui.write_log(f"Executing skill: {name}")

        # Note: video_player plays INSIDE the HUD center stage, so it stays in full HUD mode!
        orb_only_tools = {
            "screen_process", "analyze_screen", "open_app", "browser_control",
            "youtube_video", "weather_report", "flight_finder", "code_helper",
            "dev_agent", "game_updater", "send_message",
        }
        if name in orb_only_tools or (name == "aircraft_report" and str(args.get("action", "")).lower() == "map"):
            if hasattr(self.pipeline, "enter_orb_only_mode"):
                self.pipeline.enter_orb_only_mode(sleep_mode=False)
                if name in ("screen_process", "analyze_screen"):
                    time.sleep(0.35)

        # 1. Check fast single-file PluginRegistry (`plugins/*.py`)
        if self.plugin_registry and self.plugin_registry.has(name):
            ctx = {
                "player": self.ui,
                "speak": self.speak,
                "window": getattr(self.pipeline, "window", None),
            }
            return self.plugin_registry.run(name, args, ctx)

        # 2. Fast-path Screen & Camera Vision
        if name in ("screen_process", "analyze_screen"):
            angle = args.get("angle", "screen")
            query = args.get("text") or args.get("query") or "Describe what is visible."
            return run_screen_or_camera_vision(
                angle=angle,
                text=query,
                window=getattr(self.pipeline, "window", None),
            )

        # 3. Check auto-discovered Mark-LV action registry
        if self.registry and self.registry.has(name):
            ctx = {
                "player": self.ui,
                "speak": self.speak,
                "response": "",
                "session_memory": None,
            }
            res = self.registry.run(name, args, ctx)
            if name == "video_player" and isinstance(res, str) and res.startswith("status=opening"):
                src = args.get("source") or "your video"
                return f"Putting {src} on the HUD display in its original language right now, sir."
            return res

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

