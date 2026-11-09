# Premium Video Skill — v3.0
============================

**Senior-agent orchestration skill** that converts a voice script into a
premium short-form video using HyperFrames. Built for agents who need
consistent, high-quality motion design without a timeline editor.

---

## What makes this "premium" vs medium

| Medium video | Premium video (this skill) |
|--------------|---------------------------|
| Static text blocks | **Kinetic typography** — words pop/slide/scale in per-word |
| Flat colors | **Glassmorphism** — backdrop blur, gradients, drop shadows |
| Simple fade | **Motion-blur wipes** + Ken Burns camera moves |
| No audio sync | **SFX cues** (whoosh/pop/ding) + voiceover + music markers |
| Placeholder evidence | **Download commands** (yt-dlp) + citation cards |
| One safe zone | **Title-safe + action-safe** for 9:16 mobile cropping |

---

## Architecture (agent orchestration pipeline)

```
voice script
    │
    ▼
┌──────────────────┐
│ PremiumOrchestrator│ 1. Parse script (plain or [start-end] segments)
│                  │ 2. Detect topic → animation + evidence decision
│                  │ 3. Audio sync — SFX cues, voiceover, music markers
│                  │ 4. Decompose into premium scene types
│                  │ 5. Generate kinetic typography HTML
│                  │ 6. Assemble + validate vs design contract
└──────────────────┘
    │
    ▼
┌──────────────────┐  SVG diagrams + Ken Burns camera moves
│ Animations       │  Glassmorphism evidence cards
│                  │  Lower thirds + end screens
│                  │  Motion-blur transitions
└──────────────────┘
    │
    ▼
┌──────────────────┐  yt-dlp download commands
│ Media Sourcing   │  Per-platform search queries (YouTube/IG/forums/web)
│                  │  Rights/fair-use reminders
└──────────────────┘
    │
    ▼
   index.html  →  npx hyperframes preview  →  npx hyperframes render  →  MP4
```

---

## Input script formats

### Option A — plain text (auto-timed at ~145 wpm for premium readability)
```
Same resume everywhere? That's why you're rejected.
Tailor it per company.
Read the **job description**.
Match their **keywords**.
One resume does not fit every company. Customize and get shortlisted.
```

### Option B — timestamped segments (exact control)
```
[0-4s] Same resume everywhere? That's why you're rejected.
[4-10s] Tailor it per company.
[10-14s] Read the **job description**.
[14-20s] Match their **keywords**.
[20-31s] One resume does not fit every company. Customize and get shortlisted.
```

### Emphasis markup
Wrap words in `** **` → they render in brand maroon, weight 950, with a pop animation (visual anchor).

---

## Technical topics (auto premium animation + evidence)

When the script contains a recognized technical keyword, the orchestrator
automatically inserts:

| Component | Premium treatment |
|-----------|-------------------|
| **Animated SVG diagram** | Node-link flow with moving encrypted packet + Ken Burns camera move |
| **Glassmorphism evidence card** | Backdrop-blur card with claim + media placeholder + source badges |
| **Transition** | Motion-blur wipe before animation |
| **Audio cue** | "whoosh" SFX at animation start |

**Recognized topics:** tor, onion, anonymous browsing, dark web, vpn, proxy,
isp, relay, network, packet, encryption, cybersecurity, dns, cdn, blockchain,
bitcoin, ai, machine learning, how internet works, neural network,
large language model

---

## Media sourcing (evidence & B-roll)

For technical topics, search queries are generated per platform. The **agent**
executes searches and downloads using the provided `yt-dlp` commands.

```
build_search_queries("Tor") → {
  "youtube": ["Tor network how it works entry middle exit relay animation", ...],
  "instagram": ["Tor network explained infographic", ...],
  "forum": ["site:reddit.com/r/tor ...", ...],
  "website": ["https://www.torproject.org/about/ ...", ...],
  "image": ["Tor network diagram ...", ...],
}
```

**Download commands example:**
```bash
yt-dlp -f "bestvideo[height<=1080]+bestaudio/best" --merge-output-format mp4 \
  "ytsearch1:Tor network how it works entry middle exit relay animation" \
  -o "assets/media/%(title)s.%(ext)s"
```

**Platforms:** YouTube, Instagram, forums, websites, images.

**Rights:** All media must be rights-cleared or fair-use verified before publishing.

---

## Audio / voiceover

The skill generates audio cue markers but does **not** synthesize audio.
Provide your own files:

