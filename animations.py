"""
Premium Animations — v3.2 (FIXED)
==================================

Self-contained inline styles so every kinetic word actually staggers.
No invalid HTML attributes. SVG packet duration matched to scene.
TOR diagram can include evidence overlay inside the same scene.
"""

from __future__ import annotations

from design_system import PALETTE, MOTION, TYPOGRAPHY, LAYOUT

P = PALETTE
M = MOTION
T = TYPOGRAPHY
L = LAYOUT


def _word_span(word: str, delay_s: float, dur_s: float, color: str,
               weight: str = "750", style_name: str = "pop") -> str:
    """Single <span> with complete inline animation."""
    if style_name == "pop":
        anim = f"popIn {dur_s}s {M['ease_premium']} forwards {delay_s}s"
    elif style_name == "slide-left":
        anim = f"slideInLeft {dur_s}s {M['ease_premium']} forwards {delay_s}s"
    elif style_name == "slide-right":
        anim = f"slideInRight {dur_s}s {M['ease_premium']} forwards {delay_s}s"
    else:
        anim = f"scaleReveal {dur_s}s {M['ease_premium']} forwards {delay_s}s"

    return (
        f'<span style="display:inline-block; opacity:0; animation:{anim}; '
        f'color:{color}; font-weight:{weight};">{word}</span>'
    )


def kinetic_words(text: str, style: str = "pop", stagger: float = 0.12,
                  duration: float = 0.45, color: str = None,
                  weight: str = "750") -> str:
    """Per-word spans, each with its own inline animation-delay — true kinetic type."""
    color = color or P["cream"]
    words = text.split()
    return " ".join(
        _word_span(w, i * stagger, duration, color, weight, style)
        for i, w in enumerate(words)
    )


def kinetic_hook_html(text: str, emoji: str = "😩", duration: float = 4.0,
                      start: float = 0.0, track: int = 1) -> str:
    """Premium hook: kinetic pop-in words + emoji, centered top band."""
    words_html = kinetic_words(text, style="pop", duration=0.45, color="var(--cream)")
    return f"""
  <div class="scene hook" data-start="{start:.2f}" data-duration="{duration:.2f}" data-track-index="{track}">
    <div class="text-safe">
      <div style="font-size: {T['hook']['size']}; font-weight: {T['hook']['weight']};
                  line-height: {T['hook']['line_height']}; letter-spacing: {T['hook']['tracking']};
                  text-align: center; margin-bottom: 32px;">
        {words_html}
      </div>
      <div style="font-size: 64px; opacity:0; animation:popIn 0.6s {M['ease_premium']} forwards 1.2s;">
        {emoji}
      </div>
    </div>
  </div>"""


def kinetic_section_html(text: str, duration: float = 3.0,
                         start: float = 0.0, track: int = 2) -> str:
    """Premium section header: scale reveal, centered."""
    words_html = kinetic_words(text, style="scale", duration=0.5, color="var(--ink)")
    return f"""
  <div class="scene section" data-start="{start:.2f}" data-duration="{duration:.2f}" data-track-index="{track}">
    <div class="text-safe" style="color: var(--ink);">
      <div style="font-size: {T['section']['size']}; font-weight: {T['section']['weight']};
                  line-height: {T['section']['line_height']}; letter-spacing: {T['section']['tracking']};
                  text-align: center;">
        {words_html}
      </div>
    </div>
  </div>"""


