# J.A.R.V.I.S. (Just A Rather Very Intelligent System)

### Autonomous Desktop AI Assistant with 3D Holographic Interface, OS Automation & Bilingual Voice Processing

J.A.R.V.I.S. is an advanced desktop-level artificial intelligence assistant built in Python. Designed to bridge the gap between conversational large language models and native operating system execution, J.A.R.V.I.S. combines a WebGL-based 3D holographic interface, system-level automation, real-time satellite intelligence feeds, and bilingual voice communication across English and Hindi.

---

## Architectural Highlights

### 1. 3D Holographic Particle Interface (Zoey & Iris Architecture)
* **WebGL Particle Mesh:** Powered by Three.js, rendering a 1,200-node dynamic particle sphere using Fibonacci distribution that rotates and undulates organically in real time.
* **Audio-Reactive Deformation:** The particle field responds directly to microphone amplitude and speech synthesis frequencies, rippling dynamically during conversation.
* **Autonomous Personas:**
  * **J.A.R.V.I.S.:** Cyan illumination (`#00ffff`), calm British neural voice (`en-GB-RyanNeural` / `hi-IN-MadhurNeural`).
  * **F.R.I.D.A.Y.:** Ruby Crimson illumination (`#ff0033`), assertive female neural voice (`en-GB-SoniaNeural` / `hi-IN-SwaraNeural`).
  * **Z.O.E.Y.:** Amber Orange illumination (`#ff7700`), dynamic companion profile (`en-US-JennyNeural`).
* **Picture-in-Picture (PiP) Mini-Mode:** When idle (45 seconds) or executing desktop tasks, the interface condenses into a transparent, draggable desktop widget that sleeps until summoned by wake words (`"JARVIS"`, `"FRIDAY"`, `"ZOEY"`, `"IRIS"`).
* **Global Summon Shortcut:** Press `Alt + Space` anywhere in Windows to instantly bring the assistant to full focus.

### 2. Bilingual Voice & Speech Engine (English & Hindi/Hinglish)
* **Multi-Dialect Recognition:** Tuned speech recognition pipeline capturing standard English, Indian English, and conversational Hindi/Hinglish phrasing without accent degradation.
* **Zero-Lock In-Memory Neural Synthesis:** High-fidelity speech generated via Microsoft Edge Neural TTS loaded directly into system memory, eliminating file-locking bottlenecks on Windows.
* **Offline Fallback:** Automatic fallback to local Piper TTS ONNX models when network connectivity is lost.

### 3. Deep Operating System & Hardware Automation (Mark-XXXIX Engine)
* **Application Launcher:** Normalized launcher supporting 29+ desktop applications including VS Code, Google Chrome, Spotify, Discord, WhatsApp, Steam, Notepad, Calculator, and Windows Terminal.
* **Window Management:** Voice-directed window manipulation including snapping (left/right split), maximizing, minimizing, cycling workspaces (`Alt + Tab`), and showing the desktop.
* **Hardware Controls:** Direct control of master system volume, mute toggle, and display brightness via Windows Management Instrumentation (WMI).
* **Workstation Security:** Instant workstation lock (`Win + L`) and snipping tool triggers.

### 4. Real-Time Global Intel & Financial Radar (FastMCP Architecture)
* **Parallel Asynchronous Scraping:** Built-in `httpx` async workers polling live RSS wire feeds from BBC World, CNBC, The New York Times, Al Jazeera, Bloomberg, and Reuters in under two seconds.
* **Visual Radar Integration:** Automated browser summoning of interactive live satellite dashboards:
  * Global Events Radar: `https://worldmonitor.app/`
  * Global Financial Markets: `https://finance.worldmonitor.app/`

### 5. Hybrid Cognitive Brain (Cloud Acceleration + Local Fallback)
* **Cloud Turbo Mode:** Seamless integration with Google Gemini 2.5 Flash via `GEMINI_API_KEY`, delivering ~300ms sub-second response times with zero laptop CPU overhead.
* **Local Offline Engine:** Native integration with Ollama running quantized `llama3.2` locally on CPU/GPU with bounded context windows to prevent system thermal throttling.
* **Vision Inspection:** Screen analysis engine using `moondream` capable of silently inspecting the user's active display.

