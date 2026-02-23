

# FRANZ — Vision-Action Loop Desktop Controller with Ghost Memory

```
┌─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                                                                                                         │
│    ███████╗██████╗  █████╗ ███╗   ██╗███████╗                                                                           │
│    ██╔════╝██╔══██╗██╔══██╗████╗  ██║╚══███╔╝                                                                           │
│    █████╗  ██████╔╝███████║██╔██╗ ██║  ███╔╝                                                                            │
│    ██╔══╝  ██╔══██╗██╔══██║██║╚██╗██║ ███╔╝                                                                             │
│    ██║     ██║  ██║██║  ██║██║ ╚████║███████╗                                                                           │
│    ╚═╝     ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝╚══════╝                                                                           │
│                                                                                                                         │
│    Stateless embodied vision-action agent for Windows 11 desktop control                                                │
│    Temporal narrative encoded in a single image via ghost memory and radial heatmaps                                    │
│                                                                                                                         │
└─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```


## System Reproduction Prompt

The following system prompt, config, and architecture description are sufficient to reproduce Franz in full.

```
You are Franz, a vision-action agent controlling a Windows 11 desktop.

Each turn you receive an annotated screenshot of a screen region.
Orange heat = where your previous actions physically executed on screen.
Ghost images = semi-transparent imprints of regions you previously marked as interesting.
Brighter ghosts are more recent. They show WHAT WAS THERE when you looked.
Compare ghosts to current content to detect what changed.

Respond with ONLY a single JSON object:
{"observation":"<what you see and intend, max 120 words>","bboxes":[{"x1":int,"y1":int,"x2":int,"y2":int}],"actions":[{"name":"click"|"right_click"|"double_click"|"drag"|"move","x1":int,"y1":int,"x2":int,"y2":int}]}

Coordinates: integers in [0,1000]. (0,0)=top-left, (1000,1000)=bottom-right, (500,500)=center.
x2,y2 required ONLY for drag.
Max 6 bboxes, max 4 actions.
Place bboxes on regions you want to remember and compare next turn.
Describe ONLY what you see. Never hallucinate.
If unsure, output actions:[] and explain in observation.
```


## Architecture


### Complete Data Flow

```
┌─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                                                                                                         │
│                                          FRANZ — COMPLETE DATA FLOW                                                     │
│                                                                                                                         │
│  ┌──────────┐     ┌────────────┐     ┌───────────┐     ┌──────────────┐     ┌──────────┐     ┌──────────────────────┐   │
│  │          │     │            │     │           │     │              │     │          │     │                      │   │
│  │  VLM     │────>│  Cascading │────>│  Engine   │────>│  Win32 GDI   │────>│  Screen  │────>│  Ghost + Heat        │   │
│  │  Output  │     │  Parser    │     │  State    │     │  Mouse Exec  │     │  Capture │     │  Annotated Image     │   │
│  │  (JSON)  │     │  (5 level) │     │  + Ghost  │     │              │     │  + PNG   │     │                      │   │
│  │          │     │            │     │  Memory   │     │              │     │          │     │                      │   │
│  └──────────┘     └────────────┘     └───────────┘     └──────────────┘     └──────────┘     └──────────┬───────────┘   │
│       ^                                    │                                                              │              │
│       │                                    │  bboxes crop regions from raw frame                          │              │
│       │                                    │  -> stored in ghost ring buffer                              │              │
│       │                                    │  -> sent to browser via /ghosts                              v              │
│       │            ┌─────────────────────────────────────────────────────────────────────────────────────────┐           │
│       │            │                                                                                         │           │
│       │            │                        BROWSER PANEL (Chrome)                                           │           │
│       │            │                                                                                         │           │
│       │            │   GET /state ──> phase, bboxes, actions, parse_level, ghost_count (no images)          │           │
│       │            │   GET /frame ──> raw screenshot base64                                                  │           │
│       │            │   GET /ghosts ──> ghost images with age, position, opacity                              │           │
│       │            │                                                                                         │           │
│       │            │   Canvas stack (3 layers, bottom to top):                                               │           │
│       │            │     Layer 0: c-base   = raw screenshot                                                  │           │
│       │            │     Layer 1: c-ghost  = ghost images (age-faded bbox crops from prior turns)            │           │
│       │            │     Layer 2: c-heat   = orange executed-action heat blobs                               │           │
│       │            │                                                                                         │           │
│       │            │   OffscreenCanvas composites all 3 layers -> PNG base64                                 │           │
│       │            │   POST /annotated -> {seq, image_b64}                                                   │           │
│       │            │                                                                                         │           │
│       │            └─────────────────────────────────────────────────────────┬───────────────────────────────┘           │
│       │                                                                      │                                           │
│       │            ┌─────────────────────────────────────────────────────────┘                                           │
│       │            v                                                                                                     │
│       │     ┌─────────────┐     ┌───────────────────────────────────┐                                                   │
│       │     │             │     │                                   │                                                   │
│       │     │  Annotated  │────>│  HTTP POST to LM Studio           │                                                   │
│       │     │  Image b64  │     │  /v1/chat/completions             │                                                   │
│       │     │  (ghosts +  │     │  [system_prompt, user: obs+image] │                                                   │
│       │     │   heat +    │     │                                   │                                                   │
│       │     │   screen)   │     │  timeout: max(30, configured)s    │                                                   │
│       │     └─────────────┘     └───────────────┬───────────────────┘                                                   │
│       │                                          │                                                                       │
│       └──────────────────────────────────────────┘                                                                       │
│                                                                                                                         │
└─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```


