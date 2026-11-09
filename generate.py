#!/usr/bin/env python3
"""
Resume-Reject / Technical Explainer Video Skill — Generator
=============================================================

Orchestrates a HyperFrames video from a voice script using the senior-agent
pipeline in orchestrator.py.

Features:
  • Script parsing (plain text or [start-end] timestamped segments)
  • Topic detection → automatic animation + evidence insertion
  • SVG/CSS animated diagrams (TOR flow, packet hops, transitions)
  • Media sourcing queries for YouTube / Instagram / forums / websites
  • Design-system consistency (maroon/lavender, alignment rules)
  • Validation report per build

Usage:
    python3 generate.py --script my_script.txt --output index.html
    python3 generate.py --script tor_script.txt --topic Tor --output index.html

Then:
    npx hyperframes preview
    npx hyperframes render
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Allow running from any directory
sys.path.insert(0, str(Path(__file__).resolve().parent))

from orchestrator import Orchestrator


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Convert a voice script into a HyperFrames HTML video "
                    "styled like the resume-reject source video, with "
                    "optional animation and evidence blocks.")
    parser.add_argument("--script", required=True,
                        help="Path to voice script (.txt)")
    parser.add_argument("--topic", default=None,
                        help="Force a topic (e.g. 'Tor') for animation/evidence")
    parser.add_argument("--output", default="index.html",
                        help="Output HTML path (default: index.html)")
    parser.add_argument("--wpm", type=int, default=150,
                        help="Words per minute for auto-timing (default: 150)")
    args = parser.parse_args()

    script_path = Path(args.script)
    if not script_path.exists():
        print(f"ERROR: Script not found: {script_path}", file=sys.stderr)
        sys.exit(1)

    orch = Orchestrator(wpm=args.wpm)
    html, report = orch.build(str(script_path), topic=args.topic)

    with open(args.output, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"✓ Parsed {report.total_scenes} scene(s)")
    print(f"✓ Total duration: {report.total_duration:.1f}s")
    print(f"✓ Animations: {report.animations_inserted}")
    print(f"✓ Evidence blocks: {report.evidence_blocks}")
    print(f"✓ Transitions: {report.transitions}")
    print(f"✓ Wrote {args.output}")
    if report.warnings:
        print(f"⚠ Warnings: {report.warnings}")
    if report.search_queries:
        print(f"🔍 Media search queries ready for: {list(report.search_queries.keys())}")
    print("")
    print("Next steps:")
    print("  1. Place this HTML in a HyperFrames project (npx hyperframes init my-video)")
    print("  2. Fill media URLs into data-var-src attributes (evidence cards)")
    print("  3. npx hyperframes preview")
    print("  4. npx hyperframes render")


if __name__ == "__main__":
    main()
