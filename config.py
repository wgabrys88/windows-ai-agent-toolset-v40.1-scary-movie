HOST = "127.0.0.1"
PORT = 1234
LOG_LEVEL = "INFO"
LOG_TO_FILE = True
RUNS_DIR = "runs"
LOG_LAYOUT = "flat"

API_URL = "http://127.0.0.1:1235/v1/chat/completions"
MODEL = "huihui-qwen3-vl-2b-instruct-abliterated"
TEMPERATURE = 0.7
TOP_P = 0.9
MAX_TOKENS = 1000
VLM_HTTP_TIMEOUT_SECONDS = 120.0

SYSTEM_PROMPT = """\
You are Franz, a vision-action agent controlling a Windows 11 desktop.

Each turn you receive an annotated screenshot of a screen region.
Orange heat = where your previous actions physically executed on screen.
Ghost images = semi-transparent imprints of regions you previously marked as interesting. \
Brighter ghosts are more recent. They show WHAT WAS THERE when you looked. \
Compare ghosts to current content to detect what changed.

Respond with ONLY a single JSON object:
{"observation":"<what you see and intend, max 120 words>","bboxes":[{"x1":int,"y1":int,"x2":int,"y2":int}],"actions":[{"name":"click"|"right_click"|"double_click"|"drag"|"move","x1":int,"y1":int,"x2":int,"y2":int}]}

Coordinates: integers in [0,1000]. (0,0)=top-left, (1000,1000)=bottom-right, (500,500)=center.
x2,y2 required ONLY for drag.
Max 6 bboxes, max 4 actions.
Place bboxes on regions you want to remember and compare next turn.
Describe ONLY what you see. Never hallucinate.
If unsure, output actions:[] and explain in observation.
"""

CAPTURE_CROP = {"x1": 0, "y1": 0, "x2": 1000, "y2": 1000}
CAPTURE_WIDTH = 512
CAPTURE_HEIGHT = 288
CAPTURE_SCALE_PERCENT = 100
CAPTURE_DELAY = 0.0

BOOT_ENABLED = True
BOOT_VLM_OUTPUT = '{"observation":"System initialized. Awaiting first screenshot.","bboxes":[],"actions":[]}'

PHYSICAL_EXECUTION = True
ACTION_DELAY_SECONDS = 0.05
DRAG_DURATION_STEPS = 20
DRAG_STEP_DELAY = 0.01
ANNOTATED_TIMEOUT_SECONDS = 10.0
PARSE_MAX_LEVEL = 4

GHOST_MAX = 12
GHOST_MAX_AGE = 6
GHOST_OPACITY_BASE = 0.35
GHOST_OPACITY_DECAY = 0.55

UI_CONFIG = {
    "executed_heat": {
        "enabled": True,
        "radius_scale": 0.18,
        "drag_steps": 12,
        "trail_turns": 1,
        "trail_shrink": 1.0,
        "stops": [
            [0.00, "rgba(255,60,0,0.80)"],
            [0.30, "rgba(255,100,0,0.55)"],
            [0.65, "rgba(255,140,0,0.20)"],
            [1.00, "rgba(255,160,0,0.00)"],
        ],
    },
    "ghosts": {
        "enabled": True,
        "opacity_base": 0.35,
        "opacity_decay": 0.55,
        "edge_glow": True,
        "edge_color": "rgba(60,140,255,0.25)",
        "edge_width": 1,
    },
}
