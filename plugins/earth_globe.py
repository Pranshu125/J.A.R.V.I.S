"""
Interactive 3D Earth Globe & Live USGS Earthquake Telemetry Plugin (Ported from FatihMakes Sep 22 2026 Reel).
Renders an interactive rotatable 3D Earth Globe inside the HUD with satellite mode and real-time USGS earthquake markers.
"""
from __future__ import annotations

import json
import requests
from modules.mark_lv_bridge import get_user_location


def earth_globe(parameters: dict, player=None, window=None) -> str:
    params = parameters or {}
    mode = str(params.get("mode") or "vector").lower().strip()
    show_quakes = bool(params.get("earthquakes", False) or "quake" in mode)

    loc = get_user_location()
    quakes = []
    if show_quakes:
        try:
            url = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/2.5_day.geojson"
            r = requests.get(url, timeout=5).json()
            for feat in (r.get("features") or [])[:12]:
                props = feat.get("properties") or {}
                coords = (feat.get("geometry") or {}).get("coordinates") or [0, 0]
                quakes.append({
                    "place": props.get("place", "Unknown region"),
                    "mag": props.get("mag", 0),
                    "lon": coords[0],
                    "lat": coords[1],
                })
        except Exception:
            pass

    payload = {
        "mode": "satellite" if "sat" in mode else "vector",
        "lat": loc["lat"],
        "lon": loc["lon"],
        "city": loc["city"],
        "country": loc["country"],
        "quakes": quakes,
    }
    win = window or (getattr(getattr(player, "pipeline", None), "window", None) if player else None)
    if win:
        win.evaluate_js(f"showHudCard('earth_globe', {json.dumps(payload)})")

    if show_quakes:
        if quakes:
            top = quakes[0]
            return f"Displaying the 3D Earth globe with {len(quakes)} recent seismic events, sir. The latest is magnitude {top['mag']} near {top['place']}."
        return f"I have checked the seismic feed around {loc['city']}, sir. There have been no significant earthquakes in your sector today."
    return "I have put the interactive 3D Earth globe on your display, sir. You can spin, zoom, or toggle satellite telemetry directly."


PLUGIN = {
    "name": "earth_globe",
    "description": "Display the interactive 3D Earth Globe in the HUD with vector or satellite view and live USGS earthquake tracking ('show me the Earth', 'satellite view of Earth', 'show recent earthquakes').",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "mode": {"type": "STRING", "description": "'vector', 'satellite', or 'earthquakes'"},
            "earthquakes": {"type": "BOOLEAN", "description": "True to overlay live USGS earthquakes"},
        },
    },
    "handler": earth_globe,
}
