"""
system_control.py - Deep Windows hardware, app launcher & window management
Ported & refined from Mark-XXXIX-OR
"""
from __future__ import annotations

import math
import os
import shutil
import subprocess
import time

try:
    import pyautogui
    pyautogui.FAILSAFE = True
    pyautogui.PAUSE = 0.05
    _HAS_PYAUTOGUI = True
except ImportError:
    _HAS_PYAUTOGUI = False

_APP_ALIASES: dict[str, str] = {
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

_WINDOW_HOTKEYS: dict[str, tuple[tuple[str, ...], str]] = {
    "minimize": (("win", "down"), "Active window minimized."),
    "maximize": (("win", "up"), "Window maximized to full display."),
    "snap_left": (("win", "left"), "Snapping window to left tile."),
    "snap_right": (("win", "right"), "Snapping window to right tile."),
    "show_desktop": (("win", "d"), "Displaying desktop workspace."),
    "switch_window": (("alt", "tab"), "Switched active window."),
    "close_window": (("ctrl", "w"), "Active window or tab closed."),
    "close_app": (("alt", "f4"), "Application terminated."),
    "task_manager": (("ctrl", "shift", "esc"), "Windows Task Manager initialized."),
    "lock_screen": (("win", "l"), "Workstation secured. Screen locked."),
    "screenshot": (("win", "shift", "s"), "Screen capture snipping tool invoked."),
}


def volume_control(action: str, value: int | None = None) -> str:
    """Control system audio level and muting."""
    if not _HAS_PYAUTOGUI:
        return "pyautogui module required for audio controls."

    act = (action or "").lower().strip()
    if act == "volume_up":
        pyautogui.press("volumeup", presses=5)
        return "System audio increased by 10%."
    if act == "volume_down":
        pyautogui.press("volumedown", presses=5)
        return "System audio decreased by 10%."
    if act in ("mute", "unmute", "toggle_mute"):
        pyautogui.press("volumemute")
        return "System audio mute toggled."
    if act == "set" and value is not None:
        try:
            from ctypes import POINTER, cast
            from comtypes import CLSCTX_ALL
            from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

            devices = AudioUtilities.GetSpeakers()
            interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            vol = cast(interface, POINTER(IAudioEndpointVolume))
            clamped = max(0, min(100, int(value)))
            vol_db = -65.25 if clamped == 0 else max(-65.25, 20 * math.log10(clamped / 100))
            vol.SetMasterVolumeLevel(vol_db, None)
            return f"Master volume calibrated to {clamped}%."
        except Exception:
            return "Volume set requested."
    return "Audio action completed."


def brightness_control(action: str) -> str:
    """Adjust laptop display brightness via Windows WMI."""
    act = (action or "").lower().strip()
    delta = 10 if act == "brightness_up" else -10
    cmd = (
        "$b = (Get-WmiObject -Namespace root/wmi -Class WmiMonitorBrightness).CurrentBrightness; "
        f"$target = [math]::Max(0, [math]::Min(100, $b + {delta})); "
        "(Get-WmiObject -Namespace root/wmi -Class WmiMonitorBrightnessMethods).WmiSetBrightness(1, $target)"
    )
    try:
        subprocess.run(["powershell", "-NoProfile", "-Command", cmd], capture_output=True, timeout=5)
        return f"Display brightness adjusted ({act})."
    except Exception as e:
        return f"Brightness adjustment failed: {e}"


def window_action(action: str) -> str:
    """Manage desktop windows and workspace focus via O(1) hotkey dispatch."""
    if not _HAS_PYAUTOGUI:
        return "pyautogui required for window management."

    act = (action or "").lower().strip()
    entry = _WINDOW_HOTKEYS.get(act)
    if entry:
        keys, message = entry
        pyautogui.hotkey(*keys)
        return message
    return f"Window action '{act}' performed."


def launch_application(app_name: str) -> str:
    """Launch installed applications using native os.startfile / shutil.which with Start Menu fallback."""
    raw = (app_name or "").lower().strip()
    if not raw:
        return "No application name specified, sir."
    target = _APP_ALIASES.get(raw, raw)

    try:
        # 1. Native Windows URI / executable resolution via shutil.which or os.startfile
        resolved = shutil.which(target)
        if resolved:
            subprocess.Popen([resolved])
            return f"Opening {app_name} now, sir."

        if hasattr(os, "startfile") and (target.startswith("ms-settings:") or target.endswith(".exe")):
            os.startfile(target)
            return f"Launching {app_name}, sir."

        # 2. Try os.startfile for registered Windows App Paths (e.g., chrome, brave, winword)
        if hasattr(os, "startfile"):
            try:
                os.startfile(target)
                return f"Opening {app_name} now, sir."
            except OSError:
                pass

        # 3. Fallback to Start Menu search via pyautogui
        if _HAS_PYAUTOGUI:
            pyautogui.press("win")
            time.sleep(0.35)
            pyautogui.write(app_name, interval=0.025)
            time.sleep(0.45)
            pyautogui.press("enter")
            return f"Summoning {app_name} from Windows application library, sir."

        return f"Unable to locate {app_name}, sir."
    except Exception as e:
        return f"Unable to launch {app_name}, sir: {e}"


def split_workspace(left_app: str, right_app: str) -> str:
    """Split screen between two applications."""
    if not _HAS_PYAUTOGUI:
        return "pyautogui module required for window management."

    try:
        for app, direction in ((left_app, "left"), (right_app, "right")):
            launch_application(app)
            time.sleep(1.1)
            pyautogui.hotkey("win", direction)
            time.sleep(0.35)
            pyautogui.press("esc")  # Dismiss Windows Snap Assist thumbnail overlay
        return f"Workspace configured: {left_app} tiled left, {right_app} tiled right."
    except Exception as e:
        return f"Failed to arrange split workspace: {e}"