### Single Turn Lifecycle

```
┌─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                                                                                                         │
│  PHASE              ACTION                                      STATE MUTATION                    BLOCKING ON           │
│  ─────              ──────                                      ──────────────                    ───────────           │
│                                                                                                                         │
│  running            VLM JSON arrives (boot / inject /           next_vlm consumed                next_event             │
│                     previous VLM response)                      next_event cleared                                      │
│       │                                                                                                                 │
│       v                                                                                                                 │
│  running            Cascading parser (lv 0-5)                   observation, bboxes, actions      (sync)                │
│                     Prefix: [TURN N] [EXECUTED: ...]            stored in State                                         │
│                     Prefix: [FORMAT ERROR] if lv>=3             msg_id incremented                                      │
│                     Ghost crops from prev raw frame             ghost ring buffer updated                                │
│       │                                                                                                                 │
│       v                                                                                                                 │
│  executing          Win32 mouse_event / SetCursorPos            (physical world changes)          run_in_executor       │
│                     click, drag, move, right_click                                                                      │
│                     double_click with configurable delays                                                                │
│       │                                                                                                                 │
│       v                                                                                                                 │
│  capturing          GDI BitBlt full screen                      raw_b64, raw_bgra updated         run_in_executor       │
│                     crop to CAPTURE_CROP region                  raw_seq incremented                                     │
│                     optional StretchBlt resize                   raw_bgra stored for next                                │
│                     BGRA -> PNG -> base64                        turn's ghost cropping                                   │
│       │                                                                                                                 │
│       v                                                                                                                 │
│  waiting_ann        pending_seq = turn                          annotated_event cleared            annotated_event       │
│                     Browser polls /state, sees phase              (with timeout fallback            OR timeout            │
│                     Fetches /frame for raw image                  to raw frame if browser                                │
│                     Fetches /ghosts for ghost images              is disconnected)                                       │
│                     Draws ghosts (faded bbox crops)                                                                     │
│                     Draws orange heat over ghosts                                                                       │
│                     Exports composite, POSTs /annotated                                                                 │
│       │                                                                                                                 │
│       v                                                                                                                 │
│  calling_vlm        HTTP POST to LM Studio                      (network I/O)                     run_in_executor       │
│                     system_prompt + observation + image           response parsed next turn                               │
│                     image contains: screen + ghosts + heat                                                               │
│       │                                                                                                                 │
│       v                                                                                                                 │
│  running            VLM response stored as next_vlm             next_event set                    (loops to top)        │
│                                                                                                                         │
└─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```


### Ghost Memory System

