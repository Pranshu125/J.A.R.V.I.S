import threading
import asyncio
import queue
import time
import random
import json
import os
import requests
import subprocess
import webbrowser
import speech_recognition as sr
import pygame
import psutil
import webview

# Automatically load environment variables from .env
_env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
if os.path.exists(_env_path):
    try:
        with open(_env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    k, v = k.strip(), v.strip().strip('"').strip("'")
                    if k and not os.environ.get(k):
                        os.environ[k] = v
    except Exception:
        pass

# Global Process Patch (Mark-LV Architecture): Suppress background console flashing while remaining a true Popen class
if os.name == 'nt':
    _OrigPopen = subprocess.Popen
    class _SilentPopen(_OrigPopen):
        def __init__(self, *args, **kwargs):
            if 'creationflags' not in kwargs:
                kwargs['creationflags'] = subprocess.CREATE_NO_WINDOW
            super().__init__(*args, **kwargs)
    subprocess.Popen = _SilentPopen

# Modular capabilities ported from Sagar's Friday, Ultron, Mark-LV, Mark-XXXIX, Mark-X.1, AI-Assistant-1.1, and Zoey 3D HUD
from modules.world_intel import (
    get_world_news_sync,
    get_finance_news_sync,
    open_world_monitor,
    open_finance_monitor
)
from modules.system_control import (
    volume_control,
    brightness_control,
    window_action,
    launch_application,
    split_workspace
)
from modules.tts_engine import speak_text, get_instant_ack, stop_speaking, TTS_ABORT_EVENT
from modules.mark_lv_bridge import (
    UnifiedToolSuite,
    get_active_gemini_ladder,
    mark_model_exhausted,
    run_screen_or_camera_vision,
)

# ========================================================
# J.A.R.V.I.S. & F.R.I.D.A.Y. UNIFIED COGNITIVE OS
# Real-Time Voice Assistant with 3D Holographic Orb,
# MediaPipe Hand Gestures, 29+ Autonomous Tools,
# Multi-Step Agent Planner, OpenSky Airspace Radar,
# Deep Windows OS Control, World Intel & Bilingual Intelligence
# ========================================================

OLLAMA_URL = "http://localhost:11434/api/chat"
OLLAMA_MODEL = "llama3.2" 
MEMORY_DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "jarvis_state.md")

class MemoryModule:
    """Persistent Conversational & Long-Term Memory Vault (Zoey & Mark-LV style)"""
    @staticmethod
    def load():
        return []
    
    @staticmethod
    def save(history):
        try:
            with open(MEMORY_DB, 'w', encoding='utf-8') as f: 
                f.write("# J.A.R.V.I.S. Memory Vault\n\n")
                for role, msg in history[-15:]:
                    f.write(f"**{role}:** {msg}\n\n")
        except Exception:
            pass

    @staticmethod
    def get_long_term_prompt() -> str:
        try:
            from memory.memory_manager import load_memory, format_memory_for_prompt
            return format_memory_for_prompt(load_memory())
        except Exception:
            return ""


