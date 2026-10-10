"""
tts_engine.py - High-Performance Dual-Language Neural Speech Synthesis
Supports English & Hindi/Hinglish (J.A.R.V.I.S. & F.R.I.D.A.Y.)
Uses edge-tts with zero disk-locking in-memory Pygame playback,
with seamless offline fallback to Piper TTS.
"""

import asyncio
import os
import time
import re
import pygame
import subprocess

VOICE_MAP = {
    "JARVIS": {
        "en": "en-GB-RyanNeural",
        "hi": "hi-IN-MadhurNeural",
        "piper": "models/en_GB-alan-medium.onnx"
    },
    "FRIDAY": {
        "en": "en-GB-SoniaNeural",
        "hi": "hi-IN-SwaraNeural",
        "piper": "models/en_GB-jenny_dioco-medium.onnx"
    }
}

def is_hindi(text: str) -> bool:
    """Detect if text contains Devanagari script or common Hinglish phrasing."""
    if re.search(r'[\u0900-\u097F]', text):
        return True
    hinglish_markers = [
        "ji boss", "khol diya", "kya haal", "kya chal", "aapka", "hai sir",
        "bilkul", "kar diya", "bataiye", "hukum", "namaste", "dhanyawad",
        "gaana chala", "khol do", "band karo", "badha do", "kam karo"
    ]
    t_lower = text.lower()
    return any(marker in t_lower for marker in hinglish_markers)

def speak_text(text: str, mode: str = "JARVIS"):
    """Synthesize and play speech in-memory without Windows file locking."""
    if not text or not text.strip():
        return

    mode = mode.upper()
    if mode not in VOICE_MAP:
        mode = "JARVIS"

    lang = "hi" if is_hindi(text) else "en"
    edge_voice = VOICE_MAP[mode][lang]
    temp_wav = f"temp_tts_{int(time.time()*1000)}.wav"

    played = False
    # 1. High-quality Edge Neural TTS (instant, crystal-clear Hindi & English)
    try:
        import edge_tts
        communicate = edge_tts.Communicate(text, edge_voice, rate="+4%")
        asyncio.run(communicate.save(temp_wav))
        
        if os.path.exists(temp_wav):
            if not pygame.mixer.get_init():
                pygame.mixer.init()
            sound = pygame.mixer.Sound(temp_wav)
            os.remove(temp_wav) # Immediate deletion from disk — NO file locking!
            sound.play()
            while pygame.mixer.get_busy():
                pygame.time.Clock().tick(15)
            played = True
    except Exception as e:
        if os.path.exists(temp_wav):
            try: os.remove(temp_wav)
            except Exception: pass

    # 2. Offline Fallback to Piper TTS
    if not played:
        piper_model = VOICE_MAP[mode]["piper"]
        piper_exe = os.path.join("venv", "Scripts", "piper.exe")
        fallback_wav = f"temp_piper_{int(time.time()*1000)}.wav"
        try:
            subprocess.run(
                [piper_exe, "-m", piper_model, "-f", fallback_wav],
                input=text.encode('utf-8'),
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            if os.path.exists(fallback_wav):
                if not pygame.mixer.get_init():
                    pygame.mixer.init()
                sound = pygame.mixer.Sound(fallback_wav)
                os.remove(fallback_wav)
                sound.play()
                while pygame.mixer.get_busy():
                    pygame.time.Clock().tick(15)
        except Exception as e:
            print(f"Fallback TTS Error: {e}")
            if os.path.exists(fallback_wav):
                try: os.remove(fallback_wav)
                except Exception: pass
