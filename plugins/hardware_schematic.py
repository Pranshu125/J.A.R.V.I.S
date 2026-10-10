"""
Camera Hardware Schematic & Pinout Generator Plugin (Ported from FatihMakes Sep 17 2026 Reel).
Captures the webcam feed (or takes two named hardware modules) and generates an interactive pinout connection schematic in the HUD.
"""
from __future__ import annotations

import json
from modules.mark_lv_bridge import run_screen_or_camera_vision


def hardware_schematic(parameters: dict, player=None, window=None) -> str:
    params = parameters or {}
    part_a = str(params.get("part_a") or "").strip()
    part_b = str(params.get("part_b") or "").strip()
    win = window or (getattr(getattr(player, "pipeline", None), "window", None) if player else None)

    if not part_a or not part_b:
        vision_desc = run_screen_or_camera_vision(
            angle="camera",
            text="Identify the electronic components, microcontroller, or sensors held in front of the camera and list how to wire their pins together.",
            window=win,
        )
        part_a = part_a or "Microcontroller (MCU 5V)"
        part_b = part_b or "Sensor Module"
    else:
        vision_desc = f"Start by connecting the VCC and GND power rails between {part_a} and {part_b}, then bridge the digital/I2C data pins with a 4.7kΩ pull-up resistor."

    payload = {
        "title": f"Connecting {part_a} & {part_b}",
        "part_a": part_a,
        "part_b": part_b,
        "connections": [
            {"from": "VCC (5V / 3.3V)", "to": "VCC (+)", "color": "#ff4444", "note": "Regulated Power Rail"},
            {"from": "GPIO D2 / SDA", "to": "DATA / OUT", "color": "#00ff9d", "note": "4.7kΩ – 10kΩ Pull-Up to VCC"},
            {"from": "GND", "to": "GND (-)", "color": "#38bdf8", "note": "Common Ground Reference"},
        ],
        "summary": vision_desc,
    }
    if win:
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
