"""
tts_engine.py - High-Performance Dual-Language Neural Speech Synthesis
Supports English & Authentic Indian Hindi/Hinglish (J.A.R.V.I.S. & F.R.I.D.A.Y.)
Uses edge-tts (hi-IN-MadhurNeural / hi-IN-SwaraNeural / en-IN-PrabhatNeural / en-IN-NeerjaExpressiveNeural)
with automatic Roman-Hinglish-to-Devanagari phonetic conversion so Indian accents sound 100% real and natural.
"""
from __future__ import annotations

import asyncio
import hashlib
import os
import random
import re
import subprocess
import threading
import time
from pathlib import Path

import pygame

ROOT_DIR = Path(__file__).resolve().parent.parent
ACK_CACHE_DIR = ROOT_DIR / "models" / "ack_cache"

VOICE_MAP: dict[str, dict[str, str]] = {
    "JARVIS": {
        "en": "en-GB-RyanNeural",
        "en_in": "en-IN-PrabhatNeural",
        "hi": "hi-IN-MadhurNeural",
        "piper": str(ROOT_DIR / "models" / "en_GB-alan-medium.onnx"),
    },
    "FRIDAY": {
        "en": "en-GB-SoniaNeural",
        "en_in": "en-IN-NeerjaExpressiveNeural",
        "hi": "hi-IN-SwaraNeural",
        "piper": str(ROOT_DIR / "models" / "en_GB-jenny_dioco-medium.onnx"),
    },
}

# Roman-Hinglish -> Devanagari phonetic dictionary for natural Indian TTS pronunciation.
# English loanwords (sir, boss, system, online, WhatsApp, YouTube, Chrome, CPU, RAM) remain in Latin script
# so hi-IN-MadhurNeural and hi-IN-SwaraNeural pronounce them with a natural Indian-English accent while
# pronouncing all Hindi words with 100% native Hindi phonetics.
HINGLISH_PHONETIC_MAP: dict[str, str] = {
    # Greetings & Respect
    "namaste": "नमस्ते", "namaskar": "नमस्कार", "pranam": "प्रणाम", "shukriya": "शुक्रिया",
    "dhanyawad": "धन्यवाद", "dhanyavaad": "धन्यवाद", "alvida": "अलविदा", "ji": "जी",
    "hukum": "हुकुम", "sahab": "साहब", "bhai": "भाई", "dost": "दोस्त", "yaar": "यार",
    # Pronouns & Possessives
    "main": "मैं", "mai": "मैं", "mein": "में", "me": "में", "mujhe": "मुझे", "mujhko": "मुझको",
    "mera": "मेरा", "meri": "मेरी", "mere": "मेरे", "hum": "हम", "humein": "हमें",
    "humara": "हमारा", "hamara": "हमारा", "aap": "आप", "aapka": "आपका", "aapki": "आपकी",
    "aapke": "आपके", "aapko": "आपको", "tum": "तुम", "tumhara": "तुम्हारा", "tumhari": "तुम्हारी",
    "apna": "अपना", "apni": "अपनी", "apne": "अपने", "yeh": "यह", "ye": "ये", "woh": "वह",
    "wo": "वो", "iska": "इसका", "iski": "इसकी", "uska": "उसका", "uski": "उसकी",
    "inka": "इनका", "unka": "उनका",
    # Question words
    "kya": "क्या", "kyun": "क्यों", "kyo": "क्यों", "kab": "कब", "kahan": "कहाँ", "kaha": "कहाँ",
    "kaise": "कैसे", "kaisa": "कैसा", "kaisi": "कैसी", "kaun": "कौन", "kon": "कौन",
    "kitna": "कितना", "kitni": "कितनी", "kitne": "कितने", "kisne": "किसने", "kisko": "किसको",
    # Auxiliary & Copula verbs
    "hai": "है", "hain": "हैं", "hoon": "हूँ", "hu": "हूँ", "hun": "हूँ", "ho": "हो",
    "tha": "था", "thi": "थी", "the": "थे", "hoga": "होगा", "hogi": "होगी", "honge": "होंगे",
    "raha": "रहा", "rahi": "रही", "rahe": "रहे", "gaya": "गया", "gayi": "गई", "gaye": "गए",
    "diya": "दिया", "diye": "दिए", "liya": "लिया", "liye": "लिए", "chuka": "चुका",
    "chuki": "चुकी", "chuke": "चुके", "sakta": "सकता", "sakti": "सकती", "sakte": "सकते",
    "chahiye": "चाहिए", "padega": "पड़ेगा",
    # Common Action Verbs
    "kar": "कर", "karo": "करो", "kariye": "करिए", "kijiye": "कीजिए", "karna": "करना",
    "karta": "करता", "karti": "करती", "karte": "करते", "kiya": "किया", "kiye": "किए",
    "khol": "खोल", "kholo": "खोलो", "kholna": "खोलना", "khola": "खोला", "band": "बंद",
    "chala": "चला", "chalao": "चलाओ", "chalana": "चलाना", "chalu": "चालू", "chal": "चल",
    "chalo": "चलो", "ruko": "रुको", "rok": "रोक", "roko": "रोको", "bata": "बता",
    "batao": "बताओ", "bataye": "बताइए", "bataiye": "बताइए", "batana": "बताना",
    "dekho": "देखो", "dekh": "देख", "dekhiye": "देखिए", "dekhna": "देखना", "dikh": "दिख",
    "dikhao": "दिखाओ", "dikha": "दिखा", "suno": "सुनो", "sun": "सुन", "suniye": "सुनिए",
    "sunao": "सुनाओ", "bol": "बोल", "bolo": "बोलो", "boliye": "बोलिए", "likh": "लिख",
    "likho": "लिखो", "padh": "पढ़", "padho": "पढ़ो", "bhej": "भेज", "bhejo": "भेजो",
    "laga": "लगा", "lagao": "लगाओ", "badha": "बढ़ा", "badhao": "बढ़ाओ", "kam": "कम",
    "hata": "हटा", "hatao": "हटाओ", "dhundho": "ढूँढो", "khojo": "खोजो", "jao": "जाओ",
    "aao": "आओ", "uth": "उठ", "utho": "उठो",
    # Adverbs, Adjectives & Conjunctions
    "aaj": "आज", "kal": "कल", "abhi": "अभी", "ab": "अब", "baad": "बाद", "pehle": "पहले",
    "subah": "सुबह", "dopahar": "दोपहर", "shaam": "शाम", "raat": "रात", "din": "दिन",
    "waqt": "वक़्त", "samay": "समय", "yahan": "यहाँ", "wahan": "वहाँ", "upar": "ऊपर",
    "neeche": "नीचे", "andar": "अंदर", "bahar": "बाहर", "aage": "आगे", "peeche": "पीछे",
    "bilkul": "बिल्कुल", "zaroor": "ज़रूर", "acha": "अच्छा", "accha": "अच्छा", "achha": "अच्छा",
    "theek": "ठीक", "thik": "ठीक", "sahi": "सही", "galat": "ग़लत", "bahut": "बहुत",
    "bohot": "बहुत", "zyada": "ज़्यादा", "thoda": "थोड़ा", "sab": "सब", "sabhi": "सभी",
    "sara": "सारा", "saare": "सारे", "kuch": "कुछ", "koi": "कोई", "nahi": "नहीं",
    "nhi": "नहीं", "na": "ना", "mat": "मत", "haan": "हाँ", "han": "हाँ", "aur": "और",
    "ya": "या", "lekin": "लेकिन", "magar": "मगर", "agar": "अगर", "toh": "तो", "bhi": "भी",
    "hi": "ही", "se": "से", "ko": "को", "ka": "का", "ki": "की", "ke": "के", "par": "पर",
    "pe": "पे", "tak": "तक", "wala": "वाला", "wali": "वाली", "wale": "वाले",
    # Common Nouns
    "kaam": "काम", "baat": "बात", "haal": "हाल", "cheez": "चीज़", "jagah": "जगह",
    "ghar": "घर", "gaana": "गाना", "awaaz": "आवाज़", "mausam": "मौसम", "khabar": "ख़बर",
    "asman": "आसमान", "aasman": "आसमान", "chehra": "चेहरा", "haath": "हाथ", "naam": "नाम",
    "sawal": "सवाल", "jawab": "जवाब", "madad": "मदद", "taiyar": "तैयार",
}

