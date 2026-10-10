"""
Remote Smartphone Dashboard & Local Media Streamer for J.A.R.V.I.S. / F.R.I.D.A.Y.
(Ported from FatihMakes Mark-LV `dashboard/server.py` + `RemoteKeyOverlay`).

Features:
- Starts a lightweight threaded HTTP server on LAN port 8787 (`http://<LAN_IP>:8787/?key=<PIN>`).
- Generates a 6-character unambiguous one-time PIN (`A-Z, 2-9` excluding `O, I, L, 0, 1`).
- Provides `/api/state`, `/api/cmd`, and `/api/upload` for smartphone remote control and file transfer.
- Provides `/media?path=...` with HTTP Range support so local disk videos play natively inside the HUD `<video>` tag.
"""
from __future__ import annotations

import json
import mimetypes
import os
import random
import socket
import threading
import time
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

_SAFE_ALPHABET = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"
_DASHBOARD_PORT = 8787


def get_lan_ip() -> str:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


_MOBILE_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<title>J.A.R.V.I.S. Mobile Command Deck</title>
<style>
  :root { --pri: #00d4ff; --bg: #030912; --panel: rgba(6, 20, 38, 0.92); --red: #ff3355; --grn: #00ff9d; }
  * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Courier New', monospace; }
  body { background: var(--bg); color: #e2f6ff; min-height: 100vh; padding: 12px; display: flex; flex-direction: column; gap: 12px; }
  .hdr { display: flex; justify-content: space-between; align-items: center; border: 1px solid var(--pri); padding: 10px 14px; border-radius: 8px; background: var(--panel); box-shadow: 0 0 18px rgba(0,212,255,0.2); }
  .title { font-size: 18px; font-weight: 700; letter-spacing: 3px; color: var(--pri); }
  .badge { font-size: 11px; padding: 3px 8px; border-radius: 4px; background: rgba(0,255,157,0.15); border: 1px solid var(--grn); color: var(--grn); }
  .stats { display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; }
  .stat-card { background: var(--panel); border: 1px solid rgba(0,212,255,0.35); border-radius: 6px; padding: 8px; text-align: center; }
  .stat-lbl { font-size: 10px; color: #7cb8d4; }
  .stat-val { font-size: 16px; font-weight: 700; color: var(--pri); margin-top: 3px; }
  .grid-btns { display: grid; grid-template-columns: repeat(2, 1fr); gap: 8px; }
  button { background: rgba(0,212,255,0.12); border: 1px solid var(--pri); color: #fff; padding: 11px 8px; border-radius: 6px; font-size: 12px; font-weight: 700; letter-spacing: 1px; cursor: pointer; transition: 0.15s; }
  button:active { transform: scale(0.97); background: rgba(0,212,255,0.35); }
  button.danger { border-color: var(--red); background: rgba(255,51,85,0.18); color: #ff99aa; }
  .cmd-box { display: flex; gap: 8px; }
  input[type="text"] { flex: 1; background: rgba(0,12,24,0.9); border: 1px solid var(--pri); color: #fff; padding: 11px; border-radius: 6px; font-size: 13px; outline: none; }
  .log-box { flex: 1; min-height: 210px; max-height: 300px; overflow-y: auto; background: var(--panel); border: 1px solid rgba(0,212,255,0.35); border-radius: 6px; padding: 10px; font-size: 12px; display: flex; flex-direction: column; gap: 6px; }
  .log-item { line-height: 1.4; border-bottom: 1px solid rgba(0,212,255,0.1); padding-bottom: 4px; }
  .log-item b { color: var(--pri); }
  .upload-row { display: flex; align-items: center; justify-content: space-between; background: var(--panel); border: 1px dashed rgba(0,212,255,0.45); padding: 10px; border-radius: 6px; font-size: 11px; }
</style>
</head>
<body>
  <div class="hdr">
    <div>
      <div class="title" id="mode-title">J.A.R.V.I.S.</div>
      <div style="font-size:10px;color:#7cb8d4;">MARK LV REMOTE COMMAND DECK</div>
    </div>
    <div class="badge" id="conn-badge">● CONNECTED</div>
  </div>
  <div class="stats">
    <div class="stat-card"><div class="stat-lbl">CPU LOAD</div><div class="stat-val" id="st-cpu">--%</div></div>
    <div class="stat-card"><div class="stat-lbl">MEMORY</div><div class="stat-val" id="st-ram">--%</div></div>
    <div class="stat-card"><div class="stat-lbl">STATE</div><div class="stat-val" id="st-state">ONLINE</div></div>
  </div>
  <div class="cmd-box">
    <input type="text" id="cmd-in" placeholder="Speak or type command to JARVIS..." onkeydown="if(event.key==='Enter')sendCmd()">
    <button onclick="startVoice()" title="Voice Dictation">🎙</button>
    <button onclick="sendCmd()">SEND ➤</button>
  </div>
  <div class="grid-btns">
    <button class="danger" onclick="act('kill')">⏹ STOP / KILL</button>
    <button onclick="act('mute')">🔇 TOGGLE MUTE</button>
    <button onclick="act('center_cam')">◉ CENTER CAMERA</button>
    <button onclick="act('orb_mode')">◎ MINI ORB / HUD</button>
    <button onclick="act('briefing')">☀ MORNING BRIEF</button>
    <button onclick="act('radar')">✈ AIRSPACE RADAR</button>
    <button onclick="act('stop_video')">✕ CLOSE VIDEO</button>
    <button onclick="act('switch_mode')">⇄ JARVIS / FRIDAY</button>
  </div>
  <div class="upload-row">
    <span>📎 Send file to PC (file_processor):</span>
    <input type="file" id="file-in" style="max-width:175px;font-size:11px;" onchange="uploadFile(this)">
  </div>
  <div class="log-box" id="log-box"></div>
<script>
const params = new URLSearchParams(location.search);
const key = params.get('key') || localStorage.getItem('jarvis_key') || '';
if (key) localStorage.setItem('jarvis_key', key);

async function api(path, body) {
  const opts = body ? { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({...body, key}) } : {};
  const r = await fetch(path + (path.includes('?') ? '&' : '?') + 'key=' + encodeURIComponent(key), opts);
  return r.json();
}
async function sendCmd() {
  const el = document.getElementById('cmd-in');
  const text = el.value.trim();
  if (!text) return;
  el.value = '';
  await api('/api/cmd', { action: 'command', text });
  poll();
}
async function act(action) {
  await api('/api/cmd', { action });
  poll();
}
function startVoice() {
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SR) { alert('Use keyboard microphone icon on your phone keyboard.'); return; }
  const rec = new SR();
  rec.lang = 'en-IN';
  rec.onresult = (e) => {
    document.getElementById('cmd-in').value = e.results[0][0].transcript;
    sendCmd();
  };
  rec.start();
}
async function uploadFile(input) {
  if (!input.files || !input.files[0]) return;
  const f = input.files[0];
  const reader = new FileReader();
  reader.onload = async () => {
    await api('/api/upload', { filename: f.name, data_b64: reader.result.split(',')[1] || '' });
    alert('Uploaded to JARVIS: ' + f.name);
    input.value = '';
    poll();
  };
  reader.readAsDataURL(f);
}
async function poll() {
  try {
    const st = await api('/api/state');
    if (!st.ok) return;
    document.getElementById('st-cpu').innerText = st.cpu + '%';
    document.getElementById('st-ram').innerText = st.ram + '%';
    document.getElementById('st-state').innerText = st.state || 'ONLINE';
    document.getElementById('mode-title').innerText = st.mode || 'J.A.R.V.I.S.';
    const lb = document.getElementById('log-box');
    lb.innerHTML = (st.logs || []).slice(-25).reverse().map(l => `<div class="log-item"><b>[${l.sender}]</b> ${l.text}</div>`).join('');
  } catch (e) {}
}
setInterval(poll, 1500);
poll();
</script>
</body>
</html>
"""


class RemoteDashboardServer:
    """Manages the LAN smartphone dashboard & local HUD video streaming server."""

    def __init__(self, pipeline: Any, port: int = _DASHBOARD_PORT):
        self.pipeline = pipeline
        self.port = port
        self.pin = "".join(random.choice(_SAFE_ALPHABET) for _ in range(6))
        self.pin_created_at = time.time()
        self.connected_clients: int = 0
        self.recent_logs: list[dict[str, str]] = []
        self._server: ThreadingHTTPServer | None = None

    def record_log(self, sender: str, text: str) -> None:
        self.recent_logs.append({"sender": sender, "text": str(text)[:260]})
        if len(self.recent_logs) > 60:
            self.recent_logs = self.recent_logs[-60:]

    def regenerate_pin(self) -> str:
        self.pin = "".join(random.choice(_SAFE_ALPHABET) for _ in range(6))
        self.pin_created_at = time.time()
        return self.pin

    def get_pairing_info(self) -> dict[str, Any]:
        ip = get_lan_ip()
        url = f"http://{ip}:{self.port}/?key={self.pin}"
        return {
            "ip": ip,
            "port": self.port,
            "pin": self.pin,
            "url": url,
            "connected": self.connected_clients > 0,
        }

    def get_local_media_url(self, file_path: str) -> str:
        enc = urllib.parse.quote(str(Path(file_path).resolve()))
        return f"http://127.0.0.1:{self.port}/media?path={enc}"

    def start(self) -> None:
        parent = self

        class _Handler(BaseHTTPRequestHandler):
            def log_message(self, format: str, *args: Any) -> None:
                return

            def _send_json(self, data: dict[str, Any], status: int = 200) -> None:
                raw = json.dumps(data).encode("utf-8")
                self.send_response(status)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.send_header("Content-Length", str(len(raw)))
                self.end_headers()
                self.wfile.write(raw)

            def do_GET(self) -> None:
                parsed = urllib.parse.urlparse(self.path)
                qs = urllib.parse.parse_qs(parsed.query)

                if parsed.path == "/media":
                    raw_path = (qs.get("path") or [""])[0]
                    p = Path(urllib.parse.unquote(raw_path))
                    if not p.exists() or not p.is_file():
                        self.send_error(404, "Media file not found")
                        return
                    mime, _ = mimetypes.guess_type(str(p))
                    mime = mime or "video/mp4"
                    fsize = p.stat().st_size
                    range_hdr = self.headers.get("Range")
                    start, end = 0, fsize - 1
                    if range_hdr and range_hdr.startswith("bytes="):
                        parts = range_hdr[6:].split("-", 1)
                        if parts[0]:
                            start = int(parts[0])
                        if len(parts) > 1 and parts[1]:
                            end = int(parts[1])
                        end = min(end, fsize - 1)
                        length = end - start + 1
                        self.send_response(206)
                        self.send_header("Content-Range", f"bytes {start}-{end}/{fsize}")
                        self.send_header("Accept-Ranges", "bytes")
                        self.send_header("Content-Length", str(length))
                        self.send_header("Content-Type", mime)
                        self.send_header("Access-Control-Allow-Origin", "*")
                        self.end_headers()
                        with open(p, "rb") as f:
                            f.seek(start)
                            self.wfile.write(f.read(length))
                        return

                    self.send_response(200)
                    self.send_header("Accept-Ranges", "bytes")
                    self.send_header("Content-Length", str(fsize))
                    self.send_header("Content-Type", mime)
                    self.send_header("Access-Control-Allow-Origin", "*")
                    self.end_headers()
                    with open(p, "rb") as f:
                        self.wfile.write(f.read())
                    return

                if parsed.path == "/api/state":
                    if parent.connected_clients == 0:
                        parent.connected_clients = 1
                        try:
                            parent.pipeline.window.evaluate_js("markRemotePhoneConnected && markRemotePhoneConnected()")
                            parent.pipeline.window.evaluate_js("addLog('SYSTEM', 'Smartphone connected to Remote Dashboard.')")
                        except Exception:
                            pass
                    import psutil
                    self._send_json({
                        "ok": True,
                        "cpu": int(psutil.cpu_percent(interval=None)),
                        "ram": int(psutil.virtual_memory().percent),
                        "state": getattr(parent.pipeline, "current_hud_state", "ONLINE"),
                        "mode": parent.pipeline.voice_mode,
                        "logs": parent.recent_logs[-25:],
                    })
                    return

                # Serve mobile web dashboard HTML
                raw_html = _MOBILE_HTML.encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(raw_html)))
                self.end_headers()
                self.wfile.write(raw_html)

            def do_POST(self) -> None:
                parsed = urllib.parse.urlparse(self.path)
                length = int(self.headers.get("Content-Length") or 0)
                body_bytes = self.rfile.read(length) if length > 0 else b"{}"
                try:
                    payload = json.loads(body_bytes.decode("utf-8"))
                except Exception:
                    payload = {}

                if parsed.path == "/api/upload":
                    import base64
                    fname = os.path.basename(str(payload.get("filename") or "upload.bin"))
                    b64 = str(payload.get("data_b64") or "")
                    dest_dir = Path.home() / "Downloads" / "JARVIS Uploads"
                    dest_dir.mkdir(parents=True, exist_ok=True)
                    dest = dest_dir / fname
                    dest.write_bytes(base64.b64decode(b64))
                    parent.pipeline.tool_suite.ui.current_file = str(dest)
                    parent.pipeline.window.evaluate_js(f"setAttachedFile({json.dumps(fname)})")
                    parent.pipeline.window.evaluate_js(
                        f"addLog('SYSTEM', {json.dumps(f'Phone uploaded file: {fname}')})"
                    )
                    self._send_json({"ok": True, "path": str(dest)})
                    return

                if parsed.path == "/api/cmd":
                    act = str(payload.get("action") or "").lower()
                    txt = str(payload.get("text") or "").strip()
                    p = parent.pipeline
                    if act == "command" and txt:
                        p.last_active = time.time()
                        p.window.evaluate_js(f"addLog('USER', {json.dumps(f'[Phone] {txt}')})")
                        p.text_queue.put(txt)
                    elif act == "kill":
                        p.abort_current_command(spoken_text="stop")
                    elif act == "mute":
                        p.toggle_mic_mute()
                    elif act == "center_cam":
                        p.exit_orb_only_mode()
                        p.window.evaluate_js("toggleCenterCameraMode()")
                    elif act == "orb_mode":
                        if p.is_orb_only:
                            p.exit_orb_only_mode()
                        else:
                            p.enter_orb_only_mode(sleep_mode=False)
                    elif act == "briefing":
                        p.trigger_morning_briefing()
                    elif act == "radar":
                        p.text_queue.put("scan nearby airspace radar")
                    elif act == "stop_video":
                        p.tool_suite.ui.stop_video()
                    elif act == "switch_mode":
                        new_m = "FRIDAY" if p.voice_mode == "JARVIS" else "JARVIS"
                        p.voice_mode = new_m
                        p.window.evaluate_js(f"switchMode({json.dumps(new_m)})")
                    self._send_json({"ok": True})
                    return

                self._send_json({"ok": False}, status=404)

        def _serve() -> None:
            for candidate_port in (self.port, 8788, 8789):
                try:
                    self.port = candidate_port
                    self._server = ThreadingHTTPServer(("0.0.0.0", candidate_port), _Handler)
                    self._server.serve_forever()
                    break
                except Exception:
                    continue

        threading.Thread(target=_serve, daemon=True, name="jarvis-remote-dashboard").start()
        return self.get_pairing_info()["url"]

    def stop(self) -> None:
        if self._server is not None:
            try:
                self._server.shutdown()
                self._server.server_close()
            except Exception:
                pass
            self._server = None

