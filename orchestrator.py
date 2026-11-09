"""
Premium Orchestrator — v3.0
============================

Senior-agent pipeline that converts a voice script into a premium HyperFrames
video. Handles:

  1. Script parsing (plain text or [start-end] timestamped segments)
  2. Topic detection → premium animation + evidence decision
  3. Audio sync — voiceover timestamps, SFX cues (whoosh/pop/ding), music bed
  4. Scene decomposition with premium types (hook, section, body, emphasis, animation, evidence, lower_third, cta, end_screen, transition)
  5. Kinetic typography generation (per-word animation)
  6. Media download commands (yt-dlp style) for evidence sourcing
  7. Design-contract validation
  8. HTML assembly

Usage:
    from orchestrator import PremiumOrchestrator
    orch = PremiumOrchestrator()
    html, report = orch.build("my_script.txt", topic="Tor", voiceover="voice.mp3", music="music.mp3")
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Dict

from design_system import (
    PALETTE, MOTION, TYPOGRAPHY, LAYOUT, ALIGNMENT_RULES, SCENE_TYPES,
    premium_css_variables, base_scene_css, validate_scene as ds_validate,
)
from animations import (
    kinetic_hook_html, kinetic_section_html, body_line_html,
    tor_diagram_html, glass_evidence_card_html, lower_third_html,
    end_screen_html, scene_transition_html,
)
from media_sourcing import build_search_queries  # type: ignore

WIDTH = LAYOUT["canvas_w"]
HEIGHT = LAYOUT["canvas_h"]
FPS = LAYOUT["fps"]

# ── Technical topics that trigger premium animation + evidence ────────────
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
    audio_cue: Optional[str] = None  # 'whoosh' | 'pop' | 'ding' | None
    music_beat: bool = False
    warnings: List[str] = field(default_factory=list)

    @property
    def html(self) -> str:
        return build_scene_html(self)


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


class PremiumOrchestrator:
    def __init__(self, wpm: int = 145):  # slightly slower for premium readability
        self.wpm = wpm

    # ── 1. Parse script ──────────────────────────────────────────────
    def parse_script(self, path: str) -> List[dict]:
        with open(path, "r", encoding="utf-8") as f:
            raw = f.read()

        lines = [ln.strip() for ln in raw.splitlines() if ln.strip()]
        segments = []
        cursor = 0.0
        ts_re = re.compile(r"^\s*\[(\d+(?:\.\d+)?)\s*[-–—]\s*(\d+(?:\.\d+)?)\s*s?\]\s*(.*)$")

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

            # Detect emphasis: **word** or ALL-CAPS phrase
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

    # ── 3. Decompose into premium scenes ────────────────────────────
    def decompose(
        self,
        segments: List[dict],
        topic: str,
        is_technical: bool,
        add_end_screen: bool = True,
    ) -> List[Scene]:
        scenes: List[Scene] = []
        n = len(segments)

        for i, seg in enumerate(segments):
            # Determine scene type
            if i == 0:
                stype = "hook"
                audio_cue = "pop"
            elif i == n - 1:
                stype = "cta"
                audio_cue = "ding"
            elif seg["is_emphasis"]:
                stype = "body_right"
                audio_cue = "pop"
            else:
                stype = "body_left"
                audio_cue = None

            needs_anim = False
            needs_evid = False
            ev_sources = []

            if is_technical and stype == "body_left" and i == 1:
                needs_anim = True
                needs_evid = True
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
                evidence_sources=ev_sources,
                audio_cue=audio_cue,
            )
            scene.warnings = ds_validate({
                "type": stype, "duration": seg["duration"], "text": seg["text"]
            })
            scenes.append(scene)

            # Insert premium transition before animation/CTA scenes
            for j in range(len(scenes) - 1, 0, -1):
                prev = scenes[j - 1]
                curr = scenes[j]
                if curr.needs_animation or curr.scene_type == "cta":
                    trans = Scene(
                        start=prev.end, end=prev.end + 0.6, duration=0.6,
                        text="", scene_type="transition",
                        transition_kind="wipe",
                    )
                    scenes.insert(j, trans)

        # Premium end screen
        if add_end_screen and scenes:
            last = scenes[-1]
            scenes.append(Scene(
                start=last.end, end=last.end + 5.0, duration=5.0,
                text="Subscribe for more",
                scene_type="end_screen",
                audio_cue="ding",
            ))

        return scenes

    # ── 4. Assemble HTML ────────────────────────────────────────────
    def assemble(
        self,
        scenes: List[Scene],
        topic: str,
        is_technical: bool,
        search_queries: dict,
        voiceover: Optional[str] = None,
        music: Optional[str] = None,
    ) -> str:
        css = premium_css_variables() + base_scene_css()
        scene_blocks = []

        for sc in scenes:
            block = self._scene_to_html(sc, topic)
            scene_blocks.append(block)

        # Audio block (HyperFrames <hf-audio> if supported, else comment)
        audio_block = ""
        if voiceover or music:
            audio_block = f"""
  <!-- AUDIO TRACKS — HyperFrames audio engine -->
  <!-- voiceover: {voiceover or 'none'} -->
  <!-- music: {music or 'none'} -->
  <!-- SFX cues: whoosh, pop, ding placed at scene start times -->
