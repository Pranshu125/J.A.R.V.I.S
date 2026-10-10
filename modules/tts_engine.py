"""
tts_engine.py - High-Performance Dual-Language Neural Speech Synthesis
Supports English & Authentic Indian Hindi/Hinglish (J.A.R.V.I.S. & F.R.I.D.A.Y.)
Uses edge-tts (hi-IN-MadhurNeural / hi-IN-SwaraNeural / en-IN-PrabhatNeural / en-IN-NeerjaExpressiveNeural)
with automatic Roman-Hinglish-to-Devanagari phonetic conversion so Indian accents sound 100% real and natural.
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
        "en_in": "en-IN-PrabhatNeural",
        "hi": "hi-IN-MadhurNeural",
        "piper": "models/en_GB-alan-medium.onnx",
    },
    "FRIDAY": {
        "en": "en-GB-SoniaNeural",
        "en_in": "en-IN-NeerjaExpressiveNeural",
        "hi": "hi-IN-SwaraNeural",
        "piper": "models/en_GB-jenny_dioco-medium.onnx",
    },
}

# Comprehensive Roman-Hinglish -> Devanagari phonetic dictionary for natural Indian TTS pronunciation.
# English loanwords (sir, boss, system, online, WhatsApp, YouTube, Chrome, CPU, RAM) remain in Latin script
# so hi-IN-MadhurNeural and hi-IN-SwaraNeural pronounce them with a natural Indian-English accent while
# pronouncing all Hindi words with 100% native Hindi phonetics.
HINGLISH_PHONETIC_MAP = {
    # Greetings & Respect
    "namaste": "नमस्ते",
    "namaskar": "नमस्कार",
    "pranam": "प्रणाम",
    "shukriya": "शुक्रिया",
    "dhanyawad": "धन्यवाद",
    "dhanyavaad": "धन्यवाद",
    "alvida": "अलविदा",
    "ji": "जी",
    "hukum": "हुकुम",
    "sahab": "साहब",
    "bhai": "भाई",
    "dost": "दोस्त",
    "yaar": "यार",
    # Pronouns & Possessives
    "main": "मैं",
    "mai": "मैं",
    "mein": "में",
    "me": "में",
    "mujhe": "मुझे",
    "mujhko": "मुझको",
    "mera": "मेरा",
    "meri": "मेरी",
    "mere": "मेरे",
    "hum": "हम",
    "humein": "हमें",
    "humara": "हमारा",
    "hamara": "हमारा",
    "aap": "आप",
    "aapka": "आपका",
    "aapki": "आपकी",
    "aapke": "आपके",
    "aapko": "आपको",
    "tum": "तुम",
    "tumhara": "तुम्हारा",
    "tumhari": "तुम्हारी",
    "apna": "अपना",
    "apni": "अपनी",
    "apne": "अपने",
    "yeh": "यह",
    "ye": "ये",
    "woh": "वह",
    "wo": "वो",
    "iska": "इसका",
    "iski": "इसकी",
    "uska": "उसका",
    "uski": "उसकी",
    "inka": "इनका",
    "unka": "उनका",
    # Question words
    "kya": "क्या",
    "kyun": "क्यों",
    "kyo": "क्यों",
    "kab": "कब",
    "kahan": "कहाँ",
    "kaha": "कहाँ",
    "kaise": "कैसे",
    "kaisa": "कैसा",
    "kaisi": "कैसी",
    "kaun": "कौन",
    "kon": "कौन",
    "kitna": "कितना",
    "kitni": "कितनी",
    "kitne": "कितने",
    "kisne": "किसने",
    "kisko": "किसको",
    # Auxiliary & Copula verbs
    "hai": "है",
    "hain": "हैं",
    "hoon": "हूँ",
    "hu": "हूँ",
    "hun": "हूँ",
    "ho": "हो",
    "tha": "था",
    "thi": "थी",
    "the": "थे",
    "hoga": "होगा",
    "hogi": "होगी",
    "honge": "होंगे",
    "raha": "रहा",
    "rahi": "रही",
    "rahe": "रहे",
    "gaya": "गया",
    "gayi": "गई",
    "gaye": "गए",
    "diya": "दिया",
    "diye": "दिए",
    "liya": "लिया",
    "liye": "लिए",
    "chuka": "चुका",
    "chuki": "चुकी",
    "chuke": "चुके",
    "sakta": "सकता",
    "sakti": "सकती",
    "sakte": "सकते",
    "chahiye": "चाहिए",
    "padega": "पड़ेगा",
    # Common Action Verbs
    "kar": "कर",
    "karo": "करो",
    "kariye": "करिए",
    "kijiye": "कीजिए",
    "karna": "करना",
    "karta": "करता",
    "karti": "करती",
    "karte": "करते",
    "kiya": "किया",
    "kiye": "किए",
    "khol": "खोल",
    "kholo": "खोलो",
    "kholna": "खोलना",
    "khola": "खोला",
    "band": "बंद",
    "chala": "चला",
    "chalao": "चलाओ",
    "chalana": "चलाना",
    "chalu": "चालू",
    "chal": "चल",
    "chalo": "चलो",
    "ruko": "रुको",
    "rok": "रोक",
    "roko": "रोको",
    "bata": "बता",
    "batao": "बताओ",
    "bataye": "बताइए",
    "bataiye": "बताइए",
    "batana": "बताना",
    "dekho": "देखो",
    "dekh": "देख",
    "dekhiye": "देखिए",
    "dekhna": "देखना",
    "dikh": "दिख",
    "dikhao": "दिखाओ",
    "dikha": "दिखा",
    "suno": "सुनो",
    "sun": "सुन",
    "suniye": "सुनिए",
    "sunao": "सुनाओ",
    "bol": "बोल",
    "bolo": "बोलो",
    "boliye": "बोलिए",
    "likh": "लिख",
    "likho": "लिखो",
    "padh": "पढ़",
    "padho": "पढ़ो",
    "bhej": "भेज",
    "bhejo": "भेजो",
    "laga": "लगा",
    "lagao": "लगाओ",
    "badha": "बढ़ा",
    "badhao": "बढ़ाओ",
    "kam": "कम",
    "hata": "हटा",
    "hatao": "हटाओ",
    "dhundho": "ढूँढो",
    "khojo": "खोजो",
    "jao": "जाओ",
    "aao": "आओ",
    "uth": "उठ",
    "utho": "उठो",
    # Adverbs, Adjectives & Conjunctions
    "aaj": "आज",
    "kal": "कल",
    "abhi": "अभी",
    "ab": "अब",
    "baad": "बाद",
    "pehle": "पहले",
    "subah": "सुबह",
    "dopahar": "दोपहर",
    "shaam": "शाम",
    "raat": "रात",
    "din": "दिन",
    "waqt": "वक़्त",
    "samay": "समय",
    "yahan": "यहाँ",
    "wahan": "वहाँ",
    "upar": "ऊपर",
    "neeche": "नीचे",
    "andar": "अंदर",
    "bahar": "बाहर",
    "aage": "आगे",
    "peeche": "पीछे",
    "bilkul": "बिल्कुल",
    "zaroor": "ज़रूर",
    "acha": "अच्छा",
    "accha": "अच्छा",
    "achha": "अच्छा",
    "theek": "ठीक",
    "thik": "ठीक",
    "sahi": "सही",
    "galat": "ग़लत",
    "bahut": "बहुत",
    "bohot": "बहुत",
    "zyada": "ज़्यादा",
    "thoda": "थोड़ा",
    "sab": "सब",
    "sabhi": "सभी",
    "sara": "सारा",
    "saare": "सारे",
    "kuch": "कुछ",
    "koi": "कोई",
    "nahi": "नहीं",
    "nhi": "नहीं",
    "na": "ना",
    "mat": "मत",
    "haan": "हाँ",
    "han": "हाँ",
    "aur": "और",
    "ya": "या",
    "lekin": "लेकिन",
    "magar": "मगर",
    "agar": "अगर",
    "toh": "तो",
    "bhi": "भी",
    "hi": "ही",
    "se": "से",
    "ko": "को",
    "ka": "का",
    "ki": "की",
    "ke": "के",
    "par": "पर",
    "pe": "पे",
    "tak": "तक",
    "wala": "वाला",
    "wali": "वाली",
    "wale": "वाले",
    # Common Nouns
    "kaam": "काम",
    "baat": "बात",
    "haal": "हाल",
    "cheez": "चीज़",
    "jagah": "जगह",
    "ghar": "घर",
    "gaana": "गाना",
    "awaaz": "आवाज़",
    "mausam": "मौसम",
    "khabar": "ख़बर",
    "asman": "आसमान",
    "aasman": "आसमान",
    "chehra": "चेहरा",
    "haath": "हाथ",
    "naam": "नाम",
    "sawal": "सवाल",
    "jawab": "जवाब",
    "madad": "मदद",
    "taiyar": "तैयार",
}

# Distinct Hindi/Hinglish trigger words (excluding ambiguous English words like 'the', 'me', 'hi', 'to', 'in')
UNAMBIGUOUS_HINGLISH_WORDS = set(HINGLISH_PHONETIC_MAP.keys()) - {"the", "me", "hi", "main"}


def is_hindi(text: str) -> bool:
    """Detect if text contains Devanagari script or any Roman Hindi/Hinglish words."""
    if not text:
        return False
    if re.search(r"[\u0900-\u097F]", text):
        return True
    words = re.findall(r"[a-zA-Z]+", text.lower())
    if not words:
        return False
    hits = sum(1 for w in words if w in UNAMBIGUOUS_HINGLISH_WORDS)
    return hits >= 1


def normalize_hinglish_for_indian_tts(text: str) -> str:
    """
    Convert Roman-script Hindi words in a Hinglish sentence to Devanagari script
    while leaving English words intact so hi-IN-MadhurNeural / hi-IN-SwaraNeural
    speak with a 100% authentic Indian accent.
    """
    def _replace_token(match: re.Match) -> str:
        word = match.group(0)
        low = word.lower()
        # Only convert 'me', 'main', 'hi', 'the' when inside a detected Hindi/Hinglish sentence
        if low in HINGLISH_PHONETIC_MAP:
            return HINGLISH_PHONETIC_MAP[low]
        return word

    return re.sub(r"\b[a-zA-Z]+\b", _replace_token, text)


def get_instant_ack(user_text: str, mode: str = "JARVIS") -> str:
    """Return a natural, context-aware pre-processing acknowledgment in English or Hindi/Hinglish."""
    import random
    t_low = (user_text or "").lower()
    if is_hindi(t_low):
        if any(k in t_low for k in ("khol", "chala", "play", "open", "start", "laga")):
            return random.choice([
                "Ji sir, abhi khol raha hoon.",
                "Bilkul boss, abhi chala raha hoon.",
                "Ji boss, abhi karta hoon.",
            ])
        return random.choice([
            "Ji sir, abhi karta hoon.",
            "Bilkul boss, dekh raha hoon.",
            "Ek second sir, kaam chal raha hai.",
            "Hukum sir, abhi check karta hoon.",
        ])
    else:
        if any(k in t_low for k in ("screen", "camera", "looking at", "what do you see", "analyze")):
            return random.choice([
                "On it, sir. Scanning now.",
                "Working on it, sir. Analyzing visual feed.",
                "Right away, sir. Inspecting now.",
            ])
        return random.choice([
            "On it, sir.",
            "Working on it, sir.",
            "Right away, sir.",
            "Processing that now, boss.",
            "One moment, sir.",
        ])

import threading

TTS_ABORT_EVENT = threading.Event()


def stop_speaking():
    """Immediately halt any active TTS synthesis and audio playback."""
    TTS_ABORT_EVENT.set()
    try:
        if pygame.mixer.get_init():
            pygame.mixer.stop()
    except Exception:
        pass


def speak_text(text: str, mode: str = "JARVIS", cache_clip: bool = False, ignore_abort: bool = False):
    """Synthesize and play speech in-memory without Windows file locking (with instant disk cache for acknowledgments)."""
    if not text or not text.strip():
        return

    if ignore_abort:
        TTS_ABORT_EVENT.clear()
    elif TTS_ABORT_EVENT.is_set():
        return

    mode = mode.upper()
    if mode not in VOICE_MAP:
        mode = "JARVIS"

    hindi_detected = is_hindi(text)
    if hindi_detected:
        # Use native Indian Hindi/Hinglish neural voice and normalize Roman Hindi tokens to Devanagari
        edge_voice = VOICE_MAP[mode]["hi"]
        synth_text = normalize_hinglish_for_indian_tts(text)
        rate = "+4%"
    else:
        edge_voice = VOICE_MAP[mode]["en"]
        synth_text = text
        rate = "+4%"

    # Fast-path disk cache for short acknowledgment phrases (1ms playback after first synthesis)
    cache_path = None
    if cache_clip:
        import hashlib
        cache_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "models", "ack_cache")
        os.makedirs(cache_dir, exist_ok=True)
        digest = hashlib.md5(f"{edge_voice}|{rate}|{synth_text}".encode("utf-8")).hexdigest()[:16]
        cache_path = os.path.join(cache_dir, f"ack_{digest}.mp3")
        if os.path.exists(cache_path) and os.path.getsize(cache_path) > 256:
            try:
                if not ignore_abort and TTS_ABORT_EVENT.is_set():
                    return
                if not pygame.mixer.get_init():
                    pygame.mixer.init()
                sound = pygame.mixer.Sound(cache_path)
                sound.play()
                while pygame.mixer.get_busy():
                    if not ignore_abort and TTS_ABORT_EVENT.is_set():
                        pygame.mixer.stop()
                        return
                    pygame.time.Clock().tick(20)
                return
            except Exception:
                pass

    temp_wav = cache_path if cache_path else f"temp_tts_{int(time.time() * 1000)}.wav"

    played = False
    # 1. High-quality Edge Neural TTS (instant, crystal-clear Indian Hindi/Hinglish & English)
    try:
        import edge_tts
        communicate = edge_tts.Communicate(synth_text, edge_voice, rate=rate)
        asyncio.run(communicate.save(temp_wav))

        if not ignore_abort and TTS_ABORT_EVENT.is_set():
            if not cache_clip and os.path.exists(temp_wav):
                try:
                    os.remove(temp_wav)
                except Exception:
                    pass
            return

        if os.path.exists(temp_wav):
            if not pygame.mixer.get_init():
                pygame.mixer.init()
            sound = pygame.mixer.Sound(temp_wav)
            if not cache_clip:
                os.remove(temp_wav)  # Immediate deletion from disk — NO file locking!
            sound.play()
            while pygame.mixer.get_busy():
                if not ignore_abort and TTS_ABORT_EVENT.is_set():
                    pygame.mixer.stop()
                    break
                pygame.time.Clock().tick(15)
            played = True
    except Exception:
        if not cache_clip and os.path.exists(temp_wav):
            try:
                os.remove(temp_wav)
            except Exception:
                pass
        # Secondary Indian English Neural fallback if primary voice had a transient error
        if hindi_detected and (ignore_abort or not TTS_ABORT_EVENT.is_set()):
            try:
                import edge_tts
                alt_voice = VOICE_MAP[mode]["en_in"]
                communicate = edge_tts.Communicate(text, alt_voice, rate="+4%")
                asyncio.run(communicate.save(temp_wav))
                if os.path.exists(temp_wav):
                    if not pygame.mixer.get_init():
                        pygame.mixer.init()
                    sound = pygame.mixer.Sound(temp_wav)
                    os.remove(temp_wav)
                    sound.play()
                    while pygame.mixer.get_busy():
                        if not ignore_abort and TTS_ABORT_EVENT.is_set():
                            pygame.mixer.stop()
                            break
                        pygame.time.Clock().tick(15)
                    played = True
            except Exception:
                if os.path.exists(temp_wav):
                    try:
                        os.remove(temp_wav)
                    except Exception:
                        pass

    # 2. Offline Fallback to Piper TTS
    if not played and (ignore_abort or not TTS_ABORT_EVENT.is_set()):
        piper_model = VOICE_MAP[mode]["piper"]
        piper_exe = os.path.join("venv", "Scripts", "piper.exe")
        fallback_wav = f"temp_piper_{int(time.time() * 1000)}.wav"
        try:
            subprocess.run(
                [piper_exe, "-m", piper_model, "-f", fallback_wav],
                input=text.encode("utf-8"),
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
            if os.path.exists(fallback_wav):
                if not pygame.mixer.get_init():
                    pygame.mixer.init()
                sound = pygame.mixer.Sound(fallback_wav)
                os.remove(fallback_wav)
                sound.play()
                while pygame.mixer.get_busy():
                    if not ignore_abort and TTS_ABORT_EVENT.is_set():
                        pygame.mixer.stop()
                        break
                    pygame.time.Clock().tick(15)
        except Exception as e:
            print(f"Fallback TTS Error: {e}")
            if os.path.exists(fallback_wav):
                try:
                    os.remove(fallback_wav)
                except Exception:
                    pass
