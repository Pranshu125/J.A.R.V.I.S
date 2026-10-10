"""
Pomodoro Focus Session Plugin (Inspired by FatihMakes Mark-LV Pomodoro Reel).
Renders a live interactive Pomodoro countdown card inside the HUD and announces completion.
"""
from __future__ import annotations

import json


def pomodoro_timer(parameters: dict, player=None, window=None) -> str:
    params = parameters or {}
    action = str(params.get("action") or "start").lower().strip()
    minutes = int(params.get("minutes") or 40)
    label = str(params.get("task") or "Deep Focus Session").strip()

    win = window or (getattr(getattr(player, "pipeline", None), "window", None) if player else None)
    if action in ("stop", "cancel", "close"):
        if win:
            win.evaluate_js("closeHudCard()")
        return "Pomodoro focus session cancelled, sir."

    payload = {
        "minutes": max(1, min(240, minutes)),
        "task": label,
    }
    if win:
        win.evaluate_js(f"showHudCard('pomodoro', {json.dumps(payload)})")
    if player:
        player.write_log(f"Pomodoro focus block started — {minutes} min ({label})")
    return f"Focus session has started for {minutes} minutes, sir."


PLUGIN = {
    "name": "pomodoro_timer",
    "description": "Start or stop a Pomodoro focus timer on the HUD display (e.g. 'start pomodoro for 40 minutes', 'stop pomodoro').",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "action": {"type": "STRING", "description": "'start' or 'stop'"},
            "minutes": {"type": "INTEGER", "description": "Duration in minutes (default 40)"},
            "task": {"type": "STRING", "description": "Focus session label"},
        },
        "required": ["action"],
    },
    "handler": pomodoro_timer,
}
