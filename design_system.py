"""
Premium Design System — v3.0
============================

Single source of truth for all visual tokens, motion design, and consistency rules
that separate premium short-form videos from medium ones.

Premium pillars:
  1. Kinetic typography — words animate in, not just appear
  2. Depth — glassmorphism, gradients, drop shadows, layering
  3. Motion — easing curves, motion blur, camera moves (Ken Burns)
  4. Audio sync — voiceover timestamps, SFX cues, music bed markers
  5. Safe zones — title-safe + action-safe for 9:16 mobile cropping
"""

from __future__ import annotations

# ─── Premium color palette (measured + elevated) ─────────────────────────
PALETTE = {
    # Brand core
    "maroon": "rgb(108, 0, 19)",
    "maroon_dark": "rgb(60, 0, 12)",
    "cream": "rgb(255, 248, 240)",      # warmer, brighter than source
    "lavender": "rgb(235, 230, 240)",   # lighter, airier
    "ink": "rgb(15, 12, 20)",           # near-black for light mode
    "ink_soft": "rgb(80, 70, 90)",

    # Premium accents
    "gold": "rgb(255, 215, 0)",
    "gold_soft": "rgba(255, 215, 0, 0.15)",
    "cyan": "rgb(90, 200, 255)",
    "cyan_soft": "rgba(90, 200, 255, 0.1)",
    "emerald": "rgb(60, 200, 140)",

    # Glass & depth
    "glass_bg": "rgba(255, 255, 255, 0.65)",
    "glass_dark": "rgba(108, 0, 19, 0.7)",
    "glass_border": "rgba(255, 255, 255, 0.4)",
    "shadow_soft": "0 8px 32px rgba(0,0,0,0.12)",
    "shadow_hard": "0 20px 60px rgba(108, 0, 19, 0.25)",
}

# ─── Motion tokens (premium easing & timing) ─────────────────────────────
MOTION = {
    "ease_premium": "cubic-bezier(0.23, 1, 0.32, 1)",    # smooth, premium feel
    "ease_bounce": "cubic-bezier(0.68, -0.55, 0.27, 1.55)",  # playful pop
    "ease_snap": "cubic-bezier(0.4, 0, 1, 1)",           # quick, crisp
    "fade_in": "0.5s",
    "slide_in": "0.7s",
    "pop_in": "0.45s",
    "ken_burns": "8s",                                   # slow zoom on stills
    "transition_wipe": "0.5s",
    "transition_blur": "0.6s",
    "stagger": "0.12s",                                  # between kinetic words
}

# ─── Typography scale (premium hierarchy) ────────────────────────────────
TYPOGRAPHY = {
    "font_stack": "ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial, sans-serif",
    "font_display": "'Inter var', -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif",
    "hook":      {"size": "80px",  "weight": "950", "line_height": "1.0",  "tracking": "-0.02em"},
    "section":   {"size": "64px",  "weight": "900", "line_height": "1.05", "tracking": "-0.01em"},
    "body":      {"size": "44px",  "weight": "750", "line_height": "1.35", "tracking": "0"},
    "caption":   {"size": "26px",  "weight": "600", "line_height": "1.4",  "tracking": "0.02em"},
    "cta":       {"size": "56px",  "weight": "900", "line_height": "1.2",  "tracking": "-0.01em"},
    "lower_third": {"size": "32px", "weight": "700", "line_height": "1.25", "tracking": "0"},
}

# ─── Layout & safe zones (1280×720 canvas, safe for 9:16 crop) ───────────
LAYOUT = {
    "canvas_w": 1280,
    "canvas_h": 720,
    "fps": 30,
    "page_padding": "100px",
    "section_gap": "70px",
    "card_padding": "48px",
    "line_gap": "28px",
    # 9:16 mobile safe area centered in 16:9
    "safe_x": "160px",     # 12.5% each side
    "safe_y": "140px",     # ~20% top/bottom
    "max_text_width": "960px",
}

