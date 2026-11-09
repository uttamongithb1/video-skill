# Resume-Reject / Technical Explainer Video Skill
=================================================

**Senior-agent orchestration skill for HyperFrames.** Converts a voice script into a
high-quality short-form video with:

- Maroon/lavender high-contrast styling (reverse-engineered from the viral
  "resume reject" source video)
- Bold sans-serif typography with center-title / left-body / right-emphasis
- **Automatic animation + evidence insertion** for technical topics (TOR, VPN,
  cybersecurity, networking, AI, etc.)
- Media sourcing queries for YouTube / Instagram / forums / websites
- Consistency validation on every build

---

## Architecture (agent orchestration pipeline)

```
voice script
    │
    ▼
┌─────────────────┐
│  Orchestrator   │  1. Parse script (plain or [start-end] segments)
│                 │  2. Detect topic → animation/evidence decision
│                 │  3. Decompose into typed scenes
│                 │  4. Insert transitions
│                 │  5. Assemble HyperFrames HTML
└─────────────────┘
    │
    ▼
┌─────────────────┐  6. Validate scenes vs design contract
│  Design System  │     (colors, typography, alignment, duration)
└─────────────────┘
    │
    ▼
┌─────────────────┐  SVG/CSS animated diagrams (TOR flow, packet hops)
│  Animations     │  Transitions (fade/slide/wipe)
└─────────────────┘
    │
    ▼
┌─────────────────┐  Evidence cards + media search queries
│  Media Sourcing │  YouTube / Instagram / forums / websites
└─────────────────┘
    │
    ▼
   index.html  →  npx hyperframes preview  →  npx hyperframes render  →  MP4
```

---

## Input script formats

### Option A — plain text (auto-timed at ~150 wpm)
Each non-empty line becomes one scene.

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
Wrap words in `** **` → right-aligned, brand maroon, weight 900 (visual anchor).

---

## Technical topics (auto animation + evidence)

When the script contains a recognized technical keyword, the orchestrator
automatically inserts:

| Component | What it does |
|-----------|--------------|
| **Animated SVG diagram** | Node-link flow with a moving packet (e.g. TOR: User → ISP → Entry → Middle → Exit) |
| **Evidence overlay** | Citation card with source placeholders (YouTube, Website, etc.) |
| **Transition** | Fade/slide wipe before the animation |

**Recognized topics:** tor, onion, anonymous browsing, dark web, vpn, proxy,
isp, relay, network, packet, encryption, cybersecurity, dns, cdn, blockchain,
bitcoin, ai, machine learning, how internet works

### Example: TOR technical script
```
Ever wondered how Tor keeps you anonymous online?
When you search for a website, your request does not go directly.
It bounces through multiple relays — entry, middle, and exit.
Each relay only knows the previous and next hop.
Tor Project documentation shows this onion routing architecture.
Stay private. Stay secure.
```

This produces:
- Scene 0: Hook (dark maroon, centered title)
- Scene 1: TOR animated diagram (SVG packet flow) + evidence overlay
- Scenes 2-N: Body explainer lines
- Final: CTA (dark maroon, centered)

---

## Media sourcing (evidence & B-roll)

For technical topics, the orchestrator generates search queries per platform.
The **agent** runs these searches and fills real URLs into the
`data-var-src` attributes in the evidence cards.

```
build_search_queries("Tor") → {
  "youtube": ["Tor network how it works entry middle exit relay animation", ...],
  "instagram": ["Tor network explained infographic", ...],
  "forum": ["site:reddit.com/r/tor how Tor entry middle exit relay works", ...],
  "website": ["https://www.torproject.org/about/ Tor overview", ...],
  "image": ["Tor network diagram entry middle exit relay", ...],
}
```

**Platforms covered:** YouTube, Instagram, forums (Reddit, etc.), websites,
images.

---

## Design tokens (measured from source video)

| Role | Dark (hook/CTA) | Light (explainer) |
|------|-----------------|-------------------|
| Background | `#6C0013` maroon | `#DAD1DD` lavender |
| Text | `#E8DBD1` cream | `#141216` near-black |
| Accent | — | `#6C0013` maroon |
| Highlight | `#FFD700` gold (packet) | — |

**Typography scale:** title 68px/w900 → section 56px/w800 → body 40px/w700 → caption 24px/w500 → CTA 50px/w800

**Alignment rules:** title centered (top band) · body left (reading flow) · emphasis right (anchor) · CTA centered (bottom)

---

## How an agent uses this skill

```bash
# 1. Scaffold HyperFrames project (one-time)
npx hyperframes init my-video --skip-skills

# 2. Generate index.html from voice script
python3 generate.py --script my_script.txt --output index.html

# 3. For technical topics, force animation:
python3 generate.py --script tor_script.txt --topic Tor --output index.html

# 4. Fill media URLs into data-var-src attributes (evidence cards)

# 5. Preview & render
npx hyperframes preview
npx hyperframes render
```

**Agent workflow:**
1. Receive voice script + optional topic
2. Run `python3 generate.py --script <script> [--topic <topic>]`
3. Read the search queries printed in output
4. (Optional) Search the internet, fill `data-var-src` URLs in evidence cards
5. Return `index.html` + preview/render commands to the user

---

## Output validation

Every build prints a report:
```
✓ Parsed 8 scene(s)
✓ Total duration: 20.8s
✓ Animations: 1
✓ Evidence blocks: 1
✓ Transitions: 2
✓ Wrote index.html
⚠ Warnings: [...]
🔍 Media search queries ready for: ['youtube', 'instagram', 'forum', 'website', 'image']
```

Warnings flag: unknown scene types, very short/long durations, overflowing text.

---

## Files

| File | Purpose |
|------|---------|
| `generate.py` | CLI entry point — orchestrator wrapper |
| `orchestrator.py` | Pipeline: parse → detect → decompose → assemble → validate |
| `design_system.py` | Tokens, alignment rules, consistency validation |
| `animations.py` | SVG/CSS animated diagrams + transitions |
| `media_sourcing.py` | Evidence cards + per-platform search queries |
| `skill.md` | This documentation |
| `skill.json` | Machine-readable skill schema |
| `example_script.txt` | Simple resume-reject example |
| `example_technical.txt` | TOR technical example |
| `output_simple.html` | Sample output (simple) |
| `output_technical.html` | Sample output (TOR) |

---

## Requirements

- Python 3 (standard library only)
- HyperFrames CLI: `npx hyperframes init / preview / render`
- Node.js ≥ 22, FFmpeg (for rendering)

---

## License

MIT — build on it, share it, sell videos with it.