def body_line_html(text: str, align: str = "left", emphasis_word: str = None,
                   duration: float = 3.0, start: float = 0.0,
                   track: int = 2) -> str:
    """Premium body line: slide-in from left or right. Emphasis word in brand color."""
    words = text.split()
    spans = []
    for i, w in enumerate(words):
        is_emph = emphasis_word and w.strip(".,!?").lower() == emphasis_word.lower()
        style_name = "slide-left" if align == "left" else "slide-right"
        col = "var(--maroon)" if is_emph else "var(--ink-soft)"
        wt = "950" if is_emph else T["body"]["weight"]
        spans.append(_word_span(w, i * 0.12, 0.6, col, wt, style_name))
    words_html = " ".join(spans)

    side_class = "body_left" if align == "left" else "body_right"
    text_align = "left" if align == "left" else "right"

    return f"""
  <div class="scene {side_class}" data-start="{start:.2f}" data-duration="{duration:.2f}" data-track-index="{track}">
    <div style="max-width: {L['max_text_width']}; text-align: {text_align};">
      <div style="font-size: {T['body']['size']}; font-weight: {T['body']['weight']};
                  line-height: {T['body']['line_height']}; letter-spacing: {T['body']['tracking']};">
        {words_html}
      </div>
    </div>
  </div>"""


def _evidence_overlay_html(topic: str, evidence_sources: list) -> str:
    """Glassmorphism evidence card rendered inside the animation scene."""
    badges = "".join(
        f'<span style="display:inline-block; margin-top:10px; font-size:20px; font-weight:600;'
        f' color:var(--maroon); background:rgba(255,215,0,0.15); padding:6px 14px;'
        f' border-radius:10px; margin-right:8px;">[{s.get("platform","SOURCE").upper()}]'
        f' {s.get("caption","source")}</span>'
        for s in evidence_sources
    )
    return f'''
    <div style="
        position: absolute; bottom: 110px; left: 100px; right: 100px;
        background: rgba(255,255,255,0.65); backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border: 1px solid rgba(255,255,255,0.4); border-radius: 20px;
        color: var(--ink); padding: 24px 32px; max-width: 1080px;
        font-family: var(--font-display); font-size: 30px; font-weight: 800;
        text-align: center; box-shadow: 0 20px 60px rgba(108,0,19,0.25);
        animation: slideUp 0.7s {M['ease_premium']} forwards 0.3s; opacity: 0;">
      <div style="font-size: 30px; font-weight: 800; margin-bottom: 12px;
                  border-left: 5px solid var(--maroon); padding-left: 16px;">
        {topic.upper()} — verified architecture
      </div>
      <div style="font-size: 24px; font-weight: 600; margin-bottom: 10px;">EVIDENCE</div>
      <div style="display: flex; flex-wrap: wrap; gap: 8px; margin-top: 14px;">
        {badges}
      </div>
      <div style="margin-top: 14px; font-size: 20px; font-weight: 600; opacity: 0.7;
                  border-top: 1px solid rgba(255,255,255,0.4); padding-top: 10px;">
        Sources: {', '.join(s.get('platform','') for s in evidence_sources)}
      </div>
    </div>'''


