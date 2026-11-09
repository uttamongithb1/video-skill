#!/usr/bin/env python3
"""
new_scene.py — make compositions/sN-<name>.html from the anchor-grid template.

Every scene uses the invariant bottom half:
  kicker → hero → body → chip → presenter

Archetypes:
  card-led   hero + card body (proof beats)
  stat-led   hero + odometer + support line (number beats)
  type-led   hero + 2 lines, no card (statement/CTA)
"""
import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASE = ROOT / "compositions/_scene-base.html.tmpl"

ap = argparse.ArgumentParser()
ap.add_argument("--n", type=int, required=True)
ap.add_argument("--name", required=True)
ap.add_argument("--arch", choices=["card-led", "stat-led", "type-led"], default="card-led")
ap.add_argument("--field", choices=["ground", "accent", "ink", "secondary",
                        "tertiary", "quaternary"], default="ground")
ap.add_argument("--pose", default=None)
ap.add_argument("--kicker", default="")
ap.add_argument("--hero", default="")
ap.add_argument("--chip", default="")
ap.add_argument("--card-title", default="")
ap.add_argument("--card-meta", default="")
ap.add_argument("--card-body", default="",
                help="inline HTML, or @path/to/file.html")
ap.add_argument("--digits", default="",
                help="stat-led: number the odometer lands on, e.g. 94")
ap.add_argument("--support", default="")
ap.add_argument("--line1", default="")
ap.add_argument("--line2", default="")
ap.add_argument("--no-cover", action="store_true")
ap.add_argument("--force", action="store_true")
a = ap.parse_args()

P = json.loads((ROOT / "PARAMS.json").read_text())
W, H = P["format"]["w"], P["format"]["h"]
KEY = {"card-led": "A", "stat-led": "B", "type-led": "C"}[a.arch]
sid = f"s{a.n}"

out = ROOT / f"compositions/{sid}-{a.name}.html"
if out.exists() and not a.force:
    raise SystemExit(f"FAIL  {out.name} exists — pass --force to overwrite")

s = BASE.read_text()

# delete unchosen archetypes, unwrap chosen
for k in "ABC":
    if k == KEY:
        continue
    for fam in ("arch", "css", "js"):
        s = re.sub(rf"<!-- #{fam}:{k} -->.*?<!-- /#{fam}:{k} -->\n?", "", s, flags=re.S)
for fam in ("arch", "css", "js"):
    s = s.replace(f"<!-- #{fam}:{KEY} -->\n", "").replace(f"<!-- /#{fam}:{KEY} -->\n", "")

# ids + timeline key
s = s.replace("sX", sid)
s = s.replace(f'data-composition-id="{sid}"',
              f'data-composition-id="{sid}-{a.name}"')
s = s.replace(f'__timelines["{sid}"]',
              f'__timelines["{sid}-{a.name}"]')

# format + field
s = s.replace('data-width="1080" data-height="1920"',
              f'data-width="{W}" data-height="{H}"')
s = s.replace('data-field="ground"', f'data-field="{a.field}"')
if a.n == 1 and not a.no_cover:
    s = s.replace('data-cover="0"', 'data-cover="1"')

# odometer digits
strip = "<span class=\"strip\">" + "".join(f"<span>{d}</span>" for d in range(10)) + "</span>"
if a.digits:
    cols = "\n".join(f'      <div class="col" data-digit="{d}">{strip}</div>'
                     for d in a.digits)
    s = re.sub(r'(<div id="' + sid + r'-odo">)(.*?)(\n    </div>)',
               lambda m: m.group(1) + "\n" + cols + m.group(3), s, flags=re.S)
else:
    s = s.replace("{{STRIP}}", strip)

# word slots
def put(marker, text):
    global s
    if text:
        s = s.replace(f"SLOT:{marker}", text)

body = a.card_body
if body.startswith("@"):
    path = Path(body[1:]) if Path(body[1:]).is_absolute() else ROOT / body[1:]
    raw = path.read_text()
    body = raw if path.suffix == ".html" else "".join(
        f'<div class="row"><span class="ln">{i+1:02d}</span><span>{line}</span></div>'
        for i, line in enumerate(l.strip() for l in raw.splitlines() if l.strip()))
put("KICKER", a.kicker)
put("HERO", a.hero)
put("CHIP", a.chip)
put("CARD_TITLE", a.card_title)
put("CARD_META", a.card_meta)
put("CARD_BODY", body)
put("SUPPORT", a.support)
put("LINE1", a.line1)
put("LINE2", a.line2 or " ")

# pose
pose = a.pose or P["presenter"]["poses"][min(a.n - 1,
             len(P["presenter"]["poses"]) - 1)]
if not pose.startswith("assets/"):
    pose = f"../assets/presenter/cut/{pose}"
s = s.replace("SLOT:POSE", pose)

left = re.findall(r"SLOT:[A-Z_0-9]+", s)
if left:
    print(f"WARN  still unfilled: {', '.join(sorted(set(left)))}")

out.write_text(s)
print(f"{out.relative_to(ROOT)}  ·  {a.arch}  ·  field {a.field}  ·  pose {Path(pose).name}")
