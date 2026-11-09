#!/usr/bin/env python3
"""
build_index.py — writes index.html (root document) from compositions on disk.

WHY: hand-writing the root is where sessions broke — duplicate
data-composition-id makes HyperFrames refuse to render, mounts drift out of
sync with the VO, missing wipes leave black frames. The root is mechanical:
generate it, never type it.

WHAT IT DOES:
  1. finds compositions/s*.html (sorted numerically: s1, s2, ... s10)
  2. reads durations from assets/vo/timeline.json when it exists
     otherwise splits total evenly (preview only)
  3. fires a wipe 0.36s before each cut, colour = arriving scene's field
  4. makes spans contiguous (no black holes at VO gaps)
  5. writes index.html with root mount, scene mounts, wipe mounts
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WIPE_LEAD = 0.36
WIPE_DUR = 0.62
TAIL = 1.15


def die(msg):
    print(f"FAIL  {msg}")
    sys.exit(1)


def nat_key(p):
    m = re.match(r"s(\d+)", p.name)
    return (int(m.group(1)) if m else 999, p.name)


scenes = sorted((f for f in (ROOT / "compositions").glob("s*.html")),
                key=nat_key)
if not scenes:
    die("no compositions/s*.html found")

# --- durations ----------------------------------------------------------
tl_path = ROOT / "assets/vo/timeline.json"
argv = sys.argv[1:]
if "--even" in argv:
    total = float(argv[argv.index("--even") + 1])
    d = total / len(scenes)
    spans = [(i * d, (i + 1) * d) for i in range(len(scenes))]
    source = f"--even {total}s (preview timing)"
elif tl_path.exists():
    tl = json.loads(tl_path.read_text())
    secs = tl["sections"]
    if len(secs) < len(scenes):
        # Extra scenes (e.g. end_screen) share the remaining time after last section
        last_section_end = secs[-1]["end"]
        remaining = tl["root_duration"] - last_section_end
        extra_count = len(scenes) - len(secs)
        extra_dur = remaining / extra_count if extra_count > 0 else 0
        for i in range(extra_count):
            secs.append({
                "id": f"vo{len(secs) + i + 1}",
                "label": "extra",
                "start": round(last_section_end + i * extra_dur, 3),
                "dur": round(extra_dur, 3),
                "end": round(last_section_end + (i + 1) * extra_dur, 3),
                "file": "",
            })
    elif len(secs) > len(scenes):
        die(f"{len(scenes)} scenes on disk but {len(secs)} sections in "
            f"timeline.json. Each scene must own exactly one VO section.")
    spans = [(s["start"], s["end"]) for s in secs]
    source = f"assets/vo/timeline.json ({len(secs)} sections)"
else:
    die("no assets/vo/timeline.json — record the VO first, or pass "
        "--even <seconds> to preview")

# make spans contiguous: 0 -> cut -> cut -> ... -> root
root_dur = round(spans[-1][1] + TAIL, 3)
fixed_spans = []
for i in range(len(spans)):
    a = spans[i][0]
    b = spans[i + 1][0] if i + 1 < len(spans) else root_dur
    fixed_spans.append((a, round(b, 3)))
spans = fixed_spans

if tl_path.exists() and "--even" not in argv:
    root_dur = json.loads(tl_path.read_text()).get("root_duration", root_dur)

# --- fields (wipe colour = arriving scene's field) ----------------------
P = json.loads((ROOT / "PARAMS.json").read_text())
acc = P["palette"]

fields = []
for f in scenes:
    m = re.search(r'data-field="([a-z]+)"', f.read_text())
    fields.append(m.group(1) if m else "ink")


def colour(field):
    v = acc.get(field, acc["ink"])
    return acc[v] if v in acc else v


# --- emit index.html ----------------------------------------------------
fmt = P["format"]
lines = []
lines.append('<!doctype html>')
lines.append('<html lang="en">')
lines.append('<head>')
lines.append('  <meta charset="UTF-8" />')
lines.append(f'  <meta name="viewport" content="width={fmt["w"]}, '
             f'height={fmt["h"]}" />')
lines.append('  <script src="https://cdn.jsdelivr.net/npm/gsap@3.15.0/'
             'dist/gsap.min.js"></script>')
lines.append('  <style>')
lines.append('    * { margin: 0; padding: 0; box-sizing: border-box; }')
lines.append('    html, body { overflow: hidden; background: #000; }')
lines.append('    #root { position: relative; overflow: hidden; }')
lines.append('    .host { position: absolute; inset: 0; }')
lines.append('  </style>')
lines.append('</head>')
lines.append('<body>')
lines.append(f'  <div id="root" data-composition-id="main" '
             f'data-start="0" data-duration="{root_dur}" '
             f'data-width="{fmt["w"]}" data-height="{fmt["h"]}">')
lines.append('')

for i, (f, (a, b)) in enumerate(zip(scenes, spans), start=1):
    dur = round(b - a, 3)
    lines.append(f'    <!-- scene {i} · {f.name} · field {fields[i-1]} '
                 f'· {a:.3f}s → {b:.3f}s -->')
    lines.append(f'    <div id="host{i}" class="host" style="z-index:{i}"')
    lines.append(f'         data-composition-id="{f.stem}"')
    lines.append(f'         data-composition-src="compositions/{f.name}"')
    lines.append(f'         data-start="{a:.3f}" data-duration="{dur}"')
    lines.append(f'         data-width="{fmt["w"]}" data-height="{fmt["h"]}"')
    lines.append(f'         data-track-kind="graphics"></div>')
    lines.append('')

lines.append('    <!-- wipes: one before every cut, colour = arriving field -->')
for i in range(1, len(scenes)):
    scene_dur = spans[i][1] - spans[i][0]
    dur = round(min(WIPE_DUR, max(0.34, scene_dur * 0.42)), 2)
    lead = round(min(WIPE_LEAD, dur * 0.6), 3)
    start = round(max(0.0, spans[i][0] - lead), 3)
    flip = 1 if i % 2 == 0 else 0
    lines.append(f'    <div id="wipe{i}" class="host" style="z-index:'
                 f'{100 + i}"')
    lines.append(f'         data-composition-id="wipe{i}"')
    lines.append(f'         data-composition-src="compositions/wipe.html"')
    lines.append(f'         data-variable-values=\'{{"wipe-color":'
                 f'"{colour(fields[i])}","flip":"{flip}"}}\'')
    lines.append(f'         data-start="{start}" data-duration="{dur}"')
    lines.append(f'         data-width="{fmt["w"]}" data-height="{fmt["h"]}"')
    lines.append(f'         data-track-kind="graphics"></div>')
    lines.append('')

lines.append('  </div>')
lines.append('  <script>window.__timelines["main"] = '
             'gsap.timeline({ paused: true });</script>')
lines.append('</body>')
lines.append('</html>')

out = "\n".join(lines) + "\n"
if "--dry-run" in argv:
    print(out)
else:
    (ROOT / "index.html").write_text(out)
    print(f"index.html written — {len(scenes)} scene(s) + "
          f"{max(0, len(scenes) - 1)} wipe(s), root {root_dur}s")
    print(f"timing source: {source}")
