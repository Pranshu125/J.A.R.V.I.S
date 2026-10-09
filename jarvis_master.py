import threading
import asyncio
import queue
import time
import json
import os
import requests
import subprocess
import os
import webbrowser
import speech_recognition as sr
from faster_whisper import WhisperModel
import wave
from piper.voice import PiperVoice
import pygame
import psutil
import webview


import pyautogui

# ==========================================
# J.A.R.V.I.S. V2.0 THE ULTIMATE HYBRID
# Merging Our Core with Mark-XXXIX OS Control & Barehands Spatial Tech
# ==========================================

OLLAMA_URL = "http://localhost:11434/api/chat"
OLLAMA_MODEL = "llama3.2" 
VOICE_MODEL = "en-GB-RyanNeural"
MEMORY_DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "jarvis_state.md")

class MemoryModule:
    """Handles Long-Term State (fullstack-agent Markdown Vault style)"""
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
        except: pass

class ToolModule:
    """Deep OS Control (Ported from Mark-XXXIX-OR)"""
    @staticmethod
    def execute(command, window, pipeline):
        cmd = command.lower()
        
        # 1. Advanced Web Automation
        if "search for" in cmd or "google" in cmd:
            query = cmd.replace("search for", "").replace("google", "").strip()
            webbrowser.open(f"https://www.google.com/search?q={query}")
            window.evaluate_js(f"addLog('SYSTEM', 'Web Search: {query}')")
            return True, f"I have pulled up the search results for {query}, sir."
            
                elif "youtube" in cmd:
            query = cmd.replace("play", "").replace("open", "").replace("on youtube", "").replace("youtube", "").strip()
            if query:
                webbrowser.open(f"https://www.youtube.com/results?search_query={query}")
                return True, f"Searching YouTube for {query}."
            else:
                webbrowser.open("https://www.youtube.com")
                return True, "Opening YouTube."

        # 2. Keyboard & Screen Automation
        elif "type this" in cmd or "dictate" in cmd:
            text = cmd.replace("type this", "").replace("dictate", "").strip()
            pyautogui.write(text, interval=0.03)
            return True, "Dictation typed on screen."
            
        elif "take a screenshot" in cmd or "capture screen" in cmd:
            pyautogui.screenshot(os.path.join(os.path.dirname(__file__), "capture.png"))
            return True, "Screenshot saved."
            
        # 3. File & App Controller (Mark-XXXIX Port)
        elif "open notepad" in cmd:
            os.system("start notepad")
            return True, "Opening Notepad."
        elif "open calculator" in cmd:
            os.system("start calc")
            return True, "Opening Calculator."

        # 4. Core System Hooks
                elif "switch to friday" in cmd or "friday mode" in cmd:
            pipeline.voice_mode = 'FRIDAY'
            window.evaluate_js("switchMode('FRIDAY')")
            return True, "Switching to F.R.I.D.A.Y. mode, boss. All systems red."
            
        elif "minimize window" in cmd or "hide screen" in cmd:
            pipeline.window.minimize()
            return True, "Minimizing interface."
            
        elif "exit fullscreen" in cmd or "window mode" in cmd:
            pipeline.window.toggle_fullscreen()
            return True, "Toggling window mode."
            
        elif "switch to jarvis" in cmd or "jarvis mode" in cmd:
            pipeline.voice_mode = 'JARVIS'
            window.evaluate_js("switchMode('JARVIS')")
            return True, "Reverting to J.A.R.V.I.S. mode, sir. Back in blue."
            
        elif "morning brief" in cmd or "status report" in cmd:
            sys_time = time.strftime('%I:%M %p')
            cpu = psutil.cpu_percent()
            ram = psutil.virtual_memory().percent
            brief = (f"Good morning, sir. It is currently {sys_time}. "
                     f"System telemetry indicates CPU is at {cpu} percent, and memory at {ram} percent. "
                     "All core subsystems are online and your calendar is clear. What would you like to focus on today?")
            window.evaluate_js(f"addLog('SYSTEM', 'Generated Morning Brief')")
            return True, brief

        elif "lock system" in cmd:
            os.system("rundll32.exe user32.dll,LockWorkStation")
            return True, "Workstation locked."
            
        elif "time" in cmd or "what time" in cmd:
            return True, f"The current system time is {time.strftime('%I:%M %p')}."
            
        elif "stop" in cmd and ("talking" in cmd or "speaking" in cmd):
            if pygame.mixer.get_init(): pygame.mixer.music.stop()
            return True, "Audio playback canceled."
        
        return False, None

class IntelligenceModule:
    """Agentic LLM Engine with Tool Calling"""
    @staticmethod
    def chat(messages, tools, window):
        payload = {
            "model": OLLAMA_MODEL,
            "messages": messages,
            "stream": False,
            "tools": tools,
            "options": {"temperature": 0.7, "num_predict": 150}
        }
        try:
            response = requests.post(OLLAMA_URL, json=payload, timeout=45)
            if response.status_code == 200:
                return response.json().get("message", {})
            else:
                return {"role": "assistant", "content": f"LLM Error: {response.status_code}"}
        except Exception as e:
            return {"role": "assistant", "content": f"Sir, my local cognitive engine is offline. {e}"}