```
┌─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                                                                                                         │
│  GHOST MEMORY — VISUAL TEMPORAL NARRATIVE IN A SINGLE FRAME                                                             │
│                                                                                                                         │
│  When the model outputs bboxes, the engine crops those regions from the CURRENT raw screenshot                          │
│  and stores them in a ring buffer (Ghost objects). On subsequent turns, the browser overlays                             │
│  these stored crops onto the new screenshot at age-decayed opacity.                                                     │
│                                                                                                                         │
│  Turn 1: model places bbox on Start button                                                                              │
│  Turn 2: model places bbox on Settings icon                                                                             │
│  Turn 3: model places bbox on Display settings                                                                          │
│  Turn 4: model sees THIS image:                                                                                         │
│                                                                                                                         │
│  ┌──────────────────────────────────────────────────────────────────────────────────────────┐                            │
│  │                                                                                          │                            │
│  │                            CURRENT SCREENSHOT (full opacity)                              │                            │
│  │                                                                                          │                            │
│  │   ┌─────────┐                                                                            │                            │
│  │   │ Display │  <-- ghost from turn 3 (age=1, opacity=0.35 * 0.55^1 = 0.19)              │                            │
│  │   │ Settings│      semi-transparent imprint of what was there 1 turn ago                 │                            │
│  │   └─────────┘                                                                            │                            │
│  │                                                                                          │                            │
│  │          ┌──────┐                                                                        │                            │
│  │          │ Gear │  <-- ghost from turn 2 (age=2, opacity=0.35 * 0.55^2 = 0.11)          │                            │
│  │          │ icon │      fainter imprint of the Settings icon from 2 turns ago             │                            │
│  │          └──────┘                                                                        │                            │
│  │                                                                                          │                            │
│  │                                                                                          │                            │
│  │  ┌───┐                                                                                   │                            │
│  │  │Win│  <-- ghost from turn 1 (age=3, opacity=0.35 * 0.55^3 = 0.06)                     │                            │
│  │  └───┘      barely visible imprint of the Start button from 3 turns ago                  │                            │
│  │                                                                                          │                            │
│  │                                                                           ░░░▒▓▓▒░░░     │                            │
│  │                                                                           ░░▒▓██▓▒░░     │                            │
│  │                                                                           ░░░▒▓▓▒░░░     │                            │
│  │                                                                           ^ orange heat   │                            │
│  │                                                                             (last click)  │                            │
│  │                                                                                          │                            │
│  └──────────────────────────────────────────────────────────────────────────────────────────┘                            │
│                                                                                                                         │
│  THE MODEL SEES ONE IMAGE containing:                                                                                   │
│    1. Current screen state (what IS)                                                                                    │
│    2. Historical region snapshots at decreasing opacity (what WAS)                                                      │
│    3. Orange heat blobs at action execution points (what I DID)                                                         │
│                                                                                                                         │
│  This single image encodes a TEMPORAL NARRATIVE without any explicit temporal data structure.                            │
│  Recency is encoded as opacity. Change is encoded as visual interference between ghost and current content.             │
│  The model's attention history is encoded as the spatial distribution of ghosts.                                        │
│                                                                                                                         │
│  RING BUFFER:                                                                                                           │
│    GHOST_MAX = 12 (maximum stored ghosts)                                                                               │
│    GHOST_MAX_AGE = 6 (ghosts older than this are excluded from rendering)                                               │
│    GHOST_OPACITY_BASE = 0.35 (opacity of a ghost at age=0, i.e. placed this turn)                                      │
│    GHOST_OPACITY_DECAY = 0.55 (multiplier per turn of age: opacity = base * decay^age)                                 │
│                                                                                                                         │
│  OPACITY CURVE:                                                                                                         │
│    age 0: 0.350  (placed this turn — should never be visible since it matches current frame)                            │
│    age 1: 0.193  (one turn old — clearly visible ghost)                                                                 │
│    age 2: 0.106  (two turns old — moderate ghost)                                                                       │
│    age 3: 0.058  (three turns old — faint ghost)                                                                        │
│    age 4: 0.032  (four turns old — barely perceptible)                                                                  │
│    age 5: 0.018  (five turns old — nearly invisible, below VLM perception threshold)                                    │
│    age 6: 0.010  (six turns old — effectively gone)                                                                     │
│                                                                                                                         │
└─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```


### Cascading Parser

