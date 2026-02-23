"""
FRANZ CHANGELOG
===============

Complete record of architectural evolution from original codebase to final implementation.
Based on iterative analysis and design sessions.


VERSION 0.1 — ORIGINAL CODEBASE (as received)
==============================================

Files: main.py, config.py, config-first-chess-move.py, config_Dual_Epistemology.py, panel.html
State: functional prototype with significant structural issues.


VERSION 1.0 — FIRST REWRITE
============================

Trigger: exhaustive line-by-line analysis of entire codebase with 10+ mental multi-turn simulations.

BUGS FIXED
----------
[BUG-001] asyncio.get_event_loop() used throughout engine_loop.
          Deprecated in Python 3.12+, raises warning in 3.13.
          FIX: replaced all instances with asyncio.get_running_loop().

[BUG-002] Signal handler on Windows was a no-op expression statement.
          The line `loop.add_signal_handler(...) if ... else None` evaluated to None on Windows.
          FIX: removed entirely. Rely on KeyboardInterrupt propagation through asyncio.run.

[BUG-003] Global S and STOP declared without assignment at module level.
          Any import-time access would crash with NameError.
          FIX: kept declaration pattern but ensured assignment in async_main before any use.

[BUG-004] parse_vlm_json only looked for "observation" key.
          Dual Epistemology config uses "phenomenology" as the narrative field.
          FIX: parser now checks observation OR phenomenology, using first non-empty.

[BUG-005] No handler for "chess_move" action type.
          Dual Epistemology config outputs {"name":"chess_move","uci":"e2e4"} but execute_actions
          fell through to unknown action warning.
          FIX: added _uci_to_drag() translator that converts UCI notation to normalized drag coordinates
          assuming standard 8x8 board orientation.

[BUG-006] VLM_HTTP_TIMEOUT_SECONDS=0.0 resulted in timeout=None (infinite).
          If VLM hangs, Franz hangs forever.
          FIX: default 120s, enforced minimum 30s. timeout=max(30.0, configured).

[BUG-007] CAPTURE_SCALE_PERCENT=0 treated as falsy, defaulting to 100.
          The expression `_cfg("CAPTURE_SCALE_PERCENT", 100) or 100` converts 0 to 100.
          FIX: explicit check `if p > 0 and p != 100`.

[BUG-008] engine_task.cancel() called without awaiting the task.
          Task cancellation was fire-and-forget, potential resource leak.
          FIX: added `try: await task except CancelledError: pass` after cancel.

[BUG-009] Boot VLM output in config.py fabricated observations.
          "I observe the desktop. There is a canvas area in the center" — hallucinated content
          that violated the system prompt rule "never fabricate feedback."
          FIX: neutral boot: "System initialized. Awaiting first screenshot."

[BUG-010] _crop_bgra accepted dict parameter but was called with positional pixel coords.
          Inconsistent interface between _crop_px returning tuple and _crop_bgra expecting dict.
          FIX: _crop_bgra now accepts (bgra, sw, sh, x1, y1, x2, y2) directly.

DEAD CODE REMOVED
-----------------
[DEAD-001] format_user_payload() — defined but never called anywhere.
[DEAD-002] _screen_to_norm_xy() — defined but never called anywhere.
[DEAD-003] S.actions_text field — set in engine_loop but never read by any consumer.
[DEAD-004] from __future__ import annotations — unnecessary in Python 3.13 (native PEP 604).

PERFORMANCE IMPROVEMENTS
------------------------
[PERF-001] _crop_bgra now uses memoryview for row copies instead of raw byte slicing.
[PERF-002] /state endpoint no longer sends raw_b64 on every 400ms poll.
           Moved to separate /frame endpoint, fetched only when browser needs to annotate.
           Saves ~500KB/s of unnecessary localhost bandwidth.

STRUCTURAL CHANGES
------------------
[STRUCT-001] Three chess/experimental config files consolidated into one general-purpose config.py.
             Chess-specific and Dual Epistemology configs removed as separate files.
             The system is designed for general Windows 11 desktop control, not chess-specific.
             Chess and other specialized scenarios are supported through config.py modifications.

[STRUCT-002] Added ANNOTATED_TIMEOUT_SECONDS with fallback to raw frame.
             If browser disconnects or is slow, engine continues with unannotated screenshot
             instead of waiting indefinitely.

[STRUCT-003] Dual Epistemology config variables that were never read by main.py removed:
             VLM_IMAGE_SOURCE, CHESS_GUARD_BLOCK_OPPONENT, CHESS_VERIFY_MOVE,
             CHESS_VERIFY_THRESHOLD, WORLD_MARKERS_MAX, PARSE_REGEX_* (aspirational dead config).

PROMPT ENGINEERING CHANGES
--------------------------
[PROMPT-001] System prompt tightened from ~500 tokens to ~180 tokens.
             2B model has ~820 tokens remaining for response.
[PROMPT-002] Observation limit reduced from 200 words to 120 words.
             Leaves more token budget for bboxes and actions.
[PROMPT-003] One-shot JSON example added to system prompt.
             Small models benefit from concrete format demonstration.
[PROMPT-004] Max actions reduced from 6 to 4. Max bboxes kept at 6.
             Fewer actions per turn = more predictable execution.

PANEL (HTML/JS) CHANGES
------------------------
[PANEL-001] Dual-schema VLM rendering: displays both observation and phenomenology fields.
[PANEL-002] Epistemology block display for Dual Epistemology schema.
[PANEL-003] bbox_heat now reads dash property from config, supports setLineDash.
[PANEL-004] Bbox labels rendered when bb.label exists.
[PANEL-005] Raw frame fetched from /frame instead of /state.
[PANEL-006] parse_level displayed in status bar.
[PANEL-007] Error level 'bad' in uiLog corrected to 'error'.


VERSION 1.1 — CASCADING PARSER
===============================

Trigger: analysis of VLM output failure modes for 2B-class models.

FEATURE: 5-LEVEL CASCADING JSON PARSER
---------------------------------------
[PARSE-001] Level 0: json.loads(raw) — perfect JSON. ~60% of outputs.
[PARSE-002] Level 1: extract from markdown ```json...``` or outermost {braces}. ~15%.
[PARSE-003] Level 2: lenient repair (unquoted keys, trailing commas, single quotes). ~10%.
[PARSE-004] Level 3: regex field extraction (observation, bbox patterns, action patterns, UCI). ~10%.
[PARSE-005] Level 4: freetext coordinate scan ("click at 500,300"). ~4%.
[PARSE-006] Level 5: total failure — raw text as narrative, no actions. ~1%.
[PARSE-007] Corrective feedback: when level >= 3, observation is prefixed with
            [FORMAT ERROR lv=N: output ONLY valid JSON] to create self-correcting loop.
[PARSE-008] Safety gate: PARSE_MAX_LEVEL config variable. When parse level > max, actions dropped.
[PARSE-009] PARSE_CUSTOM_REGEX config: optional dict with observation/bbox/action regex overrides
            for power-user escape hatch. Default regexes hardcoded in main.py (mechanism vs policy).
[PARSE-010] parse_vlm now returns 4-tuple: (narrative, bboxes, actions, parse_level).


VERSION 1.2 — ORGANIC HEATMAPS, NO LABELS, LAYOUT CHANGES
===========================================================

Trigger: request for scientific-looking heatmaps without labels, injection pane removal.

HEATMAP REDESIGN
----------------
[HEAT-001] ORANGE (executed actions) — drag rendering completely changed.
           OLD: two radial blobs at endpoints + thin connecting line.
           NEW: N overlapping radial gradient blobs along drag vector (drag_steps=12).
           Each blob radius modulated by sin(t*PI): small at endpoints, large at midpoint.
           Creates organic egg-shaped stretched heatmap along the drag path.
           Alpha increases along path (0.6 at start, 1.0 at end) so destination is brighter.

[HEAT-002] BLUE (bboxes) — rendering completely changed.
           OLD: radial gradient fill + hard border rectangle.
           NEW: each bbox drawn as 4 edges, each edge drawn as N overlapping blobs (edge_steps=10).
           Same sin(t*PI) radius modulation per edge. Corners get double heat from overlapping edges,
           creating natural rounded corners. Center has no blobs, naturally transparent.
           Result resembles a scientific attention heatmap, not a hard rectangle.

[HEAT-003] ALL LABELS REMOVED from annotated image.
           OLD: text labels like "1. click(500,500)" rendered on c-label canvas layer.
           NEW: c-label canvas layer removed entirely. No text on the annotated image.
           Rationale: labels consume pixels, confuse VLM (it tries to OCR its own overlay),
           and the system prompt already explains color semantics.

LAYOUT CHANGES
--------------
[LAYOUT-001] Injection pane removed from panel.
             OLD: 4-pane grid (canvas TL, vlm TR, log BL, inject BR).
             NEW: 3-pane (canvas full-left spanning all rows, vlm top-right, log bottom-right).
             Rationale: inject pane was never used in production. /inject endpoint retained for
             programmatic use via curl.

[LAYOUT-002] Canvas pane now spans grid-row:1/4 (full left column height).
             Gives maximum visible area for the annotated screenshot.


VERSION 1.3 — SELF-AWARENESS MECHANISMS
========================================

Trigger: analysis of improvements to make 2B model achieve better self-awareness.

PROPOSALS ANALYZED
------------------
[SELF-001] OUTCOME VERIFICATION SIGNAL
           Proposed: compute pixel-difference metric between pre/post action frames.
           Status: SUPERSEDED by ghost memory in v2.0 (ghosts provide visual verification).

[SELF-002] ATTENTION CONTINUITY SCORE
           Proposed: report what percentage of blue regions changed.
           Status: SUPERSEDED by ghost memory (visual change detection).

[SELF-003] ACTION ECHO IN OBSERVATION — IMPLEMENTED
           Observation prefixed with [EXECUTED: click(500,500), drag(100,100,800,800)].
           Model reads explicit text record of what it did, in addition to orange heat.
           Trivial implementation: string concatenation in engine_loop.

[SELF-004] TURN COUNTER IN OBSERVATION — IMPLEMENTED
           Observation prefixed with [TURN 7].
           Provides temporal grounding for the stateless model.
           Trivial implementation: string concatenation in engine_loop.

[SELF-005] BBOX PERSISTENCE FEEDBACK
           Proposed: track cross-turn bbox overlap.
           Status: SUPERSEDED by ghost memory (persistent bbox crops are literal persistence).

[SELF-006] CONFIDENCE CALIBRATION
           Proposed: model outputs CONFIDENCE: high|medium|low, engine adjusts behavior.
           Status: NOT IMPLEMENTED. Requires prompt and parser changes. Future work.

IMPLEMENTED IN OBSERVATION PREFIX
---------------------------------
Every turn, observation is prefixed with:
  [TURN N] [EXECUTED: action_echo] [FORMAT ERROR lv=X] (if applicable)

This creates three text-based self-awareness channels that cost ~20 tokens and provide
deterministic feedback that does not depend on visual perception.


VERSION 1.4 — SELECT REGION TOOL
=================================

Trigger: request for visual crop selection instead of manual coordinate guessing.

[TOOL-001] select_region.py — standalone Win32 GDI transparent overlay tool.
           Covers entire primary monitor with a transparent layered window.
           Crosshair cursor for precision.
           Rubber-band selection with white solid + green dashed rectangle.
           Crosshair guides at selection center.
           ESC to cancel.
           On completion: outputs normalized (0-1000) coordinates + copy-paste config line.

[TOOL-002] Also outputs explanation of CAPTURE_CROP vs CAPTURE_WIDTH/CAPTURE_HEIGHT:
           - CAPTURE_CROP defines the region (what part of screen the model sees).
           - CAPTURE_WIDTH/HEIGHT resize the image resolution (how many pixels).
           - Coordinate mapping is invariant to resize. 500,500 always = center of crop.
           - Setting WIDTH=0, HEIGHT=0 keeps native crop resolution.

[TOOL-003] DPI awareness set before window creation for correct coordinates on HiDPI displays.

KNOWN LIMITATION: primary monitor only (GetSystemMetrics returns primary dimensions).


VERSION 2.0 — GHOST MEMORY SYSTEM
===================================

Trigger: idea to use bbox regions as persistent visual memory through semi-transparent image imprints.

CONCEPT
-------
When the model outputs bboxes, the engine crops those exact regions from the current raw screenshot
and stores the small images in a ring buffer (Ghost objects). On subsequent turns, the browser
overlays these stored crops onto the new screenshot at age-decayed opacity.

This transforms bboxes from abstract attention markers into concrete visual memory:
- OLD: blue heatmap rectangle = "something was interesting here"
- NEW: ghost image crop = "THIS SPECIFIC CONTENT was here N turns ago"

ANALYSIS: GHOST vs HEATMAP
--------------------------
Ghosts subsume the previous blue heatmap mechanism:
- Blue heatmap said WHERE the model looked. Ghost says WHERE AND WHAT.
- Blue heatmap was abstract (a colored rectangle). Ghost is concrete (actual pixel content).
- Blue heatmap had no temporal information. Ghost has age-based opacity.
- Blue heatmap center was transparent by accident (edge-blob design). Ghost center shows content.

Ghosts also subsume three of the six self-awareness proposals:
- 8.1 (outcome verification): ghost shows what WAS, current shows what IS. Delta is visible.
- 8.3 (action echo): ghost near orange heat = visual record of context at action time.
- 8.5 (bbox persistence): ghost IS persistence. Old bboxes literally persist as images.

IMPLEMENTATION — MAIN.PY
-------------------------
[GHOST-001] Ghost dataclass: x1, y1, x2, y2, turn, image_b64, label.
[GHOST-002] GHOST_RING: module-level deque[Ghost] ring buffer.
[GHOST-003] _bbox_crop_b64(): crops a bbox region from raw BGRA buffer, encodes as PNG base64.
            Uses normalized coords mapped to pixel coords of the capture-sized frame.
[GHOST-004] _build_ghosts(): called after parsing bboxes, crops from raw_bgra_buf stored in
            engine loop, appends to GHOST_RING, evicts oldest when > GHOST_MAX.
[GHOST-005] _ghosts_for_state(): filters ghosts by GHOST_MAX_AGE, returns list of dicts
            with age calculated from current turn.
[GHOST-006] capture() now returns 4-tuple: (b64, w, h, raw_bgra).
            raw_bgra retained in engine_loop for next turn's ghost cropping.
[GHOST-007] Engine loop stores raw_bgra_buf, raw_w, raw_h across turns.
            Ghost cropping happens at parse time using PREVIOUS turn's raw frame
            (because bboxes describe regions the model saw in the screenshot it just received).
[GHOST-008] /ghosts endpoint: GET returns {turn, ghosts: [...]}.
            Each ghost includes full image_b64 for browser rendering.
[GHOST-009] /state now includes ghost_count (integer) for status bar display.

IMPLEMENTATION — CONFIG.PY
--------------------------
[GHOST-010] GHOST_MAX = 12 (ring buffer size).
[GHOST-011] GHOST_MAX_AGE = 6 (ghosts older than this excluded from rendering).
[GHOST-012] GHOST_OPACITY_BASE = 0.35 (fresh ghost opacity).
[GHOST-013] GHOST_OPACITY_DECAY = 0.55 (per-turn decay multiplier).
            Opacity curve: 0.35, 0.19, 0.11, 0.06, 0.03, 0.02, 0.01...
[GHOST-014] UI_CONFIG.ghosts: enabled, opacity_base, opacity_decay, edge_glow, edge_color, edge_width.
[GHOST-015] System prompt updated to explain ghost semantics:
            "Ghost images = semi-transparent imprints of regions you previously marked as interesting.
             Brighter ghosts are more recent. They show WHAT WAS THERE when you looked.
             Compare ghosts to current content to detect what changed."
[GHOST-016] System prompt updated bbox instruction:
            "Place bboxes on regions you want to remember and compare next turn."

IMPLEMENTATION — PANEL.HTML
----------------------------
[GHOST-017] Canvas stack changed from 2 layers to 3 layers:
            Layer 0: c-base (raw screenshot)
            Layer 1: c-ghost (ghost images, age-faded)
            Layer 2: c-heat (orange executed-action heat)
[GHOST-018] ctxGhost context for ghost canvas layer.
[GHOST-019] drawGhosts() function:
            - Iterates ghost array from /ghosts endpoint.
            - Computes alpha = opacity_base * pow(opacity_decay, age).
            - Skips ghosts with alpha < 0.02 (below perception threshold).
            - Draws ghost image at normalized position with computed alpha.
            - Optional edge glow (subtle stroke rect) for visual separation.
[GHOST-020] ghostCache Map: caches Image objects by key (first 40 chars of base64).
            Prevents re-creating Image objects for unchanged ghosts.
            Auto-evicts when cache exceeds 50 entries.
[GHOST-021] handleFrame() now fetches /frame and /ghosts in parallel via Promise.all.
[GHOST-022] exportAnn() composites 3 layers: c-base + c-ghost + c-heat.
[GHOST-023] Status bar shows ghost count.

REMOVED — BLUE HEATMAP
-----------------------
[GHOST-024] drawBlueHeat() function removed entirely.
            Ghost images replace blue heatmaps as the bbox visualization mechanism.
[GHOST-025] UI_CONFIG.bbox_heat config section removed.
            Replaced by UI_CONFIG.ghosts.
[GHOST-026] Blue edge-blob rendering code removed from panel.html.

PHILOSOPHICAL JUSTIFICATION
----------------------------
Ghost memory implements three established cognitive science concepts:

1. CHRONOPHOTOGRAPHY (Marey, 1882): multiple exposures on one plate showing motion through
   overlaid semi-transparent images. One image encodes temporal sequence.

2. ICONIC MEMORY / SENSORY PERSISTENCE (Sperling, 1960): the visual system retains afterimages
   that overlay current perception. Ghosts replicate this biological mechanism.

3. PREDICTIVE PROCESSING (Friston, Clark): ghost = prediction (what was expected to be there).
   Current content = sensory input. Discrepancy = prediction error, rendered visually.
   The model can detect change without being told about it.


VERSION 2.0 — COMPLETE DIFFERENCES FROM ORIGINAL
==================================================

FILES
-----
ORIGINAL: main.py, config.py, config-first-chess-move.py, config_Dual_Epistemology.py, panel.html
FINAL:    main.py, config.py, panel.html, select_region.py, README.md (as docstring)

MAIN.PY LINE COUNT
------------------
ORIGINAL: ~520 lines
FINAL:    ~460 lines (despite adding cascading parser, ghost memory, action echo, turn counter)

DEAD CODE ELIMINATED
--------------------
- format_user_payload()
- _screen_to_norm_xy()
- S.actions_text
- from __future__ import annotations
- Separate label canvas layer and drawLabels()
- format_user_payload
- Injection-related UI code paths

FEATURES ADDED (not in original)
---------------------------------
- 5-level cascading VLM JSON parser with corrective feedback
- Ghost memory system (ring buffer + bbox crop + age-decayed overlay)
- Turn counter in observation prefix
- Action echo in observation prefix
- Format error corrective prefix
- Annotated timeout with fallback to raw frame
- /frame endpoint (separates image from state polling)
- /ghosts endpoint (ghost image delivery)
- select_region.py standalone tool
- UCI chess move to drag translator
- parse_level in state and status bar
- ghost_count in state and status bar
- PARSE_MAX_LEVEL safety gate
- PARSE_CUSTOM_REGEX override capability

FEATURES REMOVED (were in original)
-------------------------------------
- Injection pane in panel HTML (4th quadrant)
- c-label canvas layer (text labels on annotated image)
- drawLabels() function
- Blue heatmap edge-blob rendering (replaced by ghosts)
- bbox_heat UI config section (replaced by ghosts config)
- Three separate config files (consolidated into one)
- All dead config variables from Dual Epistemology config

API CHANGES
-----------
ORIGINAL: GET /state returned raw_b64 (full screenshot) on every poll
FINAL:    GET /state returns metadata only, GET /frame returns image, GET /ghosts returns ghosts

ORIGINAL: no parse level feedback
FINAL:    parse_level in /state, corrective prefix in observation, displayed in status bar

ORIGINAL: no ghost data
FINAL:    GET /ghosts returns ghost images with age/position/opacity metadata

CANVAS LAYERS
-------------
ORIGINAL: 3 layers (c-base, c-heat, c-label)
FINAL:    3 layers (c-base, c-ghost, c-heat) — c-label removed, c-ghost added

SYSTEM PROMPT
-------------
ORIGINAL: ~500 tokens, no example, 200-word observation limit, no ghost explanation
FINAL:    ~200 tokens, one-shot example, 120-word limit, ghost semantics explained

OBSERVATION FIELD
-----------------
ORIGINAL: raw VLM observation passed through unchanged
FINAL:    prefixed with [TURN N] [EXECUTED: ...] [FORMAT ERROR lv=N] as applicable

COORDINATE SYSTEM
-----------------
ORIGINAL: normalized 0-1000, correct but not verified against all resize combinations
FINAL:    same normalization, verified invariant across all crop/resize configurations,
          select_region.py outputs config-ready normalized coordinates

VLM TIMEOUT
-----------
ORIGINAL: 0.0 (infinite)
FINAL:    120.0 default, 30.0 minimum enforced

BROWSER ANNOTATION TIMEOUT
---------------------------
ORIGINAL: infinite (engine waits forever for browser)
FINAL:    ANNOTATED_TIMEOUT_SECONDS (default 10.0), falls back to raw frame
"""
