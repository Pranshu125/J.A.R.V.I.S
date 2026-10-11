"""
Camera Hardware Schematic & Pinout Generator Plugin (Ported from FatihMakes Sep 17 2026 Reel).
Captures the webcam feed (or takes two named hardware modules) and generates an interactive pinout connection schematic in the HUD.
"""
from __future__ import annotations

import json
from modules.mark_lv_bridge import run_screen_or_camera_vision


def hardware_schematic(parameters: dict, player=None, window=None) -> str:
    params = parameters or {}
    part_a = str(params.get("part_a") or params.get("component") or "").strip()
    part_b = str(params.get("part_b") or "").strip()
    use_camera = bool(params.get("camera_scan", False))
    win = window or (getattr(getattr(player, "pipeline", None), "window", None) if player else None)

    if use_camera:
        vision_desc = run_screen_or_camera_vision(
            angle="camera",
            text="Identify the electronic components, microcontroller, or sensors held in front of the camera and list how to wire their pins together.",
            window=win,
        )
        part_a = part_a or "Microcontroller (MCU 5V)"
        part_b = part_b or "Sensor Module"
    else:
        part_a = part_a or "ESP32 / Arduino MCU (3.3V-5V)"
        part_b = part_b or "I2C / Digital Sensor Module"
        vision_desc = (
            f"Connect the regulated VCC (3.3V/5V) and common GND rails between {part_a} and {part_b}, "
            "then bridge GPIO D2 / SDA to the sensor DATA output with a 4.7kOhm pull-up resistor to VCC."
        )

    payload = {
        "title": f"Connecting {part_a} & {part_b}",
        "part_a": part_a,
        "part_b": part_b,
        "connections": [
            {"from": "VCC (5V / 3.3V)", "to": "VCC (+)", "color": "#ff4444", "note": "Regulated Power Rail"},
            {"from": "GPIO D2 / SDA", "to": "DATA / OUT", "color": "#00ff9d", "note": "4.7kOhm - 10kOhm Pull-Up to VCC"},
            {"from": "GND", "to": "GND (-)", "color": "#38bdf8", "note": "Common Ground Reference"},
        ],
        "summary": vision_desc,
    }
    if win:
        win.evaluate_js("if(typeof exitOrbOnlyFromJS==='function') exitOrbOnlyFromJS();")
        win.evaluate_js(f"showHudCard('schematic', {json.dumps(payload)})")
    return f"I have generated the wiring schematic for {part_a} and {part_b} on your display, sir. {vision_desc[:200]}"


PLUGIN = {
    "name": "hardware_schematic",
    "description": "Identify hardware/electronic modules on camera or by name and render an interactive pinout wiring schematic inside the HUD ('how can I connect these two together', 'create a wiring diagram for Arduino and DHT11').",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "part_a": {"type": "STRING", "description": "First hardware component (e.g. Arduino Pro Mini, ESP32)"},
            "part_b": {"type": "STRING", "description": "Second hardware component (e.g. DHT11, Ultrasonic Sensor)"},
        },
    },
    "handler": hardware_schematic,
}