```
┌─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                                                                                                         │
│  RAW VLM TEXT ──────────────────────────────────────────────────────────────────────────────────> EXTRACTED DATA         │
│                                                                                                                         │
│  Level 0 ─── json.loads(raw)                        Perfect JSON               ─── ~60% of outputs                      │
│       │                                                                                                                 │
│       │ fail                                                                                                            │
│       v                                                                                                                 │
│  Level 1 ─── Extract ```json{...}``` or {outermost}  Markdown / trailing text  ─── ~15% of outputs                      │
│       │                                                                                                                 │
│       │ fail                                                                                                            │
│       v                                                                                                                 │
│  Level 2 ─── Fix unquoted keys, trailing commas,     Lenient repair            ─── ~10% of outputs                      │
│              single quotes -> double quotes                                                                             │
│       │                                                                                                                 │
│       │ fail                                                                                                            │
│       v                                                                                                                 │
│  Level 3 ─── Regex extraction of fields               Structured non-JSON       ─── ~10% of outputs                     │
│              (default regexes or PARSE_CUSTOM_REGEX)   observation, bboxes,                                              │
│              Also checks for UCI chess moves           click/drag patterns                                               │
│       │                                                                                                                 │
│       │ fail                                                                                                            │
│       v                                                                                                                 │
│  Level 4 ─── Freetext coordinate scan                Natural language coords   ─── ~4% of outputs                       │
│              "click at 500,300" -> click(500,300)                                                                       │
│       │                                                                                                                 │
│       │ fail                                                                                                            │
│       v                                                                                                                 │
│  Level 5 ─── Total failure                           Raw text as narrative     ─── ~1% of outputs                       │
│              No actions, loop continues               Corrective prefix next                                             │
│                                                                                                                         │
│  CORRECTIVE FEEDBACK:                                                                                                   │
│    Level >= 3: observation prefixed with [FORMAT ERROR lv=N: output ONLY valid JSON]                                    │
│    Level > PARSE_MAX_LEVEL: actions dropped entirely (safety gate)                                                      │
│    Every turn: observation prefixed with [TURN N] [EXECUTED: click(500,500), drag(100,100,800,800)]                     │
│                                                                                                                         │
└─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```


### Orange Heatmap Rendering

```
┌─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                                                                                                         │
│  ORANGE HEAT — executed action feedback (proprioceptive channel)                                                        │
│                                                                                                                         │
│  Point actions (click, move, right_click, double_click):                                                                │
│                                                                                                                         │
│         ░░░░░░░░░                                                                                                       │
│       ░░░░▒▒▒▒░░░░                                                                                                     │
│      ░░▒▒▒▓▓▓▓▒▒▒░░                                                                                                   │
│     ░░▒▒▓▓████▓▓▒▒░░                                                                                                  │
│      ░░▒▒▒▓▓▓▓▒▒▒░░           Single radial gradient blob at (x1,y1)                                                  │
│       ░░░░▒▒▒▒░░░░            Radius = max(canvasW, canvasH) * radius_scale                                            │
│         ░░░░░░░░░             Gradient stops: solid center -> transparent edge                                          │
│                                                                                                                         │
│  Drag actions:                                                                                                          │
│                                                                                                                         │
│       ░░░░                                                 ░░░░░░░                                                      │
│      ░░▒▒░░                                             ░░▒▒▒▒▒▒░░                                                     │
│     ░░▒▓▓▒░░         ░░░░░░░░░         ░░░░░░░░░░      ░▒▒▓▓▓▓▓▒▒░                                                    │
│      ░░▒▒░░        ░░▒▒▒▒▒▒░░░       ░░▒▒▒▓▓▒▒▒░░     ░░▒▒▓▓▓▒▒░░                                                    │
│       ░░░░           ░░▒▒▓▒▒░░         ░▒▒▓▓██▓▒░░       ░░▒▒▒░░░                                                     │
│                        ░░▒▒░░░           ░░▒▓▓▓▒░░          ░░░░                                                       │
│     start               ░░░░              ░░▒▒░░                              end                                      │
│     (small)                                 ░░░             (larger)          (tapered)                                  │
│                                                                                                                         │
│  N blobs (drag_steps=12) along the drag vector from (x1,y1) to (x2,y2).                                               │
│  Each blob radius modulated by sin(t*PI): small at endpoints, large at midpoint.                                       │
│  Creates an organic egg-shaped stretched heatmap along the drag path.                                                   │
│  Alpha increases along the path (0.6 at start -> 1.0 at end) so the destination is brighter.                           │
│                                                                                                                         │
│  Trail: configurable trail_turns with alpha decay per turn age.                                                         │
│  Older turn heat is dimmer, creating a fading spatial trajectory.                                                       │
│                                                                                                                         │
│  NO LABELS. NO TEXT. Pure radial gradient heat only.                                                                    │
│                                                                                                                         │
└─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```


