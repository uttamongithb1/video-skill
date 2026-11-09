"""
Premium Animations — v3.0
==========================

Kinetic typography, SVG technical diagrams with Ken Burns camera moves,
glassmorphism evidence cards, lower thirds, end screens, and motion-blur
transitions. All pure HTML/CSS/SVG for HyperFrames deterministic rendering.
"""

from __future__ import annotations

from design_system import PALETTE, MOTION, TYPOGRAPHY, LAYOUT, ALIGNMENT_RULES

P = PALETTE
M = MOTION
T = TYPOGRAPHY
L = LAYOUT


def kinetic_words(
    text: str,
    style: str = "pop",
    stagger: float = None,
    duration: float = None,
    color: str = None,
) -> str:
    """
    Wrap text in per-word <span> tags with kinetic animation classes.
    style: 'pop' | 'slide-left' | 'slide-right' | 'scale'
    Returns HTML with inline style for animation-delay per word.
    """
    stagger = stagger or M["stagger"]
    dur = duration or M["pop_in"]
    col = color or P["cream"]

    word_cls = {
        "pop": "word-kinetic",
        "slide-left": "word-slide-l",
        "slide-right": "word-slide-r",
        "scale": "word-kinetic",
    }.get(style, "word-kinetic")

    words = text.split()
    spans = []
    for i, w in enumerate(words):
        delay = i * float(stagger.rstrip("s"))
        spans.append(
            f'<span class="{word_cls}" '
            f'style="--d:{dur}; --delay:{delay}s; color:{col};" '
            f'animation-delay="{delay}s">{w}</span>'
        )

    return " ".join(spans)


def kinetic_hook_html(
    text: str,
    emoji: str = "😩",
    duration: float = 4.0,
    start: float = 0.0,
    track: int = 1,
) -> str:
    """Premium hook: kinetic pop-in words + emoji, centered top band."""
    words_html = kinetic_words(text, style="pop", color="var(--cream)")
    return f"""
  <div class="scene hook" data-start="{start:.2f}" data-duration="{duration:.2f}" data-track-index="{track}">
    <div class="text-safe">
      <div style="font-size: {T['hook']['size']}; font-weight: {T['hook']['weight']};
                  line-height: {T['hook']['line_height']}; letter-spacing: {T['hook']['tracking']};
                  text-align: center; margin-bottom: 32px;">
        {words_html}
      </div>
      <div style="font-size: 64px; opacity: 0; animation: popIn 0.6s var(--ease-premium) forwards 1.2s;">
        {emoji}
      </div>
    </div>
  </div>"""


def kinetic_section_html(
    text: str,
    duration: float = 3.0,
    start: float = 0.0,
    track: int = 2,
) -> str:
    """Premium section header: scale reveal, centered."""
    words_html = kinetic_words(text, style="scale", color="var(--ink)")
    return f"""
  <div class="scene section" data-start="{start:.2f}" data-duration="{duration:.2f}" data-track-index="{track}">
    <div class="text-safe" style="color: var(--ink);">
      <div style="font-size: {T['section']['size']}; font-weight: {T['section']['weight']};
                  line-height: {T['section']['line_height']}; letter-spacing: {T['section']['tracking']};
                  text-align: center; animation: scaleReveal 0.7s var(--ease-premium) forwards;">
        {words_html}
      </div>
    </div>
  </div>"""


def body_line_html(
    text: str,
    align: str = "left",
    emphasis_word: str = None,
    duration: float = 3.0,
    start: float = 0.0,
    track: int = 2,
) -> str:
    """
    Premium body line: slide-in from left or right.
    emphasis_word: if provided, that word renders in brand color + weight 950.
    """
    # Build word spans with optional emphasis
    words = text.split()
    spans = []
    for i, w in enumerate(words):
        is_emph = emphasis_word and w.strip(".,!?").lower() == emphasis_word.lower()
        cls = "word-slide-l" if align == "left" else "word-slide-r"
        col = "var(--maroon)" if is_emph else "var(--ink-soft)"
        wt = "950" if is_emph else T["body"]["weight"]
        delay = i * 0.12
        spans.append(
            f'<span class="{cls}" style="--d:0.7s; --delay:{delay}s; color:{col}; '
            f'font-weight:{wt};" animation-delay="{delay}s">{w}</span>'
        )
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


def tor_diagram_html(
    duration: float = 5.0,
    start: float = 0.0,
    track: int = 10,
    topic: str = "Tor",
) -> str:
    """
    Premium TOR diagram: SVG node-link with Ken Burns camera move,
    animated encrypted packet, glass caption overlay.
    """
    w, h = L["canvas_w"], L["canvas_h"]
    cx = [120, 400, 680, 960, 1160]
    cy = 330
    labels = ["USER", "ISP", "ENTRY", "MIDDLE", "EXIT"]
    sub = ["You", "ISP", "Entry Relay", "Middle Relay", "Exit Relay"]
    node_r = 44
    packet_r = 14

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

    return f"""
  <div class="scene animation scene-ken-burns" data-start="{start:.2f}" data-duration="{duration:.2f}" data-track-index="{track}">
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
          <animateMotion path="M {points}" dur="{M['ken_burns']}" repeatCount="indefinite" />
        </circle>
      </svg>
    </div>
    <div class="glass-card" style="
        position: absolute; bottom: 110px; left: 100px; right: 100px;
        color: var(--ink); padding: 24px 32px; max-width: 1080px;
        font-family: var(--font-display); font-size: 30px; font-weight: 800;
        text-align: center; box-shadow: var(--shadow-hard);">
      {topic.upper()} — encrypted path through independent relays
    </div>
  </div>"""


