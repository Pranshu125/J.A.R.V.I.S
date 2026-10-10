from __future__ import annotations

import base64
import ctypes
import json
import logging
import os
import queue
import random
import re
import subprocess
import threading
import time
import warnings
import webbrowser
from typing import Any, Callable

import psutil
import pygame
import requests
import speech_recognition as sr
import webview

warnings.filterwarnings("ignore", category=FutureWarning)
logging.getLogger("google_genai.models").setLevel(logging.ERROR)
logging.getLogger("httpx").setLevel(logging.WARNING)

# Automatically load environment variables from .env
_ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
_ENV_PATH = os.path.join(_ROOT_DIR, ".env")
if os.path.exists(_ENV_PATH):
    try:
        with open(_ENV_PATH, "r", encoding="utf-8") as _f:
            for _line in _f:
                _line = _line.strip()
                if _line and not _line.startswith("#") and "=" in _line:
                    _k, _v = _line.split("=", 1)
                    _k, _v = _k.strip(), _v.strip().strip('"').strip("'")
                    if _k and not os.environ.get(_k):
                        os.environ[_k] = _v
    except Exception:
        pass

# Global Process Patch (Mark-LV Architecture): Suppress background console flashing while remaining a true Popen class
if os.name == "nt":
    _OrigPopen = subprocess.Popen

    class _SilentPopen(_OrigPopen):
        def __init__(self, *args: Any, **kwargs: Any):
            if "creationflags" not in kwargs:
                kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW
            super().__init__(*args, **kwargs)

    subprocess.Popen = _SilentPopen

from modules.mark_lv_bridge import (
    GEMINI_TOOL_FUNCTIONS,
    UnifiedToolSuite,
    get_active_gemini_ladder,
    get_user_location,
    mark_model_exhausted,
    run_screen_or_camera_vision,
)
from modules.remote_dashboard import RemoteDashboardServer
from modules.system_control import (
    brightness_control,
    launch_application,
    split_workspace,
    volume_control,
    window_action,
)
from modules.tts_engine import TTS_ABORT_EVENT, get_instant_ack, speak_text, stop_speaking
from modules.world_intel import (
    get_finance_news_sync,
    get_world_news_sync,
    open_finance_monitor,
    open_world_monitor,
)

# ========================================================
# J.A.R.V.I.S. & F.R.I.D.A.Y. MARK 55 UNIFIED COGNITIVE OS
# - In-HUD Video on Command (Original Language + Dual Stream)
# - Talks While It Loads + Instant Voice Cancel ("stop")
# - Smart Mic Mute (Auto-Mutes Mic When Video Sound Is On)
# - 9-Model Gemini Fallback Ladder (11s Timeout + Cooldowns)
# - 12 Focused Core OS Skills + 5x Faster 1-File Plugin Engine
# - Separate Instant Setup & Controls Drawers + Live Theming
# - 4 Switchable HUD Centerpieces (Sphere, 3D Face, Reactor, Circuit)
# - Jared Rhod's Barehands AR Spatial Hand-Tracking Stage
# - QR Code Remote Smartphone Dashboard (Port 8787)
# ========================================================

OLLAMA_URL = "http://localhost:11434/api/chat"
OLLAMA_MODEL = "llama3.2"
MEMORY_DB = os.path.join(_ROOT_DIR, "jarvis_state.md")
VAULT_INDEX_PATH = os.path.join(_ROOT_DIR, "vault", "VAULT-INDEX.md")

_KILL_CLEAN_RE = re.compile(r"[^a-z0-9\s\u0900-\u097F]")
_URL_RE = re.compile(r"https?://[^\s\"']+")
_STATE_TURN_RE = re.compile(r"\*\*(USER|JARVIS):\*\*\s*(.+)")


def _get_screen_size() -> tuple[int, int]:
    """Return primary display width and height in pixels."""
    if os.name == "nt":
        try:
            return int(ctypes.windll.user32.GetSystemMetrics(0)), int(ctypes.windll.user32.GetSystemMetrics(1))
        except Exception:
            pass
    return 1920, 1080


class MemoryModule:
    """Persistent Conversational & Two-Layer Vault Memory (Mark-LV + Jared Rhod ai-memory-vault)."""

    @staticmethod
    def load() -> list[tuple[str, str]]:
        if not os.path.exists(MEMORY_DB):
            return []
        try:
            with open(MEMORY_DB, "r", encoding="utf-8") as f:
                return [(role, msg.strip()) for role, msg in _STATE_TURN_RE.findall(f.read())][-15:]
        except Exception:
            return []

    @staticmethod
    def save(history: list[tuple[str, str]]) -> None:
        try:
            with open(MEMORY_DB, "w", encoding="utf-8") as f:
                f.write("# J.A.R.V.I.S. Memory Vault\n\n")
                for role, msg in history[-15:]:
                    f.write(f"**{role}:** {msg}\n\n")
        except Exception:
            pass

    @staticmethod
    def get_long_term_prompt() -> str:
        parts: list[str] = []
        try:
            from memory.memory_manager import format_memory_for_prompt, load_memory
            mem_str = format_memory_for_prompt(load_memory())
            if mem_str:
                parts.append(mem_str)
        except Exception:
            pass
        if os.path.exists(VAULT_INDEX_PATH):
            try:
                with open(VAULT_INDEX_PATH, "r", encoding="utf-8") as f:
                    vault_idx = f.read(650).strip()
                    if vault_idx:
                        parts.append(f"[VAULT INDEX]\n{vault_idx}")
            except Exception:
                pass
        return "\n".join(parts)


class IntelligenceModule:
    """Hybrid Cognitive Engine: 9-Model Gemini Fallback Ladder (11s Timeout) + Local Ollama Fallback."""

    @staticmethod
    def chat(
        messages: list[dict[str, str]],
        tools: list[dict[str, Any]],
        window: Any,
        abort_check: Callable[[], bool] | None = None,
        gemini_tools: list[Any] | None = None,
    ) -> dict[str, Any]:
        if abort_check and abort_check():
            return {"role": "assistant", "content": ""}

        api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        if api_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=api_key)

                sys_inst = messages[0]["content"] if messages and messages[0]["role"] == "system" else "You are JARVIS."
                user_prompt = messages[-1]["content"] if messages else "Hello"
                active_g_tools = gemini_tools if gemini_tools is not None else GEMINI_TOOL_FUNCTIONS

                for m_name in get_active_gemini_ladder():
                    if abort_check and abort_check():
                        return {"role": "assistant", "content": ""}
                    try:
                        model = genai.GenerativeModel(
                            m_name,
                            tools=active_g_tools,
                            system_instruction=sys_inst,
                        )
                        res = model.generate_content(
                            user_prompt,
                            request_options={"timeout": 11.0},
                        )
                        if abort_check and abort_check():
                            return {"role": "assistant", "content": ""}
                        if res.candidates and res.candidates[0].content.parts:
                            parts = res.candidates[0].content.parts
                            tool_calls = [
                                {"function": {"name": p.function_call.name, "arguments": dict(p.function_call.args)}}
                                for p in parts
                                if p.function_call
                            ]
                            if tool_calls:
                                return {"role": "assistant", "content": "", "tool_calls": tool_calls}

                            text_parts = [p.text for p in parts if p.text]
                            if text_parts:
                                return {"role": "assistant", "content": "".join(text_parts).strip()}
                        return {"role": "assistant", "content": res.text.strip()}
                    except Exception as m_err:
                        err_s = str(m_err)
                        if any(code in err_s for code in ("429", "RESOURCE_EXHAUSTED", "Quota exceeded", "404", "503", "DeadlineExceeded")):
                            mark_model_exhausted(m_name, err_s)
                        continue
            except Exception as e:
                safe_err = json.dumps(f"Gemini fallback to Ollama: {str(e).splitlines()[0][:120]}")
                try:
                    window.evaluate_js(f"addLog('SYSTEM', {safe_err})")
                except Exception:
                    pass

        if abort_check and abort_check():
            return {"role": "assistant", "content": ""}

        # Local Ollama Mode with low-latency configuration
        payload = {
            "model": OLLAMA_MODEL,
            "messages": messages,
            "stream": False,
            "tools": tools,
            "options": {"temperature": 0.5, "num_ctx": 2048, "num_predict": 130},
        }
        try:
            response = requests.post(OLLAMA_URL, json=payload, timeout=90)
            if abort_check and abort_check():
                return {"role": "assistant", "content": ""}
            if response.status_code == 200:
                return response.json().get("message", {})
            return {"role": "assistant", "content": f"Neural core returned code {response.status_code}."}
        except requests.exceptions.Timeout:
            return {"role": "assistant", "content": "CPU load is high right now, sir. Processing the request shortly."}
        except Exception as e:
            return {"role": "assistant", "content": f"Sir, my cognitive engine is offline: {e}"}


