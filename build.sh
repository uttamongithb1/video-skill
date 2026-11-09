#!/usr/bin/env bash
# build.sh — the whole pipeline, in the only order that works.
# Stop at the first red step.
#
#   1. python3 scripts/process_vo.py    VO -> assets/vo/timeline.json (measured; picture cut to this)
#   2. python3 generate.py              script -> scene compositions + index.html
#   3. python3 scripts/prepare.py       validation gate (contrast, type, safe zone, field rhythm)
#   4. npx hyperframes lint             must be 0 errors
#   5. npx hyperframes render           960 frames at 1080x1920
#   6. python3 scripts/mix_audio.py     VO + bed + cues -> renders/master.wav (-14 LUFS)
#   7. ffmpeg mux                       picture + master -> renders/final.mp4
#   8. python3 scripts/qc.py            the gate; exits non-zero if deliverable not acceptable
#
# Usage:  ./build.sh                 full build
#         ./build.sh --from render   skip the VO stage (already measured)
set -euo pipefail
cd "$(dirname "$0")"

export PATH="${NODE_BIN:-/home/user/node22/bin}:$PATH"
export TMPDIR="${TMPDIR:-/home/user/tmp}"
mkdir -p "$TMPDIR" renders

OUT="renders/final.mp4"

if [[ "${1:-}" != "--from" ]]; then
  echo "== 1/8 VO"; python3 scripts/process_vo.py
fi
echo "== 2/8 scenes"; python3 generate.py --script assets/vo/sections.json --output index.html

echo "== 3/8 validate"; python3 scripts/prepare.py

echo "== 4/8 lint"; npx --yes hyperframes@0.9.19 lint | tee /tmp/hf-lint.log
grep -q "0 errors" /tmp/hf-lint.log || { echo "STOP: lint errors"; exit 1; }

echo "== 5/8 render"; npx --yes hyperframes@0.9.19 render --output renders/_raw.mp4

echo "== 6/8 mix"; python3 scripts/mix_audio.py

echo "== 7/8 mux"
ffmpeg -y -v error -i renders/_raw.mp4 -i renders/master.wav -map 0:v -map 1:a \
       -c:v copy -c:a aac -b:a 192k -shortest -movflags +faststart "$OUT"

echo "== 8/8 QC"
python3 scripts/qc.py "$OUT"
