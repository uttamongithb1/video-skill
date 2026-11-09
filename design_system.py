"""
Design System — Resume-Reject / Technical Explainer Video Skill
================================================================

Single source of truth for all visual tokens extracted from the source video
analysis, plus consistency rules that keep every generated video on-brand.

Tokens:
  • Colors: maroon / lavender high-contrast pair (measured from frames)
  • Typography: bold sans-serif scale (title 68px → body 40px → caption 24px)
  • Spacing: page padding, section gaps, line heights
  • Animation: easing, durations, FPS
  • Alignment rules: center title, left body, right emphasis

Usage:
    from design_system import DESIGN_TOKENS, validate_scene, get_scene_css
"""

from __future__ import annotations

# ─── Measured from source video frames ───────────────────────────────────
DESIGN_TOKENS = {
    "resolution": {"width": 1280, "height": 720, "fps": 30},
    "colors": {
        "maroon_bg": "rgb(108, 0, 19)",
        "maroon_near_black": "rgb(26, 21, 21)",
        "cream_text": "rgb(232, 219, 209)",
        "lavender_bg": "rgb(218, 209, 221)",
        "ink_text": "rgb(20, 18, 22)",
        "ink_soft": "rgb(60, 50, 55)",
        "accent_gold": "rgb(255, 215, 0)",      # packet / highlight accent
        "evidence_border": "rgb(108, 0, 19)",
    },
    "typography": {
        "font_stack": "ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial, sans-serif",
        "title": {"size": "68px", "weight": "900", "line_height": "1.05"},
        "section": {"size": "56px", "weight": "800", "line_height": "1.1"},
        "body": {"size": "40px", "weight": "700", "line_height": "1.35"},
        "caption": {"size": "24px", "weight": "500", "line_height": "1.4"},
        "cta": {"size": "50px", "weight": "800", "line_height": "1.25"},
    },
    "spacing": {
        "page_padding": "90px",
        "section_gap": "60px",
        "card_padding": "40px",
        "line_gap": "24px",
    },
    "animation": {
        "ease": "cubic-bezier(0.4, 0, 0.2, 1)",
        "fade_duration": "0.6s",
        "slide_duration": "0.8s",
        "packet_duration": "2.5s",
    },
}

# ─── Alignment contract (reverse-engineered from frames) ─────────────────
ALIGNMENT_RULES = {
    "hook":        {"align": "center",  "position": "top",    "bg": "maroon",  "text": "cream"},
    "section":     {"align": "center",  "position": "upper",  "bg": "lavender","text": "ink"},
    "body":        {"align": "left",    "position": "middle", "bg": "lavender","text": "ink_soft"},
    "body_left":   {"align": "left",    "position": "middle", "bg": "lavender","text": "ink_soft"},
    "body_right":  {"align": "right",   "position": "middle", "bg": "lavender","text": "maroon", "weight": "900"},
    "emphasis":    {"align": "right",   "position": "middle", "bg": "lavender","text": "maroon", "weight": "900"},
    "animation":   {"align": "center",  "position": "middle", "bg": "maroon",  "text": "cream"},
    "evidence":    {"align": "left",    "position": "lower",  "bg": "lavender","text": "ink",   "caption": True},
    "cta":         {"align": "center",  "position": "bottom", "bg": "maroon",  "text": "cream"},
}

# ─── Scene types ─────────────────────────────────────────────────────────
SCENE_TYPES = {
    "hook":        "Dark maroon title card — centered, authoritative",
    "section":     "Light section header — centered, chapter-like",
    "body":        "Explainer line — left-aligned for reading flow",
    "emphasis":    "Punch word — right-aligned, brand maroon, weight 900",
    "animation":   "Technical diagram — SVG + CSS animated packet/flow",
    "evidence":    "Source card — left-aligned, caption, citation footer",
    "cta":         "Dark call-to-action — centered, bottom",
    "transition":  "Full-screen wipe/fade between major sections",
}


def scene_css(scene_type: str) -> str:
    """Return inline CSS class block for a given scene type."""
    rules = ALIGNMENT_RULES[scene_type]
    tokens = DESIGN_TOKENS
    bg_var = f"--{rules['bg']}_bg"
    text_var = f"--{rules['text']}"
    weight = rules.get("weight", DESIGN_TOKENS["typography"]["body"]["weight"])
    align = rules["align"]

    return f"""
.scene-{scene_type} {{
  background: var({bg_var});
  color: var({text_var});
  text-align: {align};
  font-weight: {weight};
}}
"""


def validate_scene(scene: dict) -> list[str]:
    """Validate a scene dict against the design contract. Returns list of warnings."""
    warnings: list[str] = []
    stype = scene.get("type", "body")
    if stype not in ALIGNMENT_RULES:
        warnings.append(f"Unknown scene type '{stype}', defaulting to 'body'")
    dur = scene.get("duration", 0)
    if dur < 1.5:
        warnings.append(f"Scene duration {dur}s is very short (<1.5s), may be unreadable")
    if dur > 10:
        warnings.append(f"Scene duration {dur}s is long (>10s), consider splitting")
    text = scene.get("text", "")
    if len(text) > 120 and stype in ("body", "emphasis"):
        warnings.append(f"Text too long for {stype} ({len(text)} chars), may overflow")
    return warnings


__all__ = ["DESIGN_TOKENS", "ALIGNMENT_RULES", "SCENE_TYPES", "scene_css", "validate_scene"]
