import time
import uvicorn
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, PlainTextResponse 

BUTTON_CONFIG = {
    9:  {"name": "all",       "color": "#28a745", "text": "white"}, # Green
    10: {"name": "spotifyd",  "color": "#007bff", "text": "white"}, # Blue
    24: {"name": "bluetooth", "color": "#6f42c1", "text": "white"}, # Purple
    23: {"name": "cd",        "color": "#6c757d", "text": "white"}, # Grey
    22: {"name": "aux",       "color": "#ffc107", "text": "black"}, # Yellow
    27: {"name": "radio",      "color": "#dc3545", "text": "white"}, # Red
    17: {"name": "empty",      "color": "#fd7e14", "text": "white"}  # Orange
}

class AppState:
    def __init__(self):
        self.config_str = "1"
        self.active_pin = 9
        self.logs = []        
        self.controller = None
        self.volume = 33
        self.volume_locked = True
    
    def add_log(self, message):
        timestamp = time.strftime('%d.%m.%Y %H:%M:%S')
        log_entry = f"[{timestamp}] {message}"
        self.logs.append(log_entry)
        if len(self.logs) > 100: self.logs.pop(0)
        print(log_entry)

state = AppState()
app = FastAPI()

# 2. Web Server Routes
@app.get("/", response_class=HTMLResponse)
async def index():
    buttons_html = ""
    for pin, info in BUTTON_CONFIG.items():
        is_active = "active" if state.active_pin == pin else ""
        buttons_html += f"""
        <button id="btn-{pin}" 
                class="source-btn {is_active}" 
                style="background-color: {info['color']}; color: {info['text']};"
                onclick="setSource({pin})">
            {info['name'].upper()}
        </button>
        """

    return f"""
        <html>
            <head>
                <title>Rossi's Röhren Radio</title>
                <meta name="viewport" content="width=device-width, initial-scale=1">
                <style>
                    body {{ font-family: sans-serif; padding: 20px; background: #f4f4f4; text-align: center; }}
                    .container {{ max-width: 600px; margin: auto; background: white; padding: 20px; border-radius: 12px; box-shadow: 0 4px 10px rgba(0,0,0,0.1); }}
                    
                    .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-top: 20px; }}
                    
                    .source-btn {{
                        padding: 20px; border: 4px solid transparent; border-radius: 8px;
                        font-weight: bold; cursor: pointer; transition: all 0.2s; font-size: 16px;
                    }}
                    
                    /* The "Active" state style */
                    .source-btn.active {{
                        border-color: #000;
                        transform: scale(0.95);
                        box-shadow: inset 0 3px 10px rgba(0,0,0,0.3);
                        filter: brightness(1.2);
                    }}

                    /* Slider Styling */
                    .vol-container {{ margin: 30px 0; padding: 20px; background: #eee; border-radius: 10px; }}
                    .lock-btn {{ margin-top: 15px; padding: 10px 20px; border: none; border-radius: 8px; font-weight: bold; cursor: pointer; color: white; }}
                    .lock-btn.locked {{ background: #dc3545; }}
                    .lock-btn.unlocked {{ background: #28a745; }}
                    .slider {{ width: 100%; height: 15px; border-radius: 5px; background: #ddd; outline: none; cursor: pointer; }}

                    pre {{ background:#222; color:#0f0; padding:15px; height:200px; overflow-y:auto; 
                        border-radius:5px; font-family: monospace; text-align: left; white-space: pre-wrap; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>Rossi's Röhren Radio</h1>
                    <div class="grid">
                        {buttons_html}
                    </div>
                    <div class="vol-container">
                        <h3>Volume: <span id="volLabel">{state.volume}</span>%</h3>
                        <input type="range" min="0" max="100" value="{state.volume}" class="slider" id="volSlider" oninput="updateVolume(this.value)">
                        <button id="volLockBtn" class="lock-btn {'locked' if state.volume_locked else 'unlocked'}" onclick="toggleVolumeLock()">
                            WHEEL {'LOCKED' if state.volume_locked else 'UNLOCKED'}
                        </button>
                    </div>
                    <hr style="margin: 30px 0;">
                    <input type="text" id="configInput" value="{state.config_str}" style="padding:8px;">
                    <button onclick="updateConfig()">Save Config</button>

                    <h3>Live Logs</h3>
                    <pre id="logbox"></pre>
                </div>

                <script>
                    async function setSource(pin) {{
                        await fetch('/set_source?pin=' + pin);
                        
                        // Update UI immediately
                        document.querySelectorAll('.source-btn').forEach(btn => {{
                            btn.classList.remove('active');
                        }});
                        document.getElementById('btn-' + pin).classList.add('active');
                    }}

                    async function updateVolume(val) {{
                        document.getElementById('volLabel').innerText = val;
                        await fetch('/set_volume?val=' + val);
                    }}

                    function showVolumeLock(locked) {{
                        const btn = document.getElementById('volLockBtn');
                        btn.className = 'lock-btn ' + (locked ? 'locked' : 'unlocked');
                        btn.innerText = locked ? 'WHEEL LOCKED' : 'WHEEL UNLOCKED';
                        window.volumeLocked = locked;
                    }}

                    async function toggleVolumeLock() {{
                        const locked = !window.volumeLocked;
                        await fetch('/set_volume_lock?locked=' + locked);
                        showVolumeLock(locked);
                    }}

                    async function updateConfig() {{
                        const v = document.getElementById('configInput').value;
                        await fetch('/update?val=' + encodeURIComponent(v));
                    }}

                    async function syncStatus() {{
                        try {{
                            const r = await fetch('/status');
                            const data = await r.json();

                            // 1. Update Volume Slider (only if user isn't currently touching it)
                            const slider = document.getElementById('volSlider');
                            if (!window.isUserTouchingSlider) {{
                                slider.value = data.volume;
                                document.getElementById('volLabel').innerText = data.volume;
                            }}

                            showVolumeLock(data.volume_locked);

                            // 2. Update Active Button
                            document.querySelectorAll('.source-btn').forEach(btn => {{
                                if (btn.id === 'btn-' + data.active_pin) {{
                                    btn.classList.add('active');
                                }} else {{
                                    btn.classList.remove('active');
                                }}
                            }});

                            // 3. Update Logs
                            const box = document.getElementById('logbox');
                            box.innerText = data.logs;
                            box.scrollTop = box.scrollHeight;
                        }} catch (e) {{ 
                            console.error("Sync failed", e); 
                        }}
                    }}

                    // Track if user is touching slider to prevent "jumping"
                    const slider = document.getElementById('volSlider');
                    slider.onmousedown = () => {{ window.isUserTouchingSlider = true; }};
                    slider.onmouseup = () => {{ window.isUserTouchingSlider = false; }};
                    slider.ontouchstart = () => {{ window.isUserTouchingSlider = true; }};
                    slider.ontouchend = () => {{ window.isUserTouchingSlider = false; }};

                    window.volumeLocked = {'true' if state.volume_locked else 'false'};
                    setInterval(syncStatus, 500);
                </script>
            </body>
        </html>
        """