### Coordinate System Invariance

```
┌─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                                                                                                         │
│  PHYSICAL SCREEN           CAPTURE CROP              RESIZE                     NORMALIZED                              │
│  2560 x 1440               (arbitrary region)        (optional, to VLM size)    COORDINATE SPACE                        │
│                                                                                                                         │
│  ┌────────────────┐        ┌──────────┐              ┌────────┐                 ┌──────────┐                             │
│  │                │        │          │              │        │                 │(0,0)     │                             │
│  │                │        │  cropped │  StretchBlt  │ resized│   model sees   │          │                             │
│  │     desktop    │───────>│  region  │─────────────>│  image │──────────────> │   1000   │                             │
│  │                │        │          │              │        │                 │   x      │                             │
│  │                │        │          │              │        │                 │   1000   │                             │
│  │                │        └──────────┘              └────────┘                 │     (N,N)│                             │
│  └────────────────┘        e.g. 800x600             e.g. 512x288               └──────────┘                             │
│                                                                                                                         │
│  MODEL SAYS: click(500,500) = center of whatever image it received                                                      │
│                                                                                                                         │
│  REVERSE MAPPING:                                                                                                       │
│    norm(500,500) -> center of crop region on physical screen                                                            │
│    norm(0,0)     -> top-left of crop region                                                                             │
│    norm(1000,1000) -> bottom-right of crop region                                                                       │
│                                                                                                                         │
│  Resize is INVISIBLE to coordinate mapping. Whether the crop is 800x600 or resized to 512x288,                         │
│  (500,500) always maps to the same physical pixel. X and Y normalized independently.                                   │
│                                                                                                                         │
│  Ghost images are cropped from the capture-sized frame using normalized bbox coordinates,                               │
│  then drawn on the canvas at normalized positions. Same coordinate space everywhere.                                    │
│                                                                                                                         │
│  select_region.py outputs normalized coordinates directly. Copy to config and go.                                       │
│                                                                                                                         │
└─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```


### File Structure

```
┌─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                                                                                                         │
│  franz/                                                                                                                 │
│  ├── main.py              Engine, HTTP server, Win32 capture, cascading parser, ghost memory, mouse execution           │
│  ├── config.py            System prompt, VLM params, capture settings, ghost params, UI heatmap config                  │
│  ├── panel.html           Browser dashboard: 3-pane layout, ghost rendering, heatmap drawing, annotation export         │
│  ├── select_region.py     Standalone transparent overlay crop selector tool (outputs config-ready coordinates)          │
│  └── runs/                                                                                                              │
│      └── run_NNNN/                                                                                                      │
│          ├── main.log                                                                                                   │
│          ├── turns.jsonl                                                                                                │
│          ├── turn_NNNN_raw.png                                                                                          │
│          └── turn_NNNN_ann.png                                                                                          │
│                                                                                                                         │
│  4 FILES. No dependencies beyond Python 3.13 stdlib + modern Chrome + LM Studio.                                       │
│                                                                                                                         │
└─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```


### Panel Layout

