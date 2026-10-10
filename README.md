# J.A.R.V.I.S. (Just A Rather Very Intelligent System)

### Autonomous Desktop AI Assistant with 3D Holographic Interface, OS Automation, World Intelligence & Bilingual Speech Processing

J.A.R.V.I.S. is an enterprise-grade desktop artificial intelligence assistant designed for Windows operating systems. By combining a 3D WebGL holographic particle interface, low-latency asynchronous system automation, parallel real-time news telemetry, and a bilingual voice pipeline across English and Hindi/Hinglish, J.A.R.V.I.S. delivers a responsive, hands-free personal operating environment.

---

## Technical Architecture Overview

The system architecture is structured into five core subsystems:

```text
+-----------------------------------------------------------------------------------+
|                                  USER INTERFACE                                   |
|   Three.js WebGL 3D Holographic Core Orb (1,200 Dynamic Fibonacci Nodes)          |
|   Real-Time Telemetry Panels (CPU, RAM, Network Throughput, Weather Radar)        |
|   Picture-in-Picture (PiP) Transparent Floating Mode with Alt+Space Quick-Summon  |
+------------------------------------------+----------------------------------------+
                                           |
                                           v
+-----------------------------------------------------------------------------------+
|                             SPEECH PROCESSING PIPELINE                            |
|   Input:  Dual-Language Speech Recognition (Google Speech API / Faster-Whisper)   |
|   Output: In-Memory Edge Neural TTS (en-GB-RyanNeural, hi-IN-MadhurNeural,        |
|           en-GB-SoniaNeural, hi-IN-SwaraNeural) + Offline Piper TTS Fallback      |
+------------------------------------------+----------------------------------------+
                                           |
                                           v
+-----------------------------------------------------------------------------------+
|                             HYBRID COGNITIVE ENGINE                               |
|   Cloud Accelerated Tier: Google Gemini 2.5 Flash (~300ms latency, zero host CPU) |
|   Local Autonomous Tier:  Ollama LLaMA-3.2 (Quantized local inference engine)    |
|   Vision Inspection Tier: Moondream 2 Local VLM for Screen Analysis               |
+------------------------------------------+----------------------------------------+
                                           |
                                           v
+-----------------------------------------------------------------------------------+
|                             EXECUTION & TOOL ROUTING                              |
|   System Control: WMI Brightness, PyAutoGUI Snapping, App Aliases (29+ Apps)      |
|   Iris Workspace: Dual-Window Workspace Tiling (Split Screen Left/Right)          |
|   World Intel:    Parallel Asynchronous RSS Parsers + Satellite Radar Dashboards  |
|   Security:       CREATE_NO_WINDOW Silent Process Sandboxing                      |
+-----------------------------------------------------------------------------------+
```

---

## Core Capabilities

### 1. 3D Holographic Core Interface (WebGL Particle System)
* **Fibonacci Sphere Distribution:** Renders 1,200 particle nodes distributed organically across a spherical manifold using Three.js, simulating a futuristic arc reactor core.
* **Audio-Reactive Harmonic Deformation:** The particle geometry dynamically reacts to microphone frequency amplitudes and speech synthesis state changes, undulating on a mathematical wave function:
  $$\Delta r = \sin(4\phi + 3t) \cdot \cos(3\theta + 2t) \cdot (3.5 \cdot \text{Pulse})$$
* **Strict Persona Illumination:**
  * **J.A.R.V.I.S.:** Cyan illumination (`#00ffff`), British neural voice profile (`en-GB-RyanNeural` for English, `hi-IN-MadhurNeural` for Hindi).
  * **F.R.I.D.A.Y.:** Ruby Crimson illumination (`#ff0033`), tactical female voice profile (`en-GB-SoniaNeural` for English, `hi-IN-SwaraNeural` for Hindi).
* **Picture-in-Picture (PiP) Floating HUD:** When idle for 45 seconds or when executing external desktop tasks, the interface contracts into a minimal, draggable desktop orb.
* **Global Summon Hotkey:** Press `Alt + Space` globally across any Windows program to wake the assistant and restore full focus.

### 2. Seamless Bilingual Voice Engine (English & Hindi/Hinglish)
* **Bilingual Speech Recognition:** Speech-to-Text configured with multi-dialect support (`en-IN`), seamlessly parsing pure English, Indian English, and conversational Hindi/Hinglish phrasing.
* **Zero-Lock In-Memory Audio Playback:** Resolves the Windows `pygame.mixer.music` file-locking limitation by loading raw synthesized audio buffers directly into RAM via `pygame.mixer.Sound`, executing immediate disk cleanup without locking audio threads.
* **Contextual Spoken Acknowledgments:** Dispatches immediate acknowledgments ("Right away, sir", "Ji boss", "Bilkul sir") prior to tool execution to achieve near-zero perceived latency.
* **Offline Fallback Architecture:** Automatically routes to locally hosted ONNX Piper models (`en_GB-alan-medium.onnx`, `en_GB-jenny_dioco-medium.onnx`) if network connectivity drops.