UNAMBIGUOUS_HINGLISH_WORDS: frozenset[str] = frozenset(HINGLISH_PHONETIC_MAP.keys()) - {"the", "me", "hi", "main"}
_DEVANAGARI_RE = re.compile(r"[\u0900-\u097F]")
_WORD_RE = re.compile(r"\b[a-zA-Z]+\b")

TTS_ABORT_EVENT = threading.Event()


def is_hindi(text: str) -> bool:
    """Detect if text contains Devanagari script or any Roman Hindi/Hinglish words."""
    if not text:
        return False
    if _DEVANAGARI_RE.search(text):
        return True
    return any(w in UNAMBIGUOUS_HINGLISH_WORDS for w in _WORD_RE.findall(text.lower()))


def normalize_hinglish_for_indian_tts(text: str) -> str:
    """
    Convert Roman-script Hindi words in a Hinglish sentence to Devanagari script
    while leaving English words intact so hi-IN-MadhurNeural / hi-IN-SwaraNeural
    speak with a 100% authentic Indian accent.
    """
    return _WORD_RE.sub(lambda m: HINGLISH_PHONETIC_MAP.get(m.group(0).lower(), m.group(0)), text)


def get_instant_ack(user_text: str, mode: str = "JARVIS") -> str:
    """Return a natural, context-aware pre-processing acknowledgment in English or Hindi/Hinglish."""
    t_low = (user_text or "").lower()
    if is_hindi(t_low):
        if any(k in t_low for k in ("khol", "chala", "play", "open", "start", "laga")):
            return random.choice((
                "Ji sir, abhi khol raha hoon.",
                "Bilkul boss, abhi chala raha hoon.",
                "Ji boss, abhi karta hoon.",
            ))
        return random.choice((
            "Ji sir, abhi karta hoon.",
            "Bilkul boss, dekh raha hoon.",
            "Ek second sir, kaam chal raha hai.",
            "Hukum sir, abhi check karta hoon.",
        ))
    if any(k in t_low for k in ("screen", "camera", "looking at", "what do you see", "analyze")):
        return random.choice((
            "On it, sir. Scanning now.",
            "Working on it, sir. Analyzing visual feed.",
            "Right away, sir. Inspecting now.",
        ))
    return random.choice((
        "On it, sir.",
        "Working on it, sir.",
        "Right away, sir.",
        "Processing that now, boss.",
        "One moment, sir.",
    ))


