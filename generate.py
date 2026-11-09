#!/usr/bin/env python3
"""
Premium Video Skill — v3.0 Generator
====================================

Converts a voice script into a premium HyperFrames HTML video.

Features:
  • Script parsing (plain text or [start-end] timestamped segments)
  • Topic detection → premium animation + evidence insertion
  • Kinetic typography (per-word pop/slide/scale animations)
  • Glassmorphism evidence cards + lower thirds + end screens
  • Motion-blur transitions + Ken Burns camera moves
  • Audio sync cues (whoosh / pop / ding) + voiceover + music markers
  • Media download commands (yt-dlp) for evidence sourcing
  • Strict design-contract validation

Usage:
    python3 generate.py --script my_script.txt --output index.html
    python3 generate.py --script tor_script.txt --topic Tor --output index.html
    python3 generate.py --script my_script.txt --voiceover assets/audio/voice.mp3 --music assets/audio/music.mp3 --output index.html

Then:
    npx hyperframes preview
    npx hyperframes render
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from orchestrator import PremiumOrchestrator


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Convert a voice script into a premium HyperFrames HTML video "
                    "with kinetic typography, animations, and evidence sourcing.")
    parser.add_argument("--script", required=True, help="Path to voice script (.txt)")
    parser.add_argument("--topic", default=None,
                        help="Force a topic (e.g. 'Tor', 'VPN', 'AI') for animation/evidence")
    parser.add_argument("--voiceover", default=None,
                        help="Voiceover audio file path (assets/audio/voice.mp3)")
    parser.add_argument("--music", default=None,
                        help="Background music file path (assets/audio/music.mp3)")
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

    orch = PremiumOrchestrator(wpm=args.wpm)
    html, report = orch.build(
        str(script_path),
        topic=args.topic,
        voiceover=args.voiceover,
        music=args.music,
        add_end_screen=not args.no_end_screen,
    )

    with open(args.output, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"✓ Premium build: {report.total_scenes} scene(s)")
    print(f"✓ Duration: {report.total_duration:.1f}s")
    print(f"✓ Animations: {report.animations_inserted}")
    print(f"✓ Evidence blocks: {report.evidence_blocks}")
    print(f"✓ Transitions: {report.transitions}")
    print(f"✓ Kinetic scenes: {report.kinetic_scenes}")
    print(f"✓ Audio cues: {', '.join(report.audio_cues) or 'none'}")
    print(f"✓ Wrote {args.output}")
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
    print("  1. Place this HTML in a HyperFrames project (npx hyperframes init my-video)")
    print("  2. Add voiceover + music to assets/audio/")
    print("  3. Fill data-var-src URLs in evidence cards")
    print("  4. Run media download commands for evidence assets")
    print("  5. npx hyperframes preview")
    print("  6. npx hyperframes render")


if __name__ == "__main__":
    main()
