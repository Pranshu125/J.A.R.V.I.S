import asyncio
import edge_tts
import speech_recognition as sr
import os
import pygame
import webbrowser
import pyautogui
import time
import subprocess

# Set up the voice. 'en-GB-RyanNeural' is a high-quality male British voice.
VOICE = "en-GB-RyanNeural"

async def speak(text):
    print(f"J.A.R.V.I.S.: {text}")
    communicate = edge_tts.Communicate(text, VOICE)
    audio_file = "response.mp3"
    await communicate.save(audio_file)
    
    # Play the audio using pygame
    pygame.mixer.init()
    pygame.mixer.music.load(audio_file)
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        pygame.time.Clock().tick(10)
    
    pygame.mixer.quit()
    
    # Clean up the temporary audio file
    if os.path.exists(audio_file):
        try:
            os.remove(audio_file)
        except PermissionError:
            pass

def listen():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("Listening...")
        # Adjust for ambient noise
        recognizer.adjust_for_ambient_noise(source, duration=1)
        try:
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=10)
            print("Processing...")
            text = recognizer.recognize_google(audio)
            print(f"You: {text}")
            return text.lower()
        except sr.WaitTimeoutError:
            pass
        except sr.UnknownValueError:
            pass # Removed the print so it doesn't spam 'Sorry I didn't catch that'
        except sr.RequestError as e:
            print(f"Could not request results; {e}")
    return ""

async def execute_command(command):
    """The 'Hands' of J.A.R.V.I.S."""
    if "open notepad" in command:
        await speak("Opening Notepad, sir.")
        subprocess.Popen("notepad.exe")
        return True
        
    elif "open calculator" in command:
        await speak("Opening Calculator.")
        subprocess.Popen("calc.exe")
        return True
        
    elif "play music" in command or "focus music" in command:
        await speak("Playing focus music for you.")
        webbrowser.open("https://www.youtube.com/watch?v=jfKfPfyJRdk") # Lofi hip hop radio
        return True
        
    elif "lock the system" in command or "lock system" in command:
        await speak("Locking the system immediately.")
        os.system("rundll32.exe user32.dll,LockWorkStation")
        return True
        
    elif "type for me" in command:
        await speak("What would you like me to type?")
        text_to_type = listen()
        if text_to_type:
            await speak("Typing it out now.")
            # Give a second to focus on a window
            time.sleep(1)
            pyautogui.write(text_to_type, interval=0.05)
        return True
        
    return False

async def main():
    # Initial Greeting
    await speak("Good day. I am J.A.R.V.I.S. My systems are currently coming online. How can I assist you today?")
    
    while True:
        command = listen()
        if command:
            if any(word in command for word in ["exit", "quit", "goodbye", "good bye", "good night", "sleep", "bye"]):
                await speak("Powering down. Goodbye!")
                break
            elif "hello" in command or "hi jarvis" in command:
                await speak("Hello there! I am ready for your commands.")
            else:
                # Try to execute it as a system command
                executed = await execute_command(command)
                if not executed:
                    await speak(f"I heard you say: {command}. I do not have a registered action for that yet.")

if __name__ == "__main__":
    # Workaround for some Windows asyncio issues
    if os.name == 'nt':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
