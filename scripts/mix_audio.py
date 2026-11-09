#!/usr/bin/env python3
"""
mix_audio.py — VO + music bed + cue sheet → one mastered track.

Everything is placed at absolute times derived from assets/vo/timeline.json,
so the mix cannot drift from the picture: the same file that cuts the scenes
also places the audio. The cue sheet (assets/sfx/cues.json) uses
section-relative offsets so a re-record does not invalidate the design.

Two traps this file exists to avoid:
  * alimiter has level=true by default — it AUTO-LEVELS back up to the ceiling,
    so a "limiter" quietly becomes a compressor + make-up gain and the mix
    lands at -12.5 LUFS instead of -14. Use level=false.
  * loudnorm in linear mode overshoots in a single pass. Measure the integrated
    loudness, move by exactly the difference, then limit. Verifiable arithmetic
    beats a filter that guesses.

Output: renders/master.wav  (target -14 LUFS integrated, true peak <= -1 dBTP)
"""
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SFX = ROOT / "assets/sfx"
TL = json.loads((ROOT / "assets/vo/timeline.json").read_text())
CUES = json.loads((ROOT / "assets/sfx/cues.json").read_text())
P = json.loads((ROOT / "PARAMS.json").read_text())
ROOT_DUR = TL["root_duration"]
START = {s["id"]: s["start"] for s in TL["sections"]}
ORDER = [s["id"] for s in TL["sections"]]
TARGET = P["audio"]["masterLufs"]


def run(cmd):
    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode != 0:
        sys.exit("FAILED: " + " ".join(map(str, cmd)) + "\n" + p.stderr[-3000:])


def resolve(at):
    """'scenes' | 'vo2' | 'vo2+1.10' | 'vo2-0.30' | 12.5 -> absolute seconds"""
    if at == "scenes":
        return [START[i] - 0.02 for i in ORDER]
    if isinstance(at, (int, float)):
        return [float(at)]
    m = re.fullmatch(r"(vo\d+)\s*([+-])\s*([\d.]+)", at)
    if m:
        base = START[m.group(1)]
        off = float(m.group(3)) * (1 if m.group(2) == "+" else -1)
        return [max(0.0, base + off)]
    if at in START:
        return [START[at]]
    raise SystemExit(f"cue sheet: cannot resolve 'at': {at}")


# ---- expand the sheet -------------------------------------------------------------------------
cues = []
for c in CUES["cues"]:
    for t in resolve(c["at"]):
        cues.append((round(t, 3), c["file"], c.get("gain", 1.0)))
cues.sort()

# density guard: one cue per second
dense = [(a, b) for a, b in zip(cues, cues[1:]) if b[0] - a[0] < 0.05]
if dense:
    print(f"WARN  {len(dense)} cue pair(s) closer than 50 ms — check the sheet")
if len(cues) > ROOT_DUR * P["audio"]["maxCuesPerSecond"] + 2:
    print(f"WARN  {len(cues)} cues in {ROOT_DUR:.1f}s — denser than "
          f"{P['audio']['maxCuesPerSecond']}/s")


def build(label, entries, out):
    args, parts = [], []
    for i, (t, path, gain) in enumerate(entries):
        args += ["-i", str(path)]
        parts.append(f"[{i}:a]volume={gain},adelay={int(t*1000)}|{int(t*1000)}[a{i}]")
    mix = "".join(f"[a{i}]" for i in range(len(entries)))
    graph = ";".join(parts) + f";{mix}amix=inputs={len(entries)}:normalize=0:dropout_transition=0[out]"
    run(["ffmpeg", "-y", "-v", "error", *args, "-filter_complex", graph, "-map", "[out]",
         "-t", str(ROOT_DUR + 1), "-ar", "48000", "-ac", "2", str(out)])
    print(f"{label}: {len(entries)} elements -> {out.name}")


# 1. VO, each section at its measured start
build("VO", [(s["start"], ROOT / s["file"], 1.0) for s in TL["sections"]],
    ROOT / "assets/vo/vo_track.wav")

# 2. cue bus
build("CUE", [(t, SFX / f, g) for t, f, g in cues], SFX / "sfx_track.wav")

# 3. bed, trimmed to the picture with fades
bed = CUES["bed"]
run(["ffmpeg", "-y", "-v", "error", "-stream_loop", "-1", "-i", str(ROOT / bed["file"]),
     "-t", str(ROOT_DUR + 0.5), "-af",
     f"volume={bed['volume']},afade=t=in:st=0:d={bed['fadeIn']},"
     f"afade=t=out:st={ROOT_DUR - bed['fadeOut']:.2f}:d={bed['fadeOut']}",
     "-ar", "48000", "-ac", "2", str(ROOT / "assets/music/bed_track.wav")])
print("BED: looped to the picture")

# 4. sum
run(["ffmpeg", "-y", "-v", "error",
     "-i", str(ROOT / "assets/vo/vo_track.wav"),
     "-i", str(SFX / "sfx_track.wav"),
     "-i", str(ROOT / "assets/music/bed_track.wav"),
     "-filter_complex",
     f"[0:a]volume=1.0[vo];[1:a]volume={P['audio']['cueBus']}[sfx];[2:a]volume=1.0[bed];"
     "[vo][sfx][bed]amix=inputs=3:normalize=0:dropout_transition=0,"
     f"atrim=0:{ROOT_DUR + 0.3},asetpts=N/SR/TB[out]",
     "-map", "[out]", "-ar", "48000", "-ac", "2", str(ROOT / "renders/master_mix.wav")])
print(f"MIX -> renders/master_mix.wav ({ROOT_DUR + 0.3:.2f}s)")

# 5. measure, move by exactly the difference, limit without auto-level
m = subprocess.run(["ffmpeg", "-nostats", "-i", str(ROOT / "renders/master_mix.wav"),
                    "-af", "ebur128=peak=true", "-f", "null", "-"], capture_output=True, text=True)
tail = m.stderr[m.stderr.rindex("Summary:"):]
I = float(re.search(r"I:\s+(-?[\d.]+) LUFS", tail).group(1))
TP = float(re.search(r"Peak:\s+(-?[\d.]+) dBFS", tail).group(1))
gain = round(TARGET - I, 2)
run(["ffmpeg", "-y", "-v", "error", "-i", str(ROOT / "renders/master_mix.wav"), "-af",
     f"volume={gain}dB,alimiter=limit=0.85:level=false,atrim=0:{ROOT_DUR + 0.3},asetpts=N/SR/TB",
     "-ar", "48000", "-ac", "2", str(ROOT / "renders/master.wav")])
print(f"MASTER -> renders/master.wav (measured I {I} LUFS / TP {TP} dBFS, gain {gain:+} dB -> target {TARGET})")
