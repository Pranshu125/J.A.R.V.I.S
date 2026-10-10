# J.A.R.V.I.S. & F.R.I.D.A.Y. — Unified Cognitive Operating System

An enterprise-grade, real-time bilingual voice and spatial desktop operating system for Windows. This system unifies the complete action, agent, vision, radar, and UI capabilities of 11 open-source reference architectures alongside the Zoey OS 3D spatial workspace design, strictly locked to two core personas: **J.A.R.V.I.S.** (Male, Cyan HUD) and **F.R.I.D.A.Y.** (Female, Crimson HUD) with seamless English and Hindi/Hinglish execution.

---

## 1. Repository-by-Repository Comparative Analysis & Integration Matrix

All reference repositories were cloned into `Repos/`, analyzed file-by-file, and merged into this unified build so that `D:\JARVIS` acts as a strict superset of every single repository:

| Reference Repository | Core Capabilities in Reference Repo | How Integrated & Upgraded in `D:\JARVIS` |
| :--- | :--- | :--- |
| **FatihMakes/Mark-LV** | 17 auto-discovered `TOOL` modules (`open_app`, `web_search`, `weather_report`, `send_message`, `reminder`, `youtube_video`, `computer_settings`, `browser_control`, `file_controller`, `desktop_control`, `code_helper`, `dev_agent`, `computer_control`, `game_updater`, `flight_finder`, `file_processor`, `video_player`), `core/undo.py`, `core/confirm.py`, `memory/memory_manager.py`, `actions/background_monitor.py`, `actions/system_monitor.py`, `actions/proactive.py` | 100% of all 17 action modules auto-loaded via `core/action_loader.py` inside `modules/mark_lv_bridge.py`, plus `undo`, `confirm`, `memory_manager`, `background_monitor`, `system_monitor`, and `proactive` wired into `jarvis_master.py` and patched to `gemini-3.8-flash`. |
| **FatihMakes/Mark-XXXIX-OR** | Autonomous multi-step Agent (`agent/planner.py`, `agent/executor.py`, `agent/task_queue.py`, `agent/error_handler.py`) that decomposes complex goals, injects context across steps, auto-translates, and self-heals failed steps | Integrated as the `agent_task` tool in `modules/mark_lv_bridge.py` and exposed to Gemini 3.8 Flash and Ollama. |
| **FatihMakes/Mark-X.1** & **AI-Assistant-1.1** | Live 200km OpenSky Network aircraft transponder radar (`aircraft_module.py`), Haversine distance/bearing calculation, flight route lookup, and FlightRadar24 map launcher | Integrated as the `aircraft_report` tool and dedicated HUD quick-action button (`api.scan_airspace()`). |
| **FatihMakes/Mark-X-TR**, **Mark-X**, & **AI-Assistant-for-Computer** | Subprocess window suppression (`CREATE_NO_WINDOW`), dynamic path resolution, and localized multi-language system prompts | Integrated global `subprocess.Popen` console suppression in `jarvis_master.py` and bilingual English + Hindi/Hinglish prompt & neural voice routing in `modules/tts_engine.py`. |
| **SAGAR-TAMANG/ultron-by-sagar-builds** | Multi-layer Three.js holographic wireframe sphere + orbital rings (`lib/orbScene.ts`) and MediaPipe HandLandmarker 1-hand pinch-to-spin / 2-hand pinch-to-zoom (`lib/handTracker.ts`) | Integrated directly into `hud.html` (`initThreeOrb` 3-layer holographic orb + `toggleHandTracking` MediaPipe WebGL hand-gesture controller). |
| **SAGAR-TAMANG/friday-tony-stark-demo** | Parallel RSS global/financial intelligence (`modules/world_intel.py`), interactive `worldmonitor.app` satellite launch, and multi-app Windows control | Integrated via `modules/world_intel.py`, `modules/system_control.py`, and HUD quick-launch pills. |
| **Zoey OS (`zoeyos.com`)** | 3D particle centerpiece, persistent long-term memory vault, and multi-agent workspace | Integrated 1,200-node Fibonacci audio-reactive core inside the multi-ring holographic orb and structured `memory/long_term.json` prompt injection. |

---

## 2. Complete 35-Tool Autonomous Capability Inventory

Every command spoken in English or Hindi/Hinglish (or typed in the HUD) is routed by **Gemini 3.8 Flash** (with local **Ollama `llama3.2`** fallback) across 35 native tools:

