#!/usr/bin/env python3
"""
Premium Video Skill — v3.3 Generator
====================================

Converts a voice script into a premium HyperFrames HTML video using the
anchor-grid pipeline (kicker → hero → body → chip → presenter).

Pipeline:
  generate.py → new_scene.py (scene files) → prepare.py (validation)
  → build_index.py (root HTML) → hyperframes lint → hyperframes render

Features:
  • Script parsing (plain text or [start-end] timestamped segments)
  • Topic detection → premium animation + evidence insertion
  • Anchor grid: kicker, hero, body, chip, presenter (bottom-fixed)
  • Six-color field cycle (no two neighbor scenes share a color)
  • Presenter poses change every scene
  • Kinetic typography within card components
  • Motion-blur wipe transitions
  • Audio sync cues (whoosh/pop/ding) + voiceover + music markers
  • Media download commands (yt-dlp) for evidence sourcing
  • Strict design-contract validation (prepare.py)

Usage:
    python3 generate.py --script my_script.txt --output index.html
    python3 generate.py --script tor_script.txt --topic Tor --output index.html
    python3 generate.py --script my_script.txt \
        --voiceover assets/audio/voice.mp3 \
        --music assets/audio/music.mp3 \
        --output index.html

Then:
    python3 scripts/prepare.py          # validation gate
    npx hyperframes lint                # 0 errors gate
    npx hyperframes preview
    npx hyperframes render

Audio pipeline (run after rendering video):
    python3 scripts/gen_sfx.py          # synthesize SFX (one-time)
    python3 scripts/mix_audio.py        # VO + cues + bed → master.wav
    ffmpeg mux picture + master.wav → final.mp4
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from orchestrator import PremiumOrchestrator


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Convert a voice script into a premium HyperFrames HTML "
                    "video with anchor-grid layout, animations, and audio sync.")
    parser.add_argument("--script", required=True,
                        help="Path to voice script (.txt)")
    parser.add_argument("--topic", default=None,
                        help="Force a topic (e.g. 'Tor', 'VPN', 'AI') "
                             "for animation/evidence")
    parser.add_argument("--voiceover", default=None,
                        help="Voiceover audio file path "
                             "(assets/audio/voice.mp3)")
    parser.add_argument("--music", default=None,
                        help="Background music file path "
                             "(assets/audio/music.mp3)")
    parser.add_argument("--output", default="index.html",
                        help="Output HTML path (default: index.html)")
    parser.add_argument("--wpm", type=int, default=145,
                        help="Words per minute for auto-timing (default: 145)")
    parser.add_argument("--no-end-screen", action="store_true",
                        help="Skip the premium end screen")
    args = parser.parse_args()

    script_path = Path(args.script)
    if not script_path.exists():
        print(f"ERROR: Script not found: {script_path}", file=sys.stderr)
        sys.exit(1)

    # If JSON script (sections.json), convert to plain text for parsing
    if script_path.suffix == ".json":
        import json as _json
        spec = _json.loads(script_path.read_text())
        lines = [s.get("say", s.get("on_screen", "")) for s in spec.get("sections", [])]
        tmp_script = script_path.parent / "script_converted.txt"
        tmp_script.write_text("\n".join(lines))
        args.script = str(tmp_script)
        script_path = tmp_script

    orch = PremiumOrchestrator(wpm=args.wpm)
    html_path, report = orch.build(
        str(script_path),
        topic=args.topic,
        voiceover=args.voiceover,
        music=args.music,
        add_end_screen=not args.no_end_screen,
    )

    print(f"✓ Premium build: {report.total_scenes} scene(s)")
    print(f"✓ Duration: {report.total_duration:.1f}s")
    print(f"✓ Animations: {report.animations_inserted}")
    print(f"✓ Evidence blocks: {report.evidence_blocks}")
    print(f"✓ Transitions: {report.transitions}")
    print(f"✓ Kinetic scenes: {report.kinetic_scenes}")
    print(f"✓ Audio cues: {', '.join(report.audio_cues) or 'none'}")
    print(f"✓ HTML: {report.html_path}")
    if report.warnings:
        print(f"⚠ Warnings: {report.warnings}")
    if report.search_queries:
        print(f"🔍 Search queries ready: {list(report.search_queries.keys())}")
    if report.media_download_commands:
        print(f"⬇️  Media download commands ({len(report.media_download_commands)}):")
        for c in report.media_download_commands[:5]:
            print(f"     {c}")
    print("")
    print("Next steps:")
    print("  1. python3 scripts/prepare.py          # validation gate")
    print("  2. npx hyperframes lint                # 0 errors gate")
    print("  3. npx hyperframes preview")
    print("  4. npx hyperframes render              # MP4 output")
    print("  5. python3 scripts/gen_sfx.py          # synthesize SFX")
    print("  6. python3 scripts/mix_audio.py        # VO + cues + bed → master.wav")
    print("  7. ffmpeg -i rendered.mp4 -i renders/master.wav \\")
    print("         -c:v copy -c:a aac -shortest final.mp4")


if __name__ == "__main__":
    main()