```
┌─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                                                                                                         │
│  ┌──────────────────────────────────────────────┬───┬──────────────────────────────────────┐                             │
│  │                                              │   │  VLM OUTPUT                          │                             │
│  │  ANNOTATED VIEW                              │ G │                                      │                             │
│  │                                              │ U │  observation:                        │                             │
│  │  ┌────────────────────────────────────────┐  │ T │  I see the desktop with taskbar...   │                             │
│  │  │                                        │  │ T │                                      │                             │
│  │  │  raw screenshot                        │  │ E │  bboxes:                             │                             │
│  │  │  + ghost images (age-faded)            │  │ R │  [{"x1":0,"y1":950,"x2":50,...}]     │                             │
│  │  │  + orange heat (executed actions)      │  │   │                                      │                             │
│  │  │                                        │  │ V │  actions:                            │                             │
│  │  │  (this is what the VLM sees)           │  │   │  [{"name":"click","x1":25,...}]      │                             │
│  │  │                                        │  ├─X─┼──────────────────────────────────────│                             │
│  │  │                                        │  │ G │  EVENT LOG                           │                             │
│  │  │                                        │  │ U │                                      │                             │
│  │  │                                        │  │ T │  12:34:56 /ann seq=7 ok=true         │                             │
│  │  │                                        │  │ T │  12:34:55 exported ann len=43210     │                             │
│  │  │                                        │  │ E │  12:34:54 new vlm msg_id=7 turn=7   │                             │
│  │  │                                        │  │ R │  12:34:50 /state 200                 │                             │
│  │  │                                512x288 │  │   │                                      │                             │
│  │  └────────────────────────────────────────┘  │ H │                                      │                             │
│  │                                              │   │                                      │                             │
│  └──────────────────────────────────────────────┴───┴──────────────────────────────────────┘                             │
│  ┌─────────────────────────────────────────────────────────────────────────────────────────┐                             │
│  │ Franz │ phase: running │ turn: 7 │ msg: 7 │ seq: 7 │ lv: 0 │ ghosts: 4 │              │                             │
│  └─────────────────────────────────────────────────────────────────────────────────────────┘                             │
│                                                                                                                         │
│  Canvas pane spans full left column (all 3 grid rows).                                                                  │
│  Gutters are draggable. Cross-handle resizes both axes.                                                                 │
│  Split positions persist in localStorage.                                                                               │
│  No injection pane. /inject endpoint exists for programmatic use via curl.                                              │
│                                                                                                                         │
└─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```


### Self-Awareness Mechanisms

```
┌─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                                                                                                         │
│  CHANNEL          MECHANISM                    WHAT THE MODEL PERCEIVES                 COGNITIVE FUNCTION               │
│  ───────          ─────────                    ────────────────────────                 ──────────────────               │
│                                                                                                                         │
│  TEXTUAL          observation field            Its own prior narrative                  Autobiographical memory          │
│                   [TURN N] prefix              Temporal grounding                       Sense of duration                │
│                   [EXECUTED: ...] prefix       Record of own actions                    Proprioceptive echo              │
│                   [FORMAT ERROR] prefix        Awareness of own malfunction             Error monitoring                 │
│                                                                                                                         │
│  VISUAL-ORANGE    Radial heat at action pts    Where its body acted                     Proprioception                   │
│                   Egg-shaped drag heat         Path of movement                         Kinesthetic trace                │
│                   Trail with alpha decay       Older actions dimmer                     Fading motor memory              │
│                                                                                                                         │
│  VISUAL-GHOST     Bbox crop imprints           What was in attended regions             Visual working memory            │
│                   Age-decayed opacity           Recency gradient                         Temporal ordering               │
│                   Ghost vs current mismatch    Change detection signal                  Prediction error                 │
│                   Ghost accumulation           Spatial attention history                Attentional trajectory           │
│                                                                                                                         │
│  COMBINED         Single composite image       One frame encodes a story:               Narrative perception            │
│                                                 current state + recent history                                          │
│                                                 + action trace + attention map                                          │
│                                                                                                                         │
│  The model is STATELESS per API call. It has no conversation history, no hidden state, no memory beyond what is         │
│  encoded in the observation text and the annotated image. The observation is the textual story. The image is the        │
│  visual story. Together they constitute the agent's entire accessible past.                                             │
│                                                                                                                         │
│  Ghost images solve three problems simultaneously:                                                                      │
│    1. OUTCOME VERIFICATION: ghost shows what was there before; current content shows what is there now.                 │
│       The model sees the delta visually without needing numeric metrics.                                                │
│    2. OBJECT PERMANENCE: regions the model attended to persist as fading imprints, giving the illusion                  │
│       of stable objects in a stream of disconnected snapshots.                                                          │
│    3. ATTENTION CONTINUITY: the spatial distribution of ghosts shows the model where it has been looking,               │
│       enabling it to reason about what it has and hasn't explored.                                                      │
│                                                                                                                         │
└─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```