def tor_diagram_html(duration: float = 5.0, start: float = 0.0,
                     track: int = 10, topic: str = "Tor",
                     evidence_sources: list = None) -> str:
    """
    Premium TOR diagram: SVG node-link + Ken Burns + animated packet.
    Optionally includes evidence overlay inside the same scene.
    """
    w, h = L["canvas_w"], L["canvas_h"]
    cx = [120, 400, 680, 960, 1160]
    cy = 330
    labels = ["USER", "ISP", "ENTRY", "MIDDLE", "EXIT"]
    sub = ["You", "ISP", "Entry Relay", "Middle Relay", "Exit Relay"]
    node_r = 44
    packet_r = 14
    pkt_dur = min(duration, 4.0)

    points = " ".join(f"{cx[i]},{cy}" for i in range(5))
    circles = "".join(
        f'<circle cx="{cx[i]}" cy="{cy}" r="{node_r}" class="node-circle" />'
        for i in range(5)
    )
    labels_html = "".join(
        f'<text x="{cx[i]}" y="{cy+7}" class="node-label">{labels[i]}</text>'
        for i in range(5)
    )
    sub_html = "".join(
        f'<text x="{cx[i]}" y="{cy+42}" class="node-sub">{sub[i]}</text>'
        for i in range(5)
    )

    evidence_overlay = _evidence_overlay_html(topic, evidence_sources) if evidence_sources else ""

    return f"""
  <div class="scene animation" data-start="{start:.2f}" data-duration="{duration:.2f}" data-track-index="{track}">
    <div class="animation-wrapper" style="width:100%;height:100%;display:flex;
        align-items:center;justify-content:center;background:var(--maroon);overflow:hidden;">
      <svg width="{w}" height="{h}" viewBox="0 0 {w} {h}" xmlns="http://www.w3.org/2000/svg"
           class="tor-diagram">
        <defs>
          <marker id="arrowhead" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto">
            <polygon fill="var(--cream)" points="0 0, 10 3.5, 0 7" />
          </marker>
          <style>
            .node-circle {{ fill: var(--maroon-dark); stroke: var(--cream); stroke-width: 3; }}
            .node-label {{ fill: var(--cream); font-family: var(--font-display);
                           font-weight: 950; font-size: 20px; text-anchor: middle; }}
            .node-sub {{ fill: var(--gold); font-family: var(--font-display);
                         font-weight: 700; font-size: 15px; text-anchor: middle; opacity: 0.9; }}
            .path-line {{ stroke: var(--ink-soft); stroke-width: 2;
                          stroke-dasharray: 10 6; opacity: 0.5; }}
            .packet {{ fill: var(--gold); stroke: var(--maroon-dark); stroke-width: 2;
                       filter: drop-shadow(0 4px 8px rgba(255,215,0,0.4)); }}
          </style>
        </defs>
        <polyline points="{points}" class="path-line" />
        {circles}
        {labels_html}
        {sub_html}
        <circle class="packet" cx="{cx[0]}" cy="{cy}" r="{packet_r}">
          <animateMotion path="M {points}" dur="{pkt_dur}s" repeatCount="indefinite" />
        </circle>
      </svg>
    </div>
    {evidence_overlay}
  </div>"""


def glass_evidence_card_html(timestamp: str, claim: str, sources: list,
                             duration: float = 5.0, start: float = 0.0,
                             track: int = 50) -> str:
    """Standalone premium evidence card (glassmorphism + citations)."""
    dur_parts = timestamp.replace("s", "").split("-")
    scene_dur = float(dur_parts[1]) - float(dur_parts[0]) if len(dur_parts) == 2 else duration

    source_badges = "".join(
        f'<span style="display:inline-block; margin-top:10px; font-size:20px; font-weight:600;'
        f' color:var(--maroon); background:rgba(255,215,0,0.15); padding:6px 14px;'
        f' border-radius:10px; margin-right:8px;">[{s.get("platform","SOURCE").upper()}]'
        f' {s.get("caption","source")}</span>'
        for s in sources
    )

    return f"""
  <div class="scene evidence" data-start="{start:.2f}" data-duration="{scene_dur:.2f}" data-track-index="{track}">
    <div style="position: absolute; bottom: 90px; left: 100px; right: 100px;
                background: rgba(255,255,255,0.65); backdrop-filter: blur(20px);
                -webkit-backdrop-filter: blur(20px);
                border: 1px solid rgba(255,255,255,0.4); border-radius: 20px;
                color: var(--ink); padding: 32px 40px; max-width: 1080px;
                font-family: var(--font-display);
                box-shadow: 0 20px 60px rgba(108,0,19,0.25);
                animation: slideUp 0.7s {M['ease_premium']} forwards 0.2s; opacity: 0;">
      <div style="font-size: {T['lower_third']['size']}; font-weight: {T['lower_third']['weight']};
                  line-height: {T['lower_third']['line_height']}; margin-bottom: 18px;
                  border-left: 5px solid var(--maroon); padding-left: 16px;">
        {claim}
      </div>
      <div style="height: 150px; background: var(--maroon-dark); border-radius: 16px;
                  display: flex; align-items: center; justify-content: center;
                  margin: 20px 0; color: var(--cream); font-size: 24px; font-weight: 700;
                  opacity: 0.85;">
        [PREMIUM MEDIA — insert {sources[0].get('platform','image/video') if sources else 'asset'} here]
        <div style="font-size:18px; margin-top:8px; opacity:0.6;">
          data-var-src="{sources[0].get('url','') if sources else ''}"
        </div>
      </div>
      <div style="display: flex; flex-wrap: wrap; gap: 8px; margin-top: 14px;">
        {source_badges}
      </div>
      <div style="margin-top: 14px; font-size: 20px; font-weight: 600; opacity: 0.7;
                  border-top: 1px solid rgba(255,255,255,0.4); padding-top: 10px;">
        Verified sources: {', '.join(s.get('platform','') for s in sources)}
      </div>
    </div>
  </div>"""


