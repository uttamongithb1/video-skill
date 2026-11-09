"""
Orchestrator — Senior-Agent Pipeline for HyperFrames Video Generation.

Responsibilities:
  1. Parse voice script into timestamped segments
  2. Detect topic & decide if animation/evidence is needed
  3. Decompose into scenes with types (hook, body, emphasis, animation, evidence, cta)
  4. Insert transitions between major sections
  5. Generate media search queries for evidence sourcing
  6. Assemble final HyperFrames HTML with design-system consistency
  7. Validate every scene against the design contract

Usage:
    from orchestrator import Orchestrator
    orch = Orchestrator()
    html, report = orch.build("my_script.txt", topic="Tor Network")
    open("index.html","w").write(html)
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass, field
from typing import List, Tuple, Optional

from design_system import (DESIGN_TOKENS, ALIGNMENT_RULES, SCENE_TYPES,
                           scene_css, validate_scene)
from animations import tor_flow_svg, packet_hop_animation, scene_transition
from media_sourcing import (build_search_queries, evidence_card_html,
                            citation_footer, MediaSource)

WIDTH = DESIGN_TOKENS["resolution"]["width"]
HEIGHT = DESIGN_TOKENS["resolution"]["height"]
FPS = DESIGN_TOKENS["resolution"]["fps"]

# Topics that trigger automatic animation + evidence insertion
TECHNICAL_TOPICS = {
    "tor", "onion", "anonymous browsing", "dark web",
    "vpn", "proxy", "isp", "relay", "network", "packet",
    "encryption", "cybersecurity", "how internet works",
    "dns", "cdn", "blockchain", "bitcoin", "ai", "machine learning",
}


@dataclass
class Scene:
    start: float
    end: float
    duration: float
    text: str
    scene_type: str = "body"
    is_emphasis: bool = False
    needs_animation: bool = False
    needs_evidence: bool = False
    evidence_sources: List[dict] = field(default_factory=list)
    transition_in: Optional[str] = None
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
    warnings: List[str] = field(default_factory=list)
    search_queries: dict = field(default_factory=dict)


class Orchestrator:
    def __init__(self, wpm: int = 150):
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

            is_emph = bool(re.search(r"\*\*.*?\*\*", ln)) or bool(
                re.search(r"\b[A-Z][A-Z\s]{2,}\b", text))
            display = re.sub(r"\*\*(.*?)\*\*", r"\1", text).strip()

            segments.append({
                "start": start, "end": end, "duration": end - start,
                "text": display, "is_emphasis": is_emph,
            })
        return segments

    def _estimate_duration(self, text: str) -> float:
        words = len(text.split())
        return max(2.0, words / self.wpm * 60.0)

    # ── 2. Topic detection ──────────────────────────────────────────
    def detect_topic(self, segments: List[dict]) -> Tuple[str, bool, dict]:
        """
        Returns (topic, is_technical, search_queries).
        Scans all text for known technical keywords.
        """
        combined = " ".join(s["text"] for s in segments).lower()
        detected = "general"
        is_tech = False

        for topic in TECHNICAL_TOPICS:
            if re.search(rf"\b{re.escape(topic)}\b", combined):
                detected = topic
                is_tech = True
                break

        queries = build_search_queries(detected,
                                       "tor" if detected == "tor"
                                       else "generic_technical") if is_tech else {}
        return detected, is_tech, queries

    # ── 3. Decompose into scenes ────────────────────────────────────
    def decompose(self, segments: List[dict], topic: str,
                  is_technical: bool) -> List[Scene]:
        scenes: List[Scene] = []
        n = len(segments)

        for i, seg in enumerate(segments):
            # Determine scene type
            if i == 0:
                stype = "hook"
            elif i == n - 1:
                stype = "cta"
            elif seg["is_emphasis"]:
                stype = "emphasis"
            else:
                stype = "body"

            needs_anim = False
            needs_evid = False
            ev_sources = []

            # Technical topic: insert animation after the hook/explanation
            needs_anim = False
            needs_evid = False
            ev_sources = []

            if is_technical and stype == "body" and i == 1:
                needs_anim = True
                needs_evid = True
                ev_sources = [
                    {"platform": "YouTube", "url": "",
                     "caption": f"{topic} official animation"},
                    {"platform": "Website", "url": "",
                     "caption": f"{topic} project documentation"},
                ]

            scene = Scene(
                start=seg["start"], end=seg["end"], duration=seg["duration"],
                text=seg["text"], scene_type=stype, is_emphasis=seg["is_emphasis"],
                needs_animation=needs_anim, needs_evidence=needs_evid,
                evidence_sources=ev_sources,
            )
            scene.warnings = validate_scene({
                "type": stype, "duration": seg["duration"], "text": seg["text"]
            })
            scenes.append(scene)



        # Add transitions before animation scenes and before CTA
        for i in range(len(scenes) - 1, 0, -1):
            prev = scenes[i - 1]
            curr = scenes[i]
            if curr.needs_animation or curr.scene_type == "cta":
                # Insert a transition scene between prev and curr
                trans = Scene(
                    start=prev.end, end=prev.end + 0.6, duration=0.6,
                    text="", scene_type="transition",
                    transition_in="fade",
                )
                scenes.insert(i, trans)

        return scenes

    # ── 4. Assemble HTML ────────────────────────────────────────────
    def assemble(self, scenes: List[Scene], topic: str,
                 is_technical: bool, search_queries: dict) -> str:
        css = self._generate_css()
        scene_blocks = []

        for sc in scenes:
            if sc.scene_type == "transition":
                block = scene_transition(kind="fade", duration=sc.duration)
            elif sc.needs_animation:
                block = self._animation_scene_html(sc, topic)
            elif sc.needs_evidence:
                block = evidence_card_html(
                    f"{sc.start}-{sc.end}s", sc.text,
                    [MediaSource(**s) for s in sc.evidence_sources],
                    DESIGN_TOKENS["colors"],
                )
                block += citation_footer(
                    [MediaSource(**s) for s in sc.evidence_sources],
                    DESIGN_TOKENS["colors"],
                )
            else:
                block = self._text_scene_html(sc)

            scene_blocks.append(block)

        total_dur = scenes[-1].end if scenes else 30.0
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
title>Technical Explainer — {topic}</title>
<style>{css}</style>
</head>
<body>

<template id="root">
  <!-- Orchestrator build — topic: {topic} | technical: {is_technical} -->
  {''.join(scene_blocks)}
</template>

<script>
  /* HyperFrames variables — agent fills media URLs here */
  /* data-var-src attributes are in evidence cards above */
</script>
</body>
</html>"""
        return html

    def _generate_css(self) -> str:
        tokens = DESIGN_TOKENS
        return f"""
:root {{
  --maroon_bg: {tokens['colors']['maroon_bg']};
  --maroon_near_black: {tokens['colors']['maroon_near_black']};
  --cream_text: {tokens['colors']['cream_text']};
  --lavender_bg: {tokens['colors']['lavender_bg']};
  --ink_text: {tokens['colors']['ink_text']};
  --ink_soft: {tokens['colors']['ink_soft']};
  --accent_gold: {tokens['colors']['accent_gold']};
  --evidence_border: {tokens['colors']['evidence_border']};
  --font_stack: {tokens['typography']['font_stack']};
}}

* {{ margin: 0; padding: 0; box-sizing: border-box; }}

#root {{
  width: {WIDTH}px; height: {HEIGHT}px;
  position: relative; overflow: hidden;
  font-family: var(--font_stack);
  color: var(--cream_text); background: var(--maroon_bg);
}}

.scene {{
  width: 100%; height: 100%; position: absolute; top: 0; left: 0;
  display: flex; flex-direction: column;
  align-items: center; justify-content: center; padding: 0 90px;
}}

.scene.hook .hook-title {{
  font-size: {tokens['typography']['title']['size']};
  font-weight: {tokens['typography']['title']['weight']};
  line-height: {tokens['typography']['title']['line_height']};
  text-align: center; color: var(--cream_text);
  max-width: 1100px; margin-bottom: 36px;
}}
.scene.hook .hook-emoji {{ font-size: 60px; }}

.scene.section .section-title,
.scene.body .body-text {{
  font-size: {tokens['typography']['body']['size']};
  font-weight: {tokens['typography']['body']['weight']};
  line-height: {tokens['typography']['body']['line_height']};
}}

.scene.emphasis .emph-text {{
  font-size: {tokens['typography']['body']['size']};
  font-weight: 900; color: var(--maroon_bg);
  text-align: right;
}}

.scene.cta .cta-text {{
  font-size: {tokens['typography']['cta']['size']};
  font-weight: {tokens['typography']['cta']['weight']};
  line-height: {tokens['typography']['cta']['line_height']};
  text-align: center; color: var(--cream_text);
  max-width: 1100px;
}}

.tor-diagram {{ width: 100%; height: 100%; display: block; }}
.packet-lane {{ width: 100%; height: 120px; }}
"""

    def _text_scene_html(self, sc: Scene) -> str:
        dur = f"{sc.duration:.2f}"
        start = f"{sc.start:.2f}"
        if sc.scene_type == "hook":
            return f"""
  <div class="scene hook" data-start="{start}" data-duration="{dur}" data-track-index="1">
    <div class="hook-title">{self._wrap(sc.text, 24)}
       <span class="hook-emoji">😩</span></div>
  </div>"""
        elif sc.scene_type == "emphasis":
            return f"""
  <div class="scene emphasis" data-start="{start}" data-duration="{dur}" data-track-index="2">
    <div class="emph-text">{sc.text}</div>
  </div>"""
        elif sc.scene_type == "cta":
            return f"""
  <div class="scene cta" data-start="{start}" data-duration="{dur}" data-track-index="3">
    <div class="cta-text">{self._wrap(sc.text, 30)}</div>
  </div>"""
        else:  # body / section
            align = "left" if sc.scene_type == "body" else "center"
            cls = "section" if sc.scene_type == "section" else "body"
            return f"""
  <div class="scene {cls}" data-start="{start}" data-duration="{dur}" data-track-index="2">
    <div class="body-text" style="text-align:{align}">{sc.text}</div>
  </div>"""

    def _animation_scene_html(self, sc: Scene, topic: str) -> str:
        dur = f"{sc.duration:.2f}"
        start = f"{sc.start:.2f}"
        svg = tor_flow_svg(WIDTH, HEIGHT)

        evidence_overlay = ""
        if sc.needs_evidence and sc.evidence_sources:
            src_list = "".join(
                f'<div style="margin-top:8px; font-size:20px; color: var(--ink_soft); '
                f'font-weight:500;"><span style="color:var(--maroon_bg);'
                f'font-weight:700;">[{s["platform"].upper()}]</span> '
                f'{s.get("caption", "source")}</div>'
                for s in sc.evidence_sources
            )
            evidence_overlay = f"""
    <div class="evidence-overlay" style="
        position: absolute; bottom: 40px; left: 90px; right: 90px;
        background: rgba(218, 209, 221, 0.95); color: var(--ink_text);
        border-left: 6px solid var(--evidence_border);
        padding: 20px 28px; font-family: var(--font_stack);
        font-size: 24px; line-height: 1.4; border-radius: 0 12px 12px 0;
        backdrop-filter: blur(6px);">
      <div style="font-size: 28px; font-weight: 800; margin-bottom: 12px;
                  color: var(--maroon_bg);">
        EVIDENCE
      </div>
      <div style="font-size: 24px; font-weight: 700; margin-bottom: 10px;">
        {topic.upper()} architecture verified
      </div>
      {src_list}
      <div style="margin-top: 12px; font-size: 20px; font-weight: 500;
                  opacity: 0.7; border-top: 1px solid var(--evidence_border);
                  padding-top: 10px;">
        Sources: {', '.join(s['platform'] for s in sc.evidence_sources)}
      </div>
    </div>"""

        return f"""
  <div class="scene animation" data-start="{start}" data-duration="{dur}" data-track-index="10">
    <div class="animation-wrapper" style="width:100%;height:100%;display:flex;
        align-items:center;justify-content:center;background:var(--maroon_bg);">
      {svg}
    </div>
    {evidence_overlay}
    <div class="anim-caption" style="
        position:absolute; bottom:120px; left:90px; right:90px;
        color: var(--cream_text); font-family: var(--font_stack);
        font-size: 32px; font-weight: 700; text-align: center;
        background: rgba(26,21,21,0.6); padding: 16px 24px;
        border-radius: 12px; backdrop-filter: blur(4px);">
      {topic.upper()} — request path through relays
    </div>
  </div>"""

    def _wrap(self, text: str, max_chars: int = 26) -> str:
        words = text.split()
        lines, cur = [], ""
        for w in words:
            if len(cur) + len(w) + 1 > max_chars and cur:
                lines.append(cur); cur = w
            else:
                cur = (cur + " " + w).strip()
        if cur:
            lines.append(cur)
        return "<br>".join(lines)

    # ── 5. Public build ─────────────────────────────────────────────
    def build(self, script_path: str, topic: Optional[str] = None) -> Tuple[str, BuildReport]:
        segments = self.parse_script(script_path)
        detected_topic, is_technical, queries = self.detect_topic(segments)
        if topic:
            detected_topic = topic

        scenes = self.decompose(segments, detected_topic, is_technical)
        html = self.assemble(scenes, detected_topic, is_technical, queries)

        report = BuildReport(
            total_scenes=len(scenes),
            total_duration=segments[-1]["end"] if segments else 0.0,
            animations_inserted=sum(1 for s in scenes if s.needs_animation),
            evidence_blocks=sum(1 for s in scenes if s.needs_evidence),
            transitions=sum(1 for s in scenes if s.scene_type == "transition"),
            warnings=[w for s in scenes for w in s.warnings],
            search_queries=queries,
        )
        return html, report


def main():
    import argparse
    parser = argparse.ArgumentParser(
        description="Orchestrate a HyperFrames video from a voice script.")
    parser.add_argument("--script", required=True, help="Path to voice script (.txt)")
    parser.add_argument("--topic", default=None, help="Force a topic (e.g. 'Tor')")
    parser.add_argument("--output", default="index.html",
                        help="Output HTML path (default: index.html)")
    parser.add_argument("--wpm", type=int, default=150,
                        help="Words per minute for auto-timing")
    args = parser.parse_args()

    orch = Orchestrator(wpm=args.wpm)
    html, report = orch.build(args.script, topic=args.topic)

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
        print(f"🔍 Search queries generated for: {list(report.search_queries.keys())}")


if __name__ == "__main__":
    main()