### Philosophical Foundation

```
┌─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                                                                                                         │
│  Franz encodes three philosophical positions as engineering decisions:                                                   │
│                                                                                                                         │
│  1. ENACTIVISM (Varela, Thompson, Rosch):                                                                               │
│     Cognition is not computation on internal representations. It is the ongoing sensorimotor coupling                   │
│     between agent and environment. Franz has no internal world model. Its understanding of the desktop                  │
│     is constituted entirely by its perception-action loop. The observation field is not a description                   │
│     OF the world but an act of sense-making WITHIN the world.                                                           │
│                                                                                                                         │
│  2. PHENOMENOLOGICAL REDUCTION (Husserl):                                                                               │
│     The system prompt enforces phenomenological discipline: "describe ONLY what you see. Never hallucinate."            │
│     This brackets presuppositions and forces the model to attend to appearances rather than assumptions.                │
│     The bboxes are acts of intentional attention — the model directs its gaze toward specific regions,                  │
│     and those regions persist as ghosts. Attention constitutes the perceptual field.                                    │
│                                                                                                                         │
│  3. EXTENDED MIND (Clark, Chalmers):                                                                                    │
│     The ghost images and orange heat are not just feedback — they are cognitive scaffolding. The model's                │
│     memory is not stored internally but externally, in the annotated image. The image IS the model's                    │
│     working memory. The ring buffer of ghost crops IS the model's episodic memory. The environment                      │
│     (the annotated screenshot) does cognitive work that would otherwise require internal state.                          │
│                                                                                                                         │
│  Practical consequence: the entire system has exactly 0 bytes of persistent model state between turns.                  │
│  All continuity emerges from the interplay of narrative text, ghost images, and heat overlays.                          │
│  The story is the memory. The image is the mind.                                                                        │
│                                                                                                                         │
└─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```


## Configuration Reference

```
┌─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                                                                                                         │
│  VARIABLE                     DEFAULT         DESCRIPTION                                                               │
│  ────────                     ───────         ───────────                                                               │
│  HOST                         127.0.0.1       Server bind address                                                       │
│  PORT                         1234            Server port                                                               │
│  LOG_LEVEL                    INFO            Python logging level                                                      │
│  LOG_TO_FILE                  True            Write main.log in run directory                                           │
│  RUNS_DIR                     runs            Base directory for run folders                                             │
│  LOG_LAYOUT                   flat            "flat" (JSONL + files) or "turn_dirs" (subdirectories)                    │
│                                                                                                                         │
│  API_URL                      (set)           LM Studio /v1/chat/completions endpoint                                   │
│  MODEL                        (set)           Model identifier for LM Studio                                            │
│  TEMPERATURE                  0.7             Sampling temperature                                                      │
│  TOP_P                        0.9             Nucleus sampling threshold                                                │
│  MAX_TOKENS                   1000            Max response tokens                                                       │
│  VLM_HTTP_TIMEOUT_SECONDS     120.0           HTTP timeout (min 30s enforced)                                           │
│  SYSTEM_PROMPT                (set)           Behavioral contract for the VLM                                           │
│                                                                                                                         │
│  CAPTURE_CROP                 full screen     Normalized crop {x1,y1,x2,y2} in [0,1000]                                │
│  CAPTURE_WIDTH                512             Output width (0 = native crop size)                                       │
│  CAPTURE_HEIGHT               288             Output height (0 = native crop size)                                      │
│  CAPTURE_SCALE_PERCENT        100             Scale if WIDTH/HEIGHT are 0 (100 = no scale)                              │
│  CAPTURE_DELAY                0.0             Seconds to wait before capture                                            │
│                                                                                                                         │
│  BOOT_ENABLED                 True            Inject boot VLM output at startup                                         │
│  BOOT_VLM_OUTPUT              (set)           JSON string to inject at boot                                             │
│                                                                                                                         │
│  PHYSICAL_EXECUTION           True            Actually move the mouse                                                   │
│  ACTION_DELAY_SECONDS         0.05            Delay between actions                                                     │
│  DRAG_DURATION_STEPS          20              Mouse interpolation steps for drag                                        │
│  DRAG_STEP_DELAY              0.01            Delay between drag steps                                                  │
│  ANNOTATED_TIMEOUT_SECONDS    10.0            Timeout for browser annotation (falls back to raw)                        │
│  PARSE_MAX_LEVEL              4               Max parser cascade level (0=strict, 4=full recovery)                      │
│  PARSE_CUSTOM_REGEX           None            Optional dict with observation/bbox/action regex overrides                │
│                                                                                                                         │
│  GHOST_MAX                    12              Maximum stored ghost images in ring buffer                                 │
│  GHOST_MAX_AGE                6               Ghosts older than this are not rendered                                   │
│  GHOST_OPACITY_BASE           0.35            Base opacity for a fresh ghost                                            │
│  GHOST_OPACITY_DECAY          0.55            Opacity multiplier per turn of age                                        │
│                                                                                                                         │
│  UI_CONFIG                    (dict)          Sent to panel: executed_heat config + ghosts config                        │
│    .executed_heat.enabled     True            Enable orange heat rendering                                              │
│    .executed_heat.radius_scale 0.18           Blob radius as fraction of canvas diagonal                                │
│    .executed_heat.drag_steps  12              Number of blobs along drag path                                           │
│    .executed_heat.trail_turns 1               Number of past turns to show in heat trail                                │
│    .executed_heat.trail_shrink 1.0            Radius shrink factor per trail age                                        │
│    .executed_heat.stops       (gradient)      Radial gradient color stops                                               │
│    .ghosts.enabled            True            Enable ghost rendering                                                    │
│    .ghosts.opacity_base       0.35            Ghost opacity (mirrored from GHOST_OPACITY_BASE)                          │
│    .ghosts.opacity_decay      0.55            Ghost decay (mirrored from GHOST_OPACITY_DECAY)                           │
│    .ghosts.edge_glow          True            Draw subtle edge outline on ghosts                                        │
│    .ghosts.edge_color         rgba(60,140...) Edge outline color                                                        │
│    .ghosts.edge_width         1               Edge outline width                                                        │
│                                                                                                                         │
└─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```


