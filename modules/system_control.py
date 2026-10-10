"""
system_control.py - Deep Windows hardware, app launcher & window management
Ported & refined from Mark-XXXIX-OR
"""

import os
import subprocess
import time
import platform

try:
    import pyautogui
    pyautogui.FAILSAFE = True
    pyautogui.PAUSE = 0.05
    _HAS_PYAUTOGUI = True
except ImportError:
    _HAS_PYAUTOGUI = False

_APP_ALIASES = {
    "chrome": "chrome",
    "google chrome": "chrome",
    "firefox": "firefox",
    "spotify": "Spotify",
    "vscode": "code",
    "code": "code",
    "visual studio code": "code",
    "discord": "Discord",
    "telegram": "Telegram",
    "whatsapp": "WhatsApp",
    "notepad": "notepad.exe",
    "calculator": "calc.exe",
    "calc": "calc.exe",
    "terminal": "cmd.exe",
    "cmd": "cmd.exe",
    "powershell": "powershell.exe",
    "explorer": "explorer.exe",
    "file explorer": "explorer.exe",
    "paint": "mspaint.exe",
    "word": "winword",
    "excel": "excel",
    "steam": "steam",
    "task manager": "taskmgr.exe",
    "taskmgr": "taskmgr.exe",
    "settings": "ms-settings:",
    "edge": "msedge",
    "brave": "brave",
    "obsidian": "Obsidian",
    "notion": "Notion",
}

def volume_control(action: str, value: int = None) -> str:
    """Control system audio level and muting."""
    if not _HAS_PYAUTOGUI:
        return "pyautogui module required for audio controls."

    action = action.lower()
    if action == "volume_up":
        for _ in range(5): pyautogui.press("volumeup")
        return "System audio increased by 10%."
    elif action == "volume_down":
        for _ in range(5): pyautogui.press("volumedown")
        return "System audio decreased by 10%."
    elif action in ("mute", "unmute", "toggle_mute"):
        pyautogui.press("volumemute")
        return "System audio mute toggled."
    elif action == "set" and value is not None:
        try:
            import math
            from ctypes import cast, POINTER
            from comtypes import CLSCTX_ALL
            from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
            devices = AudioUtilities.GetSpeakers()
            interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            vol = cast(interface, POINTER(IAudioEndpointVolume))
            vol_db = -65.25 if value == 0 else max(-65.25, 20 * math.log10(value / 100))
            vol.SetMasterVolumeLevel(vol_db, None)
            return f"Master volume calibrated to {value}%."
        except Exception:
            return "Volume set requested."
    return "Audio action completed."

def brightness_control(action: str) -> str:
    """Adjust laptop display brightness via Windows WMI."""
    action = action.lower()
    delta = 10 if action == "brightness_up" else -10
    cmd = f"""
    $b = (Get-WmiObject -Namespace root/wmi -Class WmiMonitorBrightness).CurrentBrightness;
    $target = [math]::Max(0, [math]::Min(100, $b + {delta}));
    (Get-WmiObject -Namespace root/wmi -Class WmiMonitorBrightnessMethods).WmiSetBrightness(1, $target)
    """
    try:
        subprocess.run(["powershell", "-NoProfile", "-Command", cmd], capture_output=True, timeout=5)
        return f"Display brightness adjusted ({action})."
    except Exception as e:
        return f"Brightness adjustment failed: {e}"

def window_action(action: str) -> str:
    """Manage desktop windows and workspace focus."""
    if not _HAS_PYAUTOGUI:
        return "pyautogui required for window management."

    action = action.lower()
    if action == "minimize":
        pyautogui.hotkey("win", "down")
        return "Active window minimized."
    elif action == "maximize":
        pyautogui.hotkey("win", "up")
        return "Window maximized to full display."
    elif action == "snap_left":
        pyautogui.hotkey("win", "left")
        return "Snapping window to left tile."
    elif action == "snap_right":
        pyautogui.hotkey("win", "right")
        return "Snapping window to right tile."
    elif action == "show_desktop":
        pyautogui.hotkey("win", "d")
        return "Displaying desktop workspace."
    elif action == "switch_window":
        pyautogui.hotkey("alt", "tab")
        return "Switched active window."
    elif action == "close_window":
        pyautogui.hotkey("ctrl", "w")
        return "Active window or tab closed."
    elif action == "close_app":
        pyautogui.hotkey("alt", "f4")
        return "Application terminated."
    elif action == "task_manager":
        pyautogui.hotkey("ctrl", "shift", "esc")
        return "Windows Task Manager initialized."
    elif action == "lock_screen":
        pyautogui.hotkey("win", "l")
        return "Workstation secured. Screen locked."
    elif action == "screenshot":
        pyautogui.hotkey("win", "shift", "s")
        return "Screen capture snipping tool invoked."
    return f"Window action '{action}' performed."

def launch_application(app_name: str) -> str:
    """Launch installed applications with smart alias normalization."""
    raw = app_name.lower().strip()
    target = _APP_ALIASES.get(raw, raw)

    try:
        if target.startswith("ms-settings:") or target.endswith(".exe"):
            os.system(f"start {target}")
            return f"Launching {app_name}, sir."
        
        # Try direct process start or Windows Start Menu search
        res = subprocess.run(["where", target], capture_output=True, text=True)
        if res.returncode == 0:
            subprocess.Popen([target], shell=True)
            return f"Opening {app_name} now, sir."
        
        # Fallback to Start Menu typing via pyautogui
        if _HAS_PYAUTOGUI:
            pyautogui.press("win")
            time.sleep(0.4)
            pyautogui.write(app_name, interval=0.03)
            time.sleep(0.5)
            pyautogui.press("enter")
            return f"Summoning {app_name} from Windows application library, sir."

        os.system(f"start {target}")
        return f"Executing {app_name}."
    except Exception as e:
        return f"Unable to launch {app_name}, sir: {e}"

def split_workspace(left_app: str, right_app: str) -> str:
    """Split screen between two applications (Iris signature workflow)."""
    if not _HAS_PYAUTOGUI:
        return "pyautogui module required for window management."
    
    try:
        # Launch and snap left application
        launch_application(left_app)
        time.sleep(1.2)
        pyautogui.hotkey("win", "left")
        time.sleep(0.4)
        pyautogui.press("esc")  # Dismiss Windows Snap Assist thumbnail overlay
        
        # Launch and snap right application
        launch_application(right_app)
        time.sleep(1.2)
        pyautogui.hotkey("win", "right")
        time.sleep(0.4)
        pyautogui.press("esc")
        
        return f"Workspace configured: {left_app} tiled left, {right_app} tiled right."
    except Exception as e:
        return f"Failed to arrange split workspace: {e}"