# ─── Alignment contract (premium) ────────────────────────────────────────
ALIGNMENT_RULES = {
    "hook":         {"align": "center",  "pos": "top",     "bg": "maroon",  "text": "cream",   "style": "kinetic_pop"},
    "section":      {"align": "center",  "pos": "upper",   "bg": "lavender","text": "ink",     "style": "scale_reveal"},
    "body_left":    {"align": "left",    "pos": "middle",  "bg": "lavender","text": "ink_soft","style": "slide_left"},
    "body_right":   {"align": "right",   "pos": "middle",  "bg": "lavender","text": "maroon",  "weight": "950", "style": "slide_right"},
    "emphasis":     {"align": "right",   "pos": "middle",  "bg": "lavender","text": "maroon",  "weight": "950", "style": "pop_emphasis"},
    "animation":    {"align": "center",  "pos": "middle",  "bg": "maroon",  "text": "cream",   "style": "ken_burns"},
    "evidence":     {"align": "left",    "pos": "lower",   "bg": "glass",   "text": "ink",     "style": "glass_card"},
    "lower_third":  {"align": "left",    "pos": "bottom",  "bg": "glass_dark","text": "cream", "style": "slide_up"},
    "cta":          {"align": "center",  "pos": "bottom",  "bg": "maroon",  "text": "cream",   "style": "scale_reveal"},
    "end_screen":   {"align": "center",  "pos": "middle",  "bg": "maroon",  "text": "cream",   "style": "fade_in"},
}

SCENE_TYPES = {
    "hook":         "Premium title card — kinetic pop-in, centered, authoritative",
    "section":      "Chapter header — scale reveal, centered",
    "body_left":    "Explainer — slide-in from left, reading flow",
    "body_right":   "Punch line — slide-in from right, brand color",
    "emphasis":     "Emphasis word — pop + scale, right-aligned anchor",
    "animation":    "Technical diagram — SVG + Ken Burns camera move",
    "evidence":     "Source card — glassmorphism, citation, media embed",
    "lower_third":  "Speaker/source tag — slide up, bottom left",
    "cta":          "Call to action — scale reveal, bottom center",
    "end_screen":   "End card — fade in, subscribe/cta",
    "transition":   "Motion blur wipe between sections",
}


def premium_css_variables() -> str:
    """Generate the :root CSS variable block."""
    p = PALETTE
    m = MOTION
    t = TYPOGRAPHY
    l = LAYOUT

    return f"""
:root {{
  /* Colors */
  --maroon: {p['maroon']};
  --maroon-dark: {p['maroon_dark']};
  --cream: {p['cream']};
  --lavender: {p['lavender']};
  --ink: {p['ink']};
  --ink-soft: {p['ink_soft']};
  --gold: {p['gold']};
  --gold-soft: {p['gold_soft']};
  --cyan: {p['cyan']};
  --cyan-soft: {p['cyan_soft']};
  --emerald: {p['emerald']};
  --glass-bg: {p['glass_bg']};
  --glass-dark: {p['glass_dark']};
  --glass-border: {p['glass_border']};
  --shadow-soft: {p['shadow_soft']};
  --shadow-hard: {p['shadow_hard']};

  /* Motion */
  --ease-premium: {m['ease_premium']};
  --ease-bounce: {m['ease_bounce']};
  --ease-snap: {m['ease_snap']};
  --fade-in: {m['fade_in']};
  --slide-in: {m['slide_in']};
  --pop-in: {m['pop_in']};
  --ken-burns: {m['ken_burns']};
  --transition-wipe: {m['transition_wipe']};
  --transition-blur: {m['transition_blur']};
  --stagger: {m['stagger']};

  /* Typography */
  --font-stack: {t['font_stack']};
  --font-display: {t['font_display']};

  /* Layout */
  --canvas-w: {l['canvas_w']}px;
  --canvas-h: {l['canvas_h']}px;
  --page-padding: {l['page_padding']};
  --safe-x: {l['safe_x']};
  --safe-y: {l['safe_y']};
  --max-text-width: {l['max_text_width']};
}}
"""