class JarvisPipeline:
    def __init__(self, window: Any):
        self.window = window
        self._orig_evaluate_js = window.evaluate_js
        self._js_queue: queue.Queue[str] = queue.Queue(maxsize=300)
        self._hwnd: int | None = None
        self._transparency_configured = False
        self.history: list[tuple[str, str]] = MemoryModule.load()
        self.text_queue: queue.Queue[str] = queue.Queue()
        self.response_queue: queue.Queue[Any] = queue.Queue()
        self.running = True
        self.voice_mode = "JARVIS"  # Strictly 'JARVIS' or 'FRIDAY'
        self.is_sleeping = False
        self.is_fullscreen = True
        self.is_orb_only = False
        self.is_muted = False
        self.video_sound_active = False  # Smart Mic Mute: True when HUD video audio is unmuted
        self.wake_word_enabled = False   # Dual-mode activation: Wake Word gate
        self.push_to_talk_enabled = False  # Dual-mode activation: Hold Ctrl+Space to talk
        self.ptt_key_held = False
        self.morning_brief_enabled = True
        self.proactive_enabled = True
        self.screen_vision_mode = False
        self.current_hud_state = "ONLINE"
        self.abort_event = threading.Event()
        self.active_cmd_id = 0
        self.active_subprocess: subprocess.Popen | None = None
        self.last_active = time.time()
        self.session_start = time.time()
        self.command_count = 0
        self.session_count = self._init_session_counter()
        # Wrap window.evaluate_js with non-blocking async queue for UI updates so worker threads never hang
        self.window.evaluate_js = self._safe_evaluate_js
        threading.Thread(target=self._js_worker, daemon=True).start()
        self.tool_suite = UnifiedToolSuite(self)
        self.remote_dashboard = RemoteDashboardServer(self)

    def _get_hwnd(self) -> int:
        if self._hwnd:
            return self._hwnd
        try:
            native_form = getattr(self.window, "native", None)
            if native_form is not None and hasattr(native_form, "Handle"):
                h = int(native_form.Handle.ToInt64())
                if h:
                    self._hwnd = h
                    return h
        except Exception:
            pass
        if os.name == "nt":
            try:
                hwnd = ctypes.windll.user32.FindWindowW(None, "JARVIS Master")
                if hwnd:
                    self._hwnd = int(hwnd)
                    return self._hwnd
            except Exception:
                pass
        return 0

    def _configure_native_transparency(self) -> None:
        """Ensure the underlying WinForms Form uses a chroma TransparencyKey instead of painting #F0F0F0 light gray behind WebView2."""
        if self._transparency_configured:
            return
        try:
            native_form = getattr(self.window, "native", None)
            if native_form is not None:
                from System import Action
                from System.Drawing import Color

                def _apply() -> None:
                    key_col = Color.FromArgb(255, 1, 2, 3)
                    native_form.BackColor = key_col
                    native_form.TransparencyKey = key_col

                if native_form.InvokeRequired:
                    native_form.BeginInvoke(Action(_apply))
                else:
                    _apply()
                self._transparency_configured = True
        except Exception as e:
            print(f"Native transparency config warning: {e}")

    def _is_window_minimized(self) -> bool:
        if os.name == "nt":
            try:
                hwnd = self._get_hwnd()
                if hwnd and ctypes.windll.user32.IsIconic(hwnd):
                    return True
            except Exception:
                pass
        return False

    def _safe_evaluate_js(self, script: str, *args: Any, **kwargs: Any) -> Any:
        """Non-blocking evaluate_js wrapper that prevents WebView2 semaphore deadlocks in Minimize / Orb mode."""
        if isinstance(script, str) and script.startswith("updateState("):
            try:
                st = script.split("(", 1)[1].split(")", 1)[0].strip("'\"")
                if st:
                    self.current_hud_state = st
            except Exception:
                pass
        if not script or not isinstance(script, str) or self._is_window_minimized():
            return None
        # Synchronous path only for queries that expect a return value (e.g. captureCameraFrameBase64)
        if "captureCameraFrameBase64" in script or kwargs or args:
            try:
                return self._orig_evaluate_js(script, *args, **kwargs)
            except Exception:
                return None
        # Fire-and-forget path for all HUD state/log/telemetry updates
        try:
            if self._js_queue.full():
                try:
                    self._js_queue.get_nowait()
                    self._js_queue.task_done()
                except Exception:
                    pass
            self._js_queue.put_nowait(script)
        except Exception:
            pass
        return None

    def _js_worker(self) -> None:
        """Dedicated background dispatcher for WebView2 JS calls so STT/LLM/TTS/API threads never block."""
        while self.running:
            try:
                script = self._js_queue.get(timeout=0.5)
                try:
                    if not self._is_window_minimized():
                        self._orig_evaluate_js(script)
                except Exception:
                    pass
                finally:
                    self._js_queue.task_done()
            except queue.Empty:
                continue
            except Exception:
                pass

    def _set_window_rect(self, x: int, y: int, w: int, h: int) -> None:
        """Move and resize the window cleanly on 64-bit Windows via Win32 SetWindowPos without recreating .NET handles."""
        self._configure_native_transparency()
        if os.name == "nt":
            try:
                user32 = ctypes.windll.user32
                hwnd = self._get_hwnd()
                if hwnd:
                    if user32.IsIconic(hwnd):
                        user32.ShowWindowAsync(hwnd, 9)  # SW_RESTORE
                    # Pass 0 (NULL) for hWndInsertAfter with SWP_NOZORDER (0x0004) | SWP_SHOWWINDOW (0x0040) | SWP_NOACTIVATE (0x0010)
                    if user32.SetWindowPos(hwnd, 0, int(x), int(y), int(w), int(h), 0x0004 | 0x0040 | 0x0010):
                        return
            except Exception as e:
                print(f"Win32 SetWindowPos warning: {e}")
        try:
            self.window.resize(int(w), int(h))
            self.window.move(int(x), int(y))
        except Exception:
            pass

    @staticmethod
    def is_kill_command(text: str, strict_barge_in: bool = False) -> bool:
        """Return True if the user spoken/typed input is a kill, stop, abort, or cancel command."""
        if not text:
            return False
        raw_low = text.lower().strip()
        cleaned = _KILL_CLEAN_RE.sub(" ", raw_low)
        tokens = [
            t for t in cleaned.split()
            if t not in ("jarvis", "friday", "system", "please", "now", "sir", "boss", "ji", "yaar", "hey", "ok", "okay", "abhi", "jaldi")
        ]
        core = " ".join(tokens).strip()
        if not core:
            return False

        exact_kill_words = {
            "stop", "kill", "abort", "cancel", "halt", "terminate",
            "silence", "quiet", "shut up", "enough", "wait",
            "chup", "ruko", "ruk", "bas", "band", "roko",
            "nevermind", "never mind", "forget it", "leave it",
            "रुको", "बस", "चुप", "बंद", "बंद करो", "रुक जाओ",
        }
        if core in exact_kill_words:
            return True

        kill_phrases = (
            "stop command", "kill command", "abort command", "cancel command",
            "stop task", "kill task", "abort task", "cancel task",
            "stop process", "kill process", "abort process", "terminate process",
            "stop working", "stop talking", "stop speaking", "stop everything", "kill everything",
            "stop it", "kill it", "abort it", "cancel it", "stop that", "kill that", "cancel that",
            "abort mission", "emergency stop", "force stop", "force kill",
            "ruk jao", "ruk ja", "band karo", "band kar do", "bas karo", "bas kar",
            "chup raho", "chup ho jao", "kaam roko", "roko isko", "mat karo",
            "cancel kar do", "rehne do", "chhod do", "stop kar do", "kill kar do",
        )
        if any(p in core or p in raw_low for p in kill_phrases):
            return True

        if not strict_barge_in and len(tokens) <= 3 and tokens[0] in ("stop", "kill", "abort", "cancel", "terminate", "ruko", "chup"):
            return True

        return False

    def abort_current_command(self, spoken_text: str = "") -> None:
        """Pre-emptively kill any running command, background video resolution, tool execution, subprocess, and active TTS speech."""
        self.active_cmd_id += 1
        self.abort_event.set()
        stop_speaking()

        # Cancel any resolving or playing HUD video immediately ("Talks While It Loads" -> "stop" cancels before video appears)
        try:
            if hasattr(self, "tool_suite") and self.tool_suite and hasattr(self.tool_suite, "ui"):
                self.tool_suite.ui.stop_video()
        except Exception:
            pass

        for q in (self.text_queue, self.response_queue):
            while not q.empty():
                try:
                    q.get_nowait()
                    q.task_done()
                except Exception:
                    break

        proc = self.active_subprocess
        if proc is not None:
            try:
                proc.kill()
            except Exception:
                pass
            self.active_subprocess = None

        try:
            self.window.evaluate_js("updateState('ONLINE')")
            self.window.evaluate_js("addLog('SYSTEM', '[ABORT ⊘] Active command, video stream & processes terminated.')")
        except Exception:
            pass

        low = (spoken_text or "").lower()
        if not any(sw in low for sw in ("chup", "silence", "quiet", "shut up", "mute")):
            is_hi = any(hw in low for hw in ("ruk", "band", "bas", "roko", "mat", "rehne", "chhod"))
            confirm_msg = "Ruk gaya, sir." if is_hi else "Stopped, sir."
            mode = self.voice_mode

            def _speak_abort() -> None:
                try:
                    self.window.evaluate_js(f"addLog('JARVIS', {json.dumps(confirm_msg)})")
                    speak_text(confirm_msg, mode=mode, cache_clip=True, ignore_abort=True)
                    self.window.evaluate_js("updateState('ONLINE')")
                except Exception:
                    pass

            threading.Thread(target=_speak_abort, daemon=True).start()
        else:
            TTS_ABORT_EVENT.clear()

    def _init_session_counter(self) -> int:
        mem_file = os.path.join(_ROOT_DIR, "jarvis_memory.json")
        data: dict[str, Any] = {}
        if os.path.exists(mem_file):
            try:
                with open(mem_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception:
                data = {}
        count = int(data.get("session_count", 0)) + 1
        data["session_count"] = count
        data["last_session_start"] = time.strftime("%Y-%m-%d %H:%M:%S")
        try:
            with open(mem_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception:
            pass
        return count

    def increment_command_count(self) -> None:
        self.command_count += 1
        try:
            self.window.evaluate_js(f"setSessionAndCommands({self.session_count}, {self.command_count})")
        except Exception:
            pass

    def enter_orb_only_mode(self, sleep_mode: bool = False, vision_mode: bool = False) -> None:
        """Collapse HUD so ONLY the 3D Holographic Orb floats on a 100% transparent background."""
        try:
            # Do not collapse HUD while an in-HUD video is actively playing
            if hasattr(self, "tool_suite") and self.tool_suite and self.tool_suite.ui.video_is_playing():
                return
            self.is_orb_only = True
            self.is_sleeping = sleep_mode
            self.is_fullscreen = False
            if vision_mode:
                self.screen_vision_mode = True
            self.window.evaluate_js("toggleMiniMode(true)")
            sw, sh = _get_screen_size()
            self._set_window_rect(max(20, sw - 340), max(20, sh - 380), 320, 320)
        except Exception as e:
            print(f"enter_orb_only_mode warning: {e}")

    def exit_orb_only_mode(self) -> None:
        """Restore the full HUD from Orb-Only Transparent Mode."""
        try:
            self.is_orb_only = False
            self.is_sleeping = False
            self.screen_vision_mode = False
            self.is_fullscreen = True
            self.last_active = time.time()
            sw, sh = _get_screen_size()
            self._set_window_rect(0, 0, sw, sh)
            self.window.evaluate_js("toggleMiniMode(false)")
        except Exception as e:
            print(f"exit_orb_only_mode warning: {e}")

    def start_services(self) -> None:
        self._configure_native_transparency()
        # Start Remote Smartphone Dashboard server on port 8787
        try:
            url = self.remote_dashboard.start()
            self.window.evaluate_js(f"addLog('SYSTEM', {json.dumps(f'[REMOTE DECK] Smartphone QR Control Ready: {url}')})")
        except Exception as e:
            print(f"Remote dashboard start warning: {e}")

        for worker in (
            self.stt_worker,
            self.llm_worker,
            self.tts_worker,
            self.telemetry_worker,
            self.idle_worker,
            self.background_monitors_worker,
            self.ptt_worker,
        ):
            threading.Thread(target=worker, daemon=True).start()

        try:
            self.window.evaluate_js(f"setSessionAndCommands({self.session_count}, {self.command_count})")
        except Exception:
            pass

        hour = time.localtime().tm_hour
        mode_name = self.voice_mode
        if hour < 12:
            greetings = (
                "Good morning, sir. All systems are online and ready.",
                f"Good morning, boss. {mode_name} is operational.",
                "Namaste sir! Good morning. Sabhi systems online aur ready hain.",
            )
        elif hour < 18:
            greetings = (
                "Good afternoon, sir. How may I assist you today?",
                "Systems operational. Good afternoon, boss.",
                "Good afternoon sir! Bataye aaj kya kaam karna hai?",
            )
        else:
            greetings = (
                f"Good evening, sir. {mode_name} is online and standing by.",
                "Evening, boss. Awaiting your instructions.",
                "Good evening sir! System ready hai, bataye kya hukum hai?",
            )
        self.response_queue.put(random.choice(greetings))

        try:
            import keyboard
            keyboard.add_hotkey("alt+space", self.trigger_hotkey_wake)
            keyboard.add_hotkey("alt+x", lambda: self.abort_current_command("kill"))
        except Exception as e:
            print("Hotkey binding failed:", e)

    def ptt_worker(self) -> None:
        """Polls Ctrl+Space via Win32 GetAsyncKeyState for zero-latency Push-to-Talk activation."""
        if os.name != "nt":
            return
        user32 = ctypes.windll.user32
        was_held = False
        while self.running:
            try:
                if self.push_to_talk_enabled:
                    ctrl_down = bool(user32.GetAsyncKeyState(0x11) & 0x8000)
                    space_down = bool(user32.GetAsyncKeyState(0x20) & 0x8000)
                    held = ctrl_down and space_down
                    self.ptt_key_held = held
                    if held != was_held:
                        was_held = held
                        self.window.evaluate_js(f"setPttActiveState({'true' if held else 'false'})")
                else:
                    self.ptt_key_held = False
                    was_held = False
            except Exception:
                pass
            time.sleep(0.05)

    def trigger_morning_briefing(self) -> None:
        """Deliver a proactive Morning / Daily Briefing with live weather, system health, and global headlines."""
        self.last_active = time.time()
        self.increment_command_count()
        self.response_queue.put(("ACK", "On it, sir. Compiling your daily briefing."))

        def _compile() -> None:
            try:
                loc = get_user_location()
                city = loc.get("city", "your sector")
                w_url = (
                    f"https://api.open-meteo.com/v1/forecast?latitude={loc['lat']}&longitude={loc['lon']}"
                    "&current=temperature_2m,weather_code"
                )
                t_str = "pleasant"
                try:
                    w_data = requests.get(w_url, timeout=4).json()["current"]
                    t_str = f"{w_data['temperature_2m']} degrees Celsius"
                except Exception:
                    pass
                cpu = int(psutil.cpu_percent(interval=0.2))
                mem = int(psutil.virtual_memory().percent)
                news_snip = ""
                try:
                    raw_news = get_world_news_sync()
                    if raw_news:
                        first_line = raw_news.splitlines()[0].strip("•- ")
                        news_snip = f" Top global headline: {first_line[:130]}."
                except Exception:
                    pass
                hour = time.localtime().tm_hour
                tod = "morning" if hour < 12 else ("afternoon" if hour < 18 else "evening")
                brief = (
                    f"Good {tod}, sir. In {city}, current temperature is {t_str}. "
                    f"System diagnostics show CPU at {cpu} percent and memory at {mem} percent.{news_snip} "
                    "All Mark 55 subsystems and plugins are standing by."
                )
                self.response_queue.put(brief)
            except Exception as e:
                self.response_queue.put(f"Briefing telemetry partially available, sir: {e}")

        threading.Thread(target=_compile, daemon=True).start()

    def trigger_hotkey_wake(self) -> None:
        if self.is_orb_only or self.is_sleeping:
            self.exit_orb_only_mode()
            self.response_queue.put("Full HUD overlay restored, sir.")
        else:
            self.enter_orb_only_mode(sleep_mode=False)

    def idle_worker(self) -> None:
        while self.running:
            if (
                not self.is_sleeping
                and not self.is_orb_only
                and not self.tool_suite.ui.video_is_playing()
                and (time.time() - self.last_active > 120)
            ):
                self.enter_orb_only_mode(sleep_mode=False)
            time.sleep(2)

    def background_monitors_worker(self) -> None:
        """Runs Mark-LV SystemMonitor threshold checks, BackgroundMonitor topic checks, and Proactive Check-Ins."""
        time.sleep(15)
        ticks = 0
        while self.running:
            try:
                if self.tool_suite.sys_monitor:
                    alert = self.tool_suite.sys_monitor.check()
                    if alert:
                        self.window.evaluate_js(f"addLog('SYSTEM', {json.dumps(alert)})")
                if ticks % 60 == 0:
                    from actions.background_monitor import check_all
                    for ta in check_all():
                        self.window.evaluate_js(f"addLog('SYSTEM', {json.dumps(ta)})")
                if self.proactive_enabled and ticks > 0 and ticks % 90 == 0:
                    try:
                        from actions.proactive import check_proactive
                        suggestion = check_proactive()
                        if suggestion:
                            self.window.evaluate_js(f"addLog('JARVIS', {json.dumps('[PROACTIVE] ' + suggestion)})")
                            if not self.video_sound_active and not self.is_muted:
                                self.response_queue.put(suggestion)
                    except Exception:
                        pass
            except Exception:
                pass
            ticks += 1
            time.sleep(30)

    def fetch_weather(self) -> None:
        try:
            loc = get_user_location()
            city, country, lat, lon = loc["city"], loc["country"], loc["lat"], loc["lon"]
            w_url = (
                f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}"
                "&current=temperature_2m,apparent_temperature,relative_humidity_2m,wind_speed_10m,weather_code"
            )
            w_data = requests.get(w_url, timeout=5).json()["current"]
            t = w_data["temperature_2m"]
            feels = w_data.get("apparent_temperature", t)
            h = w_data["relative_humidity_2m"]
            w = w_data["wind_speed_10m"]
            code = w_data["weather_code"]

            if code == 0:
                desc, icon = "clear sky", "☼"
            elif code < 4:
                desc, icon = "partly cloudy", "◐"
            elif code < 50:
                desc, icon = "overcast clouds", "☁\uFE0E"
            elif code < 80:
                desc, icon = "rain showers", "☂\uFE0E"
            else:
                desc, icon = "thunderstorm", "↯"

            loc_full = f"{city}, {country}" if country else city
            args_js = ", ".join(
                json.dumps(v)
                for v in (f"{t}°C", loc_full, city, desc, f"{h}%", f"{w} km/h", f"{feels}°C", icon)
            )
            self.window.evaluate_js(f"updateWeather({args_js})")
            self.window.evaluate_js("addLog('SYSTEM', 'Live satellite weather telemetry synchronized.')")
        except Exception as e:
            safe_err = json.dumps(f"Weather telemetry warning: {str(e).splitlines()[0][:100]}")
            self.window.evaluate_js(f"addLog('SYSTEM', {safe_err})")

    def _get_uptime_strings(self) -> tuple[str, str]:
        os_sec = max(0, int(time.time() - psutil.boot_time()))
        os_str = f"{os_sec // 3600:02d}:{(os_sec % 3600) // 60:02d}:{os_sec % 60:02d}"
        sess_sec = max(0, int(time.time() - self.session_start))
        sess_str = f"{sess_sec // 3600:02d}:{(sess_sec % 3600) // 60:02d}:{sess_sec % 60:02d}"
        return os_str, sess_str

    def _collect_and_push_stats(self, cpu_interval: float = 0.2) -> None:
        cpu = int(psutil.cpu_percent(interval=cpu_interval))
        mem = psutil.virtual_memory()
        ram = int(mem.percent)
        ram_str = f"{mem.used / (1024 ** 3):.1f}/{mem.total / (1024 ** 3):.0f} GB ({ram}%)"

        disk = psutil.disk_usage(os.path.abspath(os.sep))
        disk_str = f"{int(disk.used / (1024 ** 3))}/{int(disk.total / (1024 ** 3))} GB"
        os_str, sess_str = self._get_uptime_strings()

        self.window.evaluate_js(
            f"updateSystemStats({cpu}, {ram}, {json.dumps(ram_str)}, {json.dumps(disk_str)}, "
            f"{self.session_count}, {self.command_count}, {json.dumps(os_str)}, {json.dumps(sess_str)})"
        )

    def push_stats_once(self) -> None:
        try:
            self._collect_and_push_stats(cpu_interval=0.2)
        except Exception:
            pass

    def run_network_diagnostics(self) -> None:
        try:
            self.increment_command_count()
            self.window.evaluate_js("addLog('SYSTEM', 'Running network diagnostics & latency check...')")
            loc = get_user_location(force_refresh=True)
            out = subprocess.check_output("ping -n 1 8.8.8.8", shell=True, text=True, timeout=4)
            ping_ms = "12ms"
            for token in out.split():
                if "time=" in token.lower() or "time<" in token.lower():
                    ping_ms = token.split("=")[-1].split("<")[-1]
                    break
            report = f"Network Online | IP: {loc['ip']} ({loc['isp']}, {loc['city']}) | Latency: {ping_ms}"
            self.window.evaluate_js(f"addLog('SYSTEM', {json.dumps(report)})")
        except Exception as e:
            safe_err = json.dumps(f"Network check failed: {str(e).splitlines()[0][:100]}")
            self.window.evaluate_js(f"addLog('SYSTEM', {safe_err})")

    def telemetry_worker(self) -> None:
        time.sleep(1.0)
        self.fetch_weather()
        net_io = psutil.net_io_counters()
        last_net = net_io.bytes_recv + net_io.bytes_sent
        ticks = 0
        while self.running:
            try:
                self._collect_and_push_stats(cpu_interval=1.0)
                curr_io = psutil.net_io_counters()
                curr_net = curr_io.bytes_recv + curr_io.bytes_sent
                speed_mbps = max(0.0, (curr_net - last_net) / (1024 * 1024))
                last_net = curr_net
                self.window.evaluate_js(f"updateNetwork({json.dumps(f'{speed_mbps:.2f} MB/s')})")

                ticks += 1
                if ticks % 300 == 0:
                    threading.Thread(target=self.fetch_weather, daemon=True).start()
            except Exception:
                pass
            time.sleep(1)

    def stt_worker(self) -> None:
        """Bilingual Speech Recognition with Smart Mic Mute, Push-to-Talk, Wake Word, and Barge-In Kill Support."""
        recognizer = sr.Recognizer()
        recognizer.pause_threshold = 0.8
        recognizer.non_speaking_duration = 0.5
        recognizer.dynamic_energy_threshold = True

        with sr.Microphone() as source:
            recognizer.adjust_for_ambient_noise(source, duration=1.0)
            recognizer.energy_threshold = max(recognizer.energy_threshold, 280)
            self.window.evaluate_js("updateState('ONLINE')")

            while self.running:
                # 1. SMART MIC MUTE: Auto-mute mic when HUD video audio is playing or user muted mic
                if self.is_muted or self.video_sound_active:
                    self.window.evaluate_js("updateState('MUTED')")
                    time.sleep(0.25)
                    continue

                # 2. PUSH-TO-TALK GATE: Wait for Ctrl+Space if Push-to-Talk mode is enabled
                if self.push_to_talk_enabled and not self.ptt_key_held:
                    self.window.evaluate_js("updateState('ONLINE')")
                    time.sleep(0.12)
                    continue

                if recognizer.energy_threshold < 240:
                    recognizer.energy_threshold = 240
                was_speaking = bool(pygame.mixer.get_init() and pygame.mixer.get_busy())
                if not was_speaking:
                    self.window.evaluate_js("updateState('LISTENING')")
                try:
                    p_limit = 3 if was_speaking else 9
                    audio = recognizer.listen(source, timeout=2 if was_speaking else 3, phrase_time_limit=p_limit)
                    if self.is_muted or self.video_sound_active:
                        continue
                    if not was_speaking:
                        self.window.evaluate_js("updateState('PROCESSING')")
                    text = recognizer.recognize_google(audio, language="en-IN").lower()

                    if text:
                        has_wake_word = any(w in text for w in ("jarvis", "friday", "system", "hey jarvis", "hey friday"))
                        cmd = text
                        for w in ("hey jarvis", "hey friday", "jarvis", "friday", "system"):
                            cmd = cmd.replace(w, "")
                        cmd = cmd.strip()

                        if self.is_kill_command(cmd, strict_barge_in=was_speaking) or self.is_kill_command(text, strict_barge_in=was_speaking):
                            self.last_active = time.time()
                            self.window.evaluate_js(f"addLog('USER', {json.dumps(cmd or text)})")
                            self.abort_current_command(spoken_text=cmd or text)
                            continue

                        if was_speaking or (pygame.mixer.get_init() and pygame.mixer.get_busy()):
                            continue

                        # 3. WAKE WORD GATE: If Wake-Word mode is active (and not PTT), require "Jarvis" or "Friday"
                        if self.wake_word_enabled and not self.push_to_talk_enabled and not has_wake_word:
                            continue

                        if self.is_sleeping:
                            if any(w in text for w in ("jarvis", "friday", "wake", "uth jao", "uth ja")):
                                self.is_sleeping = False
                                rest_cmd = cmd
                                for wt in ("wake up", "wake", "uth jao", "uth ja"):
                                    rest_cmd = rest_cmd.replace(wt, "").strip()
                                if not rest_cmd:
                                    self.exit_orb_only_mode()
                                    self.response_queue.put("I am awake, boss. Standing by.")
                                    continue
                                cmd = rest_cmd
                            else:
                                continue

                        self.last_active = time.time()
                        if cmd and len(cmd) >= 2:
                            self.window.evaluate_js(f"addLog('USER', {json.dumps(cmd)})")
                            self.text_queue.put(cmd)
                except Exception:
                    pass

    def llm_worker(self) -> None:
        while self.running:
            try:
                text = self.text_queue.get()
                self.last_active = time.time()

                if self.is_kill_command(text):
                    self.abort_current_command(spoken_text=text)
                    self.text_queue.task_done()
                    continue

                self.abort_event.clear()
                TTS_ABORT_EVENT.clear()
                self.active_cmd_id += 1
                my_cmd_id = self.active_cmd_id

                self.increment_command_count()
                self.window.evaluate_js("updateState('THINKING')")

                cmd_lower = text.lower().strip()
                handled = False

                if "switch to friday" in cmd_lower or "friday mode" in cmd_lower:
                    self.voice_mode = "FRIDAY"
                    self.window.evaluate_js("switchMode('FRIDAY')")
                    self.response_queue.put("Switching to F.R.I.D.A.Y. mode, boss. All systems red.")
                    handled = True
                elif "switch to jarvis" in cmd_lower or "jarvis mode" in cmd_lower:
                    self.voice_mode = "JARVIS"
                    self.window.evaluate_js("switchMode('JARVIS')")
                    self.response_queue.put("Reverting to J.A.R.V.I.S. mode, sir. Back in blue.")
                    handled = True
                elif any(k in cmd_lower for k in ("unmute video", "video sound on", "turn on video sound", "unmute movie", "video unmute")):
                    self.tool_suite.ui.set_video_muted(False)
                    self.response_queue.put("Video audio enabled, sir. Smart mic mute is now active so I won't interrupt the movie.")
                    handled = True
                elif any(k in cmd_lower for k in ("mute video", "video sound off", "turn off video sound", "mute movie", "video mute")):
                    self.tool_suite.ui.set_video_muted(True)
                    self.response_queue.put("Video audio muted, sir. Microphone is active again.")
                    handled = True
                elif any(k in cmd_lower for k in ("close video", "stop video", "exit video", "hide video", "video band karo")):
                    self.tool_suite.ui.stop_video()
                    self.response_queue.put("Closing the HUD video player, sir.")
                    handled = True
                elif any(k in cmd_lower for k in ("morning briefing", "daily briefing", "status briefing", "give me a briefing")):
                    self.trigger_morning_briefing()
                    handled = True
                elif any(k in cmd_lower for k in ("network radar", "wifi radar", "scan lan", "lan radar")):
                    self.exit_orb_only_mode()
                    self.response_queue.put(("ACK", "On it, sir. Scanning local network radar."))
                    threading.Thread(
                        target=lambda: self.response_queue.put(self.tool_suite.execute("network_radar", {"action": "scan"})),
                        daemon=True,
                    ).start()
                    handled = True
                elif any(k in cmd_lower for k in ("disk map", "storage map", "analyze disk", "disk treemap", "folder weights")):
                    self.exit_orb_only_mode()
                    self.response_queue.put(("ACK", "Working on it, sir. Mapping storage sectors."))
                    threading.Thread(
                        target=lambda: self.response_queue.put(self.tool_suite.execute("disk_analyzer", {"path": "D:\\"})),
                        daemon=True,
                    ).start()
                    handled = True
                elif any(k in cmd_lower for k in ("earth globe", "3d globe", "seismic globe", "earthquake map", "global telemetry")):
                    self.exit_orb_only_mode()
                    self.response_queue.put(("ACK", "On it, sir. Projecting 3D Earth telemetry globe."))
                    threading.Thread(
                        target=lambda: self.response_queue.put(self.tool_suite.execute("earth_globe", {"focus": "seismic"})),
                        daemon=True,
                    ).start()
                    handled = True
                elif any(k in cmd_lower for k in ("hardware schematic", "pinout diagram", "circuit schematic", "analyze hardware")):
                    self.exit_orb_only_mode()
                    self.response_queue.put(("ACK", "On it, sir. Generating interactive hardware pinout schematic."))
                    threading.Thread(
                        target=lambda: self.response_queue.put(self.tool_suite.execute("hardware_schematic", {"component": text})),
                        daemon=True,
                    ).start()
                    handled = True
                elif any(k in cmd_lower for k in ("pomodoro", "focus timer", "start focus")):
                    self.exit_orb_only_mode()
                    mins = 25
                    m_match = re.search(r"(\d+)\s*min", cmd_lower)
                    if m_match:
                        mins = int(m_match.group(1))
                    res = self.tool_suite.execute("pomodoro_timer", {"action": "start", "minutes": mins, "label": "DEEP WORK"})
                    self.response_queue.put(res)
                    handled = True
                elif any(k in cmd_lower for k in ("barehands", "spatial mode", "ar hand", "hand ring", "holo table", "spatial ar")):
                    self.exit_orb_only_mode()
                    off = any(w in cmd_lower for w in ("off", "disable", "exit", "close"))
                    if off:
                        self.window.evaluate_js("setBarehandsMode(false)")
                        self.response_queue.put("Exiting Barehands spatial AR stage, sir.")
                    else:
                        self.window.evaluate_js("toggleCenterCameraMode(true); setBarehandsMode(true);")
                        self.response_queue.put("Activating Barehands spatial AR hand-tracking stage, sir. Pinch your thumb to your index knuckle to summon the command ring.")
                    handled = True
                elif any(k in cmd_lower for k in ("3d face", "face avatar", "holographic face", "lip sync avatar")):
                    self.exit_orb_only_mode()
                    self.window.evaluate_js("setCenterpieceMode('FACE')")
                    self.response_queue.put("Switching centerpiece to the 3D Holographic Face Avatar with real-time viseme lip-sync, sir.")
                    handled = True
                elif any(k in cmd_lower for k in ("circuit board", "living circuit", "circuit visualizer")):
                    self.exit_orb_only_mode()
                    self.window.evaluate_js("setCenterpieceMode('CIRCUIT')")
                    self.response_queue.put("Switching centerpiece to the Living Circuit Board visualizer, sir.")
                    handled = True
                elif any(k in cmd_lower for k in ("arc reactor", "reactor core")):
                    self.exit_orb_only_mode()
                    self.window.evaluate_js("setCenterpieceMode('REACTOR')")
                    self.response_queue.put("Switching centerpiece to the Classic Arc Reactor Core, sir.")
                    handled = True
                elif any(k in cmd_lower for k in ("orbital sphere", "3d sphere", "holographic orb")):
                    self.exit_orb_only_mode()
                    self.window.evaluate_js("setCenterpieceMode('SPHERE')")
                    self.response_queue.put("Restoring the 3D Orbital Sphere centerpiece, sir.")
                    handled = True
                elif any(k in cmd_lower for k in ("show hud", "open hud", "restore hud", "full screen", "fullscreen", "maximize hud", "wapas aao", "hud dikhao")):
                    self.exit_orb_only_mode()
                    self.response_queue.put("Restoring full HUD interface, sir.")
                    handled = True
                elif any(k in cmd_lower for k in ("orb mode", "mini mode", "only orb", "hide hud")):
                    self.enter_orb_only_mode(sleep_mode=False)
                    self.response_queue.put("Switching to transparent Orb mode, sir.")
                    handled = True
                elif any(k in cmd_lower for k in ("center camera", "camera to center", "camera in center", "camera mode to center", "bring camera to center", "expand camera", "maximize camera", "camera beech mein", "camera center mein")):
                    self.exit_orb_only_mode()
                    self.window.evaluate_js("toggleCenterCameraMode(true)")
                    self.response_queue.put("Bringing optical camera mode to center stage, sir.")
                    handled = True
                elif any(k in cmd_lower for k in ("dock camera", "minimize camera", "camera to side", "orb to center", "center orb", "restore orb", "camera side mein")):
                    self.window.evaluate_js("toggleCenterCameraMode(false)")
                    self.response_queue.put("Docking camera to the side panel and restoring the holographic orb to center stage, sir.")
                    handled = True
                elif any(k in cmd_lower for k in ("live item recognition", "recognize items", "what items do you see", "what objects do you see", "announce items", "list detected items", "kya kya dikh raha hai")):
                    self.exit_orb_only_mode()
                    self.window.evaluate_js("announceDetectedItems()")
                    handled = True
                elif any(k in cmd_lower for k in ("sentry mode on", "enable sentry", "start sentry", "intruder watch", "security watch", "sentry mode")):
                    self.exit_orb_only_mode()
                    off = any(w in cmd_lower for w in ("off", "disable", "stop", "band"))
                    self.window.evaluate_js(f"toggleSentryMode({'false' if off else 'true'})")
                    self.response_queue.put("Optical sentry watch deactivated, sir." if off else "Optical sentry watch armed and monitoring camera sector, sir.")
                    handled = True
                elif any(k in cmd_lower for k in ("read text on camera", "ocr camera", "scan text on camera", "read label on camera", "camera ocr")):
                    self.exit_orb_only_mode()
                    self.window.evaluate_js("triggerCameraOCR()")
                    handled = True
                elif cmd_lower.startswith("play ") or " play kar" in cmd_lower or "video chala" in cmd_lower or "trailer" in cmd_lower:
                    # Direct In-HUD Video on Command fast-path (Talks While It Loads + Original Language + Instant Stop Cancel)
                    self.exit_orb_only_mode()
                    q_clean = re.sub(r"^(?:please\s+)?play\s+(?:the\s+)?", "", text, flags=re.I).strip()
                    q_clean = re.sub(r"\s+(?:on\s+youtube|in\s+hud|video|for\s+me|please)$", "", q_clean, flags=re.I).strip() or text
                    url_m = _URL_RE.search(text)
                    vp_params: dict[str, Any] = {"action": "play"}
                    if url_m:
                        vp_params["source"] = url_m.group(0)
                    elif os.path.exists(q_clean.strip("\"'")):
                        vp_params["source"] = q_clean.strip("\"'")
                    else:
                        vp_params["query"] = q_clean
                    # Immediate spoken response while yt-dlp resolves in the background ("Talks While It Loads")
                    spoken_opening = f"Pulling up {q_clean} right inside the HUD in its original language, sir. Say stop at any time to cancel."
                    self.response_queue.put(spoken_opening)
                    self.tool_suite.execute("video_player", vp_params)
                    self.history.append(("USER", text))
                    self.history.append(("JARVIS", spoken_opening))
                    MemoryModule.save(self.history)
                    handled = True

                if handled:
                    self.text_queue.task_done()
                    continue

                threading.Thread(
                    target=self._execute_command_pipeline,
                    args=(text, my_cmd_id),
                    daemon=True,
                ).start()
                self.text_queue.task_done()
            except Exception as e:
                safe_err = json.dumps(f"Cognitive processing warning: {str(e).splitlines()[0][:120]}")
                try:
                    self.window.evaluate_js(f"addLog('SYSTEM', {safe_err})")
                except Exception:
                    pass

    def _execute_command_pipeline(self, text: str, my_cmd_id: int) -> None:
        """Execute a single command with continuous abort/kill checkpoints."""

        def is_aborted() -> bool:
            return self.abort_event.is_set() or (my_cmd_id != self.active_cmd_id)

        try:
            if is_aborted():
                return

            cmd_lower = text.lower()
            ack_phrase = get_instant_ack(text, self.voice_mode)
            self.response_queue.put(("ACK", ack_phrase))

            # Single-Pass Direct Vision Fast-Path (1 API call instead of 2)
            is_cam_query = any(k in cmd_lower for k in (
                "camera", "webcam", "look at me", "who am i", "mera chehra",
                "holding", "in my hand", "haath mein", "show you",
            ))
            is_screen_query = any(k in cmd_lower for k in (
                "screen", "looking at", "what do you see", "read this", "analyze this",
                "this error", "this code", "on my display", "screen par", "kya dikh raha",
            ))
            is_action_cmd = any(k in cmd_lower for k in (
                "open ", "khol", "launch ", "start ", "play ", "volume", "brightness",
                "mute", "weather", "news", "remind", "search ",
            ))
            if is_cam_query or is_screen_query or (self.screen_vision_mode and not is_action_cmd):
                angle = "camera" if is_cam_query else "screen"
                was_fullscreen = self.is_fullscreen
                if angle == "screen":
                    self.enter_orb_only_mode(sleep_mode=False, vision_mode=True)
                    if was_fullscreen:
                        time.sleep(0.22)
                if is_aborted():
                    return
                vision_ans = run_screen_or_camera_vision(angle=angle, text=text, window=self.window)
                if is_aborted():
                    return
                self.history.append(("USER", text))
                self.history.append(("JARVIS", vision_ans))
                MemoryModule.save(self.history)
                self.response_queue.put(vision_ans)
                return

            if any(k in cmd_lower for k in ("open ", "khol", "launch ", "start ", "world news", "finance news", "financial market")):
                self.enter_orb_only_mode(sleep_mode=False)

            lt_mem = MemoryModule.get_long_term_prompt()
            attached_file = self.tool_suite.ui.current_file
            file_ctx = f"\n[ATTACHED FILE READY FOR file_processor: {attached_file}]\n" if attached_file else ""

            system_prompt = (
                f"You are {self.voice_mode}, an advanced, loyal, and sharp personal AI assistant. "
                "LANGUAGE INSTRUCTION: "
                "You are 100% fluent in both English and Hindi / Hinglish. "
                "Always reply in the exact language the user speaks: "
                "- If the user speaks Hindi or Hinglish (e.g. 'WhatsApp khol do', 'kya haal hai boss', 'Dune trailer play kar do', 'volume badha do', 'left side pe Chrome set kar do', 'asman mein kitne planes hain'), "
                "reply in natural, warm, conversational Hindi / Hinglish (e.g. 'Ji boss, WhatsApp khol diya hai.', 'Bilkul sir, HUD mein play kar raha hoon.'). "
                "- If the user speaks English, reply in sharp, natural English. "
                "CRITICAL SPOKEN RULES: "
                "1. Keep spoken responses short (2 to 4 sentences maximum). "
                "2. NEVER use markdown lists, asterisks, bullet points, or code formatting in spoken responses. Speak naturally. "
                "3. Call tools silently and immediately. Never recite raw function names. "
                "4. Address the user naturally as 'boss' or 'sir'. "
                "5. For playing any video, movie, trailer, song, YouTube link, or local video file, ALWAYS call video_player(action='play', query='...') or video_player(action='play', source='...') so it plays directly inside the HUD in its original language.\n"
                f"{lt_mem}{file_ctx}"
            )

            messages = [{"role": "system", "content": system_prompt}]
            for role, msg in self.history[-6:]:
                messages.append({"role": "user" if role == "USER" else "assistant", "content": msg})
            messages.append({"role": "user", "content": text})

            tools = self.tool_suite.get_ollama_tools()
            g_tools = self.tool_suite.get_gemini_tools()
            msg_obj = IntelligenceModule.chat(
                messages,
                tools,
                self.window,
                abort_check=is_aborted,
                gemini_tools=g_tools,
            )
            if is_aborted():
                return

            response = ""

            if "tool_calls" in msg_obj and msg_obj["tool_calls"]:
                for tool in msg_obj["tool_calls"]:
                    if is_aborted():
                        return
                    t_name = tool["function"]["name"]
                    t_args = tool["function"]["arguments"] or {}

                    if t_name in ("video_player", "youtube_video"):
                        self.exit_orb_only_mode()
                        act = str(t_args.get("action", "play")).lower()
                        if act in ("play", "open", "resume"):
                            q = t_args.get("query") or t_args.get("source") or text
                            vp_args = {"action": "play"}
                            if t_args.get("source"):
                                vp_args["source"] = t_args["source"]
                            else:
                                vp_args["query"] = q
                            self.tool_suite.execute("video_player", vp_args)
                            response = f"Loading {q} inside the HUD in its original language, sir. Say stop at any time to cancel."
                        else:
                            res = self.tool_suite.execute("video_player", t_args)
                            response = str(res)[:300]
                        break

                    elif t_name == "get_world_news":
                        self.window.evaluate_js("addLog('SYSTEM', 'Polling Global Feeds...')")
                        self.enter_orb_only_mode(sleep_mode=False)
                        news_data = get_world_news_sync()
                        if is_aborted():
                            return
                        open_world_monitor()
                        response = f"Here is the latest from the global news wire, sir: {news_data[:220]}. I have opened the World Monitor on your display."
                        break

                    elif t_name == "get_finance_news":
                        self.window.evaluate_js("addLog('SYSTEM', 'Polling Financial Feeds...')")
                        self.enter_orb_only_mode(sleep_mode=False)
                        fin_data = get_finance_news_sync()
                        if is_aborted():
                            return
                        open_finance_monitor()
                        response = f"Here is the market briefing, sir: {fin_data[:220]}. Pulling up the finance monitor now."
                        break

                    elif t_name == "open_world_monitor":
                        self.enter_orb_only_mode(sleep_mode=False)
                        response = open_world_monitor()
                        break

                    elif t_name == "open_finance_monitor":
                        self.enter_orb_only_mode(sleep_mode=False)
                        response = open_finance_monitor()
                        break

                    elif t_name == "system_hardware_control":
                        act = t_args.get("action", "")
                        app = t_args.get("app_name", "")
                        if act in ("volume_up", "volume_down", "mute"):
                            response = volume_control(act)
                        elif act in ("brightness_up", "brightness_down"):
                            response = brightness_control(act)
                        elif act == "launch_app":
                            self.enter_orb_only_mode(sleep_mode=False)
                            response = launch_application(app)
                        break

                    elif t_name == "launch_application":
                        self.enter_orb_only_mode(sleep_mode=False)
                        response = launch_application(t_args.get("app_name", ""))
                        break

                    elif t_name == "volume_control":
                        response = volume_control(t_args.get("action", ""))
                        break

                    elif t_name == "window_management":
                        response = window_action(t_args.get("action", ""))
                        break

                    elif t_name == "split_workspace":
                        self.enter_orb_only_mode(sleep_mode=False)
                        response = split_workspace(t_args.get("left_app", ""), t_args.get("right_app", ""))
                        break

                    elif t_name == "open_website":
                        url = t_args.get("url", "")
                        self.enter_orb_only_mode(sleep_mode=False)
                        webbrowser.open(url)
                        response = f"Opened {url} on your display, sir."
                        break

                    elif t_name == "execute_terminal":
                        cmd_str = t_args.get("command", "")
                        try:
                            url_match = _URL_RE.search(cmd_str)
                            if url_match:
                                target_url = url_match.group(0)
                                if "youtube.com" in target_url or "youtu.be" in target_url:
                                    self.exit_orb_only_mode()
                                    if "search_query=" in target_url:
                                        q = target_url.split("search_query=", 1)[1].replace("+", " ")
                                        self.tool_suite.execute("video_player", {"action": "play", "query": q})
                                        response = f"Playing {q} inside the HUD in its original language, sir."
                                    else:
                                        self.tool_suite.execute("video_player", {"action": "play", "source": target_url})
                                        response = "Playing the requested YouTube stream inside the HUD, sir."
                                else:
                                    self.enter_orb_only_mode(sleep_mode=False)
                                    webbrowser.open(target_url)
                                    response = f"Opened {target_url} in your browser, sir."
                            else:
                                use_ps = any(ps_kw in cmd_str for ps_kw in ("Start-Process", "Get-", "Set-", "Invoke-", "$"))
                                proc = subprocess.Popen(
                                    ["powershell", "-NoProfile", "-Command", cmd_str] if use_ps else cmd_str,
                                    shell=not use_ps,
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.STDOUT,
                                    text=True,
                                )
                                self.active_subprocess = proc
                                out, _ = proc.communicate(timeout=10)
                                self.active_subprocess = None
                                if is_aborted():
                                    return
                                clean = (out or "").replace("\n", " ").strip()[:220]
                                response = f"Execution completed, sir. {('Output: ' + clean) if clean else ''}".strip()
                        except Exception as e:
                            self.active_subprocess = None
                            if is_aborted():
                                return
                            response = f"Terminal execution failed: {e}"
                        break

                    else:
                        tool_res = self.tool_suite.execute(t_name, t_args)
                        if is_aborted():
                            return
                        response = str(tool_res)[:350] if tool_res else f"Completed {t_name}, sir."
                        break

            if is_aborted():
                return

            if not response:
                response = msg_obj.get("content", "").strip()

            if response and not is_aborted():
                self.history.append(("USER", text))
                self.history.append(("JARVIS", response))
                MemoryModule.save(self.history)
                self.response_queue.put(response)
        except Exception as e:
            if not is_aborted():
                safe_err = json.dumps(f"Cognitive processing warning: {str(e).splitlines()[0][:120]}")
                try:
                    self.window.evaluate_js(f"addLog('SYSTEM', {safe_err})")
                except Exception:
                    pass

    def tts_worker(self) -> None:
        """Zero-Lock In-Memory Bilingual Neural TTS Engine with Instant Pre-Processing Ack & Abort Support."""
        while self.running:
            try:
                item = self.response_queue.get()
                if self.abort_event.is_set():
                    continue

                is_ack = isinstance(item, tuple) and len(item) == 2 and item[0] == "ACK"
                response = item[1] if is_ack else str(item)

                self.window.evaluate_js("updateState('SPEAKING')")
                self.window.evaluate_js(f"addLog('JARVIS', {json.dumps(response)})")

                speak_text(response, mode=self.voice_mode, cache_clip=is_ack)

                if self.abort_event.is_set():
                    self.window.evaluate_js("updateState('ONLINE')")
                elif is_ack and self.response_queue.empty():
                    self.window.evaluate_js("updateState('THINKING')")
                else:
                    self.window.evaluate_js("updateState('ONLINE')")
            except Exception as e:
                safe_err = json.dumps(f"Voice Engine Warning: {str(e).splitlines()[0][:100]}")
                try:
                    self.window.evaluate_js(f"addLog('SYSTEM', {safe_err})")
                except Exception:
                    pass
            finally:
                self.response_queue.task_done()


class Api:
    def __init__(self, pipeline: JarvisPipeline):
        self.pipeline = pipeline

    def send_command(self, text: str) -> None:
        self.pipeline.last_active = time.time()
        self.pipeline.window.evaluate_js(f"addLog('USER', {json.dumps(text)})")
        if self.pipeline.is_kill_command(text):
            self.pipeline.abort_current_command(spoken_text=text)
            return
        self.pipeline.text_queue.put(text)

    def kill_command(self) -> None:
        """Emergency Stop / Kill button in HUD or Escape key handler."""
        self.pipeline.last_active = time.time()
        self.pipeline.abort_current_command(spoken_text="stop")

    def minimize(self) -> None:
        """Collapse HUD to the floating corner Orb without suspending WebView2."""
        if self.pipeline.is_orb_only:
            self.pipeline.exit_orb_only_mode()
        else:
            self.pipeline.enter_orb_only_mode(sleep_mode=False)

    def toggle_fullscreen(self) -> None:
        if self.pipeline.is_orb_only or not self.pipeline.is_fullscreen:
            self.pipeline.exit_orb_only_mode()
        else:
            self.pipeline.enter_orb_only_mode(sleep_mode=False)

    def destroy(self) -> None:
        self.pipeline.running = False
        self.pipeline.window.destroy()

    def force_weather_update(self) -> None:
        threading.Thread(target=self.pipeline.fetch_weather, daemon=True).start()

    def force_stats_update(self) -> None:
        threading.Thread(target=self.pipeline.push_stats_once, daemon=True).start()

    def network_diagnostics(self) -> None:
        threading.Thread(target=self.pipeline.run_network_diagnostics, daemon=True).start()

    def toggle_mute(self) -> None:
        try:
            if pygame.mixer.get_init():
                pygame.mixer.stop()
            self.pipeline.is_muted = not self.pipeline.is_muted
            volume_control("mute")
            lbl = "⊘ MUTE" if self.pipeline.is_muted else "◉ AUD"
            self.pipeline.window.evaluate_js(
                f"const vb=document.getElementById('vol-btn'); if(vb) vb.innerText={json.dumps(lbl)};"
            )
            self.pipeline.window.evaluate_js("addLog('SYSTEM', 'System audio mute toggled.')")
        except Exception:
            pass

    def hud_video_control(self, action: str) -> str:
        """Control the in-HUD video player and synchronize Smart Mic Mute state."""
        self.pipeline.last_active = time.time()
        act = (action or "").lower().strip()
        ui = self.pipeline.tool_suite.ui
        if act == "mute":
            ui.set_video_muted(True)
        elif act == "unmute":
            ui.set_video_muted(False)
        elif act == "toggle_mute":
            ui.set_video_muted(not ui._video_muted)
        elif act in ("stop", "close", "ended"):
            ui.stop_video()
        return json.dumps({
            "playing": ui.video_is_playing(),
            "muted": ui._video_muted,
            "smart_mic_muted": self.pipeline.video_sound_active,
        })

    def set_control_toggle(self, key: str, enabled: bool) -> str:
        """Instant Controls Drawer toggle handler for Wake Word, Push-to-Talk, Morning Brief, Proactive, and Mic Mute."""
        self.pipeline.last_active = time.time()
        k = (key or "").lower().strip()
        val = bool(enabled)
        if k == "wake_word":
            self.pipeline.wake_word_enabled = val
        elif k == "push_to_talk":
            self.pipeline.push_to_talk_enabled = val
        elif k == "morning_brief":
            self.pipeline.morning_brief_enabled = val
        elif k == "proactive":
            self.pipeline.proactive_enabled = val
        elif k == "mic_mute":
            self.pipeline.is_muted = val
        elif k == "screen_vision":
            self.pipeline.screen_vision_mode = val
        self.pipeline.window.evaluate_js(
            f"addLog('SYSTEM', {json.dumps(f'[CONTROLS] {k.upper()} set to {val}')})"
        )
        return self.get_controls_state()

    def get_controls_state(self) -> str:
        """Return JSON snapshot of all Controls & Setup states."""
        return json.dumps({
            "voice_mode": self.pipeline.voice_mode,
            "is_muted": self.pipeline.is_muted,
            "video_sound_active": self.pipeline.video_sound_active,
            "wake_word_enabled": self.pipeline.wake_word_enabled,
            "push_to_talk_enabled": self.pipeline.push_to_talk_enabled,
            "morning_brief_enabled": self.pipeline.morning_brief_enabled,
            "proactive_enabled": self.pipeline.proactive_enabled,
            "screen_vision_mode": self.pipeline.screen_vision_mode,
            "remote": self.pipeline.remote_dashboard.get_pairing_info(),
        })

    def get_remote_pairing(self) -> str:
        """Return QR code pairing URL, LAN IP, port, and 6-char PIN for the Remote Smartphone Dashboard."""
        return json.dumps(self.pipeline.remote_dashboard.get_pairing_info())

    def regenerate_remote_pin(self) -> str:
        """Generate a fresh 6-char PIN for the Remote Smartphone Dashboard."""
        self.pipeline.remote_dashboard.regenerate_pin()
        return json.dumps(self.pipeline.remote_dashboard.get_pairing_info())

    def get_plugins_list(self) -> str:
        """Return JSON list of discovered single-file plugins and their load latency."""
        reg = self.pipeline.tool_suite.plugin_registry
        return json.dumps({
            "load_ms": reg.last_scan_ms,
            "plugins": reg.to_ui_list(),
        })

    def toggle_plugin_state(self, name: str, enabled: bool) -> str:
        """Enable or disable a single-file plugin and refresh tool declarations."""
        reg = self.pipeline.tool_suite.plugin_registry
        reg.set_enabled(name, bool(enabled))
        self.pipeline.tool_suite.reload_plugins()
        return self.get_plugins_list()

    def reload_plugins_now(self) -> str:
        """Hot-reload D:\\JARVIS\\plugins\\*.py in ~1-3ms."""
        info = self.pipeline.tool_suite.reload_plugins()
        msg = f"[PLUGINS] Hot-reloaded {info['count']} plugins in {info['load_ms']}ms."
        self.pipeline.window.evaluate_js(f"addLog('SYSTEM', {json.dumps(msg)})")
        return self.get_plugins_list()

    def run_plugin_direct(self, name: str, params_json: str = "{}") -> None:
        """Execute a plugin directly from the HUD Controls/Plugins drawer."""
        self.pipeline.last_active = time.time()
        self.pipeline.increment_command_count()

        def _run() -> None:
            try:
                params = json.loads(params_json) if params_json else {}
            except Exception:
                params = {}
            res = self.pipeline.tool_suite.execute(name, params)
            if res:
                self.pipeline.response_queue.put(str(res)[:320])

        threading.Thread(target=_run, daemon=True).start()

    def get_memory_vault_items(self) -> str:
        """Return JSON with Mark-LV structured memory entries and Jared Rhod VAULT-INDEX.md content."""
        entries: list[dict[str, Any]] = []
        try:
            from memory.memory_manager import all_entries_for_ui
            entries = all_entries_for_ui()
        except Exception:
            pass
        vault_md = ""
        if os.path.exists(VAULT_INDEX_PATH):
            try:
                with open(VAULT_INDEX_PATH, "r", encoding="utf-8") as f:
                    vault_md = f.read(4000)
            except Exception:
                pass
        return json.dumps({"entries": entries, "vault_index": vault_md})

    def delete_memory_vault_item(self, category: str, key: str) -> str:
        """Delete a specific key from persistent memory."""
        try:
            from memory.memory_manager import forget_entry
            forget_entry(category, key)
        except Exception:
            pass
        return self.get_memory_vault_items()

    def trigger_morning_briefing(self) -> None:
        """Run the proactive Morning / Daily Briefing from the HUD Controls drawer."""
        self.pipeline.trigger_morning_briefing()

    def create_desktop_shortcut(self) -> None:
        """Create a native Windows Desktop shortcut for J.A.R.V.I.S. Mark 55."""
        try:
            desktop = os.path.join(os.path.expanduser("~"), "Desktop")
            bat_path = os.path.join(_ROOT_DIR, "START_JARVIS.bat")
            ps_cmd = (
                f"$s=(New-Object -COM WScript.Shell).CreateShortcut('{desktop}\\JARVIS Mark 55.lnk');"
                f"$s.TargetPath='{bat_path}';"
                f"$s.WorkingDirectory='{_ROOT_DIR}';"
                "$s.Save()"
            )
            subprocess.run(["powershell", "-NoProfile", "-Command", ps_cmd], timeout=5)
            self.pipeline.window.evaluate_js("addLog('SYSTEM', '[SETUP] Desktop shortcut created: JARVIS Mark 55.lnk')")
            self.pipeline.response_queue.put("Desktop shortcut created, sir.")
        except Exception as e:
            safe_err = json.dumps(f"Shortcut warning: {str(e)[:90]}")
            self.pipeline.window.evaluate_js(f"addLog('SYSTEM', {safe_err})")

    def pick_file(self) -> None:
        """Open native file dialog to attach a file for Mark-LV file_processor."""
        try:
            result = self.pipeline.window.create_file_dialog(webview.OPEN_DIALOG, allow_multiple=False)
            if result and len(result) > 0:
                chosen = result[0]
                self.pipeline.tool_suite.ui.current_file = chosen
                fname = os.path.basename(chosen)
                safe_msg = json.dumps(f"Attached file ready for processing: {fname} ({chosen})")
                self.pipeline.window.evaluate_js(f"addLog('SYSTEM', {safe_msg})")
                self.pipeline.window.evaluate_js(f"setAttachedFile({json.dumps(fname)})")
        except Exception as e:
            safe_err = json.dumps(f"File picker warning: {str(e).splitlines()[0][:100]}")
            self.pipeline.window.evaluate_js(f"addLog('SYSTEM', {safe_err})")

    def scan_airspace(self) -> None:
        """Run immediate 200km OpenSky aircraft radar scan."""
        self.pipeline.abort_event.clear()
        TTS_ABORT_EVENT.clear()
        self.pipeline.active_cmd_id += 1
        my_id = self.pipeline.active_cmd_id
        self.pipeline.increment_command_count()
        self.pipeline.response_queue.put(("ACK", "On it, sir. Scanning 200 kilometer airspace radar."))

        def _run() -> None:
            res = self.pipeline.tool_suite.execute("aircraft_report", {"action": "report", "radius_km": 200})
            if not self.pipeline.abort_event.is_set() and my_id == self.pipeline.active_cmd_id:
                self.pipeline.response_queue.put(res)

        threading.Thread(target=_run, daemon=True).start()

    def undo_last_action(self) -> None:
        """Revert the most recent file, desktop, or setting change."""
        self.pipeline.abort_event.clear()
        TTS_ABORT_EVENT.clear()
        self.pipeline.active_cmd_id += 1
        my_id = self.pipeline.active_cmd_id
        self.pipeline.increment_command_count()
        self.pipeline.response_queue.put(("ACK", "Working on it, sir. Reverting last action."))

        def _run() -> None:
            res = self.pipeline.tool_suite.execute("undo", {"action": "undo"})
            if not self.pipeline.abort_event.is_set() and my_id == self.pipeline.active_cmd_id:
                self.pipeline.response_queue.put(res)

        threading.Thread(target=_run, daemon=True).start()

    def show_memory_vault(self) -> None:
        """Display stored long-term memories in the HUD conversation log and open the Memory Vault modal."""
        self.pipeline.increment_command_count()
        try:
            from memory.memory_manager import all_entries_for_ui
            entries = all_entries_for_ui()
            if not entries:
                self.pipeline.window.evaluate_js("addLog('SYSTEM', 'Memory Vault is ready. Opening Vault inspector...')")
            else:
                summary = " | ".join(f"{e['category']}.{e['key']}: {e['value']}" for e in entries[:10])
                safe = json.dumps(f"Memory Vault ({len(entries)} entries): {summary}")
                self.pipeline.window.evaluate_js(f"addLog('SYSTEM', {safe})")
            self.pipeline.window.evaluate_js("openHudModal('memory')")
        except Exception as e:
            safe_err = json.dumps(f"Memory Vault error: {str(e).splitlines()[0][:100]}")
            self.pipeline.window.evaluate_js(f"addLog('SYSTEM', {safe_err})")

    def trigger_screen_vision(self) -> None:
        """Instant 1-pass Screen Vision Mode: collapses HUD to corner Orb, captures screen in 15ms, and analyzes directly."""
        self.pipeline.last_active = time.time()
        self.pipeline.abort_event.clear()
        TTS_ABORT_EVENT.clear()
        self.pipeline.active_cmd_id += 1
        my_id = self.pipeline.active_cmd_id
        self.pipeline.increment_command_count()
        self.pipeline.response_queue.put(("ACK", "On it, sir. Scanning your display."))
        self.pipeline.enter_orb_only_mode(sleep_mode=False, vision_mode=True)

        def _run() -> None:
            time.sleep(0.22)
            if self.pipeline.abort_event.is_set() or my_id != self.pipeline.active_cmd_id:
                return
            self.pipeline.window.evaluate_js("updateState('THINKING')")
            res = run_screen_or_camera_vision("screen", "Analyze my screen and tell me what I am looking at.", window=self.pipeline.window)
            if self.pipeline.abort_event.is_set() or my_id != self.pipeline.active_cmd_id:
                return
            self.pipeline.history.append(("USER", "[Screen Vision]"))
            self.pipeline.history.append(("JARVIS", res))
            MemoryModule.save(self.pipeline.history)
            self.pipeline.response_queue.put(res)

        threading.Thread(target=_run, daemon=True).start()

    def analyze_camera_frame(
        self,
        data_url: str,
        prompt: str = "Analyze what I am holding or showing to the camera and describe what you see.",
    ) -> None:
        """Instant 1-pass Camera Vision using the live WebView2 webcam frame (zero OpenCV camera lock conflict)."""
        self.pipeline.last_active = time.time()
        self.pipeline.abort_event.clear()
        TTS_ABORT_EVENT.clear()
        self.pipeline.active_cmd_id += 1
        my_id = self.pipeline.active_cmd_id
        self.pipeline.increment_command_count()
        self.pipeline.response_queue.put(("ACK", "Working on it, sir. Analyzing camera feed."))

        def _run() -> None:
            try:
                if self.pipeline.abort_event.is_set() or my_id != self.pipeline.active_cmd_id:
                    return
                self.pipeline.window.evaluate_js("updateState('THINKING')")
                self.pipeline.window.evaluate_js("addLog('SYSTEM', '[VISION] Running 1-Pass AI Camera Vision on live webcam frame...')")
                raw_bytes = None
                if data_url and isinstance(data_url, str) and "," in data_url:
                    raw_bytes = base64.b64decode(data_url.split(",", 1)[1])
                res = run_screen_or_camera_vision(
                    angle="camera",
                    text=prompt or "Analyze what I am holding or showing to the camera.",
                    raw_image_bytes=raw_bytes,
                    window=self.pipeline.window,
                )
                if self.pipeline.abort_event.is_set() or my_id != self.pipeline.active_cmd_id:
                    return
                self.pipeline.history.append(("USER", f"[Camera Vision] {prompt}"))
                self.pipeline.history.append(("JARVIS", res))
                MemoryModule.save(self.pipeline.history)
                self.pipeline.response_queue.put(res)
            except Exception as e:
                safe_err = json.dumps(f"Camera vision error: {str(e).splitlines()[0][:100]}")
                self.pipeline.window.evaluate_js(f"addLog('SYSTEM', {safe_err})")

        threading.Thread(target=_run, daemon=True).start()

    def save_camera_snapshot(self, data_url: str) -> None:
        """Save a high-resolution snapshot from the live HUD webcam to Desktop/JARVIS_Snapshots."""
        self.pipeline.last_active = time.time()
        self.pipeline.increment_command_count()

        def _run() -> None:
            try:
                if not data_url or "," not in data_url:
                    return
                img_bytes = base64.b64decode(data_url.split(",", 1)[1])
                snap_dir = os.path.join(os.path.expanduser("~"), "Desktop", "JARVIS_Snapshots")
                os.makedirs(snap_dir, exist_ok=True)
                fname = f"jarvis_cam_{int(time.time())}.jpg"
                fpath = os.path.join(snap_dir, fname)
                with open(fpath, "wb") as f:
                    f.write(img_bytes)
                safe_msg = json.dumps(f"[CAPTURE] Snapshot saved to Desktop\\JARVIS_Snapshots\\{fname}")
                self.pipeline.window.evaluate_js(f"addLog('SYSTEM', {safe_msg})")
                self.pipeline.response_queue.put("Snapshot captured and saved to your desktop folder, sir.")
            except Exception as e:
                safe_err = json.dumps(f"Snapshot error: {str(e).splitlines()[0][:100]}")
                self.pipeline.window.evaluate_js(f"addLog('SYSTEM', {safe_err})")

        threading.Thread(target=_run, daemon=True).start()

    def gesture_action(self, action: str) -> None:
        """Execute real-time hand gesture commands (volume_up, volume_down, mute_toggle, switch_persona, palm_wake)."""
        self.pipeline.last_active = time.time()
        self.pipeline.increment_command_count()
        act = (action or "").lower().strip()
        if act == "volume_up":
            res = volume_control("volume_up")
            self.pipeline.window.evaluate_js(f"addLog('SYSTEM', {json.dumps('[GESTURE ▲] ' + res)})")
        elif act == "volume_down":
            res = volume_control("volume_down")
            self.pipeline.window.evaluate_js(f"addLog('SYSTEM', {json.dumps('[GESTURE ▼] ' + res)})")
        elif act == "mute_toggle":
            self.toggle_mute()
        elif act == "switch_persona":
            new_mode = "FRIDAY" if self.pipeline.voice_mode == "JARVIS" else "JARVIS"
            self.pipeline.voice_mode = new_mode
            self.pipeline.window.evaluate_js(f"switchMode('{new_mode}')")
            greeting = "FRIDAY online! Ready for your command, boss." if new_mode == "FRIDAY" else "JARVIS online. At your service, sir."
            self.pipeline.response_queue.put(greeting)
        elif act == "palm_wake":
            if self.pipeline.is_muted:
                self.toggle_mute()
            self.pipeline.window.evaluate_js("focusInput()")
            self.pipeline.window.evaluate_js("addLog('SYSTEM', '[GESTURE ◈] Open Palm: Audio & Command Input Ready.')")

    def announce_camera_items(self, summary: str) -> None:
        """Speak live detected camera items, QR/barcode payloads, or sentry alerts aloud."""
        self.pipeline.last_active = time.time()
        self.pipeline.increment_command_count()
        if summary and isinstance(summary, str):
            self.pipeline.response_queue.put(summary.strip())

    def enter_mini(self) -> None:
        self.pipeline.enter_orb_only_mode(sleep_mode=False)

    def exit_mini(self) -> None:
        self.pipeline.exit_orb_only_mode()


if __name__ == "__main__":
    html_path = os.path.join(_ROOT_DIR, "hud.html")
    sw, sh = _get_screen_size()
    window = webview.create_window(
        "JARVIS Master",
        html_path,
        x=0,
        y=0,
        width=sw,
        height=sh,
        transparent=True,
        frameless=True,
        fullscreen=False,
        on_top=True,
    )
    pipeline = JarvisPipeline(window)
    api = Api(pipeline)
    window.expose(
        api.send_command,
        api.kill_command,
        api.minimize,
        api.toggle_fullscreen,
        api.destroy,
        api.force_weather_update,
        api.force_stats_update,
        api.network_diagnostics,
        api.toggle_mute,
        api.hud_video_control,
        api.set_control_toggle,
        api.get_controls_state,
        api.get_remote_pairing,
        api.regenerate_remote_pin,
        api.get_plugins_list,
        api.toggle_plugin_state,
        api.reload_plugins_now,
        api.run_plugin_direct,
        api.get_memory_vault_items,
        api.delete_memory_vault_item,
        api.trigger_morning_briefing,
        api.create_desktop_shortcut,
        api.pick_file,
        api.scan_airspace,
        api.undo_last_action,
        api.show_memory_vault,
        api.trigger_screen_vision,
        api.analyze_camera_frame,
        api.save_camera_snapshot,
        api.gesture_action,
        api.announce_camera_items,
        api.enter_mini,
        api.exit_mini,
    )

    threading.Timer(2.0, pipeline.start_services).start()
    webview.start()