### 3. Deep Operating System & Hardware Control
* **Dual-Window Workspace Tiling:** Automates side-by-side application organization with one voice command (e.g., launching WhatsApp on the left half and Google Chrome on the right half).
* **Normalized Application Launcher:** Direct alias resolution for over 29 desktop applications, including VS Code, Google Chrome, Spotify, Discord, WhatsApp, Windows Terminal, Steam, Notepad, Calculator, and Task Manager.
* **Display & Volume Automation:** Interacts with Windows Management Instrumentation (WMI) to adjust monitor brightness in real time and adjusts master audio volume levels via PyAutoGUI.
* **Silent Process Execution:** Enforces `CREATE_NO_WINDOW` across all background command executions, preventing disruptive black command prompt windows from interrupting the user.

### 4. Live Global Intelligence & Financial Telemetry
* **Parallel Asynchronous Scraping:** Built-in `httpx` async workers polling live RSS wire feeds from BBC World, CNBC, The New York Times, Al Jazeera, Bloomberg, and Reuters in under two seconds.
* **Live Radar Dashboards:** Direct summoning of satellite dashboards:
  * Global Conflict & Event Radar: `https://worldmonitor.app/`
  * Global Market Radar: `https://finance.worldmonitor.app/`

---

## Installation & Environment Configuration

### Prerequisites
* Windows 10 or Windows 11 (64-bit)
* Python 3.10, 3.11, or 3.12
* Optional: [Ollama](https://ollama.com/) (for 100% offline local inference)

### Step 1: Clone the Repository
```powershell
git clone https://github.com/Pranshu125/J.A.R.V.I.S.git
cd J.A.R.V.I.S
```

### Step 2: Set Up Virtual Environment
```powershell
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

### Step 3: Configure Environment Variables
To enable sub-second cloud inference with zero host CPU usage, set your free Google Gemini API key:
```powershell
$env:GEMINI_API_KEY="your-gemini-api-key-here"
```
Or create a `.env` file in the project root:
```ini
GEMINI_API_KEY=your-gemini-api-key-here
```
If no API key is detected, the engine defaults automatically to local Ollama (`llama3.2`).

### Step 4: Launch J.A.R.V.I.S.
Execute the one-click startup batch script:
```powershell
.\START_JARVIS.bat
```
Or run directly via Python:
```powershell
python jarvis_master.py
```

---

## Voice & Interaction Reference

### Workspace & Window Management
* "Split screen between WhatsApp and Chrome"
* "Left side pe WhatsApp set kar aur right side pe Chrome"
* "Snap this window to the left"
* "Maximize window"
* "Minimize window"
* "Show desktop"
* "Lock workstation"
* "Take a screenshot"

### Hardware & Volume Controls
* "Increase volume by 10 percent"
* "System ka volume badha do"
* "Mute system audio"
* "Chup raho" / "Stop talking"
* "Increase screen brightness"
* "Brightness kam karo"

### World Intelligence & Financial Radar
* "What is happening in the world today?"
* "Give me a global news brief"
* "Market news update"
* "Open the world monitor"
* "Open the finance monitor"

### Strict Persona Switching
* "Switch to Friday" (Activates F.R.I.D.A.Y. mode, crimson HUD, female neural voice)
* "Switch to Jarvis" (Activates J.A.R.V.I.S. mode, cyan HUD, male neural voice)

---

## Repository Structure

```text
D:\JARVIS
├── modules/
│   ├── system_control.py      # WMI hardware control, 29+ app launcher aliases, split-screen tiling
│   ├── tts_engine.py          # Zero-lock in-memory neural speech synthesis (Edge-TTS + Piper)
│   └── world_intel.py         # Parallel async RSS news scraping & satellite radar launchers
├── models/                    # Offline Piper ONNX neural voice models
├── hud.html                   # Three.js 3D WebGL holographic particle orb & real-time telemetry HUD
├── jarvis_master.py           # Core orchestrator: pipeline threads, tool dispatch, hybrid LLM routing
├── jarvis_state.md            # Rolling conversational memory vault
├── requirements.txt           # Python package dependencies
├── START_JARVIS.bat           # Production startup batch launcher
└── README.md                  # System documentation
```

---

## Technical Specifications

| Parameter | Specification |
| :--- | :--- |
| Interface Framework | PyWebView with HTML5, CSS3, Three.js WebGL |
| 3D Geometry | 1,200 particle nodes, Fibonacci spherical distribution |
| Speech-to-Text | Dual-Language Google Speech API (`en-IN`) / Faster-Whisper |
| Text-to-Speech | Edge-TTS (`hi-IN-MadhurNeural`, `hi-IN-SwaraNeural`, `en-GB-RyanNeural`, `en-GB-SoniaNeural`) |
| Offline TTS Fallback | Piper ONNX (`en_GB-alan-medium`, `en_GB-jenny_dioco-medium`) |
| Cognitive Processing | Google Gemini 2.5 Flash (Cloud) / Ollama LLaMA-3.2 (Local) |
| Vision Processing | Moondream 2 Local VLM |
| Hardware Abstraction | Windows Management Instrumentation (WMI), PyAutoGUI, PSUtil |
| Process Management | `subprocess.CREATE_NO_WINDOW` background isolation |

---

## License

This project is licensed under the MIT License.
