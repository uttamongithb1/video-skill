#!/usr/bin/env python3
"""
process_vo.py — Voice-over pipeline: trim → tempo → loudnorm → 48k stereo,
then write assets/vo/timeline.json (the clock the picture is cut to).

The VO is the clock: nothing downstream is allowed to know a duration that
is not in this file.

Usage: python3 scripts/process_vo.py
"""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VO = ROOT / "assets" / "vo"
OUT = VO / "wav"
OUT.mkdir(parents=True, exist_ok=True)

SPEC_PATH = VO / "sections.json"
if not SPEC_PATH.exists():
    print(f"ERROR: {SPEC_PATH} not found — write your script sections first")
    sys.exit(1)

SPEC = json.loads(SPEC_PATH.read_text())
SECTIONS = SPEC["sections"]
SCRIPT_TARGET = SPEC.get("script_target")  # seconds, or None → measure from VO
LEAD_IN = 0.30
TAIL = 1.15
GAP = 0.30
MAX_SPEEDUP = 1.40


def run(cmd):
    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode != 0:
        sys.exit(f"FAILED: {' '.join(cmd)}\n{p.stderr[-2000:]}")
    return p


def dur(path):
    p = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "csv=p=0", str(path)],
        capture_output=True, text=True,
    )
    return float(p.stdout.strip())


# ---- Pass 1: trim silence ------------------------------------------------
trimmed = {}
for s in SECTIONS:
    name = s["id"]
    src = VO / f"{name}.mp3"
    if not src.exists():
        # Also try .wav
        src = VO / f"{name}.wav"
    if not src.exists():
        sys.exit(f"ERROR: VO file not found: {name} (tried .mp3 and .wav)")
    dst = OUT / f"{name}_trim.wav"
    run(["ffmpeg", "-y", "-v", "error", "-i", str(src), "-af",
         "silenceremove=start_periods=1:start_silence=0.02:start_threshold=-42dB:"
         "detection=peak,areverse,"
         "silenceremove=start_periods=1:start_silence=0.02:start_threshold=-42dB:"
         "detection=peak,areverse",
         "-ar", "48000", "-ac", "2", str(dst)])
    trimmed[name] = dur(dst)

raw_sum = sum(trimmed.values())
gaps = GAP * (len(SECTIONS) - 1)

if SCRIPT_TARGET:
    budget = SCRIPT_TARGET - gaps - LEAD_IN - TAIL
    factor = raw_sum / budget
    print(f"trimmed total {raw_sum:.3f}s | target {SCRIPT_TARGET}s | "
          f"budget {budget:.3f}s | factor {factor:.4f}")
    assert factor <= MAX_SPEEDUP, (
        f"speed-up {factor:.2f}x exceeds {MAX_SPEEDUP}x — cut words instead")
    factor = min(round(factor, 4), MAX_SPEEDUP)
else:
    budget = raw_sum
    factor = 1.0  # measured, not compressed
    print(f"trimmed total {raw_sum:.3f}s | no script_target → measured from VO")

# ---- Pass 2: tempo + loudnorm -------------------------------------------
timeline = []
t = LEAD_IN
for s in SECTIONS:
    name = s["id"]
    dst = OUT / f"{name}.wav"
    run(["ffmpeg", "-y", "-v", "error", "-i", str(OUT / f"{name}_trim.wav"), "-af",
         f"atempo={factor},loudnorm=I=-16:TP=-1.5:LRA=7",
         "-ar", "48000", "-ac", "2", str(dst)])
    d = dur(dst)
    timeline.append({
        "id": name,
        "label": s.get("label", name),
        "script_start": s.get("script_start"),
        "script_end": s.get("script_end"),
        "start": round(t, 3),
        "dur": round(d, 3),
        "end": round(t + d, 3),
        "file": f"assets/vo/wav/{name}.wav",
    })
    t = round(t + d + GAP, 3)

root_dur = round(timeline[-1]["end"] + TAIL, 3)
data = {
    "tempo_factor": factor,
    "lead_in": LEAD_IN,
    "tail": TAIL,
    "gap": GAP,
    "script_target": SCRIPT_TARGET,
    "root_duration": root_dur,
    "sections": timeline,
}
(ROOT / "assets" / "vo" / "timeline.json").write_text(json.dumps(data, indent=2))
print(json.dumps(data["sections"], indent=1))
print(f"\nROOT DURATION -> {root_dur}s"
      + (f" (script declares {SCRIPT_TARGET}s)" if SCRIPT_TARGET
         else " (measured from VO)"))
