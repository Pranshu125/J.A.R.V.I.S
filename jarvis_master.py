import threading
import asyncio
import queue
import time
import json
import os
import requests
import subprocess
import webbrowser
import speech_recognition as sr
import edge_tts
import pygame
import psutil
import webview


import pyautogui

# ==========================================
# J.A.R.V.I.S. V2.0 THE ULTIMATE HYBRID
# Merging Our Core with Mark-XXXIX OS Control & Barehands Spatial Tech
# ==========================================

OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "llama3" 
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
            
        elif "play" in cmd and "on youtube" in cmd:
            query = cmd.replace("play", "").replace("on youtube", "").strip()
            webbrowser.open(f"https://www.youtube.com/results?search_query={query}")
            return True, f"Searching YouTube for {query}."

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
    """Local LLM Engine"""
    @staticmethod
    def generate(prompt, window):
        payload = {
            "model": OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0.7, "num_predict": 100}
        }
        try:
            response = requests.post(OLLAMA_URL, json=payload, timeout=45)
            if response.status_code == 200:
                return response.json().get('response', '').strip()
            else:
                return f"LLM Error: {response.status_code}"
        except:
            return "Sir, my local cognitive engine is offline. Please ensure Ollama is running."

class JarvisPipeline:
    def __init__(self, window):
        self.window = window
        self.history = MemoryModule.load()
        self.audio_queue = queue.Queue()
        self.text_queue = queue.Queue()
        self.response_queue = queue.Queue()
        self.running = True
        self.gesture_mode = False 

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
                    prompt = "You are JARVIS. Respond concisely and wittily in a British tone. Never use emojis.\n"
                    for role, msg in self.history:
                        prompt += f"{role}: {msg}\n"
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
                
                async def _speak():
                    communicate = edge_tts.Communicate(response, VOICE_MODEL)
                    audio_file = f"temp_{int(time.time())}.mp3"
                    await communicate.save(audio_file)
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

                if os.name == 'nt':
                    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
                asyncio.run(_speak())
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

if __name__ == '__main__':
    html_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'hud.html')
    # Create window without API first to get the instance
    window = webview.create_window('JARVIS Master', html_path, transparent=True, frameless=True, fullscreen=True, on_top=True)
    pipeline = JarvisPipeline(window)
    window.expose(Api(pipeline).send_command) # expose API
    
    threading.Timer(2.0, pipeline.start_services).start()
    webview.start()