@app.get("/set_source")
def set_source(pin: int):
    if pin in BUTTON_CONFIG and not state.active_pin == pin:
        state.active_pin = pin
        source_name = BUTTON_CONFIG[pin]['name']
        state.add_log(f"SWITCHED TO: {source_name} (GPIO {pin}) via webpage")
        state.controller.set_source_external(pin)
        
    return {"status": "ok"}

def set_source_external(pin: int):
    state.active_pin = pin
    source_name = BUTTON_CONFIG[pin]['name']
    state.add_log(f"SWITCHED TO: {source_name} (GPIO {pin}) via radio buttons")

@app.get("/update")
def update_config(val: str):
    state.config_str = val
    state.add_log(f"CONFIG CHANGED TO: {val}")
    print(f"Web UI changed config to: {val}") # Visible in your terminal
    return {"status": "ok"}

@app.get("/logs")
def get_logs():
    # Returns the last 20 lines of logs as plain text
    content = "\n".join(state.logs[-20:])
    return PlainTextResponse(content)

@app.get("/set_volume")
def set_volume(val: int):
    if state.controller and hasattr(state.controller, 'vc'):
        state.controller.vc.set_volume(val)
        state.volume = val
        state.add_log(f"Volume changed to {val}")
    return {"status": "ok"}

@app.get("/set_volume_lock")
def set_volume_lock(locked: bool):
    state.volume_locked = locked
    if state.controller:
        state.controller.set_volume_lock(locked)
    return {"status": "ok"}

# 3. Threading Helper
def run_web_server(controller_instance):
    state.controller = controller_instance
    state.volume = controller_instance.vc.get_volume()
    state.volume_locked = controller_instance.lock_hardware_volume
    # Disable signal handlers so it can run in a background thread
    config = uvicorn.Config(app, host="0.0.0.0", port=8000, log_level="error")
    server = uvicorn.Server(config)
    server.install_signal_handlers = lambda: None 
    print("Webserver started!")
    server.run()


@app.get("/status")
def get_status():
    return {
        "active_pin": state.active_pin,
        "volume": state.volume,
        "volume_locked": state.volume_locked,
        "logs": "\n".join(state.logs[-100:])
    }

# for outside usage
def print_to_log(message: str):
    state.add_log(message)