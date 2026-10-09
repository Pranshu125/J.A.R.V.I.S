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
import cv2
import mediapipe as mp
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
    """Deep OS Control (Inspired by Mark-XXXIX-OR)"""
    @staticmethod
    def execute(command, window, pipeline):
        cmd = command.lower()
        
        # 1. Advanced Web Automation
        if "search for" in cmd or "google" in cmd:
            query = cmd.replace("search for", "").replace("google", "").strip()
            webbrowser.open(f"https://www.google.com/search?q={query}")
            window.evaluate_js(f"addLog('SYSTEM', 'Tool: Web Search -> {query}')")
            return True, f"I have pulled up the search results for {query}, sir."
            
        elif "play" in cmd and "on youtube" in cmd:
            query = cmd.replace("play", "").replace("on youtube", "").strip()
            webbrowser.open(f"https://www.youtube.com/results?search_query={query}")
            return True, f"Searching YouTube for {query}."

        # 2. Keyboard & Screen Automation (PyAutoGUI)
        elif "type this" in cmd or "dictate" in cmd:
            text = cmd.replace("type this", "").replace("dictate", "").strip()
            pyautogui.write(text, interval=0.03)
            return True, "Dictation typed on screen."
            
        elif "take a screenshot" in cmd or "capture screen" in cmd:
            pyautogui.screenshot(os.path.join(os.path.dirname(__file__), "capture.png"))
            return True, "Screen captured and saved to the primary directory."

        # 3. Core System Hooks
        elif "lock system" in cmd:
            os.system("rundll32.exe user32.dll,LockWorkStation")
            return True, "Workstation locked."
            
        elif "time" in cmd or "what time" in cmd:
            return True, f"The current system time is {time.strftime('%I:%M %p')}."
            
        elif "stop" in cmd and ("talking" in cmd or "speaking" in cmd):
            if pygame.mixer.get_init(): pygame.mixer.music.stop()
            return True, "Audio playback canceled."
        
        # 4. Barehands Spatial Toggle
        elif "enable gestures" in cmd or "turn on webcam" in cmd:
            pipeline.gesture_mode = True
            return True, "Barehands spatial tracking online."
            
        elif "disable gestures" in cmd or "turn off webcam" in cmd:
            pipeline.gesture_mode = False
            window.evaluate_js("setGestureMode(false)")
            return True, "Spatial tracking deactivated."
            
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
        threading.Thread(target=self.vision_worker, daemon=True).start()

    def vision_worker(self):
        """Barehands MediaPipe Computer Vision Tracking"""
        mp_hands = mp.solutions.hands
        hands = mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.7)
        cap = None
        
        while self.running:
            if self.gesture_mode:
                if cap is None:
                    cap = cv2.VideoCapture(0)
                    if not cap.isOpened():
                        self.window.evaluate_js(f"addLog('SYSTEM', 'Webcam Error: Device in use.')")
                        self.gesture_mode = False
                        self.window.evaluate_js("setGestureMode(false)")
                        continue
                        
                ret, frame = cap.read()
                if ret:
                    frame = cv2.flip(frame, 1) 
                    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    results = hands.process(rgb_frame)
                    
                    if results.multi_hand_landmarks:
                        for hand_landmarks in results.multi_hand_landmarks:
                            # Index finger tracking
                            x = hand_landmarks.landmark[8].x
                            y = hand_landmarks.landmark[8].y
                            self.window.evaluate_js(f"updateParallaxFromVision({x}, {y})")
                            
                            # Pinch Detection (Thumb tip 4 + Index tip 8)
                            tx, ty = hand_landmarks.landmark[4].x, hand_landmarks.landmark[4].y
                            distance = ((x - tx)**2 + (y - ty)**2)**0.5
                            if distance < 0.05:
                                # Trigger a UI interaction on pinch
                                self.window.evaluate_js(f"addLog('SYSTEM', 'Gesture: Pinch Detected')")
                                time.sleep(1) # Cooldown
            else:
                if cap is not None:
                    cap.release()
                    cap = None
            time.sleep(0.03) 

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
                        if "jarvis" in text or "system" in text:
                            if pygame.mixer.get_init() and pygame.mixer.music.get_busy():
                                pygame.mixer.music.stop()
                            cmd = text.replace("jarvis", "").replace("system", "").strip()
                            if cmd:
                                self.window.evaluate_js(f"addLog('USER', `{cmd}`)")
                                self.text_queue.put(cmd)
                        else:
                            self.window.evaluate_js(f"addLog('SYSTEM', `[Ambient]: {text}`)")
                except: pass

    def llm_worker(self):
        while self.running:
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

    def tts_worker(self):
        while self.running:
            response = self.response_queue.get()
            self.window.evaluate_js("updateState('SPEAKING')")
            self.window.evaluate_js(f"addLog('JARVIS', `{response}`)")
            
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
            self.response_queue.task_done()

if __name__ == '__main__':
    html_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'hud.html')
    window = webview.create_window('JARVIS Master', html_path, transparent=True, frameless=True, width=1050, height=600, on_top=True)
    pipeline = JarvisPipeline(window)
    threading.Timer(2.0, pipeline.start_services).start()
    webview.start()
