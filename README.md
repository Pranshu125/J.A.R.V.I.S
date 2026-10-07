<div align="center">
  <h1>J.A.R.V.I.S. </h1>
  <p><b>Just A Rather Very Intelligent System</b></p>
  <p><i>A Mixed Reality, Local-First AI Assistant with Spatial Hand Tracking</i></p>
</div>

---

## 🔮 Overview

J.A.R.V.I.S. is an advanced, offline-first personal AI assistant built in Python. Designed to break free from standard 2D chat interfaces, this project utilizes a combination of **Local LLMs**, **WebAudio visualizers**, and **Computer Vision** to create a highly responsive, spatial Command Center.

By leveraging Google MediaPipe, J.A.R.V.I.S. maps your physical hand movements to a holographic HUD, allowing you to manipulate the parallax UI using gestures in thin air.

## ✨ Core Features

*   **🧠 Local Intelligence Engine:** Powered entirely by [Ollama](https://ollama.com/) (Llama-3). 100% offline, private, and free from API rate limits.
*   **🖐️ "Barehands" Spatial Tracking:** Integrates `opencv-python` and `mediapipe` to track your hand coordinates via webcam. Control the 3D parallax interface with physical gestures instead of a mouse.
*   **👁️ Mixed Reality HUD:** A beautiful, borderless, frameless glassmorphism UI built with `pywebview`, featuring a 3D parallax core, real-time hardware telemetry (CPU/RAM), and a scrolling command ticker.
*   **🎙️ Native Audio Reactivity:** An HTML5 Canvas engine acts as a real-time oscilloscope, causing the UI to physically spike and pulse perfectly in sync with the AI's synthesized voice.
*   **📓 Markdown Memory Vault:** Long-term conversational state is dynamically serialized into readable `.md` files (Obsidian-style vault) rather than complex vector databases.
*   **⚙️ Agentic Tool Execution:** Built-in ReAct logic allowing J.A.R.V.I.S. to natively interact with Windows (locking the system, launching browsers, system time, etc.).

## 🛠️ Tech Stack

*   **Backend:** Python 3, `requests` (Ollama REST integration), `speech_recognition`, `edge-tts`.
*   **Computer Vision:** OpenCV (`cv2`), Google MediaPipe (`mp.solutions.hands`).
*   **Frontend UI:** PyWebView, HTML5 Canvas, CSS Grid, Glassmorphism.
*   **Telemetry:** `psutil`

## 🚀 Installation & Setup

### 1. Install the Local Brain (Ollama)
J.A.R.V.I.S. requires a local LLM to function offline. 
1. Download and install [Ollama for Windows](https://ollama.com/download/windows).
2. Open your terminal and pull the Llama-3 neural weights:
   ```bash
   ollama pull llama3
   ```

### 2. Install Python Dependencies
Clone this repository and install the required libraries:
```bash
git clone https://github.com/Pranshu125/J.A.R.V.I.S.git
cd J.A.R.V.I.S
pip install opencv-python mediapipe pywebview SpeechRecognition edge-tts pygame psutil
```

## 🎮 Usage

Launch the master pipeline:
```bash
python jarvis_master.py
```

### Voice Commands
J.A.R.V.I.S. listens continuously in the background. Aside from general conversation, you can trigger specific system tools:
*   *"Open YouTube"* / *"Play a song"*
*   *"Lock the system"*
*   *"What is the time?"*
*   **Spatial Tracking Toggle:** Say *"Enable gestures"* or *"Turn on webcam"* to activate the MediaPipe vision engine. The UI will lock onto your physical hand. Say *"Disable gestures"* to return to normal mouse tracking.

## 🤝 Contributing
Contributions are welcome! Whether it's adding new Agentic tools, refining the CSS HUD, or expanding the computer vision capabilities. Feel free to open a pull request.

---
<div align="center">
  <i>"Good day. Advanced cognitive systems are now fully independent."</i>
</div>
