import threading
import asyncio
import edge_tts
import speech_recognition as sr
import os
import pygame
import webbrowser
import pyautogui
import time
import json
import webview
import psutil
from google import genai

# ----- CONFIG -----
VOICE = "en-GB-RyanNeural"
GEMINI_API_KEY = "YOUR_API_KEY_HERE"
MEMORY_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "jarvis_memory.json")

try:
    client = genai.Client(api_key=GEMINI_API_KEY)
except Exception as e:
    print("GenAI Init Error:", e)
    client = None

# --- PERSISTENT MEMORY ---
def load_memory():
    if os.path.exists(MEMORY_FILE):
        try:
            with open(MEMORY_FILE, 'r') as f:
                return json.load(f)
        except:
            pass
    return []

def save_memory(history):
    with open(MEMORY_FILE, 'w') as f:
        # Keep only the last 10 interactions to avoid token bloat
        json.dump(history[-10:], f)

# --- AI CORE (With 429 Backoff) ---
def get_ai_response(history, window, retries=4):
    if not client: return "AI Core Offline."
    
    # Build context prompt
    prompt = (
        "You are J.A.R.V.I.S., an advanced AI assistant. "
        "Keep your responses concise, witty, British, and highly competent. "
        "Do not use emojis or markdown formatting. Speak naturally.\n\n"
        "Conversation History:\n"
    )
    for role, msg in history:
        prompt += f"{role}: {msg}\n"
    prompt += "JARVIS:"

    for attempt in range(retries):
        try:
            response = client.models.generate_content(
                model='gemini-flash-latest',
                contents=prompt
            )
            return response.text.strip()
        except Exception as e:
            err_str = str(e)
            # Handle API Limits (429) and Server Overloads (503)
            if "429" in err_str or "503" in err_str:
                window.evaluate_js(f"addLog('SYSTEM', 'Bypassing API rate limit... attempt {attempt+1}')")
                time.sleep((attempt + 1) * 2.5) # Exponential backoff: 2.5s, 5.0s, 7.5s...
                continue
            return f"Neural network error: {err_str[:40]}"
    
    return "I apologize, sir. The cognitive servers are currently congested. Please give me a moment to reset."

# --- TELEMETRY ---
def telemetry_loop(window):
    while True:
        try:
            cpu = int(psutil.cpu_percent(interval=1))
            ram = int(psutil.virtual_memory().percent)
            window.evaluate_js(f"updateTelemetry({cpu}, {ram})")
        except:
            pass
        time.sleep(1)

# --- AUDIO / SPEECH ---
def speak_sync(text, window):
    window.evaluate_js("updateState('SPEAKING')")
    window.evaluate_js(f"addLog('JARVIS', `{text}`)")
    
    async def _speak():
        communicate = edge_tts.Communicate(text, VOICE)
        audio_file = "response.mp3"
        await communicate.save(audio_file)
        
        pygame.mixer.init()
        pygame.mixer.music.load(audio_file)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)
        pygame.mixer.quit()
        
        if os.path.exists(audio_file):
            try: os.remove(audio_file)
            except: pass

    if os.name == 'nt':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(_speak())

def listen_for_command(window, recognizer, source):
    window.evaluate_js("updateState('LISTENING')")
    recognizer.adjust_for_ambient_noise(source, duration=0.2)
    try:
        audio = recognizer.listen(source, timeout=5, phrase_time_limit=15)
        window.evaluate_js("updateState('PROCESSING')")
        text = recognizer.recognize_google(audio)
        window.evaluate_js(f"addLog('USER', `{text}`)")
        return text.lower()
    except sr.WaitTimeoutError:
        pass
    except sr.UnknownValueError:
        pass
    except Exception as e:
        pass
    return ""

def execute_command(command, window):
    if "youtube" in command or ("play" in command and ("music" in command or "song" in command)):
        is_music = "play" in command and ("music" in command or "song" in command)
        target_url = "https://www.youtube.com/watch?v=jfKfPfyJRdk" if is_music else "https://www.youtube.com"
        
        speak_sync("Which browser would you prefer to use for this?", window)
        recognizer = sr.Recognizer()
        with sr.Microphone() as source:
            browser_choice = listen_for_command(window, recognizer, source)
        
        browser_cmd = "start"
        browser_name = "default browser"
        
        if "brave" in browser_choice:
            browser_cmd = "start brave"
            browser_name = "Brave"
        elif "chrome" in browser_choice:
            browser_cmd = "start chrome"
            browser_name = "Chrome"
        elif "edge" in browser_choice:
            browser_cmd = "start msedge"
            browser_name = "Edge"
        elif not browser_choice:
            speak_sync("I didn't catch a browser name. Canceling.", window)
            return True
            
        speak_sync(f"Opening it in {browser_name}.", window)
        os.system(f"{browser_cmd} {target_url}")
        return True
    elif "lock" in command and "system" in command:
        speak_sync("Locking the system immediately.", window)
        os.system("rundll32.exe user32.dll,LockWorkStation")
        return True
    elif "type" in command:
        speak_sync("What would you like me to type?", window)
        recognizer = sr.Recognizer()
        with sr.Microphone() as source:
            text_to_type = listen_for_command(window, recognizer, source)
        if text_to_type:
            speak_sync("Typing it out now.", window)
            time.sleep(1)
            pyautogui.write(text_to_type, interval=0.05)
        return True
    elif "open" in command or "launch" in command:
        app_name = command.replace("open", "").replace("launch", "").replace("the", "").replace("can you", "").replace("hey", "").replace("jarvis", "").strip()
        speak_sync(f"Searching Windows for {app_name}, sir.", window)
        pyautogui.press('win')
        time.sleep(0.5)
        pyautogui.write(app_name, interval=0.05)
        time.sleep(0.5)
        pyautogui.press('enter')
        return True
    return False

# --- MAIN LOOP ---
def run_jarvis(window):
    time.sleep(2) # Wait for UI load
    speak_sync("Good day. Advanced cognitive systems are now fully independent.", window)
    
    # Load persistent memory from disk
    history = load_memory()
    recognizer = sr.Recognizer()

    while True:
        window.evaluate_js("updateState('ONLINE')")
        with sr.Microphone() as source:
            # Active Listening Loop
            command = listen_for_command(window, recognizer, source)
            
            if command:
                if any(w in command for w in ["exit", "quit", "goodbye", "sleep", "bye"]):
                    speak_sync("Powering down cognitive systems. Goodbye!", window)
                    time.sleep(2)
                    window.destroy()
                    break
                
                # Try physical tools first
                executed = execute_command(command, window)
                
                # If not a physical command, use AI Conversation Engine
                if not executed:
                    window.evaluate_js("updateState('THINKING')")
                    history.append(("USER", command))
                    
                    response = get_ai_response(history, window)
                    
                    history.append(("JARVIS", response))
                    save_memory(history) # Save to persistent memory
                    
                    speak_sync(response, window)

if __name__ == '__main__':
    html_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'hud.html')
    window = webview.create_window('JARVIS HUD', html_path, transparent=True, frameless=True, width=1050, height=600, on_top=True)
    
    threading.Thread(target=run_jarvis, args=(window,), daemon=True).start()
    threading.Thread(target=telemetry_loop, args=(window,), daemon=True).start()
    
    webview.start()