class IntelligenceModule:
    """Hybrid Cognitive Engine: Cloud Gemini 3.8 Flash (29+ Native Tools) + Local Ollama Fallback"""
    @staticmethod
    def chat(messages, tools, window, abort_check=None):
        if abort_check and abort_check():
            return {"role": "assistant", "content": ""}
        api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        if api_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=api_key)

                # Native Function Calling declarations covering all 29+ integrated repo capabilities
                def open_app(app_name: str, action: str = "open"):
                    """Open, close, minimize, maximize, or switch to any installed desktop application (action: open | close | minimize | maximize | switch)."""
                    pass

                def web_search(query: str, mode: str = "search", items: str = "", aspect: str = ""):
                    """Search the web via DuckDuckGo (mode='search'), search breaking news (mode='news'), or compare products (mode='compare' with comma-separated items)."""
                    pass

                def weather_report(city: str, time: str = "today"):
                    """Get detailed weather report and open live Windy radar for any city (time: today | tomorrow | week)."""
                    pass

                def send_message(platform: str, contact: str, message: str):
                    """Send a message on WhatsApp, Telegram, Instagram, or Discord to a contact."""
                    pass

                def reminder(date: str, time: str, message: str):
                    """Schedule a desktop reminder via Windows Task Scheduler (date: YYYY-MM-DD, time: HH:MM)."""
                    pass

                def youtube_video(action: str, query: str = "", url: str = "", save: bool = False):
                    """Control YouTube: play a video (action='play', query='...'), summarize a video transcript (action='summarize', url='...'), get video info (action='info'), or show trending (action='trending')."""
                    pass

                def computer_settings(action: str, value: str = ""):
                    """Control computer settings: volume_up, volume_down, volume_set, mute, unmute, brightness_up, brightness_down, brightness_set, dark_mode, wifi_toggle, bluetooth_toggle, lock_screen, sleep, restart, shutdown, reload_page, close_tab, new_tab, zoom_in, zoom_out, scroll_up, scroll_down."""
                    pass

                def browser_control(action: str, url: str = "", query: str = "", text: str = "", selector: str = "", direction: str = "down"):
                    """Automate web browser via Playwright/CDP: go_to, search, click, type, scroll, fill_form, smart_click, smart_type, get_text, press, close."""
                    pass

                def file_controller(action: str, path: str = "", name: str = "", destination: str = "", content: str = "", extension: str = ""):
                    """Manage files and folders: list, create_file, create_folder, delete, move, copy, rename, read, write, find, largest, disk_usage, organize, info."""
                    pass

                def desktop_control(action: str, path: str = "", url: str = "", mode: str = "by_type"):
                    """Manage Windows Desktop: wallpaper (from file path), wallpaper_url (from image URL), organize (by_type or by_date), clean, list, stats."""
                    pass

                def code_helper(action: str, description: str = "", language: str = "python", file_path: str = "", code: str = "", save_path: str = ""):
                    """Write, edit, explain, run, or fix code files in any programming language and open in VS Code (action: write | edit | explain | run | auto | build)."""
                    pass

                def dev_agent(description: str, project_name: str = "", language: str = "python", open_vscode: bool = True, run_project: bool = False):
                    """Autonomous multi-file software engineer: plans architecture, writes all project files, installs dependencies, opens VS Code, and auto-fixes bugs."""
                    pass

                def computer_control(action: str, text: str = "", x: int = 0, y: int = 0, key: str = "", description: str = "", window_title: str = ""):
                    """Direct GUI mouse/keyboard automation: type, smart_type, click, double_click, right_click, hotkey, press, scroll, move, drag, copy, paste, screenshot, wait, clear_field, focus_window, screen_find, random_data."""
                    pass

                def game_updater(action: str, game: str = "", platform: str = "all", schedule_time: str = "03:00"):
                    """Manage PC games across Steam, Epic, Riot, Xbox, GOG, Ubisoft, EA, Battle.net: launch, list_installed, update, update_all, install, status, schedule, cancel_schedule."""
                    pass

                def flight_finder(origin: str, destination: str, departure_date: str, return_date: str = "", passengers: int = 1, cabin: str = "economy", save: bool = False):
                    """Search Google Flights for live flight routes, airlines, durations, and prices."""
                    pass

                def file_processor(action: str, file_path: str = "", question: str = "", target_language: str = "en", output_format: str = "png"):
                    """Process uploaded or local files (PDF, image, DOCX, Excel/CSV, audio/video, ZIP): analyze, summarize, ocr, describe, extract_text, to_word, translate, fix_writing, resize, compress, convert, filter, chart."""
                    pass

                def video_player(action: str, source: str = "", timestamp: str = "", question: str = ""):
                    """Play, stop, summarize, or analyze local or online video streams (action: play | stop | Summary | analyze | timestamp | mute | unmute)."""
                    pass

                def screen_process(text: str, angle: str = "screen"):
                    """Capture the user's screen (angle='screen') or webcam camera (angle='camera') and analyze what is visible using Gemini Vision."""
                    pass

                def aircraft_report(action: str = "report", radius_km: int = 200):
                    """Scan live OpenSky airspace radar within 200km for nearby aircraft (callsign, country, distance, speed, heading) or open the FlightRadar24 map (action: report | map)."""
                    pass

                def agent_task(goal: str):
                    """Deploy the Mark-XXXIX autonomous multi-step Agent Planner and Executor for complex multi-step goals."""
                    pass

                def save_memory(category: str, key: str, value: str):
                    """Save a permanent fact about the user to structured long-term memory (category: identity | preferences | projects | relationships | wishes | notes)."""
                    pass

                def recall_memory(query: str = ""):
                    """Search structured long-term memory for stored facts about the user."""
                    pass

                def manage_monitor(action: str, topic: str = ""):
                    """Manage background daily news/topic monitors (action: add | remove | list | check)."""
                    pass

                def system_status():
                    """Get a full hardware diagnostic report: CPU %, RAM GB, GPU %, CPU temperature, uptime, and process count."""
                    pass

                def undo(action: str = "undo"):
                    """Undo the last reversible file, desktop, or setting change made by the assistant (action: undo | list)."""
                    pass

                def split_workspace(left_app: str, right_app: str):
                    """Tile two applications side-by-side on screen (e.g. WhatsApp left, Chrome right)."""
                    pass

                def launch_application(app_name: str):
                    """Launch or open an installed desktop application (e.g. whatsapp, chrome, spotify, vscode, notepad, calculator)."""
                    pass

                def system_hardware_control(action: str, app_name: str = ""):
                    """Control volume (volume_up, volume_down, mute), brightness (brightness_up, brightness_down), or launch an application (launch_app with app_name)."""
                    pass

                def window_management(action: str):
                    """Manage desktop windows (minimize, maximize, snap_left, snap_right, show_desktop, lock_screen, screenshot, task_manager)."""
                    pass

                def open_website(url: str):
                    """Open any website URL, YouTube song or video search in the default web browser."""
                    pass

                def get_world_news():
                    """Fetch live breaking global news headlines and open the interactive satellite World Monitor dashboard."""
                    pass

                def get_finance_news():
                    """Fetch current market and financial news headlines and open the interactive Finance Monitor dashboard."""
                    pass

                def open_world_monitor():
                    """Open the live interactive satellite World Monitor dashboard on screen."""
                    pass

                def open_finance_monitor():
                    """Open the live financial markets dashboard on screen."""
                    pass

                def execute_terminal(command: str):
                    """Execute a shell or PowerShell command on the machine."""
                    pass

                gemini_tools = [
                    open_app,
                    web_search,
                    weather_report,
                    send_message,
                    reminder,
                    youtube_video,
                    computer_settings,
                    browser_control,
                    file_controller,
                    desktop_control,
                    code_helper,
                    dev_agent,
                    computer_control,
                    game_updater,
                    flight_finder,
                    file_processor,
                    video_player,
                    screen_process,
                    aircraft_report,
                    agent_task,
                    save_memory,
                    recall_memory,
                    manage_monitor,
                    system_status,
                    undo,
                    split_workspace,
                    launch_application,
                    system_hardware_control,
                    window_management,
                    open_website,
                    get_world_news,
                    get_finance_news,
                    open_world_monitor,
                    open_finance_monitor,
                    execute_terminal,
                ]

                sys_inst = messages[0]["content"] if messages and messages[0]["role"] == "system" else "You are JARVIS."
                user_prompt = messages[-1]["content"] if messages else "Hello"

                for m_name in get_active_gemini_ladder():
                    if abort_check and abort_check():
                        return {"role": "assistant", "content": ""}
                    try:
                        model = genai.GenerativeModel(m_name, tools=gemini_tools, system_instruction=sys_inst)
                        res = model.generate_content(user_prompt)
                        if abort_check and abort_check():
                            return {"role": "assistant", "content": ""}
                        if res.candidates and res.candidates[0].content.parts:
                            parts = res.candidates[0].content.parts
                            tool_calls = []
                            for p in parts:
                                if p.function_call:
                                    fn = p.function_call
                                    tool_calls.append({
                                        "function": {
                                            "name": fn.name,
                                            "arguments": dict(fn.args)
                                        }
                                    })
                            if tool_calls:
                                return {"role": "assistant", "content": "", "tool_calls": tool_calls}

                            text_parts = [p.text for p in parts if p.text]
                            if text_parts:
                                return {"role": "assistant", "content": "".join(text_parts).strip()}
                        return {"role": "assistant", "content": res.text.strip()}
                    except Exception as m_err:
                        err_s = str(m_err)
                        if "429" in err_s or "RESOURCE_EXHAUSTED" in err_s or "Quota exceeded" in err_s or "404" in err_s:
                            mark_model_exhausted(m_name)
                        continue
            except Exception as e:
                safe_err = json.dumps(f"Gemini fallback to Ollama: {str(e).splitlines()[0][:120]}")
                try:
                    window.evaluate_js(f"addLog('SYSTEM', {safe_err})")
                except Exception:
                    pass

        if abort_check and abort_check():
            return {"role": "assistant", "content": ""}

        # 2. Local Ollama Mode with low-latency configuration
        payload = {
            "model": OLLAMA_MODEL,
            "messages": messages,
            "stream": False,
            "tools": tools,
            "options": {
                "temperature": 0.5,
                "num_ctx": 2048,
                "num_predict": 130
            }
        }
        try:
            response = requests.post(OLLAMA_URL, json=payload, timeout=90)
            if abort_check and abort_check():
                return {"role": "assistant", "content": ""}
            if response.status_code == 200:
                return response.json().get("message", {})
            else:
                return {"role": "assistant", "content": f"Neural core returned code {response.status_code}."}
        except requests.exceptions.Timeout:
            return {"role": "assistant", "content": "CPU load is high right now, sir. Processing the request shortly."}
        except Exception as e:
            return {"role": "assistant", "content": f"Sir, my cognitive engine is offline: {e}"}