"""

        total_dur = scenes[-1].end if scenes else 30.0

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Premium Explainer — {topic}</title>
<style>{css}</style>
</head>
<body>

<template id="root">
  <!-- Premium Orchestrator v3.0 — topic: {topic} | technical: {is_technical} -->
  {''.join(scene_blocks)}
</template>

{audio_block}

<script>
  /* HyperFrames variables — fill media URLs here */
  /* data-var-src attributes are in evidence cards above */
  /* Audio: voiceover="{voiceover or ''}" music="{music or ''}" */
</script>
</body>
</html>"""
        return html

    def _scene_to_html(self, sc: Scene, topic: str) -> str:
        if sc.scene_type == "transition":
            return scene_transition_html(
                kind=sc.transition_kind, duration=sc.duration,
                start=sc.start, track=99,
            )
        if sc.needs_animation:
            return tor_diagram_html(
                duration=sc.duration, start=sc.start, track=10, topic=topic,
            ) + (glass_evidence_card_html(
                f"{sc.start}-{sc.end}s", sc.text, sc.evidence_sources,
                duration=sc.duration, start=sc.start, track=50,
            ) if sc.needs_evidence else "")
        if sc.needs_evidence:
            return glass_evidence_card_html(
                f"{sc.start}-{sc.end}s", sc.text, sc.evidence_sources,
                duration=sc.duration, start=sc.start, track=50,
            )
        if sc.scene_type == "hook":
            return kinetic_hook_html(
                sc.text, emoji="😩", duration=sc.duration,
                start=sc.start, track=1,
            )
        if sc.scene_type == "section":
            return kinetic_section_html(
                sc.text, duration=sc.duration, start=sc.start, track=2,
            )
        if sc.scene_type == "emphasis" or (sc.scene_type == "body_right" and sc.is_emphasis):
            return body_line_html(
                sc.text, align="right", emphasis_word=sc.emphasis_word,
                duration=sc.duration, start=sc.start, track=3,
            )
        if sc.scene_type == "body_right":
            return body_line_html(
                sc.text, align="right", duration=sc.duration,
                start=sc.start, track=3,
            )
        if sc.scene_type == "body_left":
            return body_line_html(
                sc.text, align="left", duration=sc.duration,
                start=sc.start, track=2,
            )
        if sc.scene_type == "cta":
            return f"""
  <div class="scene cta" data-start="{sc.start:.2f}" data-duration="{sc.duration:.2f}" data-track-index="4">
    <div class="text-safe">
      <div style="font-size: {TYPOGRAPHY['cta']['size']}; font-weight: {TYPOGRAPHY['cta']['weight']};
                  line-height: {TYPOGRAPHY['cta']['line_height']}; letter-spacing: {TYPOGRAPHY['cta']['tracking']};
                  text-align: center; color: var(--cream); margin-bottom: 24px;
                  animation: scaleReveal 0.8s var(--ease-premium) forwards;">
        {sc.text}
      </div>
      <div style="font-size: 28px; font-weight: 600; color: var(--gold);
                  animation: popIn 0.6s var(--ease-premium) forwards 1s;">
        Tap the link in bio
      </div>
    </div>
  </div>"""
        if sc.scene_type == "end_screen":
            return end_screen_html(
                sc.text, duration=sc.duration, start=sc.start, track=90,
            )
        if sc.scene_type == "lower_third":
            return lower_third_html(
                sc.lower_third_label or "SOURCE",
                sc.lower_third_value or sc.text,
                duration=sc.duration, start=sc.start, track=60,
            )
        # Fallback
        return body_line_html(
            sc.text, align="left", duration=sc.duration,
            start=sc.start, track=2,
        )

    # ── 5. Public build ─────────────────────────────────────────────
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

        scenes = self.decompose(segments, detected_topic, is_technical, add_end_screen)
        html = self.assemble(
            scenes, detected_topic, is_technical, queries,
            voiceover=voiceover, music=music,
        )

        report = BuildReport(
            total_scenes=len(scenes),
            total_duration=segments[-1]["end"] if segments else 0.0,
            animations_inserted=sum(1 for s in scenes if s.needs_animation),
            evidence_blocks=sum(1 for s in scenes if s.needs_evidence),
            transitions=sum(1 for s in scenes if s.scene_type == "transition"),
            lower_thirds=sum(1 for s in scenes if s.scene_type == "lower_third"),
            kinetic_scenes=sum(1 for s in scenes if s.scene_type in ("hook", "section", "body_left", "body_right")),
            warnings=[w for s in scenes for w in s.warnings],
            search_queries=queries,
            audio_cues=[s.audio_cue for s in scenes if s.audio_cue],
        )

        # Media download commands for evidence sourcing
        if is_technical and queries:
            cmds = []
            for platform, qlist in queries.items():
                for q in qlist[:2]:  # top 2 per platform
                    if platform == "youtube":
                        cmds.append(f'yt-dlp -f "bestvideo[height<=1080]+bestaudio/best" --merge-output-format mp4 "ytsearch1:{q}" -o "assets/media/%(title)s.%(ext)s"')
                    elif platform == "image":
                        cmds.append(f'# Download image: {q}')
            report.media_download_commands = cmds

        return html, report