def base_scene_css() -> str:
    """Core scene layout + premium utility classes."""
    return """
* {{ margin: 0; padding: 0; box-sizing: border-box; }}

#root {{
  width: var(--canvas-w);
  height: var(--canvas-h);
  position: relative;
  overflow: hidden;
  font-family: var(--font-display);
  color: var(--cream);
  background: var(--maroon);
}}

/* Safe zone guide (not rendered, just for reference in preview) */
.safe-zone {{
  position: absolute;
  top: var(--safe-y); left: var(--safe-x);
  right: var(--safe-x); bottom: var(--safe-y);
  border: 2px dashed rgba(255,255,255,0.15);
  pointer-events: none;
  z-index: 0;
}}

.scene {{
  width: 100%; height: 100%; position: absolute; top: 0; left: 0;
  display: flex; flex-direction: column;
  align-items: center; justify-content: center;
  padding: var(--page-padding);
  z-index: 1;
}}

.text-safe {{
  max-width: var(--max-text-width);
  text-align: center;
}}

/* Premium utility classes */
.glass-card {{
  background: var(--glass-bg);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid var(--glass-border);
  border-radius: 20px;
  box-shadow: var(--shadow-soft);
}}

.glass-dark-card {{
  background: var(--glass-dark);
  backdrop-filter: blur(24px);
  -webkit-backdrop-filter: blur(24px);
  border: 1px solid var(--glass-border);
  border-radius: 20px;
  box-shadow: var(--shadow-hard);
}}

.gradient-text {{
  background: linear-gradient(135deg, var(--cream) 0%, var(--gold) 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}}

.gold-accent {{
  color: var(--gold);
}}

/* Kinetic typography animations */
@keyframes popIn {{
  0% {{ opacity: 0; transform: scale(0.6) rotate(-2deg); }}
  60% {{ transform: scale(1.1) rotate(1deg); }}
  100% {{ opacity: 1; transform: scale(1) rotate(0); }}
}}

@keyframes slideInLeft {{
  0% {{ opacity: 0; transform: translateX(-40px); }}
  100% {{ opacity: 1; transform: translateX(0); }}
}}

@keyframes slideInRight {{
  0% {{ opacity: 0; transform: translateX(40px); }}
  100% {{ opacity: 1; transform: translateX(0); }}
}}

@keyframes scaleReveal {{
  0% {{ opacity: 0; transform: scale(0.85); }}
  100% {{ opacity: 1; transform: scale(1); }}
}}

@keyframes slideUp {{
  0% {{ opacity: 0; transform: translateY(30px); }}
  100% {{ opacity: 1; transform: translateY(0); }}
}}

@keyframes kenBurns {{
  0% {{ transform: scale(1) translate(0, 0); }}
  100% {{ transform: scale(1.12) translate(20px, -10px); }}
}}

@keyframes motionBlurWipe {{
  0% {{ clip-path: inset(0 100% 0 0); }}
  100% {{ clip-path: inset(0 0 0 0); }}
}}

.word-kinetic {{
  display: inline-block;
  opacity: 0;
  animation: popIn var(--pop-in) var(--ease-premium) forwards;
}}

.word-slide-l {{
  display: inline-block;
  opacity: 0;
  animation: slideInLeft var(--slide-in) var(--ease-premium) forwards;
}}

.word-slide-r {{
  display: inline-block;
  opacity: 0;
  animation: slideInRight var(--slide-in) var(--ease-premium) forwards;
}}

.scene-ken-burns {{
  animation: kenBurns var(--ken-burns) var(--ease-premium) alternate infinite;
}}

.transition-wipe {{
  position: absolute; top: 0; left: 0; width: 100%; height: 100%;
  z-index: 100;
  animation: motionBlurWipe var(--transition-wipe) var(--ease-premium) forwards;
}}
"""


def validate_scene(scene: dict) -> list[str]:
    """Premium validation — stricter than medium."""
    warnings: list[str] = []
    stype = scene.get("type", "body_left")
    dur = scene.get("duration", 0)
    text = scene.get("text", "")

    if stype not in ALIGNMENT_RULES:
        warnings.append(f"Unknown scene type '{stype}', defaulting to 'body_left'")

    if dur < 2.0:
        warnings.append(f"Duration {dur}s too short for premium readability (<2s)")
    if dur > 12:
        warnings.append(f"Duration {dur}s too long (>12s), split for retention")

    # Premium: kinetic text shouldn't be too long per word-group
    if stype in ("hook", "section", "cta") and len(text) > 60:
        warnings.append(f"Hook/CTA text too long ({len(text)} chars) — kinetic type gets crowded")

    if stype in ("body_left", "body_right") and len(text) > 90:
        warnings.append(f"Body text too long ({len(text)} chars) — consider splitting into two scenes")

    # Audio sync check
    if scene.get("audio_cue") and not scene.get("start"):
        warnings.append("Audio cue present but no start timestamp — sync may drift")

    return warnings


__all__ = ["PALETTE", "MOTION", "TYPOGRAPHY", "LAYOUT",
           "ALIGNMENT_RULES", "SCENE_TYPES",
           "premium_css_variables", "base_scene_css", "validate_scene"]