class JarvisPipeline:
    def __init__(self, window):
        self.window = window
        self._orig_evaluate_js = window.evaluate_js
        self._js_queue = queue.Queue(maxsize=300)
        self._hwnd = None
        self.history = MemoryModule.load()
        self.text_queue = queue.Queue()
        self.response_queue = queue.Queue()
        self.running = True
        self.voice_mode = 'JARVIS' # Strictly 'JARVIS' or 'FRIDAY'
        self.is_sleeping = False
        self.is_fullscreen = True
        self.is_orb_only = False
        self.screen_vision_mode = False
        self.abort_event = threading.Event()
        self.active_cmd_id = 0
        self.active_subprocess = None
        self.last_active = time.time()
        self.session_start = time.time()
        self.command_count = 0
        self.session_count = self._init_session_counter()
        # Wrap window.evaluate_js with non-blocking async queue for UI updates so worker threads never hang
        self.window.evaluate_js = self._safe_evaluate_js
        threading.Thread(target=self._js_worker, daemon=True).start()
        self.tool_suite = UnifiedToolSuite(self)

    def _get_hwnd(self) -> int:
        if self._hwnd:
            return self._hwnd
        if os.name == 'nt':
            try:
                import ctypes
                hwnd = ctypes.windll.user32.FindWindowW(None, "JARVIS Master")
                if hwnd:
                    self._hwnd = hwnd
                    return hwnd
            except Exception:
                pass
        return 0

    def _is_window_minimized(self) -> bool:
        if os.name == 'nt':
            try:
                import ctypes
                hwnd = self._get_hwnd()
                if hwnd and ctypes.windll.user32.IsIconic(hwnd):
                    return True
            except Exception:
                pass
        return False

    def _safe_evaluate_js(self, script: str, *args, **kwargs):
        """Non-blocking evaluate_js wrapper that prevents WebView2 semaphore deadlocks in Minimize / Orb mode."""
        if not script or not isinstance(script, str):
            return None
        if self._is_window_minimized():
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

    def _js_worker(self):
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

    def _set_window_rect(self, x: int, y: int, w: int, h: int):
        """Move and resize the window asynchronously via Win32 SetWindowPos (SWP_ASYNCWINDOWPOS) without recreating .NET handles."""
        if os.name == 'nt':
            try:
                import ctypes
                user32 = ctypes.windll.user32
                hwnd = self._get_hwnd()
                if hwnd:
                    if user32.IsIconic(hwnd):
                        user32.ShowWindowAsync(hwnd, 9)  # SW_RESTORE
                    # HWND_TOPMOST = -1, SWP_SHOWWINDOW = 0x0040, SWP_ASYNCWINDOWPOS = 0x4000, SWP_NOACTIVATE = 0x0010
                    user32.SetWindowPos(hwnd, -1, int(x), int(y), int(w), int(h), 0x0040 | 0x4000 | 0x0010)
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
        import re
        raw_low = text.lower().strip()
        # Strip punctuation and filler/wake words to inspect the core command
        cleaned = re.sub(r"[^a-z0-9\s\u0900-\u097F]", " ", raw_low)
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
            "रुको", "बस", "चुप", "बंद", "बंद करो", "रुक जाओ"
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
            "cancel kar do", "rehne do", "chhod do", "stop kar do", "kill kar do"
        )
        if any(p in core or p in raw_low for p in kill_phrases):
            return True

        if not strict_barge_in and len(tokens) <= 3 and tokens[0] in ("stop", "kill", "abort", "cancel", "terminate", "ruko", "chup"):
            return True

        return False

    def abort_current_command(self, spoken_text: str = ""):
        """Pre-emptively kill any running command, tool execution, subprocess, and active TTS speech."""
        self.active_cmd_id += 1
        self.abort_event.set()
        stop_speaking()

        # Drain queued commands and queued TTS responses immediately
        while not self.text_queue.empty():
            try:
                self.text_queue.get_nowait()
                self.text_queue.task_done()
            except Exception:
                break
        while not self.response_queue.empty():
            try:
                self.response_queue.get_nowait()
                self.response_queue.task_done()
            except Exception:
                break

        # Kill any active shell/PowerShell subprocess
        proc = getattr(self, "active_subprocess", None)
        if proc is not None:
            try:
                proc.kill()
            except Exception:
                pass
            self.active_subprocess = None

        # Cancel Mark-XXXIX AgentExecutor if running
        try:
            if hasattr(self, "tool_suite") and getattr(self.tool_suite, "agent_executor", None):
                ae = self.tool_suite.agent_executor
                if hasattr(ae, "cancel"):
                    ae.cancel()
                elif hasattr(ae, "running"):
                    ae.running = False
        except Exception:
            pass

        try:
            self.window.evaluate_js("updateState('ONLINE')")
            self.window.evaluate_js("addLog('SYSTEM', '[ABORT ⊘] Active command & processes terminated.')")
        except Exception:
            pass

        low = (spoken_text or "").lower()
        silent_words = ("chup", "silence", "quiet", "shut up", "mute")
        if not any(sw in low for sw in silent_words):
            is_hi = any(hw in low for hw in ("ruk", "band", "bas", "roko", "mat", "rehne", "chhod"))
            confirm_msg = "Ruk gaya, sir." if is_hi else "Stopped, sir."
            mode = getattr(self, "voice_mode", "JARVIS")
            def _speak_abort():
                try:
                    safe_c = json.dumps(confirm_msg)
                    self.window.evaluate_js(f"addLog('JARVIS', {safe_c})")
                    speak_text(confirm_msg, mode=mode, cache_clip=True, ignore_abort=True)
                    self.window.evaluate_js("updateState('ONLINE')")
                except Exception:
                    pass
            threading.Thread(target=_speak_abort, daemon=True).start()
        else:
            TTS_ABORT_EVENT.clear()

    def _init_session_counter(self) -> int:
        mem_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "jarvis_memory.json")
        data = {}
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

    def increment_command_count(self):
        self.command_count += 1
        try:
            self.window.evaluate_js(f"setSessionAndCommands({self.session_count}, {self.command_count})")
        except Exception:
            pass

    def enter_orb_only_mode(self, sleep_mode: bool = False, vision_mode: bool = False):
        """Collapse HUD so ONLY the 3D Holographic Orb floats on a 100% transparent background."""
        try:
            self.is_orb_only = True
            self.is_sleeping = sleep_mode
            self.is_fullscreen = False
            if vision_mode:
                self.screen_vision_mode = True
            self.window.evaluate_js("toggleMiniMode(true)")
            sw, sh = 1920, 1080
            if os.name == 'nt':
                try:
                    import ctypes
                    sw = ctypes.windll.user32.GetSystemMetrics(0)
                    sh = ctypes.windll.user32.GetSystemMetrics(1)
                except Exception:
                    pass
            self._set_window_rect(max(20, sw - 340), max(20, sh - 380), 320, 320)
        except Exception as e:
            print(f"enter_orb_only_mode warning: {e}")

    def exit_orb_only_mode(self):
        """Restore the full HUD from Orb-Only Transparent Mode."""
        try:
            self.is_orb_only = False
            self.is_sleeping = False
            self.screen_vision_mode = False
            self.is_fullscreen = True
            self.last_active = time.time()
            sw, sh = 1920, 1080
            if os.name == 'nt':
                try:
                    import ctypes
                    sw = ctypes.windll.user32.GetSystemMetrics(0)
                    sh = ctypes.windll.user32.GetSystemMetrics(1)
                except Exception:
                    pass
            self._set_window_rect(0, 0, sw, sh)
            self.window.evaluate_js("toggleMiniMode(false)")
        except Exception as e:
            print(f"exit_orb_only_mode warning: {e}")

    def start_services(self):
        threading.Thread(target=self.stt_worker, daemon=True).start()
        threading.Thread(target=self.llm_worker, daemon=True).start()
        threading.Thread(target=self.tts_worker, daemon=True).start()
        threading.Thread(target=self.telemetry_worker, daemon=True).start()
        threading.Thread(target=self.idle_worker, daemon=True).start()
        threading.Thread(target=self.background_monitors_worker, daemon=True).start()
        try:
            self.window.evaluate_js(f"setSessionAndCommands({self.session_count}, {self.command_count})")
        except Exception:
            pass
        
        # Dynamic Time-of-Day Bilingual Boot Greeting
        hour = time.localtime().tm_hour
        mode_name = getattr(self, "voice_mode", "JARVIS")
        if hour < 12:
            g = [
                "Good morning, sir. All systems are online and ready.",
                f"Good morning, boss. {mode_name} is operational.",
                "Namaste sir! Good morning. Sabhi systems online aur ready hain."
            ]
        elif hour < 18:
            g = [
                "Good afternoon, sir. How may I assist you today?",
                f"Systems operational. Good afternoon, boss.",
                "Good afternoon sir! Bataye aaj kya kaam karna hai?"
            ]
        else:
            g = [
                f"Good evening, sir. {mode_name} is online and standing by.",
                "Evening, boss. Awaiting your instructions.",
                "Good evening sir! System ready hai, bataye kya hukum hai?"
            ]
        
        self.response_queue.put(random.choice(g))
        
        # Global Quick-Summon Overlay Hotkey (Alt + Space) & Emergency Kill Hotkey (Alt + X)
        try:
            import keyboard
            keyboard.add_hotkey('alt+space', self.trigger_hotkey_wake)
            keyboard.add_hotkey('alt+x', lambda: self.abort_current_command("kill"))
        except Exception as e:
            print("Hotkey binding failed: ", e)

    def trigger_hotkey_wake(self):
        if getattr(self, "is_orb_only", False) or getattr(self, "is_sleeping", False):
            self.exit_orb_only_mode()
            self.response_queue.put("Full HUD overlay restored, sir.")
        else:
            self.enter_orb_only_mode(sleep_mode=False)

    def idle_worker(self):
        while self.running:
            if not getattr(self, "is_sleeping", False) and not getattr(self, "is_orb_only", False) and time.time() - self.last_active > 90:
                self.enter_orb_only_mode(sleep_mode=False)
            time.sleep(2)

    def background_monitors_worker(self):
        """Runs Mark-LV SystemMonitor threshold checks and BackgroundMonitor topic checks."""
        time.sleep(15)
        ticks = 0
        while self.running:
            try:
                if self.tool_suite.sys_monitor:
                    alert = self.tool_suite.sys_monitor.check()
                    if alert:
                        safe_alert = json.dumps(alert)
                        self.window.evaluate_js(f"addLog('SYSTEM', {safe_alert})")
                if ticks % 60 == 0:
                    from actions.background_monitor import check_all
                    topic_alerts = check_all()
                    for ta in topic_alerts:
                        safe_ta = json.dumps(ta)
                        self.window.evaluate_js(f"addLog('SYSTEM', {safe_ta})")
            except Exception:
                pass
            ticks += 1
            time.sleep(30)
            
    def fetch_weather(self):
        try:
            city, country, lat, lon = "Unknown", "", None, None
            try:
                loc = requests.get('http://ip-api.com/json/', timeout=4).json()
                city = loc.get('city', 'Unknown')
                country = loc.get('countryCode', '')
                lat, lon = loc.get('lat'), loc.get('lon')
            except Exception:
                loc = requests.get('https://ipapi.co/json/', timeout=4).json()
                city = loc.get('city', 'Unknown')
                country = loc.get('country_code', '')
                lat, lon = loc.get('latitude'), loc.get('longitude')

            if lat is not None and lon is not None:
                w_url = (
                    f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}"
                    "&current=temperature_2m,apparent_temperature,relative_humidity_2m,wind_speed_10m,weather_code"
                )
                w_data = requests.get(w_url, timeout=5).json()['current']
                t = w_data['temperature_2m']
                feels = w_data.get('apparent_temperature', t)
                h = w_data['relative_humidity_2m']
                w = w_data['wind_speed_10m']
                code = w_data['weather_code']

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
                self.window.evaluate_js(
                    f"updateWeather('{t}°C', '{loc_full}', '{city}', '{desc}', '{h}%', '{w} km/h', '{feels}°C', '{icon}')"
                )
                self.window.evaluate_js("addLog('SYSTEM', 'Live satellite weather telemetry synchronized.')")
        except Exception as e:
            safe_err = json.dumps(f"Weather telemetry warning: {str(e).splitlines()[0][:100]}")
            self.window.evaluate_js(f"addLog('SYSTEM', {safe_err})")

    def _get_uptime_strings(self):
        os_sec = max(0, int(time.time() - psutil.boot_time()))
        os_str = f"{os_sec // 3600:02d}:{(os_sec % 3600) // 60:02d}:{os_sec % 60:02d}"
        sess_sec = max(0, int(time.time() - getattr(self, 'session_start', time.time())))
        sess_str = f"{sess_sec // 3600:02d}:{(sess_sec % 3600) // 60:02d}:{sess_sec % 60:02d}"
        return os_str, sess_str

    def push_stats_once(self):
        try:
            cpu = int(psutil.cpu_percent(interval=0.2))
            mem = psutil.virtual_memory()
            ram = int(mem.percent)
            ram_used_gb = mem.used / (1024 ** 3)
            ram_total_gb = mem.total / (1024 ** 3)
            ram_str = f"{ram_used_gb:.1f}/{ram_total_gb:.0f} GB ({ram}%)"

            disk = psutil.disk_usage(os.path.abspath(os.sep))
            disk_used_gb = int(disk.used / (1024 ** 3))
            disk_total_gb = int(disk.total / (1024 ** 3))
            disk_str = f"{disk_used_gb}/{disk_total_gb} GB"
            os_str, sess_str = self._get_uptime_strings()

            self.window.evaluate_js(
                f"updateSystemStats({cpu}, {ram}, '{ram_str}', '{disk_str}', {self.session_count}, {self.command_count}, '{os_str}', '{sess_str}')"
            )
        except Exception:
            pass

    def run_network_diagnostics(self):
        try:
            self.increment_command_count()
            self.window.evaluate_js("addLog('SYSTEM', 'Running network diagnostics & latency check...')")
            loc = requests.get('http://ip-api.com/json/', timeout=4).json()
            ip = loc.get('query', 'Unknown')
            isp = loc.get('isp', 'Unknown ISP')
            city = loc.get('city', 'Unknown')
            out = subprocess.check_output("ping -n 1 8.8.8.8", shell=True, text=True, timeout=4)
            ping_ms = "12ms"
            for token in out.split():
                if "time=" in token.lower() or "time<" in token.lower():
                    ping_ms = token.split("=")[-1].split("<")[-1]
                    break
            report = f"Network Online | IP: {ip} ({isp}, {city}) | Latency: {ping_ms}"
            safe_rep = json.dumps(report)
            self.window.evaluate_js(f"addLog('SYSTEM', {safe_rep})")
        except Exception as e:
            safe_err = json.dumps(f"Network check failed: {str(e).splitlines()[0][:100]}")
            self.window.evaluate_js(f"addLog('SYSTEM', {safe_err})")

    def telemetry_worker(self):
        time.sleep(1.0)
        self.fetch_weather()
        last_net = psutil.net_io_counters().bytes_recv + psutil.net_io_counters().bytes_sent
        ticks = 0
        while self.running:
            try:
                cpu = int(psutil.cpu_percent(interval=1))
                mem = psutil.virtual_memory()
                ram = int(mem.percent)
                ram_used_gb = mem.used / (1024 ** 3)
                ram_total_gb = mem.total / (1024 ** 3)
                ram_str = f"{ram_used_gb:.1f}/{ram_total_gb:.0f} GB ({ram}%)"

                disk = psutil.disk_usage(os.path.abspath(os.sep))
                disk_used_gb = int(disk.used / (1024 ** 3))
                disk_total_gb = int(disk.total / (1024 ** 3))
                disk_str = f"{disk_used_gb}/{disk_total_gb} GB"

                curr_net = psutil.net_io_counters().bytes_recv + psutil.net_io_counters().bytes_sent
                speed_mbps = (curr_net - last_net) / (1024 * 1024)
                last_net = curr_net
                os_str, sess_str = self._get_uptime_strings()
                
                self.window.evaluate_js(
                    f"updateSystemStats({cpu}, {ram}, '{ram_str}', '{disk_str}', {self.session_count}, {self.command_count}, '{os_str}', '{sess_str}')"
                )
                self.window.evaluate_js(f"updateNetwork('{speed_mbps:.2f} MB/s')")

                ticks += 1
                if ticks % 300 == 0:
                    threading.Thread(target=self.fetch_weather, daemon=True).start()
            except Exception:
                pass
            time.sleep(1)

    def stt_worker(self):
        """Bilingual Speech Recognition (English & Hindi/Hinglish) with Voice Barge-In Kill Support"""
        recognizer = sr.Recognizer()
        
        with sr.Microphone() as source:
            recognizer.adjust_for_ambient_noise(source, duration=1.0)
            self.window.evaluate_js("updateState('ONLINE')")
            
            while self.running:
                was_speaking = bool(pygame.mixer.get_init() and pygame.mixer.get_busy())
                if not was_speaking:
                    self.window.evaluate_js("updateState('LISTENING')")
                try:
                    p_limit = 3 if was_speaking else 9
                    audio = recognizer.listen(source, timeout=2 if was_speaking else 3, phrase_time_limit=p_limit)
                    if not was_speaking:
                        self.window.evaluate_js("updateState('PROCESSING')")
                    # 'en-IN' seamlessly recognizes both Indian English and common Hinglish phrases
                    text = recognizer.recognize_google(audio, language="en-IN").lower()
                    
                    if text:
                        cmd = text
                        for w in ["jarvis", "friday", "system"]:
                            cmd = cmd.replace(w, "")
                        cmd = cmd.strip()

                        # Instant Pre-emptive Kill / Stop Check (works even during active speech or slow tool runs)
                        if self.is_kill_command(cmd, strict_barge_in=was_speaking) or self.is_kill_command(text, strict_barge_in=was_speaking):
                            self.last_active = time.time()
                            safe_cmd = json.dumps(cmd or text)
                            self.window.evaluate_js(f"addLog('USER', {safe_cmd})")
                            self.abort_current_command(spoken_text=cmd or text)
                            continue

                        # Ignore speaker bleed when TTS is actively playing unless it was a kill command above
                        if was_speaking or (pygame.mixer.get_init() and pygame.mixer.get_busy()):
                            continue

                        wake_triggers = ["jarvis", "friday", "wake", "uth jao", "uth ja"]
                        
                        # Wake-Word handling in Sleep Mode without dropping follow-up commands
                        if getattr(self, "is_sleeping", False):
                            if any(w in text for w in wake_triggers):
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
                                self.is_sleeping = False
                            
                        self.last_active = time.time()
                        if cmd:
                            safe_cmd = json.dumps(cmd)
                            self.window.evaluate_js(f"addLog('USER', {safe_cmd})")
                            self.text_queue.put(cmd)
                except Exception:
                    pass

    def llm_worker(self):
        while self.running:
            try:
                text = self.text_queue.get()
                self.last_active = time.time()

                # Pre-emptive Kill / Stop check
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
                
                cmd_lower = text.lower()
                handled = False
                
                # Strict Persona Mode Switches (JARVIS & FRIDAY only)
                if "switch to friday" in cmd_lower or "friday mode" in cmd_lower:
                    self.voice_mode = 'FRIDAY'
                    self.window.evaluate_js("switchMode('FRIDAY')")
                    self.response_queue.put("Switching to F.R.I.D.A.Y. mode, boss. All systems red.")
                    handled = True
                elif "switch to jarvis" in cmd_lower or "jarvis mode" in cmd_lower:
                    self.voice_mode = 'JARVIS'
                    self.window.evaluate_js("switchMode('JARVIS')")
                    self.response_queue.put("Reverting to J.A.R.V.I.S. mode, sir. Back in blue.")
                    handled = True
                elif any(k in cmd_lower for k in ("show hud", "open hud", "restore hud", "full screen", "fullscreen", "maximize hud", "wapas aao", "hud dikhao")):
                    self.exit_orb_only_mode()
                    self.response_queue.put("Restoring full HUD interface, sir.")
                    handled = True
                elif any(k in cmd_lower for k in ("orb mode", "mini mode", "only orb", "hide hud")):
                    self.enter_orb_only_mode(sleep_mode=False)
                    self.response_queue.put("Switching to transparent Orb mode, sir.")
                    handled = True

                if handled:
                    self.text_queue.task_done()
                    continue

                # Run command execution in a non-blocking worker thread so kill/stop commands can pre-empt at any millisecond
                threading.Thread(
                    target=self._execute_command_pipeline,
                    args=(text, my_cmd_id),
                    daemon=True
                ).start()
                self.text_queue.task_done()
            except Exception as e:
                safe_err = json.dumps(f"Cognitive processing warning: {str(e).splitlines()[0][:120]}")
                try:
                    self.window.evaluate_js(f"addLog('SYSTEM', {safe_err})")
                except Exception:
                    pass

    def _execute_command_pipeline(self, text: str, my_cmd_id: int):
        """Execute a single command with continuous abort/kill checkpoints."""
        def is_aborted() -> bool:
            return self.abort_event.is_set() or (my_cmd_id != self.active_cmd_id)

        try:
            if is_aborted():
                return

            cmd_lower = text.lower()

            # Instant Pre-Processing Voice Acknowledgment (spoken immediately in parallel before LLM/Vision execution)
            ack_phrase = get_instant_ack(text, getattr(self, "voice_mode", "JARVIS"))
            self.response_queue.put(("ACK", ack_phrase))

            # Single-Pass Direct Vision Fast-Path (Mark-LV / Mark-XXXIX-OR Architecture: 1 API call instead of 2)
            is_cam_query = any(k in cmd_lower for k in (
                "camera", "webcam", "look at me", "who am i", "mera chehra",
                "holding", "in my hand", "haath mein", "show you"
            ))
            is_screen_query = any(k in cmd_lower for k in (
                "screen", "looking at", "what do you see", "read this", "analyze this",
                "this error", "this code", "on my display", "screen par", "kya dikh raha"
            ))
            is_action_cmd = any(k in cmd_lower for k in (
                "open ", "khol", "launch ", "start ", "play ", "volume", "brightness",
                "mute", "weather", "news", "remind", "search "
            ))
            if is_cam_query or is_screen_query or (getattr(self, "screen_vision_mode", False) and not is_action_cmd):
                angle = "camera" if is_cam_query else "screen"
                was_fullscreen = getattr(self, "is_fullscreen", False)
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

            # Pre-emptively enter Orb-Only Transparent Mode if command asks to open something
            if any(k in cmd_lower for k in ("open ", "khol", "launch ", "start ", "play ", "world news", "finance news", "financial market")):
                self.enter_orb_only_mode(sleep_mode=False)

            # Bilingual Spoken Persona + Long-Term Memory Injection (Mark-LV + Iris)
            lt_mem = MemoryModule.get_long_term_prompt()
            attached_file = self.tool_suite.ui.current_file
            file_ctx = f"\n[ATTACHED FILE READY FOR file_processor: {attached_file}]\n" if attached_file else ""

            system_prompt = (
                f"You are {self.voice_mode}, an advanced, loyal, and sharp personal AI assistant. "
                "LANGUAGE INSTRUCTION: "
                "You are 100% fluent in both English and Hindi / Hinglish. "
                "Always reply in the exact language the user speaks: "
                "- If the user speaks Hindi or Hinglish (e.g. 'WhatsApp khol do', 'kya haal hai boss', 'Starboy play kar do YouTube pe', 'volume badha do', 'left side pe Chrome set kar do', 'asman mein kitne planes hain'), "
                "reply in natural, warm, conversational Hindi / Hinglish (e.g. 'Ji boss, WhatsApp khol diya hai.', 'Bilkul sir, YouTube par play kar diya hai.'). "
                "- If the user speaks English, reply in sharp, natural English. "
                "CRITICAL SPOKEN RULES: "
                "1. Keep spoken responses short (2 to 4 sentences maximum). "
                "2. NEVER use markdown lists, asterisks, bullet points, or code formatting in spoken responses. Speak naturally. "
                "3. Call tools silently and immediately. Never recite raw function names. "
                "4. Address the user naturally as 'boss' or 'sir'. "
                "5. For playing YouTube videos or songs (even if Brave or Chrome is mentioned), ALWAYS call youtube_video(action='play', query='...') or open_website(url='...'). Never use execute_terminal to launch browsers or URLs.\n"
                f"{lt_mem}{file_ctx}"
            )

            messages = [{"role": "system", "content": system_prompt}]
            for role, msg in self.history[-6:]:
                messages.append({"role": "user" if role == "USER" else "assistant", "content": msg})
            messages.append({"role": "user", "content": text})

            tools = self.tool_suite.get_ollama_tools()

            msg_obj = IntelligenceModule.chat(messages, tools, self.window, abort_check=is_aborted)
            if is_aborted():
                return

            response = ""

            # Tool Routing & Execution across all 35+ tools
            if "tool_calls" in msg_obj and msg_obj["tool_calls"]:
                for tool in msg_obj["tool_calls"]:
                    if is_aborted():
                        return
                    t_name = tool["function"]["name"]
                    t_args = tool["function"]["arguments"] or {}

                    if t_name == "get_world_news":
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
                        app = t_args.get("app_name", "")
                        self.enter_orb_only_mode(sleep_mode=False)
                        response = launch_application(app)
                        break

                    elif t_name == "volume_control":
                        act = t_args.get("action", "")
                        response = volume_control(act)
                        break

                    elif t_name == "window_management":
                        act = t_args.get("action", "")
                        response = window_action(act)
                        break

                    elif t_name == "split_workspace":
                        l_app = t_args.get("left_app", "")
                        r_app = t_args.get("right_app", "")
                        self.enter_orb_only_mode(sleep_mode=False)
                        response = split_workspace(l_app, r_app)
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
                            import re
                            url_match = re.search(r"https?://[^\s\"']+", cmd_str)
                            if url_match:
                                target_url = url_match.group(0)
                                self.enter_orb_only_mode(sleep_mode=False)
                                if "youtube.com/results?search_query=" in target_url:
                                    q = target_url.split("search_query=", 1)[1].replace("+", " ")
                                    tool_res = self.tool_suite.execute("youtube_video", {"action": "play", "query": q})
                                    response = str(tool_res)[:350] if tool_res else f"Playing {q} on YouTube, sir."
                                else:
                                    webbrowser.open(target_url)
                                    response = f"Opened {target_url} in your browser, sir."
                            else:
                                if any(ps_kw in cmd_str for ps_kw in ("Start-Process", "Get-", "Set-", "Invoke-", "$")):
                                    proc = subprocess.Popen(
                                        ["powershell", "-NoProfile", "-Command", cmd_str],
                                        stdout=subprocess.PIPE,
                                        stderr=subprocess.STDOUT,
                                        text=True
                                    )
                                else:
                                    proc = subprocess.Popen(
                                        cmd_str,
                                        shell=True,
                                        stdout=subprocess.PIPE,
                                        stderr=subprocess.STDOUT,
                                        text=True
                                    )
                                self.active_subprocess = proc
                                out, _ = proc.communicate(timeout=10)
                                self.active_subprocess = None
                                if is_aborted():
                                    return
                                clean = (out or "").replace('\n', ' ').strip()[:220]
                                response = f"Execution completed, sir. {('Output: ' + clean) if clean else ''}".strip()
                        except Exception as e:
                            self.active_subprocess = None
                            if is_aborted():
                                return
                            response = f"Terminal execution failed: {e}"
                        break

                    else:
                        # Dispatch to UnifiedToolSuite (17 Mark-LV actions + Mark-XXXIX Agent + OpenSky Radar + Vision + Memory + Undo)
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

    def tts_worker(self):
        """Zero-Lock In-Memory Bilingual Neural TTS Engine with Instant Pre-Processing Ack & Abort Support"""
        while self.running:
            try:
                item = self.response_queue.get()
                if self.abort_event.is_set():
                    continue

                is_ack = False
                if isinstance(item, tuple) and len(item) == 2 and item[0] == "ACK":
                    is_ack = True
                    response = item[1]
                else:
                    response = str(item)

                self.window.evaluate_js("updateState('SPEAKING')")
                safe_resp = json.dumps(response)
                self.window.evaluate_js(f"addLog('JARVIS', {safe_resp})")
                
                # Bilingual Synthesis (Hindi/Hinglish: Indian Neural Madhur/Swara, English: Ryan/Sonia)
                mode = getattr(self, "voice_mode", "JARVIS")
                speak_text(response, mode=mode, cache_clip=is_ack)
                
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
                if hasattr(self, 'response_queue'):
                    self.response_queue.task_done()

