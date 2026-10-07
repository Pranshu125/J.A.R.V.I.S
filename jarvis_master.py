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

# ==========================================
# J.A.R.V.I.S. MASTER PIPELINE ARCHITECTURE
# Combined Methodologies: Barehands, OpenJarvis, Pipecat, Ollama
# ==========================================

OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "llama3" 
VOICE_MODEL = "en-GB-RyanNeural"
MEMORY_DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "jarvis_state.md")

class MemoryModule:
    """Handles Long-Term State (Markdown Vault - fullstack-agent style)"""
    @staticmethod
    def load():
        if os.path.exists(MEMORY_DB):
            try:
                with open(MEMORY_DB, 'r') as f: 
                    # Parse simple markdown logs back to list if needed
                    pass
            except: pass
        return []
    
    @staticmethod
    def save(history):
        with open(MEMORY_DB, 'w') as f: 
            f.write("# J.A.R.V.I.S. Memory Vault\n\n")
            for role, msg in history[-15:]:
                f.write(f"**{role}:** {msg}\n\n")

class ToolModule:
    """Agentic Tool Calling & OS Hooks"""
    @staticmethod
    def execute(command, window, pipeline):
        cmd = command.lower()
        if "youtube" in cmd:
            window.evaluate_js(f"addLog('SYSTEM', 'Tool Executed: Open Browser (YouTube)')")
            os.system("start brave https://www.youtube.com")
            return True, "I have opened YouTube for you, sir."
        elif "lock system" in cmd:
            window.evaluate_js(f"addLog('SYSTEM', 'Tool Executed: Lock Workstation')")
            os.system("rundll32.exe user32.dll,LockWorkStation")
            return True, "System locked."
        elif "time" in cmd:
            current_time = time.strftime("%I:%M %p")
            return True, f"The current time is {current_time}."
        
        # --- BAREHANDS TOGGLES ---
        elif "enable gestures" in cmd or "turn on webcam" in cmd or "activate vision" in cmd:
            pipeline.gesture_mode = True
            return True, "Gesture control is now online. I am tracking your hand movements."
        elif "disable gestures" in cmd or "turn off webcam" in cmd or "deactivate vision" in cmd:
            pipeline.gesture_mode = False
            window.evaluate_js("setGestureMode(false)")
            return True, "Gesture control deactivated. Returning to standard tracking."
            
        return False, None

class IntelligenceModule:
    """Local LLM Engine"""
    @staticmethod
    def generate(prompt, window):
        payload = {
            "model": OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0.7}
        }
        try:
            response = requests.post(OLLAMA_URL, json=payload, timeout=30)
            if response.status_code == 200:
                return response.json().get('response', '').strip()
            else:
                return f"LLM Error: {response.status_code}"
        except requests.exceptions.ConnectionError:
            window.evaluate_js(f"addLog('SYSTEM', 'CRITICAL ERROR: Ollama Not Running')")
            return "Sir, my local cognitive engine is offline. Please ensure Ollama is running."
        except Exception as e:
            return f"Error: {str(e)}"

class JarvisPipeline:
    def __init__(self, window):
        self.window = window
        self.history = MemoryModule.load()
        
        self.audio_queue = queue.Queue()
        self.text_queue = queue.Queue()
        self.response_queue = queue.Queue()
        
        self.running = True
        self.gesture_mode = False # Barehands tracker state

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
                ret, frame = cap.read()
                if ret:
                    frame = cv2.flip(frame, 1) # Mirror for natural interaction
                    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    results = hands.process(rgb_frame)
                    
                    if results.multi_hand_landmarks:
                        for hand_landmarks in results.multi_hand_landmarks:
                            # Use Index Finger tip (landmark 8) for parallax anchor
                            x = hand_landmarks.landmark[8].x
                            y = hand_landmarks.landmark[8].y
                            self.window.evaluate_js(f"updateParallaxFromVision({x}, {y})")
            else:
                if cap is not None:
                    cap.release()
                    cap = None
            time.sleep(0.03) # Prevent CPU hogging (~30 FPS)

    def telemetry_worker(self):
        while self.running:
            try:
                cpu = int(psutil.cpu_percent(interval=1))
                ram = int(psutil.virtual_memory().percent)
                self.window.evaluate_js(f"updateTelemetry({cpu}, {ram})")
            except: pass
            time.sleep(1)

    def stt_worker(self):
        recognizer = sr.Recognizer()
        with sr.Microphone() as source:
            recognizer.adjust_for_ambient_noise(source, duration=1)
            self.window.evaluate_js("updateState('ONLINE')")
            
            while self.running:
                self.window.evaluate_js("updateState('LISTENING')")
                try:
                    audio = recognizer.listen(source, timeout=2, phrase_time_limit=10)
                    self.window.evaluate_js("updateState('PROCESSING')")
                    text = recognizer.recognize_google(audio).lower()
                    if text:
                        self.window.evaluate_js(f"addLog('USER', `{text}`)")
                        self.text_queue.put(text)
                except sr.WaitTimeoutError:
                    pass
                except Exception:
                    pass

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
                await communicate.save("temp.mp3")
                pygame.mixer.init()
                pygame.mixer.music.load("temp.mp3")
                pygame.mixer.music.play()
                while pygame.mixer.music.get_busy():
                    pygame.time.Clock().tick(10)
                pygame.mixer.quit()
                try: os.remove("temp.mp3")
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