def stop_speaking() -> None:
    """Immediately halt any active TTS synthesis and audio playback."""
    TTS_ABORT_EVENT.set()
    try:
        if pygame.mixer.get_init():
            pygame.mixer.stop()
    except Exception:
        pass


def _remove_quietly(path: str | Path) -> None:
    try:
        if os.path.exists(path):
            os.remove(path)
    except Exception:
        pass


def _play_audio_file(filepath: str, delete_after: bool = True, ignore_abort: bool = False) -> bool:
    """Load audio into memory via pygame.mixer.Sound, optionally delete file immediately, and play with abort checks."""
    if not os.path.exists(filepath):
        return False
    try:
        if not ignore_abort and TTS_ABORT_EVENT.is_set():
            if delete_after:
                _remove_quietly(filepath)
            return False
        if not pygame.mixer.get_init():
            pygame.mixer.init()
        sound = pygame.mixer.Sound(filepath)
        if delete_after:
            _remove_quietly(filepath)
        sound.play()
        clock = pygame.time.Clock()
        while pygame.mixer.get_busy():
            if not ignore_abort and TTS_ABORT_EVENT.is_set():
                pygame.mixer.stop()
                break
            clock.tick(20)
        return True
    except Exception:
        if delete_after:
            _remove_quietly(filepath)
        return False


def speak_text(text: str, mode: str = "JARVIS", cache_clip: bool = False, ignore_abort: bool = False) -> None:
    """Synthesize and play speech in-memory without Windows file locking (with instant disk cache for acknowledgments)."""
    if not text or not text.strip():
        return

    if ignore_abort:
        TTS_ABORT_EVENT.clear()
    elif TTS_ABORT_EVENT.is_set():
        return

    voice_cfg = VOICE_MAP.get(mode.upper(), VOICE_MAP["JARVIS"])
    hindi_detected = is_hindi(text)
    edge_voice = voice_cfg["hi"] if hindi_detected else voice_cfg["en"]
    synth_text = normalize_hinglish_for_indian_tts(text) if hindi_detected else text
    rate = "+4%"

    # Fast-path disk cache for short acknowledgment phrases (~1ms playback after first synthesis)
    cache_path: str | None = None
    if cache_clip:
        ACK_CACHE_DIR.mkdir(parents=True, exist_ok=True)
        digest = hashlib.md5(f"{edge_voice}|{rate}|{synth_text}".encode("utf-8")).hexdigest()[:16]
        cache_path = str(ACK_CACHE_DIR / f"ack_{digest}.mp3")
        if os.path.exists(cache_path) and os.path.getsize(cache_path) > 256:
            if _play_audio_file(cache_path, delete_after=False, ignore_abort=ignore_abort):
                return

    temp_wav = cache_path if cache_path else str(ROOT_DIR / f"temp_tts_{int(time.time() * 1000)}.wav")

    # 1. Primary Edge Neural TTS (Indian Hindi/Hinglish & British English)
    try:
        import edge_tts
        asyncio.run(edge_tts.Communicate(synth_text, edge_voice, rate=rate).save(temp_wav))
        if _play_audio_file(temp_wav, delete_after=not cache_clip, ignore_abort=ignore_abort):
            return
    except Exception:
        if not cache_clip:
            _remove_quietly(temp_wav)
        # Secondary Indian-English Neural fallback if primary voice had a transient error
        if hindi_detected and (ignore_abort or not TTS_ABORT_EVENT.is_set()):
            try:
                import edge_tts
                asyncio.run(edge_tts.Communicate(text, voice_cfg["en_in"], rate=rate).save(temp_wav))
                if _play_audio_file(temp_wav, delete_after=True, ignore_abort=ignore_abort):
                    return
            except Exception:
                _remove_quietly(temp_wav)

    # 2. Offline Fallback to Local Piper ONNX TTS
    if ignore_abort or not TTS_ABORT_EVENT.is_set():
        piper_exe = str(ROOT_DIR / "venv" / "Scripts" / "piper.exe")
        fallback_wav = str(ROOT_DIR / f"temp_piper_{int(time.time() * 1000)}.wav")
        try:
            subprocess.run(
                [piper_exe, "-m", voice_cfg["piper"], "-f", fallback_wav],
                input=text.encode("utf-8"),
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
                timeout=15,
            )
            _play_audio_file(fallback_wav, delete_after=True, ignore_abort=ignore_abort)
        except Exception as e:
            print(f"Fallback TTS Error: {e}")
            _remove_quietly(fallback_wav)