---

## System Architecture

```text
Microphone Input ───────► Bilingual STT (Google Speech / Whisper)
                                   │
                                   ▼
                            Cognitive Engine
                     ┌─────────────┴─────────────┐
                     ▼                           ▼
            Cloud Gemini Flash            Local Ollama 3.2
            (Zero CPU, ~300ms)          (100% Offline Core)
                     │                           │
                     └─────────────┬─────────────┘
                                   │
             ┌─────────────────────┼─────────────────────┐
             ▼                     ▼                     ▼
     Deep OS Automation    Live World Intel      Bilingual Neural TTS
    - Application Launch   - Parallel RSS Feeds  - hi-IN-MadhurNeural
    - Window Snapping      - World Monitor Radar - hi-IN-SwaraNeural
    - Volume & Brightness  - Market Briefings    - en-GB-RyanNeural
             │                     │                     │
             └─────────────────────┼─────────────────────┘
                                   │
                                   ▼
             3D Holographic Particle Interface (Three.js WebGL)
             - Floating Draggable Mini-Mode (PiP)
             - Global Quick-Summon Overlay (Alt + Space)
```

---

## Installation & Setup

### Prerequisites
* Operating System: Windows 10 or Windows 11
* Python: Version 3.10, 3.11, or 3.12
* Optional: [Ollama](https://ollama.com/) (for offline local execution)

### 1. Clone the Repository
```bash
git clone https://github.com/Pranshu125/J.A.R.V.I.S.git
cd J.A.R.V.I.S
```

### 2. Configure Virtual Environment & Dependencies
```powershell
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Optional Environment Configuration
For sub-second cloud acceleration (recommended for zero CPU usage), set your free Gemini API key:
```powershell
# In PowerShell:
$env:GEMINI_API_KEY="your-gemini-api-key-here"

# Or create a .env file in the root directory:
GEMINI_API_KEY=your-gemini-api-key-here
```
If no API key is specified, the system automatically uses local Ollama (`llama3.2`).

### 4. Launch J.A.R.V.I.S.
Run the startup batch script or launch directly via Python:
```powershell
python jarvis_master.py
```

---

## Command Reference

### System & Window Automation
* `"Open VS Code"` / `"Launch Spotify"` / `"Open WhatsApp"`
* `"Snap this window to the left"` / `"Snap right"`
* `"Maximize window"` / `"Minimize window"` / `"Show desktop"`
* `"Volume up"` / `"Volume down"` / `"Mute audio"`
* `"Brightness up"` / `"Brightness down"`
* `"Lock workstation"` / `"Take a screenshot"`

### Bilingual Hindi & Hinglish Interactions
* `"WhatsApp khol do"` (Launches WhatsApp)
* `"YouTube pe Starboy chala do"` (Searches and plays music on YouTube)
* `"System ka volume badha do"` (Increases master volume)
* `"Left side pe WhatsApp set kar aur right side pe Chrome"` (Window tiling)
* `"Aaj ka mausam kaisa hai?"` (Reports localized satellite weather)
* `"Kaisa chal raha hai boss?"` (Conversational status check)

### World Intel & Financial Intelligence
* `"What's happening in the world?"` / `"Give me a world news brief"`
* `"What's the financial update?"` / `"Market news"`
* `"Open the world monitor"` (Launches interactive world radar)
* `"Open the finance monitor"` (Launches market visualizer)

### Persona Switching
* `"Switch to Friday"` (Switches to F.R.I.D.A.Y. mode, crimson HUD, female voice)
* `"Switch to Zoey"` (Switches to Z.O.E.Y. mode, amber HUD)
* `"Switch to Jarvis"` (Switches back to J.A.R.V.I.S. mode, cyan HUD, male voice)

---

## License
This project is open-source and licensed under the MIT License.