class Api:
    def __init__(self, pipeline):
        self.pipeline = pipeline
    
    def send_command(self, text):
        self.pipeline.last_active = time.time()
        safe_text = json.dumps(text)
        self.pipeline.window.evaluate_js(f"addLog('USER', {safe_text})")
        if self.pipeline.is_kill_command(text):
            self.pipeline.abort_current_command(spoken_text=text)
            return
        self.pipeline.text_queue.put(text)

    def kill_command(self):
        """Emergency Stop / Kill button in HUD or Escape key handler."""
        self.pipeline.last_active = time.time()
        self.pipeline.abort_current_command(spoken_text="stop")
        
    def minimize(self):
        """Collapse HUD to the floating corner Orb without suspending WebView2."""
        if getattr(self.pipeline, "is_orb_only", False):
            self.pipeline.exit_orb_only_mode()
        else:
            self.pipeline.enter_orb_only_mode(sleep_mode=False)
        
    def toggle_fullscreen(self):
        if getattr(self.pipeline, "is_orb_only", False) or not getattr(self.pipeline, "is_fullscreen", True):
            self.pipeline.exit_orb_only_mode()
        else:
            self.pipeline.enter_orb_only_mode(sleep_mode=False)
        
    def destroy(self):
        self.pipeline.window.destroy()
        
    def force_weather_update(self):
        threading.Thread(target=self.pipeline.fetch_weather, daemon=True).start()

    def force_stats_update(self):
        threading.Thread(target=self.pipeline.push_stats_once, daemon=True).start()

    def network_diagnostics(self):
        threading.Thread(target=self.pipeline.run_network_diagnostics, daemon=True).start()

    def toggle_mute(self):
        try:
            if pygame.mixer.get_init():
                pygame.mixer.stop()
            volume_control("mute")
            self.pipeline.window.evaluate_js("addLog('SYSTEM', 'System audio mute toggled.')")
        except Exception:
            pass

    def pick_file(self):
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

    def scan_airspace(self):
        """Run immediate 200km OpenSky aircraft radar scan."""
        self.pipeline.abort_event.clear()
        TTS_ABORT_EVENT.clear()
        self.pipeline.active_cmd_id += 1
        my_id = self.pipeline.active_cmd_id
        self.pipeline.increment_command_count()
        self.pipeline.response_queue.put(("ACK", "On it, sir. Scanning 200 kilometer airspace radar."))
        def _run():
            res = self.pipeline.tool_suite.execute("aircraft_report", {"action": "report", "radius_km": 200})
            if not self.pipeline.abort_event.is_set() and my_id == self.pipeline.active_cmd_id:
                self.pipeline.response_queue.put(res)
        threading.Thread(target=_run, daemon=True).start()

    def undo_last_action(self):
        """Revert the most recent file, desktop, or setting change."""
        self.pipeline.abort_event.clear()
        TTS_ABORT_EVENT.clear()
        self.pipeline.active_cmd_id += 1
        my_id = self.pipeline.active_cmd_id
        self.pipeline.increment_command_count()
        self.pipeline.response_queue.put(("ACK", "Working on it, sir. Reverting last action."))
        def _run():
            res = self.pipeline.tool_suite.execute("undo", {"action": "undo"})
            if not self.pipeline.abort_event.is_set() and my_id == self.pipeline.active_cmd_id:
                self.pipeline.response_queue.put(res)
        threading.Thread(target=_run, daemon=True).start()

    def show_memory_vault(self):
        """Display stored long-term memories in the HUD conversation log."""
        self.pipeline.increment_command_count()
        try:
            from memory.memory_manager import all_entries_for_ui
            entries = all_entries_for_ui()
            if not entries:
                self.pipeline.window.evaluate_js("addLog('SYSTEM', 'Memory Vault is currently empty. Tell me facts to remember!')")
            else:
                summary = " | ".join([f"{e['category']}.{e['key']}: {e['value']}" for e in entries[:10]])
                safe = json.dumps(f"Memory Vault ({len(entries)} entries): {summary}")
                self.pipeline.window.evaluate_js(f"addLog('SYSTEM', {safe})")
        except Exception as e:
            safe_err = json.dumps(f"Memory Vault error: {str(e).splitlines()[0][:100]}")
            self.pipeline.window.evaluate_js(f"addLog('SYSTEM', {safe_err})")

    def trigger_screen_vision(self):
        """Instant 1-pass Screen Vision Mode: collapses HUD to corner Orb, captures screen in 15ms, and analyzes directly."""
        self.pipeline.last_active = time.time()
        self.pipeline.abort_event.clear()
        TTS_ABORT_EVENT.clear()
        self.pipeline.active_cmd_id += 1
        my_id = self.pipeline.active_cmd_id
        self.pipeline.increment_command_count()
        self.pipeline.response_queue.put(("ACK", "On it, sir. Scanning your display."))
        self.pipeline.enter_orb_only_mode(sleep_mode=False, vision_mode=True)
        def _run():
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

    def analyze_camera_frame(self, data_url: str, prompt: str = "Analyze what I am holding or showing to the camera and describe what you see."):
        """Instant 1-pass Camera Vision using the live WebView2 webcam frame (zero OpenCV camera lock conflict)."""
        self.pipeline.last_active = time.time()
        self.pipeline.abort_event.clear()
        TTS_ABORT_EVENT.clear()
        self.pipeline.active_cmd_id += 1
        my_id = self.pipeline.active_cmd_id
        self.pipeline.increment_command_count()
        self.pipeline.response_queue.put(("ACK", "Working on it, sir. Analyzing camera feed."))
        def _run():
            try:
                import base64
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

    def save_camera_snapshot(self, data_url: str):
        """Save a high-resolution snapshot from the live HUD webcam to Desktop/JARVIS_Snapshots."""
        self.pipeline.last_active = time.time()
        self.pipeline.increment_command_count()
        def _run():
            try:
                import base64
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

    def gesture_action(self, action: str):
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
            if getattr(self.pipeline, "is_muted", False):
                self.toggle_mute()
            self.pipeline.window.evaluate_js("focusInput()")
            self.pipeline.window.evaluate_js("addLog('SYSTEM', '[GESTURE ◈] Open Palm: Audio & Command Input Ready.')")

    def enter_mini(self):
        self.pipeline.enter_orb_only_mode(sleep_mode=False)
        
    def exit_mini(self):
        self.pipeline.exit_orb_only_mode()

if __name__ == '__main__':
    html_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'hud.html')
    sw, sh = 1920, 1080
    if os.name == 'nt':
        try:
            import ctypes
            sw = ctypes.windll.user32.GetSystemMetrics(0)
            sh = ctypes.windll.user32.GetSystemMetrics(1)
        except Exception:
            pass
    window = webview.create_window(
        'JARVIS Master',
        html_path,
        x=0,
        y=0,
        width=sw,
        height=sh,
        transparent=True,
        frameless=True,
        fullscreen=False,
        on_top=True
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
        api.pick_file,
        api.scan_airspace,
        api.undo_last_action,
        api.show_memory_vault,
        api.trigger_screen_vision,
        api.analyze_camera_frame,
        api.save_camera_snapshot,
        api.gesture_action,
        api.enter_mini,
        api.exit_mini
    )
    
    threading.Timer(2.0, pipeline.start_services).start()
    webview.start()

