# Premium Video Skill — v3.3 (Anchor Grid + Sound)
==================================================

A senior-agent orchestration skill that converts a voice script into a
premium HyperFrames short-form video with:

- **Anchor grid** (kicker → hero → body → chip → presenter, bottom-fixed)
- **Kinetic typography** (per-word staggered animation)
- **SVG animations** (technical diagrams with moving elements)
- **Glassmorphism evidence cards** + lower thirds + end screens
- **Motion-blur wipe transitions**
- **Complete sound system** (SFX synthesis, cue sheet, audio mixing)
- **Design-contract validation** (prepare.py gate)
- **Reproducible pipeline** (scenes.sh → prepare.py → build_index.py)

---

## Pipeline (order is not negotiable)

```
voice script
    │
    ▼
generate.py  →  new_scene.py  →  prepare.py  →  build_index.py
  (parse)      (scene files)   (validate)    (root HTML + wipes)
    │                                         │
    ▼                                         ▼
npx hyperframes lint  →  npx hyperframes render
  (0 errors gate)         (MP4 output)
    │
    ▼
python3 scripts/gen_sfx.py       # synthesize SFX (one-time)
python3 scripts/mix_audio.py     # VO + cues + bed → master.wav
ffmpeg mux → final.mp4
```

### Step-by-step

```bash
# 1. Generate scene compositions + root HTML from voice script
python3 generate.py --script my_script.txt --topic Tor --output index.html

# 2. Validation gate (contrast, type, safe zone, field rhythm)
python3 scripts/prepare.py

# 3. Lint (must be 0 errors)
npx hyperframes lint

# 4. Preview and render
npx hyperframes preview
npx hyperframes render

# 5. Audio pipeline
python3 scripts/gen_sfx.py              # synthesize 14 SFX from scratch
python3 scripts/mix_audio.py            # VO + cues + bed → master.wav
ffmpeg -i rendered.mp4 -i renders/master.wav \
  -c:v copy -c:a aac -shortest final.mp4
```

---

## Anchor Grid (bottom-fixed, invariant)

Every scene uses the same bottom half — only the top half re-composes:

| Anchor | Element | Position | Animation |
|--------|---------|----------|-----------|
| 1 | **Kicker** | Top left | Slide up from y:-26, fade in 0.32s |
| 2 | **Hero** | Top band (1–3 words) | Scale 1.3→1, drift 44px→0, slow drift up |
| 3 | **Body** | Card / odometer / lines | Slide up 56px→0, scale .95→1 |
| 4 | **Chip** | Bottom area (3–6 words) | Slide up 30px→0, fade in 0.26s |
| 5 | **Presenter** | Bottom right, cropped by frame | Scale .92→1, y:46→0, fade in 0.34s |

**Frame 0 is a poster** — scene 1 (`data-cover="1"`) opens fully composed.

---

## Six-Color Field Cycle

No two neighbor scenes share a background field:

`accent → ground → ink → secondary → tertiary → quaternary`

`prepare.py` fails the build if two scenes in a row share a field.

All text/background pairs meet WCAG ≥ 4.5:1 contrast.

---

## Sound System

### SFX Synthesis (no downloads, no licensing)
`python3 scripts/gen_sfx.py` creates 14 sound effects:

| SFX | Use |
|-----|-----|
| `pop.wav` | Every scene cut |
| `click.wav` / `key.wav` | UI elements, list ticking |
| `chime.wav` | Reveal / score |
| `ping.wav` | Notification |
| `notify.wav` | CTA |
| `riser.wav` | Big turns before cut |
| `impact.wav` | Strong visual hit |
| `whoosh.wav` | Fast movement |
| `error.wav` | Wrong / rejected |

### Cue Sheet — `assets/sfx/cues.json`
Section-relative offsets (survive VO re-records):

```json
{ "at": "scenes", "file": "pop.wav", "gain": 0.5 }
{ "at": "vo2-0.30", "file": "riser.wav", "gain": 0.3 }
{ "at": "vo9+0.55", "file": "notify.wav", "gain": 0.4 }
```

### Audio Mixing — `scripts/mix_audio.py`
- VO + SFX cues + music bed → `renders/master.wav`
- Measures loudness with `ebur128`, corrects to **−14 LUFS**
- True peak ≤ **−1 dBTP**
- `alimiter` with `level=false` (avoids auto-level trap)
- Bed at 0.15 volume → **−29 LUFS** (~13 LU under −16 LUFS VO)
- No sidechain ducking — the level gap is the duck

---

## Technical Topics (auto animation + evidence)

When the script contains a recognized keyword, the orchestrator inserts:

| Component | Treatment |
|-----------|-----------|
| **SVG diagram** | Node-link flow with moving element + animateMotion |
| **Evidence overlay** | Glassmorphism card with source badges |
| **Transition** | Motion-blur wipe before animation |
| **Audio cue** | "whoosh" SFX at animation start |

**Recognized:** tor, onion, vpn, proxy, isp, relay, network, packet,
encryption, cybersecurity, dns, cdn, blockchain, ai, machine learning,
and more.

---

## Input Script Formats

### Plain text (auto-timed ~145 wpm)
```
Same resume everywhere? That's why you're rejected.
Tailor it per company.
Read the **job description**.
One resume does not fit every company. Customize and get shortlisted.
```

### Timestamped segments
```
[0-4s] Same resume everywhere? That's why you're rejected.
[4-10s] Tailor it per company.
[10-14s] Read the **job description**.
```

**Emphasis:** `**word**` → right-aligned, brand color, weight 950, pop animation.

---

## Files

| File | Purpose |
|------|---------|
| `generate.py` | CLI entry point |
| `orchestrator.py` | Pipeline: parse → detect → decompose → generate scenes → build root |
| `design_system.py` | Design tokens, alignment rules, validation |
| `PARAMS.json` | The ONLY design file you edit |
| `scripts/prepare.py` | Validation gate + token injection |
| `scripts/new_scene.py` | Anchor-grid scene composition generator |
| `scripts/build_index.py` | Root HTML with contiguous timing + adaptive wipes |
| `scripts/gen_sfx.py` | SFX synthesis from scratch |
| `scripts/mix_audio.py` | VO + cues + bed → master.wav |
| `assets/sfx/cues.json` | Section-relative cue sheet |
| `scenes.sh` | Reproducible scene list template |
| `compositions/_scene-base.html.tmpl` | Anchor-grid skeleton |
| `compositions/wipe.html` | Motion-blur transition |
| `skill.md` · `skill.json` | Documentation + schema |

---

## Requirements

- Python 3 (standard library)
- HyperFrames CLI: `npx hyperframes init / preview / render / lint`
- Node.js ≥ 22, FFmpeg
- ffprobe (for audio measurement)

---

## License

MIT — build on it, share it, sell videos with it.

