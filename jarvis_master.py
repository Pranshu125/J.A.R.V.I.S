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

# Global Process Patch (Mark-LV Architecture): Suppress background console flashing
if os.name == 'nt':
    _orig_popen = subprocess.Popen
    def _silent_popen(*args, **kwargs):
        if 'creationflags' not in kwargs:
            kwargs['creationflags'] = subprocess.CREATE_NO_WINDOW
        return _orig_popen(*args, **kwargs)
    subprocess.Popen = _silent_popen

# Modular capabilities ported from Sagar's Friday, Mark-LV, Mark-XXXIX, and Zoey 3D HUD
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

# ========================================================
# J.A.R.V.I.S. & F.R.I.D.A.Y. UNIFIED COGNITIVE OS
# Real-Time Voice Assistant with 3D Holographic Orb,
# Deep Windows OS Control, World Intel & Bilingual Intelligence
# ========================================================

OLLAMA_URL = "http://localhost:11434/api/chat"
OLLAMA_MODEL = "llama3.2" 
MEMORY_DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "jarvis_state.md")

class MemoryModule:
    """Persistent Conversational Memory Vault (Zoey & Mark-LV style)"""
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

class IntelligenceModule:
    """Hybrid Cognitive Engine: Cloud Gemini 2.5 Flash + Local Ollama Fallback"""
    @staticmethod
    def chat(messages, tools, window):
        # 1. Cloud Fast Mode if GEMINI_API_KEY is present
        api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        if api_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel('gemini-2.5-flash')
                last_user_prompt = messages[-1]["content"] if messages else "Hello"
                res = model.generate_content(last_user_prompt)
                return {"role": "assistant", "content": res.text}
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
        
        # Dynamic Time-of-Day Bilingual Boot Greeting
        hour = time.localtime().tm_hour
        mode_name = getattr(self, "voice_mode", "JARVIS")
        if hour < 12:
            g = [
                "Good morning, sir. Core systems are online.",
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
            if not getattr(self, "is_sleeping", False) and time.time() - self.last_active > 45:
                self.is_sleeping = True
                self.window.evaluate_js("toggleMiniMode(true)")
                self.window.resize(400, 400)
            time.sleep(2)
            
    def fetch_weather(self):
        try:
            loc = requests.get('http://ip-api.com/json/', timeout=4).json()
            city = loc.get('city', 'Unknown')
            lat, lon = loc.get('lat'), loc.get('lon')
            if lat and lon:
                w_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,relative_humidity_2m,wind_speed_10m,weather_code"
                w_data = requests.get(w_url, timeout=4).json()['current']
                t, h, w = w_data['temperature_2m'], w_data['relative_humidity_2m'], w_data['wind_speed_10m']
                desc = "Clear" if w_data['weather_code'] < 3 else "Cloudy" if w_data['weather_code'] < 50 else "Rain"
                self.window.evaluate_js(f"updateWeather('{t}°C', '{city}', '{desc}', '{h}%', '{w} km/h')")
                self.window.evaluate_js(f"addLog('SYSTEM', 'Weather synchronized with satellite telemetry.')")
        except Exception as e:
            self.window.evaluate_js(f"addLog('SYSTEM', 'Weather telemetry error: {e}')")

    def telemetry_worker(self):
        self.fetch_weather()
        last_net = psutil.net_io_counters().bytes_recv + psutil.net_io_counters().bytes_sent
        while self.running:
            try:
                cpu = int(psutil.cpu_percent(interval=1))
                ram = int(psutil.virtual_memory().percent)
                curr_net = psutil.net_io_counters().bytes_recv + psutil.net_io_counters().bytes_sent
                speed_mbps = (curr_net - last_net) / (1024 * 1024)
                last_net = curr_net
                
                self.window.evaluate_js(f"updateSystemStats({cpu}, {ram})")
                self.window.evaluate_js(f"updateNetwork('{speed_mbps:.2f} MB/s')")
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
                        mode_name = getattr(self, "voice_mode", "JARVIS").lower()
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

                # Bilingual Spoken Persona (Ported from Iris & Mark-LV)
                system_prompt = (
                    f"You are {self.voice_mode}, an advanced, loyal, and sharp personal AI assistant. "
                    "LANGUAGE INSTRUCTION: "
                    "You are 100% fluent in both English and Hindi / Hinglish. "
                    "Always reply in the exact language the user speaks: "
                    "- If the user speaks Hindi or Hinglish (e.g. 'WhatsApp khol do', 'kya haal hai boss', 'Starboy play kar do YouTube pe', 'volume badha do', 'left side pe Chrome set kar do'), "
                    "reply in natural, warm, conversational Hindi / Hinglish (e.g. 'Ji boss, WhatsApp khol raha hoon.', 'Bilkul sir, YouTube par play kar diya hai.'). "
                    "- If the user speaks English, reply in sharp, natural English. "
                    "CRITICAL SPOKEN RULES: "
                    "1. Keep spoken responses short (2 to 4 sentences maximum). "
                    "2. NEVER use markdown lists, asterisks, bullet points, or code formatting in spoken responses. Speak naturally. "
                    "3. Call tools silently and immediately. Never recite raw function names. "
                    "4. Address the user naturally as 'boss' or 'sir'."
                )

                messages = [{"role": "system", "content": system_prompt}]
                for role, msg in self.history[-6:]:
                    messages.append({"role": "user" if role == "USER" else "assistant", "content": msg})
                messages.append({"role": "user", "content": text})

                tools = [
                    {
                        "type": "function",
                        "function": {
                            "name": "get_world_news",
                            "description": "Fetch live breaking world news headlines from major international wire services.",
                            "parameters": {"type": "object", "properties": {}}
                        }
                    },
                    {
                        "type": "function",
                        "function": {
                            "name": "get_finance_news",
                            "description": "Fetch current market and financial news headlines from global market feeds.",
                            "parameters": {"type": "object", "properties": {}}
                        }
                    },
                    {
                        "type": "function",
                        "function": {
                            "name": "open_world_monitor",
                            "description": "Open the live visual satellite World Monitor dashboard on screen.",
                            "parameters": {"type": "object", "properties": {}}
                        }
                    },
                    {
                        "type": "function",
                        "function": {
                            "name": "open_finance_monitor",
                            "description": "Open the live visual financial markets dashboard on screen.",
                            "parameters": {"type": "object", "properties": {}}
                        }
                    },
                    {
                        "type": "function",
                        "function": {
                            "name": "system_hardware_control",
                            "description": "Control laptop audio volume, mute, brightness, or launch applications.",
                            "parameters": {
                                "type": "object",
                                "properties": {
                                    "action": {"type": "string", "enum": ["volume_up", "volume_down", "mute", "brightness_up", "brightness_down", "launch_app"]},
                                    "app_name": {"type": "string", "description": "Application name to open (e.g. chrome, vscode, notepad, spotify, steam, calc, whatsapp)."}
                                },
                                "required": ["action"]
                            }
                        }
                    },
                    {
                        "type": "function",
                        "function": {
                            "name": "window_management",
                            "description": "Manage desktop windows (minimize, maximize, snap left/right, show desktop, lock screen).",
                            "parameters": {
                                "type": "object",
                                "properties": {
                                    "action": {"type": "string", "enum": ["minimize", "maximize", "snap_left", "snap_right", "show_desktop", "lock_screen", "screenshot", "task_manager"]}
                                },
                                "required": ["action"]
                            }
                        }
                    },
                    {
                        "type": "function",
                        "function": {
                            "name": "split_workspace",
                            "description": "Split screen between two applications: snaps the first application to the left tile and the second application to the right tile (e.g. WhatsApp left, Chrome right).",
                            "parameters": {
                                "type": "object",
                                "properties": {
                                    "left_app": {"type": "string", "description": "Application name to snap on the left side (e.g. whatsapp, code, spotify)."},
                                    "right_app": {"type": "string", "description": "Application name to snap on the right side (e.g. chrome, edge, terminal)."}
                                },
                                "required": ["left_app", "right_app"]
                            }
                        }
                    },
                    {
                        "type": "function",
                        "function": {
                            "name": "open_website",
                            "description": "Open any website, YouTube song/video, or web search in the browser.",
                            "parameters": {
                                "type": "object",
                                "properties": {
                                    "url": {"type": "string", "description": "The exact URL or YouTube video search to open."}
                                },
                                "required": ["url"]
                            }
                        }
                    },
                    {
                        "type": "function",
                        "function": {
                            "name": "execute_terminal",
                            "description": "Execute a shell or PowerShell command on the machine.",
                            "parameters": {
                                "type": "object",
                                "properties": {
                                    "command": {"type": "string", "description": "Command line string to execute."}
                                },
                                "required": ["command"]
                            }
                        }
                    },
                    {
                        "type": "function",
                        "function": {
                            "name": "analyze_screen",
                            "description": "Take a silent screenshot and inspect what the user is reading or viewing on screen.",
                            "parameters": {
                                "type": "object",
                                "properties": {
                                    "query": {"type": "string", "description": "Visual query description."}
                                },
                                "required": ["query"]
                            }
                        }
                    }
                ]

                msg_obj = IntelligenceModule.chat(messages, tools, self.window)
                response = ""
                
                # Context-aware Instant Acknowledgments
                if "khol" in cmd_lower or "chala" in cmd_lower or "kar" in cmd_lower:
                    ack = random.choice(["Ji boss.", "Bilkul sir.", "Abhi karta hoon, sir.", "Hukum sir."])
                else:
                    ack = random.choice(["Right away, sir.", "At your service, sir.", "Processing, sir.", "On it, boss."])

                # Tool Routing & Execution
                if "tool_calls" in msg_obj and msg_obj["tool_calls"]:
                    for tool in msg_obj["tool_calls"]:
                        t_name = tool["function"]["name"]
                        t_args = tool["function"]["arguments"]

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
                                self.is_sleeping = True
                                self.window.evaluate_js("toggleMiniMode(true)")
                                self.window.resize(400, 400)
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
                            url = t_args.get("url")
                            webbrowser.open(url)
                            response = f"{ack} Opening {url}."
                            self.is_sleeping = True
                            self.window.evaluate_js("toggleMiniMode(true)")
                            self.window.resize(400, 400)
                            break

                        elif t_name == "execute_terminal":
                            cmd_str = t_args.get("command")
                            try:
                                out = subprocess.check_output(cmd_str, shell=True, text=True, stderr=subprocess.STDOUT, timeout=8)
                                clean = out.replace('\n', ' ')[:180]
                                response = f"Execution completed, sir. Output: {clean}"
                            except Exception as e:
                                response = f"Terminal execution failed: {e}"
                            break

                        elif t_name == "analyze_screen":
                            q = t_args.get("query", "Describe this display.")
                            try:
                                import pyautogui, base64
                                pyautogui.screenshot("vision_cache.png")
                                with open("vision_cache.png", "rb") as img:
                                    b64 = base64.b64encode(img.read()).decode('utf-8')
                                payload = {
                                    "model": "moondream",
                                    "prompt": q,
                                    "images": [b64],
                                    "stream": False
                                }
                                res = requests.post("http://localhost:11434/api/generate", json=payload, timeout=30).json()
                                vis_text = res.get('response', '')
                                response = f"Looking at your display now, sir. {vis_text}"
                            except Exception:
                                response = "Vision sensors are processing slowly. Please verify moondream is ready."
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
        api.enter_mini,
        api.exit_mini
    )
    
    threading.Timer(2.0, pipeline.start_services).start()
    webview.start()