def lower_third_html(label: str, value: str, duration: float = 4.0,
                     start: float = 0.0, track: int = 60) -> str:
    """Premium lower third: slide-up glass card, bottom left."""
    return f"""
  <div class="scene lower_third" data-start="{start:.2f}" data-duration="{duration:.2f}" data-track-index="{track}">
    <div style="position: absolute; bottom: 70px; left: 100px;
                background: rgba(108,0,19,0.7); backdrop-filter: blur(24px);
                -webkit-backdrop-filter: blur(24px);
                border: 1px solid rgba(255,255,255,0.4); border-radius: 20px;
                color: var(--cream); padding: 16px 28px; max-width: 560px;
                font-family: var(--font-display);
                box-shadow: 0 20px 60px rgba(108,0,19,0.25);
                animation: slideUp 0.7s {M['ease_premium']} forwards 0.2s; opacity: 0;">
      <div style="font-size: 22px; font-weight: 700; color: var(--gold); text-transform: uppercase;
                  letter-spacing: 0.05em; margin-bottom: 4px;">{label}</div>
      <div style="font-size: 32px; font-weight: 800; line-height: 1.1;">{value}</div>
    </div>
  </div>"""


def end_screen_html(cta_text: str, duration: float = 5.0,
                    start: float = 0.0, track: int = 90) -> str:
    """Premium end screen: fade in, centered CTA + subscribe placeholder."""
    words_html = kinetic_words(cta_text, style="scale", duration=0.5, color="var(--cream)")
    return f"""
  <div class="scene end_screen" data-start="{start:.2f}" data-duration="{duration:.2f}" data-track-index="{track}">
    <div class="text-safe">
      <div style="font-size: {T['cta']['size']}; font-weight: {T['cta']['weight']};
                  line-height: {T['cta']['line_height']}; letter-spacing: {T['cta']['tracking']};
                  text-align: center; color: var(--cream); margin-bottom: 32px;">
        {words_html}
      </div>
      <div style="font-size: 28px; font-weight: 600; color: var(--gold);
                  opacity:0; animation:popIn 0.6s {M['ease_premium']} forwards 1s;">
        Subscribe for more
      </div>
    </div>
  </div>"""


def scene_transition_html(kind: str = "wipe", duration: float = 0.6,
                          start: float = 0.0, track: int = 99) -> str:
    """Premium transition: motion-blur wipe."""
    return f"""
  <div class="scene transition" data-start="{start:.2f}" data-duration="{duration:.2f}" data-track-index="{track}">
    <div style="position: absolute; top: 0; left: 0; width: 100%; height: 100%;
                background: var(--maroon); z-index: 100;
                animation: motionBlurWipe {duration}s {M['ease_premium']} forwards;"></div>
  </div>"""


__all__ = [
    "kinetic_words", "kinetic_hook_html", "kinetic_section_html",
    "body_line_html", "tor_diagram_html", "glass_evidence_card_html",
    "lower_third_html", "end_screen_html", "scene_transition_html",
]