### A. Mark-LV Auto-Discovered Action Suite (17 Modules)
1. **`open_app`**: Launch, close, minimize, maximize, or switch to any installed desktop application (`winreg`, `psutil`, `pyautogui`).
2. **`web_search`**: DuckDuckGo search (`mode='search'`), breaking news (`mode='news'`), and multi-product comparison (`mode='compare'`).
3. **`weather_report`**: City/timeframe weather forecasts (`today`, `tomorrow`, `week`) plus live Windy.com radar display.
4. **`send_message`**: Automated messaging across WhatsApp, Telegram, Instagram, and Discord.
5. **`reminder`**: Persistent desktop notifications scheduled via Windows Task Scheduler (`schtasks`).
6. **`youtube_video`**: Play YouTube videos, summarize video transcripts (`youtube_transcript_api`), fetch metadata (`yt_dlp`), or list trending videos.
7. **`computer_settings`**: Volume up/down/set/mute, brightness up/down/set, dark mode toggle, Wi-Fi/Bluetooth toggles, lock screen, sleep, restart, shutdown, tab/zoom/scroll controls.
8. **`browser_control`**: Playwright/CDP smart browser automation (`go_to`, `search`, `click`, `type`, `scroll`, `fill_form`, `smart_click`, `smart_type`, `get_text`, `press`, `close`).
9. **`file_controller`**: File & directory operations (`list`, `create_file`, `create_folder`, `delete` via `send2trash`, `move`, `copy`, `rename`, `read`, `write`, `find`, `largest`, `disk_usage`, `organize`, `info`).
10. **`desktop_control`**: Set desktop wallpaper from local file or URL (`SystemParametersInfoW`), organize desktop by file type or date, clean desktop, inspect desktop stats.
11. **`code_helper`**: Generate, edit, explain, run, or auto-fix code in any programming language and open in VS Code.
12. **`dev_agent`**: Autonomous multi-file software architect that plans, scaffolds, installs dependencies, opens VS Code, runs, and auto-debugs full projects.
13. **`computer_control`**: Direct GUI mouse/keyboard automation (`type`, `smart_type`, `click`, `double_click`, `right_click`, `hotkey`, `press`, `scroll`, `move`, `drag`, `copy`, `paste`, `screenshot`, `screen_find`, `focus_window`, `random_data`).
14. **`game_updater`**: Game launcher, installer, updater, and scheduled background updater across Steam, Epic Games, Riot, Xbox, GOG, Ubisoft, EA, and Battle.net.
15. **`flight_finder`**: Live Google Flights route, airline, duration, and price search.
16. **`file_processor`**: Multi-format file intelligence for attached/local files (`📎` button in HUD): PDFs (summarize, extract text, convert to Word), Images (OCR, describe, resize, compress, convert), DOCX/TXT (summarize, translate, fix writing), Excel/CSV (analyze, filter, sort), Audio/Video, and Archives.
17. **`video_player`**: Play, stop, summarize, or analyze specific timestamps of video files and streams.

### B. Core, Agent, Radar, Memory, Vision & Workspace Tools (18 Tools)
18. **`screen_process` / `analyze_screen`**: Captures the display (`mss`) or webcam (`cv2`) and analyzes it with **Gemini 3.8 Flash Vision**.
19. **`aircraft_report`**: Scans a 200km radius around the user's coordinates via the **OpenSky Network API** (reporting callsign, registration country, distance, speed in km/h, and heading) or opens the live **FlightRadar24** map.
20. **`agent_task`**: Deploys the **Mark-XXXIX Autonomous Agent Planner & Executor** (`agent/planner.py`, `agent/executor.py`) for complex multi-step goals with automatic error recovery.
21. **`save_memory`**: Stores structured user facts (`identity`, `preferences`, `projects`, `relationships`, `wishes`, `notes`) in `memory/long_term.json`.
22. **`recall_memory`**: Searches the permanent long-term memory vault by keyword.
23. **`manage_monitor`**: Adds, removes, lists, or checks daily background news/topic monitors (`actions/background_monitor.py`).
24. **`system_status`**: Deep hardware telemetry report (CPU %, RAM GB, NVML GPU %, WMI CPU temperature, uptime, and active process count).
25. **`undo`**: Reverses the last file, desktop, or system setting operation (`core/undo.py`) or lists the undo stack.
26. **`split_workspace`**: Tiles two applications side-by-side (`Win+Left` and `Win+Right`).
27. **`get_world_news` & `open_world_monitor`**: Parallel RSS global intelligence + interactive satellite dashboard (`worldmonitor.app`).
28. **`get_finance_news` & `open_finance_monitor`**: Live financial market feeds + interactive market monitor.
29. **`launch_application` / `system_hardware_control` / `window_management` / `open_website` / `execute_terminal`**: Fast-path OS & PowerShell execution.

---

## 3. Architecture & File Structure

```text
D:\JARVIS\
├── jarvis_master.py          # Master pipeline, Gemini 3.8 Flash + Ollama router, STT/TTS workers, pywebview API
├── hud.html                  # 3-Layer Three.js Holographic Orb, MediaPipe Hand Gestures, Telemetry & Tactical HUD
├── START_JARVIS.bat          # One-click desktop launcher
├── modules\
│   ├── mark_lv_bridge.py     # Unified bridge loading all 17 Mark-LV actions, Mark-XXXIX Agent, OpenSky Radar & Vision
│   ├── system_control.py     # Win32 hardware, window management, and split-screen workspace tiling
│   ├── tts_engine.py         # Zero-lock in-memory bilingual Edge-TTS engine (JARVIS & FRIDAY voices)
│   └── world_intel.py        # Parallel RSS news & financial intelligence scrapers
└── Repos\                    # Cloned reference repositories (Mark-LV, Mark-XXXIX-OR, ultron-by-sagar-builds, etc.)
```

---

## 4. Installation & Usage

### Prerequisites
- Windows 10 or Windows 11 (64-bit)
- Python 3.10+ with virtual environment in `D:\JARVIS\venv`
- `GEMINI_API_KEY` configured in `.env` or Windows User Environment Variables

### Launching
Double-click the **`J.A.R.V.I.S`** shortcut on your Desktop, or run:

```powershell
D:\JARVIS\START_JARVIS.bat
```