def main():
    import argparse
    parser = argparse.ArgumentParser(
        description="Premium Orchestrator: voice script → HyperFrames HTML")
    parser.add_argument("--script", required=True, help="Path to voice script (.txt)")
    parser.add_argument("--topic", default=None, help="Force topic (e.g. 'Tor')")
    parser.add_argument("--voiceover", default=None, help="Voiceover audio file path")
    parser.add_argument("--music", default=None, help="Background music file path")
    parser.add_argument("--output", default="index.html", help="Output HTML path")
    parser.add_argument("--wpm", type=int, default=145, help="Words per minute")
    parser.add_argument("--no-end-screen", action="store_true", help="Skip end screen")
    args = parser.parse_args()

    from pathlib import Path
    script_path = Path(args.script)
    if not script_path.exists():
        print(f"ERROR: Script not found: {script_path}")
        raise SystemExit(1)

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
        print(f"🔍 Search queries: {list(report.search_queries.keys())}")
    if report.media_download_commands:
        print(f"⬇️  Media download commands: {len(report.media_download_commands)}")
    print("")
    print("Next steps:")
    print("  1. Place HTML in HyperFrames project (npx hyperframes init my-video)")
    print("  2. Add voiceover + music files to assets/audio/")
    print("  3. Fill data-var-src URLs in evidence cards")
    print("  4. Run media download commands for evidence assets")
    print("  5. npx hyperframes preview")
    print("  6. npx hyperframes render")


if __name__ == "__main__":
    main()