## HTTP API

```
┌─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                                                                                                         │
│  METHOD   PATH          DIRECTION        PAYLOAD / RESPONSE                                                             │
│  ──────   ────          ─────────        ──────────────────                                                             │
│                                                                                                                         │
│  GET      /             server->browser  panel.html                                                                     │
│  GET      /config       server->browser  {ui, capture_width, capture_height}                                            │
│  GET      /state        server->browser  {phase, error, turn, msg_id, pending_seq, annotated_seq,                      │
│                                           raw_seq, bboxes, actions, observation, vlm_json,                              │
│                                           parse_level, ghost_count}  (no image data)                                    │
│  GET      /frame        server->browser  {seq, raw_b64}  (raw screenshot, fetched only when needed)                    │
│  GET      /ghosts       server->browser  {turn, ghosts: [{x1,y1,x2,y2,turn,age,image_b64,label}]}                     │
│                                                                                                                         │
│  POST     /annotated    browser->server  {seq: int, image_b64: string}  -> {ok, seq}                                   │
│  POST     /inject       client->server   {vlm_text: string}  -> {ok}                                                   │
│                                                                                                                         │
│  Polling: browser fetches /state every 400ms.                                                                           │
│  When phase="waiting_annotated" and new pending_seq detected:                                                           │
│    browser fetches /frame and /ghosts in parallel, renders, exports, POSTs /annotated.                                  │
│                                                                                                                         │
└─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```


## Requirements

```
- Windows 11
- Python 3.13+
- LM Studio with a VLM loaded (tested: Qwen3-VL-2B-Instruct abliterated via huihui)
- Modern Chrome (OffscreenCanvas, ES2022+)
- No pip packages required
- No build tools required
```


## Quick Start

```
1. Start LM Studio, load the VLM, enable server on port 1235
2. Run: python select_region.py
   -> drag to select screen region, copy the CAPTURE_CROP line to config.py
3. Edit config.py: set CAPTURE_CROP, adjust SYSTEM_PROMPT if needed
4. Run: python main.py
5. Browser opens automatically. The loop begins.
```
