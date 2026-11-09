"""
Animation Authoring — SVG + CSS motion components for technical explainers.

Generates HyperFrames-compatible HTML blocks for animated diagrams such as:
  • TOR request flow (User → ISP → Entry → Middle → Exit → Website)
  • Packet hop animation (moving dot along a path)
  • Node-link network diagrams
  • Scene transitions (fade / slide wipes)

All output is pure HTML/CSS/SVG — HyperFrames renders it through headless Chrome
+ FFmpeg deterministically.
"""

from __future__ import annotations

from design_system import DESIGN_TOKENS, ALIGNMENT_RULES

TOKENS = DESIGN_TOKENS


def tor_flow_svg(width: int = 1280, height: int = 720) -> str:
    """
    SVG diagram of the TOR network path.
    Nodes: User -> ISP -> Entry Relay -> Middle Relay -> Exit Relay.
    A CSS-animated packet travels along the path.
    """
    cx = [100, 380, 660, 940, 1180]
    cy = 360
    labels = ["USER", "ISP", "ENTRY", "MIDDLE", "EXIT"]
    node_r = 42
    packet_r = 14
    pdur = TOKENS["animation"]["packet_duration"]
    ease = TOKENS["animation"]["ease"]

    points = " ".join(f"{cx[i]},{cy}" for i in range(5))
    circles = "".join(
        f'<circle cx="{cx[i]}" cy="{cy}" r="{node_r}" class="node-circle" />'
        for i in range(5)
    )
    labels_html = "".join(
        f'<text x="{cx[i]}" y="{cy + 7}" class="node-label">{labels[i]}</text>'
        for i in range(5)
    )
    sub_labels = "".join(
        f'<text x="{cx[i]}" y="{cy + 40}" class="node-label" '
        f'style="font-size:16px; font-weight:600; opacity:0.85">'
        f'{["You", "ISP", "Entry Relay", "Middle Relay", "Exit Relay"][i]}</text>'
        for i in range(5)
    )

    svg = f"""<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}"
     xmlns="http://www.w3.org/2000/svg" class="tor-diagram">
  <defs>
    <marker id="arrowhead" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto">
      <polygon fill="var(--cream_text)" points="0 0, 10 3.5, 0 7" />
    </marker>
    <style>
      .node-circle {{ fill: var(--maroon_bg); stroke: var(--cream_text); stroke-width: 3; }}
      .node-label {{ fill: var(--cream_text); font-family: var(--font_stack);
                     font-weight: 900; font-size: 20px; text-anchor: middle; }}
      .line {{ stroke: var(--cream_text); stroke-width: 3; fill: none; }}
      .packet {{ fill: var(--accent_gold); stroke: var(--maroon_bg); stroke-width: 2; }}
      .path-line {{ stroke: var(--ink_soft); stroke-width: 2;
                    stroke-dasharray: 8 4; opacity: 0.6; }}
      @keyframes movePacket {{
        0%   {{ offset-distance: 0%; }}
        100% {{ offset-distance: 100%; }}
      }}
      #packet {{
        animation: movePacket {pdur} {ease} infinite alternate;
      }}
    </style>
  </defs>

  <!-- Connection path -->
  <polyline points="{points}" class="path-line" />

  <!-- Nodes -->
  {circles}
  {labels_html}
  {sub_labels}

  <!-- Animated packet -->
  <circle id="packet" cx="{cx[0]}" cy="{cy}" r="{packet_r}" class="packet">
    <animateMotion path="M {points}"
                   dur="{pdur}" repeatCount="indefinite" />
  </circle>
</svg>"""
    return svg


def packet_hop_animation(start: tuple, end: tuple, duration: float = 2.0,
                         label: str = "encrypted packet") -> str:
    """CSS-animated single packet moving from start to end coordinates."""
    sx, sy = start
    ex, ey = end
    mx, my = (sx + ex) / 2, sy - 20
    return f"""
<div class="packet-lane" style="position:relative; width:100%; height:120px;">
  <svg width="100%" height="120">
    <line x1="{sx}" y1="{sy}" x2="{ex}" y2="{ey}" class="line" />
    <circle cx="{sx}" cy="{sy}" r="12" class="packet">
      <animateMotion path="M {sx},{sy} L {ex},{ey}" dur="{duration}s"
                     repeatCount="indefinite" />
    </circle>
    <text x="{mx}" y="{my}" fill="var(--cream_text)"
          font-family="var(--font_stack)" font-weight="700" font-size="20px"
          text-anchor="middle">{label}</text>
  </svg>
</div>"""


def scene_transition(kind: str = "fade", duration: float = 0.6,
                     direction: str = "left") -> str:
    """
    Generate a full-screen transition overlay block.
    kind: 'fade' | 'slide' | 'wipe'
    """
    fade = TOKENS["animation"]["fade_duration"]
    slide = TOKENS["animation"]["slide_duration"]
    ease = TOKENS["animation"]["ease"]
    dur = duration if duration else (fade if kind == "fade" else slide)

    if kind == "fade":
        return f"""
<div class="transition transition-fade" data-start="0" data-duration="{dur}"
     data-track-index="99">
  <style>
    .transition-fade {{
      position: absolute; top: 0; left: 0; width: 100%; height: 100%;
      background: var(--maroon_bg); z-index: 100;
      animation: fadeOut {dur}s {ease} forwards;
    }}
    @keyframes fadeOut {{ to {{ opacity: 0; }} }}
  </style>
</div>"""
    elif kind == "slide":
        off = "-100%" if direction == "left" else "100%"
        return f"""
<div class="transition transition-slide" data-start="0" data-duration="{dur}"
     data-track-index="99">
  <style>
    .transition-slide {{
      position: absolute; top: 0; left: {off}; width: 100%; height: 100%;
      background: var(--lavender_bg); z-index: 100;
      animation: slide {dur}s {ease} forwards;
    }}
    @keyframes slide {{ to {{ left: 0%; }} }}
  </style>
</div>"""
    else:  # wipe
        return f"""
<div class="transition transition-wipe" data-start="0" data-duration="{dur}"
     data-track-index="99">
  <style>
    .transition-wipe {{
      position: absolute; top: 0; left: 0; width: 0%; height: 100%;
      background: var(--maroon_bg); z-index: 100;
      animation: wipe {dur}s {ease} forwards;
    }}
    @keyframes wipe {{ to {{ width: 100%; }} }}
  </style>
</div>"""


__all__ = ["tor_flow_svg", "packet_hop_animation", "scene_transition"]
