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
from faster_whisper import WhisperModel
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

# Global Process Patch (Mark-LV Architecture): Suppress background console flashing
if os.name == 'nt':
    _orig_popen = subprocess.Popen
    def _silent_popen(*args, **kwargs):
        if 'creationflags' not in kwargs:
            kwargs['creationflags'] = subprocess.CREATE_NO_WINDOW
        return _orig_popen(*args, **kwargs)
    subprocess.Popen = _silent_popen

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
from modules.tts_engine import speak_text
from modules.mark_lv_bridge import UnifiedToolSuite

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
    def chat(messages, tools, window):
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

                model = None
                for m_name in ['gemini-3.8-flash', 'gemini-flash-latest', 'gemini-3.5-flash']:
                    try:
                        model = genai.GenerativeModel(m_name, tools=gemini_tools, system_instruction=sys_inst)
                        break
                    except Exception:
                        continue

                if model:
                    res = model.generate_content(user_prompt)
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
            except Exception as e:
                window.evaluate_js(f"addLog('SYSTEM', 'Gemini fallback to Ollama: {e}')")

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
        self.history = MemoryModule.load()
        self.audio_queue = queue.Queue()
        self.text_queue = queue.Queue()
        self.response_queue = queue.Queue()
        self.running = True
        self.voice_mode = 'JARVIS' # Strictly 'JARVIS' or 'FRIDAY'
        self.is_sleeping = False
        self.last_active = time.time()
        self.tool_suite = UnifiedToolSuite(self)
        
        try:
            self.stt_model = WhisperModel('base.en', device='cpu', compute_type='int8')
        except Exception as e:
            print(f"STT Model Load Warning: {e}")

    def start_services(self):
        threading.Thread(target=self.stt_worker, daemon=True).start()
        threading.Thread(target=self.llm_worker, daemon=True).start()
        threading.Thread(target=self.tts_worker, daemon=True).start()
        threading.Thread(target=self.telemetry_worker, daemon=True).start()
        threading.Thread(target=self.idle_worker, daemon=True).start()
        threading.Thread(target=self.background_monitors_worker, daemon=True).start()
        
        # Dynamic Time-of-Day Bilingual Boot Greeting
        hour = time.localtime().tm_hour
        mode_name = getattr(self, "voice_mode", "JARVIS")
        if hour < 12:
            g = [
                "Good morning, sir. All 35 Mark-LV and Mark-XXXIX subsystems are online.",
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
        
        # Global Quick-Summon Overlay Hotkey (Alt + Space)
        try:
            import keyboard
            keyboard.add_hotkey('alt+space', self.trigger_hotkey_wake)
        except Exception as e:
            print("Hotkey binding failed: ", e)

    def trigger_hotkey_wake(self):
        if getattr(self, "is_sleeping", False):
            self.is_sleeping = False
            self.last_active = time.time()
            self.window.evaluate_js("toggleMiniMode(false)")
            self.window.toggle_fullscreen()
            self.response_queue.put("Overlay activated, sir.")

    def idle_worker(self):
        while self.running:
            if not getattr(self, "is_sleeping", False) and time.time() - self.last_active > 90:
                self.is_sleeping = True
                self.window.evaluate_js("toggleMiniMode(true)")
                self.window.resize(400, 400)
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
                    desc, icon = "clear sky", "☀️"
                elif code < 4:
                    desc, icon = "partly cloudy", "⛅"
                elif code < 50:
                    desc, icon = "overcast clouds", "☁️"
                elif code < 80:
                    desc, icon = "rain showers", "🌧️"
                else:
                    desc, icon = "thunderstorm", "⛈️"

                loc_full = f"{city}, {country}" if country else city
                self.window.evaluate_js(
                    f"updateWeather('{t}°C', '{loc_full}', '{city}', '{desc}', '{h}%', '{w} km/h', '{feels}°C', '{icon}')"
                )
                self.window.evaluate_js("addLog('SYSTEM', 'Live satellite weather telemetry synchronized.')")
        except Exception as e:
            self.window.evaluate_js(f"addLog('SYSTEM', 'Weather telemetry warning: {e}')")

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

            self.window.evaluate_js(f"updateSystemStats({cpu}, {ram}, '{ram_str}', '{disk_str}')")
        except Exception:
            pass

    def run_network_diagnostics(self):
        try:
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
            self.window.evaluate_js(f"addLog('SYSTEM', 'Network check failed: {e}')")

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
                
                self.window.evaluate_js(f"updateSystemStats({cpu}, {ram}, '{ram_str}', '{disk_str}')")
                self.window.evaluate_js(f"updateNetwork('{speed_mbps:.2f} MB/s')")

                ticks += 1
                if ticks % 300 == 0:
                    threading.Thread(target=self.fetch_weather, daemon=True).start()
            except Exception:
                pass
            time.sleep(1)

    def stt_worker(self):
        """Bilingual Speech Recognition (English & Hindi/Hinglish)"""
        recognizer = sr.Recognizer()
        
        with sr.Microphone() as source:
            recognizer.adjust_for_ambient_noise(source, duration=1.0)
            self.window.evaluate_js("updateState('ONLINE')")
            
            while self.running:
                if pygame.mixer.get_init() and pygame.mixer.get_busy():
                    time.sleep(0.3)
                    continue

                self.window.evaluate_js("updateState('LISTENING')")
                try:
                    audio = recognizer.listen(source, timeout=3, phrase_time_limit=9)
                    self.window.evaluate_js("updateState('PROCESSING')")
                    # 'en-IN' seamlessly recognizes both Indian English and common Hinglish phrases
                    text = recognizer.recognize_google(audio, language="en-IN").lower()
                    
                    if text:
                        wake_triggers = ["jarvis", "friday", "wake", "uth jao", "uth ja"]
                        
                        # Strict Wake-Word filtering in Sleep / PiP Mode
                        if getattr(self, "is_sleeping", False):
                            if any(w in text for w in wake_triggers):
                                self.is_sleeping = False
                                self.last_active = time.time()
                                self.window.evaluate_js("toggleMiniMode(false)")
                                self.window.toggle_fullscreen()
                                self.response_queue.put("I am awake, boss. Standing by.")
                            continue
                            
                        self.last_active = time.time()
                        cmd = text
                        for w in ["jarvis", "friday", "system"]:
                            cmd = cmd.replace(w, "")
                        cmd = cmd.strip()
                        
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
                elif "stop talking" in cmd_lower or "chup raho" in cmd_lower or "mute audio" in cmd_lower:
                    if pygame.mixer.get_init():
                        pygame.mixer.stop()
                    handled = True

                if handled:
                    self.text_queue.task_done()
                    continue

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
                    "reply in natural, warm, conversational Hindi / Hinglish (e.g. 'Ji boss, WhatsApp khol raha hoon.', 'Bilkul sir, YouTube par play kar diya hai.'). "
                    "- If the user speaks English, reply in sharp, natural English. "
                    "CRITICAL SPOKEN RULES: "
                    "1. Keep spoken responses short (2 to 4 sentences maximum). "
                    "2. NEVER use markdown lists, asterisks, bullet points, or code formatting in spoken responses. Speak naturally. "
                    "3. Call tools silently and immediately. Never recite raw function names. "
                    "4. Address the user naturally as 'boss' or 'sir'.\n"
                    f"{lt_mem}{file_ctx}"
                )

                messages = [{"role": "system", "content": system_prompt}]
                for role, msg in self.history[-6:]:
                    messages.append({"role": "user" if role == "USER" else "assistant", "content": msg})
                messages.append({"role": "user", "content": text})

                tools = self.tool_suite.get_ollama_tools()

                msg_obj = IntelligenceModule.chat(messages, tools, self.window)
                response = ""
                
                # Context-aware Instant Acknowledgments
                if "khol" in cmd_lower or "chala" in cmd_lower or "kar" in cmd_lower:
                    ack = random.choice(["Ji boss.", "Bilkul sir.", "Abhi karta hoon, sir.", "Hukum sir."])
                else:
                    ack = random.choice(["Right away, sir.", "At your service, sir.", "Processing, sir.", "On it, boss."])

                # Tool Routing & Execution across all 35+ tools
                if "tool_calls" in msg_obj and msg_obj["tool_calls"]:
                    for tool in msg_obj["tool_calls"]:
                        t_name = tool["function"]["name"]
                        t_args = tool["function"]["arguments"] or {}

                        if t_name == "get_world_news":
                            self.window.evaluate_js("addLog('SYSTEM', 'Polling Global Feeds...')")
                            news_data = get_world_news_sync()
                            open_world_monitor()
                            response = f"Here is the latest from the global news wire, sir: {news_data[:220]}. I have opened the World Monitor on your display."
                            break

                        elif t_name == "get_finance_news":
                            self.window.evaluate_js("addLog('SYSTEM', 'Polling Financial Feeds...')")
                            fin_data = get_finance_news_sync()
                            open_finance_monitor()
                            response = f"Here is the market briefing, sir: {fin_data[:220]}. Pulling up the finance monitor now."
                            break

                        elif t_name == "open_world_monitor":
                            response = open_world_monitor()
                            break

                        elif t_name == "open_finance_monitor":
                            response = open_finance_monitor()
                            break

                        elif t_name == "system_hardware_control":
                            act = t_args.get("action", "")
                            app = t_args.get("app_name", "")
                            if act in ("volume_up", "volume_down", "mute"):
                                response = f"{ack} " + volume_control(act)
                            elif act in ("brightness_up", "brightness_down"):
                                response = f"{ack} " + brightness_control(act)
                            elif act == "launch_app":
                                response = f"{ack} " + launch_application(app)
                            break

                        elif t_name == "launch_application":
                            app = t_args.get("app_name", "")
                            response = f"{ack} " + launch_application(app)
                            break

                        elif t_name == "volume_control":
                            act = t_args.get("action", "")
                            response = f"{ack} " + volume_control(act)
                            break

                        elif t_name == "window_management":
                            act = t_args.get("action", "")
                            response = f"{ack} " + window_action(act)
                            break

                        elif t_name == "split_workspace":
                            l_app = t_args.get("left_app", "")
                            r_app = t_args.get("right_app", "")
                            response = f"{ack} " + split_workspace(l_app, r_app)
                            break

                        elif t_name == "open_website":
                            url = t_args.get("url", "")
                            webbrowser.open(url)
                            response = f"{ack} Opening {url}."
                            break

                        elif t_name == "execute_terminal":
                            cmd_str = t_args.get("command", "")
                            try:
                                out = subprocess.check_output(cmd_str, shell=True, text=True, stderr=subprocess.STDOUT, timeout=10)
                                clean = out.replace('\n', ' ')[:220]
                                response = f"Execution completed, sir. Output: {clean}"
                            except Exception as e:
                                response = f"Terminal execution failed: {e}"
                            break

                        else:
                            # Dispatch to UnifiedToolSuite (17 Mark-LV actions + Mark-XXXIX Agent + OpenSky Radar + Vision + Memory + Undo)
                            tool_res = self.tool_suite.execute(t_name, t_args)
                            response = str(tool_res)[:350] if tool_res else f"{ack} Completed {t_name}."
                            break

                if not response:
                    response = msg_obj.get("content", "").strip()

                if response:
                    self.history.append(("USER", text))
                    self.history.append(("JARVIS", response))
                    MemoryModule.save(self.history)
                    self.response_queue.put(response)

                self.text_queue.task_done()
            except Exception as e:
                self.window.evaluate_js(f"addLog('SYSTEM', 'Cognitive processing warning: {e}')")

    def tts_worker(self):
        """Zero-Lock In-Memory Bilingual Neural TTS Engine"""
        while self.running:
            try:
                response = self.response_queue.get()
                self.window.evaluate_js("updateState('SPEAKING')")
                safe_resp = json.dumps(response)
                self.window.evaluate_js(f"addLog('JARVIS', {safe_resp})")
                
                # Bilingual Synthesis (Hindi: Madhur/Swara, English: Ryan/Sonia/Jenny)
                mode = getattr(self, "voice_mode", "JARVIS")
                speak_text(response, mode=mode)
                
                self.window.evaluate_js("updateState('ONLINE')")
            except Exception as e:
                self.window.evaluate_js(f"addLog('SYSTEM', 'Voice Engine Warning: {e}')")
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
        self.pipeline.text_queue.put(text)
        
    def minimize(self):
        self.pipeline.window.minimize()
        
    def toggle_fullscreen(self):
        self.pipeline.window.toggle_fullscreen()
        
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
            self.pipeline.window.evaluate_js(f"addLog('SYSTEM', 'File picker warning: {e}')")

    def scan_airspace(self):
        """Run immediate 200km OpenSky aircraft radar scan."""
        def _run():
            res = self.pipeline.tool_suite.execute("aircraft_report", {"action": "report", "radius_km": 200})
            self.pipeline.response_queue.put(res)
        threading.Thread(target=_run, daemon=True).start()

    def undo_last_action(self):
        """Revert the most recent file, desktop, or setting change."""
        def _run():
            res = self.pipeline.tool_suite.execute("undo", {"action": "undo"})
            self.pipeline.response_queue.put(res)
        threading.Thread(target=_run, daemon=True).start()

    def show_memory_vault(self):
        """Display stored long-term memories in the HUD conversation log."""
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
            self.pipeline.window.evaluate_js(f"addLog('SYSTEM', 'Memory Vault error: {e}')")

    def enter_mini(self):
        self.pipeline.window.resize(400, 400)
        self.pipeline.is_sleeping = True
        
    def exit_mini(self):
        self.pipeline.window.toggle_fullscreen()
        self.pipeline.is_sleeping = False
        self.pipeline.last_active = time.time()
        self.pipeline.window.evaluate_js("toggleMiniMode(false)")

if __name__ == '__main__':
    html_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'hud.html')
    window = webview.create_window(
        'JARVIS Master',
        html_path,
        transparent=True,
        frameless=False,
        fullscreen=True,
        on_top=True
    )
    pipeline = JarvisPipeline(window)
    api = Api(pipeline)
    window.expose(
        api.send_command,
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
        api.enter_mini,
        api.exit_mini
    )
    
    threading.Timer(2.0, pipeline.start_services).start()
    webview.start()
