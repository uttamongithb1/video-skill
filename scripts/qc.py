#!/usr/bin/env python3
"""
qc.py — one command that answers "is this deliverable acceptable?" with PASS/FAIL.

Runs, in order:
  1. prepare.py --check-only        quality floor: contrast, type, safe zone,
                                    collision, field rhythm
  2. hyperframes lint               0 errors is a gate; warnings must be accepted
  3. hyperframes snapshot           9 frames including frame 0
  4. ffprobe                        resolution, fps, frame count vs duration
  5. ebur128                        integrated loudness and true peak of final mp4
  6. silence probe                  any 1s window below -45 dB is a dead hole

Usage: python3 scripts/qc.py [renders/final.mp4]
Exit code 0 only if every gate passes.
"""
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
P = json.loads((ROOT / "PARAMS.json").read_text())
TL = json.loads((ROOT / "assets" / "vo" / "timeline.json").read_text())
VID = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "renders" / "final.mp4"
if not VID.is_absolute():
    VID = ROOT / VID
AF = P["audio"]

rows = []


def add(name, ok, detail=""):
    rows.append((ok, name, detail))


def sh(cmd, shell=False):
    return subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT,
                          shell=shell)


# 1. Quality floor (prepare.py) -------------------------------------------------------------------
r = sh([sys.executable, "scripts/prepare.py", "--check-only"])
add("quality floor (prepare.py)", r.returncode == 0,
    (r.stdout.strip().splitlines() or ["no output"])[-1])

# 2. Lint -----------------------------------------------------------------------------------------
r = sh("npx --yes hyperframes@0.9.19 lint")
m = re.search(r"(\d+) errors?, (\d+) warnings?", r.stdout + r.stderr)
errs, warns = (int(m.group(1)), int(m.group(2))) if m else (-1, -1)
add("lint: 0 errors", errs == 0, f"{errs} errors / {warns} warnings")

# 3. Snapshots ------------------------------------------------------------------------------------
times = ["0", "1.5", "4", "8", "13", "18", "23",
         str(max(0.0, TL["root_duration"] - 0.6))]
r = sh(f"npx --yes hyperframes@0.9.19 snapshot --at \"{','.join(times)}\"")
sheet = re.search(r"(/\S+contact-sheet[^\s]*)", r.stdout)
add("snapshots rendered", bool(sheet),
    sheet.group(1) if sheet else "no contact sheet")

# 4. Container (ffprobe) --------------------------------------------------------------------------
if VID.exists():
    pr = sh(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
             "stream=width,height,r_frame_rate,nb_frames", "-show_entries",
             "format=duration", "-of", "json", str(VID)]).stdout
    j = json.loads(pr)
    st = j["streams"][0]
    w, h, fps, frames = st["width"], st["height"], st["r_frame_rate"], \
        int(st["nb_frames"])
    dur = float(j["format"]["duration"])
    add("resolution", (w, h) == (P["format"]["w"], P["format"]["h"]),
        f"{w}x{h}")
    add("fps", fps == f"{P['format']['fps']}/1", fps)
    drift = abs(frames / P["format"]["fps"] - dur)
    add("frames match duration", drift < 0.1,
        f"{frames} frames / {dur:.3f}s (drift {drift:.3f})")

    # 5. Loudness + peak
    e = sh(["ffmpeg", "-nostats", "-i", str(VID), "-af", "ebur128=peak=true",
            "-f", "null", "-"]).stderr
    tail = e[e.rindex("Summary:"):]
    I = float(re.search(r"I:\s+(-?[\d.]+) LUFS", tail).group(1))
    TP = float(re.search(r"Peak:\s+(-?[\d.]+) dBFS", tail).group(1))
    add("integrated loudness", abs(I - AF["masterLufs"]) <= 0.5,
        f"{I} LUFS (target {AF['masterLufs']})")
    add("true peak", TP <= AF["truePeakMax"] + 0.01,
        f"{TP} dBTP (max {AF['truePeakMax']})")

    # 6. Silence holes
    holes = []
    t = 0.4
    while t < dur - 1.2:
        v = sh(["ffmpeg", "-hide_banner", "-ss", f"{t}", "-t", "1", "-i", str(VID),
                "-map", "0:a", "-af", "volumedetect", "-f", "null", "-"]).stderr
        mm = re.search(r"mean_volume:\s*(-?[\d.]+) dB", v)
        if mm and float(mm.group(1)) < -45:
            holes.append(round(t, 1))
        t += 1.0
    add("no silent holes", not holes,
        "clean" if not holes else f"{len(holes)} holes at {holes[:6]}")
else:
    add("video exists", False, f"{VID.name} not found — render before QC")

# Report ------------------------------------------------------------------------------------------
print("\n" + "=" * 74)
for ok, name, detail in rows:
    print(f" {'PASS' if ok else 'FAIL'}  {name:<28} {detail}")
print("=" * 74)
bad = [r for r in rows if not r[0]]
print(f"{len(rows) - len(bad)}/{len(rows)} gates passed\n")
sys.exit(1 if bad else 0)
