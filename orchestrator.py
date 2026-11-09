#!/usr/bin/env python3
"""
Premium Orchestrator — v3.3 (Anchor Grid + Sound)

Pipeline:
  1. Parse voice script into timestamped segments
  2. Detect topic → animation + evidence decision
  3. Generate scene compositions (compositions/sN-*.html) using anchor grid
  4. Run prepare.py (validation gate + token injection)
  5. Run build_index.py (root HTML with contiguous timing + wipes)
  6. Return report with audio cues + media search queries

Usage:
    from orchestrator import PremiumOrchestrator
    orch = PremiumOrchestrator()
    html_path, report = orch.build("my_script.txt", topic="Tor")
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Tuple, Dict

from design_system import DESIGN_TOKENS, ALIGNMENT_RULES, SCENE_TYPES, validate_scene
from media_sourcing import build_search_queries

WIDTH = DESIGN_TOKENS["resolution"]["width"]
HEIGHT = DESIGN_TOKENS["resolution"]["height"]
FPS = DESIGN_TOKENS["resolution"]["fps"]

TECHNICAL_TOPICS = {
    "tor", "onion", "anonymous browsing", "dark web", "vpn", "proxy",
    "isp", "relay", "network", "packet", "encryption", "cybersecurity",
    "dns", "cdn", "blockchain", "bitcoin", "ai", "machine learning",
    "how internet works", "neural network", "large language model",
}


@dataclass
class Scene:
    start: float
    end: float
    duration: float
    text: str
    scene_type: str = "body_left"
    is_emphasis: bool = False
    emphasis_word: Optional[str] = None
    needs_animation: bool = False
    needs_evidence: bool = False
    evidence_sources: List[dict] = field(default_factory=list)
    needs_lower_third: bool = False
    lower_third_label: Optional[str] = None
    lower_third_value: Optional[str] = None
    needs_transition_in: bool = False
    transition_kind: str = "wipe"
    audio_cue: Optional[str] = None
    warnings: List[str] = field(default_factory=list)


@dataclass
class BuildReport:
    total_scenes: int = 0
    total_duration: float = 0.0
    animations_inserted: int = 0
    evidence_blocks: int = 0
    transitions: int = 0
    lower_thirds: int = 0
    kinetic_scenes: int = 0
    warnings: List[str] = field(default_factory=list)
    search_queries: dict = field(default_factory=dict)
    audio_cues: List[str] = field(default_factory=list)
    media_download_commands: List[str] = field(default_factory=list)
    html_path: str = ""


class PremiumOrchestrator:
    def __init__(self, wpm: int = 145):
        self.wpm = wpm
        self.root = Path(__file__).resolve().parent

    # ── 1. Parse script ──────────────────────────────────────────────
    def parse_script(self, path: str) -> List[dict]:
        with open(path, "r", encoding="utf-8") as f:
            raw = f.read()
        lines = [ln.strip() for ln in raw.splitlines() if ln.strip()]
        segments = []
        cursor = 0.0
        ts_re = re.compile(
            r"^\s*\[(\d+(?:\.\d+)?)\s*[-–—]\s*(\d+(?:\.\d+)?)\s*s?\]\s*(.*)$"
        )
        for ln in lines:
            m = ts_re.match(ln)
            if m:
                start, end = float(m.group(1)), float(m.group(2))
                text = m.group(3).strip()
                cursor = end
            else:
                text = ln
                dur = self._estimate_duration(text)
                start, end = cursor, cursor + dur
                cursor = end
            is_emph = bool(re.search(r"\*\*.*?\*\*", ln)) or bool(
                re.search(r"\b[A-Z][A-Z\s]{2,}\b", text))
            emphasis_word = None
            if is_emph:
                m2 = re.search(r"\*\*(.*?)\*\*", ln)
                emphasis_word = m2.group(1) if m2 else None
                if not emphasis_word:
                    m3 = re.search(r"\b([A-Z][A-Z\s]{2,})\b", text)
                    emphasis_word = m3.group(1).strip() if m3 else None
            display = re.sub(r"\*\*(.*?)\*\*", r"\1", text).strip()
            segments.append({
                "start": start, "end": end, "duration": end - start,
                "text": display, "is_emphasis": is_emph,
                "emphasis_word": emphasis_word,
            })
        return segments

    def _estimate_duration(self, text: str) -> float:
        words = len(text.split())
        return max(2.0, words / self.wpm * 60.0)

    # ── 2. Topic detection ──────────────────────────────────────────
    def detect_topic(self, segments: List[dict]) -> Tuple[str, bool, dict]:
        combined = " ".join(s["text"] for s in segments).lower()
        detected = "general"
        is_tech = False
        for topic in TECHNICAL_TOPICS:
            if re.search(rf"\b{re.escape(topic)}\b", combined):
                detected = topic
                is_tech = True
                break
        category = "tor" if detected == "tor" else "generic_technical"
        queries = build_search_queries(detected, category) if is_tech else {}
        return detected, is_tech, queries

    # ── 3. Decompose into anchor-grid scenes ─────────────────────────
    def decompose(
        self,
        segments: List[dict],
        topic: str,
        is_technical: bool,
        add_end_screen: bool = True,
    ) -> List[Scene]:
        raw: List[Scene] = []
        n = len(segments)
        for i, seg in enumerate(segments):
            if i == 0:
                stype, audio_cue = "hook", "pop"
            elif i == n - 1:
                stype, audio_cue = "cta", "ding"
            elif seg["is_emphasis"]:
                stype, audio_cue = "body_right", "pop"
            else:
                stype, audio_cue = "body_left", None

            needs_anim = needs_evid = False
            ev_sources = []
            if is_technical and stype == "body_left" and i == 1:
                needs_anim = needs_evid = True
                ev_sources = [
                    {"platform": "YouTube", "url": "",
                     "caption": f"{topic} official animation"},
                    {"platform": "Website", "url": "",
                     "caption": f"{topic} project documentation"},
                ]
                audio_cue = "whoosh"

            scene = Scene(
                start=seg["start"], end=seg["end"], duration=seg["duration"],
                text=seg["text"], scene_type=stype,
                is_emphasis=seg["is_emphasis"],
                emphasis_word=seg["emphasis_word"],
                needs_animation=needs_anim, needs_evidence=needs_evid,
                evidence_sources=ev_sources, audio_cue=audio_cue,
            )
            scene.warnings = validate_scene({
                "type": stype, "duration": seg["duration"], "text": seg["text"]
            })
            raw.append(scene)

        if add_end_screen and raw:
            last = raw[-1]
            raw.append(Scene(
                start=last.end, end=last.end + 5.0, duration=5.0,
                text="Subscribe for more",
                scene_type="end_screen", audio_cue="ding",
            ))

        # Build final list with transitions + cumulative timing
        scenes: List[Scene] = []
        cursor = 0.0
        TRANS = 0.6
        for i, sc in enumerate(raw):
            sc.start = cursor
            sc.end = cursor + sc.duration
            cursor = sc.end
            scenes.append(sc)
            is_first = (i == 0)
            needs_trans = (
                not is_first and
                (sc.needs_animation or sc.scene_type == "cta")
            )
            if needs_trans:
                trans_start = scenes[-2].end if len(scenes) >= 2 else 0.0
                trans = Scene(
                    start=trans_start, end=trans_start + TRANS,
                    duration=TRANS, text="", scene_type="transition",
                    transition_kind="wipe",
                )
                scenes.insert(-1, trans)
                sc.start += TRANS
                sc.end += TRANS
                cursor += TRANS

        return scenes

    # ── 4. Generate scene composition files ──────────────────────────
    def generate_scenes(self, scenes: List[Scene], topic: str,
                        is_technical: bool) -> None:
        """Write compositions/sN-*.html files using new_scene.py logic."""
        comp_dir = self.root / "compositions"
        comp_dir.mkdir(parents=True, exist_ok=True)

        # Clear old scene files (keep template + wipe)
        for f in comp_dir.glob("s*.html"):
            if f.name not in ("_scene-base.html.tmpl", "wipe.html"):
                f.unlink()

        field_cycle = ["accent", "ground", "ink", "secondary",
                       "tertiary", "quaternary"]
        poses = ["p1_shrug.png", "p2_facepalm.png", "p3_present.png",
                 "p4_chin.png", "p5_memory.png", "p6_thumbs.png",
                 "p7_cta.png", "p8_point.png", "p9_idea.png"]

        scene_idx = 0
        for i, sc in enumerate(scenes):
            if sc.scene_type == "transition":
                continue  # transitions handled by build_index.py

            # Determine archetype
            if sc.scene_type == "cta" or sc.scene_type == "end_screen":
                arch = "type-led"
            elif sc.scene_type == "animation":
                arch = "card-led"
            elif sc.scene_type == "hook":
                arch = "card-led"
            elif sc.scene_type in ("body_left", "body_right"):
                arch = "card-led" if len(sc.text) > 60 else "type-led"
            else:
                arch = "card-led"

            # Field cycle (never repeat neighbor)
            field = field_cycle[scene_idx % len(field_cycle)]
            if scene_idx > 0:
                prev_field = field_cycle[(scene_idx - 1) % len(field_cycle)]
                if field == prev_field:
                    field = field_cycle[(scene_idx + 1) % len(field_cycle)]

            pose = poses[scene_idx % len(poses)]

            # Build hero/chip/card from text
            words = sc.text.split()
            hero = " ".join(words[:3]) if len(words) > 3 else sc.text
            chip = sc.text if len(sc.text) <= 40 else " ".join(words[3:6])
            if len(chip) < 3:
                chip = sc.text

            card_title = ""
            card_meta = ""
            card_body = ""
            line1 = ""
            line2 = ""

            # SVG animation for technical topics (embedded in card body)
            svg_anim = (
                '<div style="position:absolute;inset:0;background:var(--maroon);'
                'display:flex;align-items:center;justify-content:center;">'
                '<svg width="600" height="400" viewBox="0 0 600 400" '
                'xmlns="http://www.w3.org/2000/svg">'
                '<polyline points="80,200 220,200 360,200 500,200 560,200" '
                'stroke="var(--ink-soft)" stroke-width="3" fill="none" '
                'stroke-dasharray="10 6" opacity="0.5"/>'
                '<circle cx="80" cy="200" r="20" fill="var(--maroon-dark)" '
                'stroke="var(--cream)" stroke-width="3"/>'
                '<circle cx="220" cy="200" r="20" fill="var(--maroon-dark)" '
                'stroke="var(--cream)" stroke-width="3"/>'
                '<circle cx="360" cy="200" r="20" fill="var(--maroon-dark)" '
                'stroke="var(--cream)" stroke-width="3"/>'
                '<circle cx="500" cy="200" r="20" fill="var(--maroon-dark)" '
                'stroke="var(--cream)" stroke-width="3"/>'
                '<circle cx="560" cy="200" r="20" fill="var(--maroon-dark)" '
                'stroke="var(--cream)" stroke-width="3"/>'
                '<text x="80" y="225" text-anchor="middle" fill="var(--cream)" '
                'font-family="var(--font-display)" font-weight="950" font-size="14">USER</text>'
                '<text x="220" y="225" text-anchor="middle" fill="var(--cream)" '
                'font-family="var(--font-display)" font-weight="950" font-size="14">ISP</text>'
                '<text x="360" y="225" text-anchor="middle" fill="var(--cream)" '
                'font-family="var(--font-display)" font-weight="950" font-size="14">ENTRY</text>'
                '<text x="500" y="225" text-anchor="middle" fill="var(--cream)" '
                'font-family="var(--font-display)" font-weight="950" font-size="14">EXIT</text>'
                '<circle cx="80" cy="200" r="8" fill="var(--gold)">'
                '<animateMotion path="M 80,200 L 220,200 L 360,200 L 500,200 L 560,200" '
                'dur="4s" repeatCount="indefinite"/></circle>'
                '</svg></div>'
            )

            if sc.scene_type == "hook":
                card_title = sc.text
                card_meta = topic.upper()
            elif sc.needs_animation:
                card_title = topic.upper() + " Architecture"
                card_meta = "Verified path"
                card_body = svg_anim
                sc.scene_type = "animation"
            elif sc.scene_type == "cta":
                card_title = "Get shortlisted"
                card_meta = "Customize per company"
            elif sc.scene_type == "end_screen":
                card_title = "Subscribe"
                card_meta = "@uttambhartiyaa"
            elif sc.scene_type in ("body_left", "body_right"):
                card_title = sc.text
                card_meta = ""

            # Build new_scene.py CLI args
            cmd = [
                sys.executable,
                str(self.root / "scripts" / "new_scene.py"),
                "--n", str(scene_idx + 1),
                "--name", sc.scene_type,
                "--arch", arch,
                "--field", field,
                "--pose", pose,
                "--kicker", topic.upper(),
                "--hero", hero,
                "--chip", chip,
                "--card-title", card_title,
                "--card-meta", card_meta,
            ]
            if card_body:
                cmd += ["--card-body", card_body]
            if line1:
                cmd += ["--line1", line1]
            if line2:
                cmd += ["--line2", line2]
            if sc.scene_type == "end_screen":
                cmd += ["--no-cover"]
            if i == len(scenes) - 1:
                cmd += ["--no-cover"]

            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                print(f"WARN  new_scene.py failed for scene {scene_idx + 1}: "
                      f"{result.stderr}")
            scene_idx += 1

    # ── 5. Build root HTML ──────────────────────────────────────────
    def build_root(self) -> str:
        """Run build_index.py and return index.html path."""
        idx = self.root / "index.html"
        cmd = [sys.executable, str(self.root / "scripts" / "build_index.py")]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"WARN  build_index.py failed: {result.stderr}")
        return str(idx)

    # ── 6. Public build ─────────────────────────────────────────────
    def build(
        self,
        script_path: str,
        topic: Optional[str] = None,
        voiceover: Optional[str] = None,
        music: Optional[str] = None,
        add_end_screen: bool = True,
    ) -> Tuple[str, BuildReport]:
        segments = self.parse_script(script_path)
        detected_topic, is_technical, queries = self.detect_topic(segments)
        if topic:
            detected_topic = topic

        scenes = self.decompose(segments, detected_topic, is_technical,
                                add_end_screen)
        self.generate_scenes(scenes, detected_topic, is_technical)

        # Create/overwrite timeline.json from segments when no real VO timeline exists
        sections_path = self.root / "assets" / "vo" / "sections.json"
        tl_path = self.root / "assets" / "vo" / "timeline.json"
        if not sections_path.exists():
            tl_path.parent.mkdir(parents=True, exist_ok=True)
            # Timeline sections match non-transition scene compositions
            # Uses FINAL scene timings (after transitions inserted)
            non_trans = [s for s in scenes if s.scene_type != "transition"]
            tl_data = {
                "tempo_factor": 1.0,
                "lead_in": 0.30,
                "tail": 1.15,
                "gap": 0.30,
                "script_target": None,
                "root_duration": round(scenes[-1].end + 1.15, 3),
                "sections": [
                    {
                        "id": f"vo{i+1}",
                        "label": s.scene_type.upper(),
                        "script_start": None,
                        "script_end": None,
                        "start": round(s.start, 3),
                        "dur": round(s.duration, 3),
                        "end": round(s.end, 3),
                        "file": f"assets/vo/wav/vo{i+1}.wav",
                    }
                    for i, s in enumerate(non_trans)
                ],
            }
            tl_path.write_text(json.dumps(tl_data, indent=2))

        # Run prepare.py validation
        prep_cmd = [sys.executable,
                    str(self.root / "scripts" / "prepare.py")]
        prep_result = subprocess.run(prep_cmd, capture_output=True, text=True)
        prep_warnings = []
        if prep_result.returncode != 0:
            prep_warnings = [l.strip() for l in prep_result.stdout.splitlines()
                             if l.strip().startswith(("FAIL", "WARN"))]

        # Build root HTML
        html_path = self.build_root()

        report = BuildReport(
            total_scenes=len(scenes),
            total_duration=scenes[-1].end if scenes else 0.0,
            animations_inserted=sum(1 for s in scenes if s.needs_animation),
            evidence_blocks=sum(1 for s in scenes if s.needs_evidence),
            transitions=sum(1 for s in scenes if s.scene_type == "transition"),
            lower_thirds=sum(1 for s in scenes if s.scene_type == "lower_third"),
            kinetic_scenes=sum(1 for s in scenes
                               if s.scene_type in ("hook", "section",
                                                   "body_left", "body_right")),
            warnings=prep_warnings,
            search_queries=queries,
            audio_cues=[s.audio_cue for s in scenes if s.audio_cue],
            html_path=html_path,
        )
        return html_path, report


def main():
    import argparse
    parser = argparse.ArgumentParser(
        description="Premium Orchestrator: voice script → HyperFrames HTML")
    parser.add_argument("--script", required=True, help="Path to voice script")
    parser.add_argument("--topic", default=None,
                        help="Force topic (e.g. 'Tor') for animation")
    parser.add_argument("--voiceover", default=None,
                        help="Voiceover audio file path")
    parser.add_argument("--music", default=None,
                        help="Background music file path")
    parser.add_argument("--output", default="index.html",
                        help="Output HTML path")
    parser.add_argument("--wpm", type=int, default=145)
    parser.add_argument("--no-end-screen", action="store_true")
    args = parser.parse_args()

    from pathlib import Path as _Path
    script_path = _Path(args.script)
    if not script_path.exists():
        print(f"ERROR: Script not found: {script_path}")
        sys.exit(1)

    orch = PremiumOrchestrator(wpm=args.wpm)
    html_path, report = orch.build(
        str(script_path), topic=args.topic,
        voiceover=args.voiceover, music=args.music,
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
        print(f"🔍 Search queries: {list(report.search_queries.keys())}")
    print("")
    print("Next steps:")
    print("  1. python3 scripts/prepare.py          (validation gate)")
    print("  2. npx hyperframes lint                (0 errors gate)")
    print("  3. npx hyperframes preview")
    print("  4. npx hyperframes render")
    print("  5. python3 scripts/gen_sfx.py          (synthesize SFX)")
    print("  6. python3 scripts/mix_audio.py        (VO + cues + bed → master.wav)")
    print("  7. ffmpeg mux → final.mp4")


if __name__ == "__main__":
    main()