class JarvisPipeline:
    def __init__(self, window):
        self.window = window
        self.history = MemoryModule.load()
        self.audio_queue = queue.Queue()
        self.text_queue = queue.Queue()
        self.response_queue = queue.Queue()
        self.running = True
        self.gesture_mode = False 
        self.voice_mode = 'JARVIS'
        try:
            self.window.evaluate_js("addLog('SYSTEM', 'Loading Offline STT Model...')")
            self.stt_model = WhisperModel('base.en', device='cpu', compute_type='int8')
            self.window.evaluate_js("addLog('SYSTEM', 'Loading Offline TTS Models...')")
            self.jarvis_voice = PiperVoice('models/en_GB-alan-medium.onnx')
            self.friday_voice = PiperVoice('models/en_GB-jenny_dioco-medium.onnx')
        except Exception as e:
            print(f"Model Load Error: {e}")

    def start_services(self):
        threading.Thread(target=self.stt_worker, daemon=True).start()
        threading.Thread(target=self.llm_worker, daemon=True).start()
        threading.Thread(target=self.tts_worker, daemon=True).start()
        threading.Thread(target=self.telemetry_worker, daemon=True).start()
        # Vision offloaded to JS (barehands architecture)


    def telemetry_worker(self):
        while self.running:
            try:
                cpu = int(psutil.cpu_percent(interval=1))
                ram = int(psutil.virtual_memory().percent)
                self.window.evaluate_js(f"updateTelemetry({cpu}, {ram})")
            except: pass
            time.sleep(1.5)

    def stt_worker(self):
        recognizer = sr.Recognizer()
        pygame.mixer.init()
        
        with sr.Microphone() as source:
            recognizer.adjust_for_ambient_noise(source, duration=1.0)
            self.window.evaluate_js("updateState('ONLINE')")
            
            while self.running:
                if pygame.mixer.get_init() and pygame.mixer.music.get_busy():
                    time.sleep(0.5)
                    continue

                self.window.evaluate_js("updateState('LISTENING')")
                try:
                    audio = recognizer.listen(source, timeout=3, phrase_time_limit=10)
                    self.window.evaluate_js("updateState('PROCESSING')")
                    text = recognizer.recognize_google(audio).lower()
                    
                    if text:
                        # Removed strict wake-word so it responds instantly
                        cmd = text.replace("jarvis", "").replace("system", "").strip()
                        if cmd:
                            safe_cmd = json.dumps(cmd)
                            self.window.evaluate_js(f"addLog('USER', {safe_cmd})")
                            self.text_queue.put(cmd)
                except Exception as e:
                    pass

    def llm_worker(self):
        while self.running:
            try:
                text = self.text_queue.get()
                is_tool, tool_response = ToolModule.execute(text, self.window, self)
                
                if is_tool:
                    self.response_queue.put(tool_response)
                else:
                    self.window.evaluate_js("updateState('THINKING')")
                    
                    # INTELLIGENT WEB KNOWLEDGE ROUTING (Inspired by Sukeesh/Microsoft JARVIS)
                    # If the user asks a factual question, scrape the web invisibly first!
                    context_injection = ""
                    if any(q in text.lower() for q in ["who is", "what is", "why did", "how to", "tell me about"]):
                        try:
                            from duckduckgo_search import DDGS
                            self.window.evaluate_js(f"addLog('SYSTEM', 'Scanning internet databases...')")
                            results = DDGS().text(text, max_results=1)
                            if results:
                                context_injection = f"\n[LATEST INTERNET DATA: {results[0]['body']}]\n"
                        except: pass

                    prompt = "You are JARVIS. Respond concisely and wittily in a British tone. Never use emojis. Use the internet data provided to answer accurately if applicable.\n"
                    for role, msg in self.history:
                        prompt += f"{role}: {msg}\n"
                    
                    prompt += context_injection
                    prompt += f"USER: {text}\nJARVIS:"
                    
                    response = IntelligenceModule.generate(prompt, self.window)
                    
                    self.history.append(("USER", text))
                    self.history.append(("JARVIS", response))
                    MemoryModule.save(self.history)
                    
                    self.response_queue.put(response)
                
                self.text_queue.task_done()
            except Exception as e:
                self.window.evaluate_js(f"addLog('SYSTEM', 'LLM Error: {e}')")

    def tts_worker(self):
        while self.running:
            try:
                response = self.response_queue.get()
                self.window.evaluate_js("updateState('SPEAKING')")
                safe_resp = json.dumps(response)
                self.window.evaluate_js(f"addLog('JARVIS', {safe_resp})")
                audio_file = f"temp_{int(time.time())}.wav"
                
                # Use Piper CLI for bulletproof file generation
                model_path = "models/en_GB-jenny_dioco-medium.onnx" if getattr(self, "voice_mode", "JARVIS") == "FRIDAY" else "models/en_GB-alan-medium.onnx"
                piper_exe = os.path.join("venv", "Scripts", "piper.exe")
                
                subprocess.run([piper_exe, "-m", model_path, "-f", audio_file], input=response.encode('utf-8'), creationflags=subprocess.CREATE_NO_WINDOW)
                
                try:
                    if not pygame.mixer.get_init(): pygame.mixer.init()
                    pygame.mixer.music.load(audio_file)
                    pygame.mixer.music.play()
                    while pygame.mixer.music.get_busy():
                        pygame.time.Clock().tick(10)
                except: pass
                try:
                    pygame.mixer.music.unload()
                    os.remove(audio_file)
                except: pass

                self.window.evaluate_js("updateState('ONLINE')")
            except Exception as e:
                self.window.evaluate_js(f"addLog('SYSTEM', 'TTS Error: {e}')")
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
        os._exit(0)

if __name__ == '__main__':
    html_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'hud.html')
    # Create window without API first to get the instance
    window = webview.create_window('JARVIS Master', html_path, transparent=True, frameless=False, fullscreen=True, on_top=True)
    pipeline = JarvisPipeline(window)
    api = Api(pipeline)
    window.expose(api.send_command, api.minimize, api.toggle_fullscreen, api.destroy)
    
    threading.Timer(2.0, pipeline.start_services).start()
    webview.start()









