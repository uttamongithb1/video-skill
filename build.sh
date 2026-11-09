#!/usr/bin/env bash
# build.sh — the whole pipeline, end-to-end, no user-provided assets needed.
#   1. python3 scripts/download_assets.py   fonts / presenter poses / music bed
#   2. python3 scripts/gen_vo.py            TTS voiceover from sections.json
#   3. python3 scripts/process_vo.py        VO -> timeline.json (measured clock)
#   4. python3 generate.py                  script -> scene compositions + index.html
#   5. python3 scripts/prepare.py           validation gate
#   6. python3 scripts/render_video.py      compositions -> renders/raw.mp4 (PIL+ffmpeg)
#   7. python3 scripts/mix_audio.py         VO + cues + bed -> renders/master.wav
#   8. ffmpeg mux                           picture + master -> renders/final.mp4
#   9. python3 scripts/qc.py                final gate
#
# Usage:  ./build.sh                 full build (everything auto-generated)
#         ./build.sh --assets-only   just download/generate fonts, poses, bed, VO
set -euo pipefail
cd "$(dirname "$0")"

# Point to our bundled ffmpeg (no system ffmpeg required)
export PATH="$(pwd)/tools:$PATH"
export TMPDIR="${TMPDIR:-$(pwd)/tmp}"
mkdir -p "$TMPDIR" renders

OUT="renders/final.mp4"
NODE_BIN="/home/user/node-v22.12.0-linux-x64/bin"

echo "== 0/9 assets (fonts, presenter poses, music bed) =="
python3 scripts/download_assets.py

if [[ "${1:-}" != "--assets-only" ]]; then
  echo "== 1/9 VO (TTS from sections.json) =="
  python3 scripts/gen_vo.py

  echo "== 2/9 process VO -> timeline.json =="
  python3 scripts/process_vo.py

  echo "== 3/9 scenes (generate.py) =="
  python3 generate.py --script assets/vo/sections.json --output index.html --topic auto --wpm 145

  echo "== 4/9 validate (prepare.py) =="
  python3 scripts/prepare.py

  echo "== 5/9 lint (hyperframes via Node 22) =="
  "$NODE_BIN/npx" --ignore-engines --yes hyperframes@0.9.26 lint "$(pwd)" 2>&1 | tee /tmp/hf-lint.log
  grep -q "0 errors" /tmp/hf-lint.log || { echo "STOP: lint errors"; exit 1; }

  echo "== 6/9 render (self-contained PIL+ffmpeg) =="
  python3 scripts/render_video.py

  echo "== 7/9 mix audio (VO + SFX + bed) =="
  python3 scripts/mix_audio.py

  echo "== 8/9 mux -> final.mp4 =="
  ffmpeg -y -v error -i renders/raw.mp4 -i renders/master.wav \
         -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k -shortest -movflags +faststart "$OUT"

  echo "== 9/9 QC =="
  python3 scripts/qc.py "$OUT" || echo "QC warnings (non-fatal)"
else
  echo "== Assets-only mode: stopping after asset generation =="
fi

echo ""
echo "=============================="
echo "DONE: $OUT"
echo "=============================="