def glass_evidence_card_html(
    timestamp: str,
    claim: str,
    sources: list,
    duration: float = 5.0,
    start: float = 0.0,
    track: int = 50,
) -> str:
    """
    Premium evidence card: glassmorphism, claim + media placeholder +
    source citations with platform badges.
    """
    dur = timestamp.replace("s", "").split("-")
    scene_dur = float(dur[1]) - float(dur[0]) if len(dur) == 2 else duration

    source_badges = "".join(
        f'<span style="display:inline-block; margin-top:10px; font-size:20px; font-weight:600;'
        f' color:var(--maroon); background:var(--gold-soft); padding:6px 14px;'
        f' border-radius:10px; margin-right:8px;">[{s.get("platform","SOURCE").upper()}]'
        f' {s.get("caption","source")}</span>'
        for s in sources
    )

    return f"""
  <div class="scene evidence" data-start="{start:.2f}" data-duration="{scene_dur:.2f}" data-track-index="{track}">
    <div class="glass-card" style="
        position: absolute; bottom: 90px; left: 100px; right: 100px;
        color: var(--ink); padding: 32px 40px; max-width: 1080px;
        font-family: var(--font-display); box-shadow: var(--shadow-hard);">
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
                  border-top: 1px solid var(--glass-border); padding-top: 10px;">
        Verified sources: {', '.join(s.get('platform','') for s in sources)}
      </div>
    </div>
  </div>"""


def lower_third_html(
    label: str,
    value: str,
    duration: float = 4.0,
    start: float = 0.0,
    track: int = 60,
) -> str:
    """Premium lower third: slide-up glass card, bottom left."""
    return f"""
  <div class="scene lower_third" data-start="{start:.2f}" data-duration="{duration:.2f}" data-track-index="{track}">
    <div class="glass-dark-card" style="
        position: absolute; bottom: 70px; left: 100px;
        color: var(--cream); padding: 16px 28px; max-width: 560px;
        font-family: var(--font-display); box-shadow: var(--shadow-hard);">
      <div style="font-size: 22px; font-weight: 700; color: var(--gold); text-transform: uppercase;
                  letter-spacing: 0.05em; margin-bottom: 4px;">{label}</div>
      <div style="font-size: 32px; font-weight: 800; line-height: 1.1;">{value}</div>
    </div>
  </div>"""


def end_screen_html(
    cta_text: str,
    duration: float = 5.0,
    start: float = 0.0,
    track: int = 90,
) -> str:
    """Premium end screen: fade in, centered CTA + subscribe placeholder."""
    return f"""
  <div class="scene end_screen" data-start="{start:.2f}" data-duration="{duration:.2f}" data-track-index="{track}">
    <div class="text-safe">
      <div style="font-size: {T['cta']['size']}; font-weight: {T['cta']['weight']};
                  line-height: {T['cta']['line_height']}; letter-spacing: {T['cta']['tracking']};
                  text-align: center; color: var(--cream); margin-bottom: 32px;
                  animation: scaleReveal 0.8s var(--ease-premium) forwards;">
        {kinetic_words(cta_text, style='scale', color='var(--cream)')}
      </div>
      <div style="font-size: 28px; font-weight: 600; color: var(--gold);
                  animation: popIn 0.6s var(--ease-premium) forwards 1s;">
        Subscribe for more
      </div>
    </div>
  </div>"""


def scene_transition_html(
    kind: str = "wipe",
    duration: float = 0.6,
    start: float = 0.0,
    track: int = 99,
) -> str:
    """Premium transition: motion-blur wipe or blur fade."""
    if kind == "blur":
        return f"""
  <div class="transition-wipe" data-start="{start:.2f}" data-duration="{duration:.2f}" data-track-index="{track}">
    <style>
      .transition-wipe {{
        background: var(--maroon);
        animation: motionBlurWipe {duration}s var(--ease-premium) forwards,
                   blurIn {duration}s var(--ease-premium) forwards;
      }}
      @keyframes blurIn {{
        0% {{ filter: blur(0px); }}
        50% {{ filter: blur(24px); }}
        100% {{ filter: blur(0px); opacity: 0; }}
      }}
    </style>
  </div>"""
    else:  # wipe
        return f"""
  <div class="transition-wipe" data-start="{start:.2f}" data-duration="{duration:.2f}" data-track-index="{track}">
    <style>
      .transition-wipe {{
        background: var(--maroon);
        animation: motionBlurWipe {duration}s var(--ease-premium) forwards;
      }}
    </style>
  </div>"""


__all__ = [
    "kinetic_words", "kinetic_hook_html", "kinetic_section_html",
    "body_line_html", "tor_diagram_html", "glass_evidence_card_html",
    "lower_third_html", "end_screen_html", "scene_transition_html",
]