```bash
python3 generate.py --script my_script.txt \
  --voiceover assets/audio/voice.mp3 \
  --music assets/audio/music.mp3 \
  --output index.html
```

Then download audio with yt-dlp:
```bash
yt-dlp -x --audio-format mp3 --audio-quality 0 "ytsearch1:your voiceover query" \
  -o "assets/audio/%(title)s.%(ext)s"
```

---

## Design tokens (premium, measured from source + elevated)

| Role | Dark (hook/CTA) | Light (explainer) |
|------|-----------------|-------------------|
| Background | `#6C0013` maroon | `#EBE6F0` lavender |
| Text | `#FFF8F0` cream | `#0F0C14` near-black |
| Accent | `#FFD700` gold | — |
| Glass | `rgba(255,255,255,0.65)` | `rgba(108,0,19,0.7)` |

**Typography scale:** hook 80px/w950 → section 64px/w900 → body 44px/w750 → caption 26px/w600 → CTA 56px/w900

**Motion:** ease-premium (cubic-bezier 0.23,1,0.32,1) · pop-in 0.45s · slide 0.7s · Ken Burns 8s · stagger 0.12s

**Layout:** 1280×720 @ 30fps · title-safe + action-safe zones for 9:16 mobile

---

## Scene types

| Type | Style | When it appears |
|------|-------|-----------------|
| hook | kinetic pop, centered top | First line |
| section | scale reveal, centered | Chapter breaks |
| body_left | slide-in from left | Regular explainer |
| body_right | slide-in from right, brand color | Punch lines |
| emphasis | pop + scale, right anchor | **word** markup |
| animation | SVG + Ken Burns | Technical topics |
| evidence | glass card, citation | Technical topics |
| lower_third | slide-up glass, bottom left | Speaker tags |
| cta | scale reveal, bottom center | Last content line |
| end_screen | fade in, centered CTA | Video end |
| transition | motion-blur wipe | Before major sections |

---

## How an agent uses this skill

```bash
# 1. Clone the skill
git clone https://github.com/uttamongithb1/video-skill.git
cd video-skill

# 2. Scaffold HyperFrames (one-time)
npx hyperframes init my-video --skip-skills

# 3. Generate premium HTML from voice script
python3 generate.py --script my_script.txt --output index.html

# 4. For technical topics, force animation:
python3 generate.py --script tor_script.txt --topic Tor --output index.html

# 5. With voiceover + music:
python3 generate.py --script my_script.txt \
  --voiceover assets/audio/voice.mp3 \
  --music assets/audio/music.mp3 \
  --output index.html

# 6. Fill media URLs into data-var-src attributes
# 7. Run yt-dlp download commands for evidence assets
# 8. Preview & render
npx hyperframes preview
npx hyperframes render
```

**Agent workflow:**
1. Receive voice script + optional topic + optional audio files
2. Run `python3 generate.py`
3. Read printed search queries + download commands
4. (Optional) Source/download media, fill `data-var-src` URLs
5. Return `index.html` + preview/render commands to user

---

## Output validation report

```
✓ Premium build: 13 scene(s)
✓ Duration: 21.4s
✓ Animations: 1
✓ Evidence blocks: 1
✓ Transitions: 6
✓ Kinetic scenes: 5
✓ Audio cues: pop, whoosh, ding, ding
✓ Wrote index.html
⚠ Warnings: [...]
🔍 Search queries ready: ['youtube', 'instagram', 'forum', 'website', 'image']
⬇️  Media download commands (4): [...]
```

Warnings flag: sub-2s durations, long hook text, overflow risk, missing audio sync.

---

## Files

| File | Purpose |
|------|---------|
| `generate.py` | Premium CLI entry point |
| `orchestrator.py` | Pipeline: parse → detect → decompose → assemble → validate |
| `design_system.py` | Premium tokens, motion, typography, layout, validation |
| `animations.py` | Kinetic type, SVG diagrams, glass cards, transitions |
| `media_sourcing.py` | Search queries, yt-dlp commands, rights notes |
| `skill.md` | This documentation |
| `skill.json` | Machine-readable skill schema |
| `example_script.txt` | Simple resume-reject example |
| `example_technical.txt` | TOR technical example |
| `output_simple.html` | Sample premium simple output |
| `output_technical.html` | Sample premium TOR output |

---

## Requirements

- Python 3 (standard library only)
- HyperFrames CLI: `npx hyperframes init / preview / render`
- Node.js ≥ 22, FFmpeg (for rendering)
- yt-dlp (for media download commands, optional)

---

## License

MIT — build on it, share it, sell videos with it.

