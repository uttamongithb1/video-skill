#!/usr/bin/env python3
"""
Self-contained video renderer for the premium skill.
Reads index.html + compositions, renders frames with PIL,
encodes with ffmpeg, mixes audio, produces final MP4.
No Chrome, no Node, no root required.
"""
import re
import sys
import json
import subprocess
import math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
FFMPEG = ROOT / "tools" / "ffmpeg"

# ── Design tokens (mirrors PARAMS.json / prepare.py) ─────────────────────────
W, H = 1080, 1920
FPS = 30

FIELDS = {
    "accent":      {"bg": "#6F0017", "fg": "#EDE3D6"},
    "ink":         {"bg": "#0C0A0B", "fg": "#EDE3D6"},
    "secondary":   {"bg": "#CEDBD1", "fg": "#0C0A0B"},
    "tertiary":    {"bg": "#0A172A", "fg": "#EDE3D6"},
    "quaternary":  {"bg": "#DCD5E1", "fg": "#0C0A0B"},
    "ground":      {"bg": "#EDE3D6", "fg": "#0C0A0B"},
}

TOKENS = {
    "margin_x": 60.5,
    "kicker_top": 128.1,
    "hero_top": 193.2,
    "card_top": 577.9,
    "card_w": 960.0,
    "card_h": 470.4,
    "chip_top": 1128.0,
    "chip_h": 86.0,
    "chip_pad": 38.0,
    "presenter_top": 1217.3,
    "presenter_h": 794.9,
    "presenter_x": 223.6,
    "size_hero": 180,
    "size_kicker": 32.4,
    "size_chip": 36.0,
    "size_body": 28.1,
}

FONT_PATHS = {
    "Anton": ROOT / "assets" / "fonts" / "Anton-Regular.ttf",
    "ArchivoBlack": ROOT / "assets" / "fonts" / "ArchivoBlack-Regular.ttf",
    "SpaceMono": ROOT / "assets" / "fonts" / "SpaceMono-Regular.ttf",
    "SpaceMonoBold": ROOT / "assets" / "fonts" / "SpaceMono-Bold.ttf",
}

_font_cache = {}
def get_font(name, size):
    key = (name, int(size))
    if key not in _font_cache:
        path = FONT_PATHS.get(name, FONT_PATHS["SpaceMono"])
        _font_cache[key] = ImageFont.truetype(str(path), int(size))
    return _font_cache[key]

# ── Parse index.html for scene order & timings ───────────────────────────────
def parse_index(index_path):
    """Return list of (scene_id, start, duration) in order."""
    content = index_path.read_text()
    # Find root duration
    root_match = re.search(r'data-duration="([\d.]+)"', content)
    root_dur = float(root_match.group(1)) if root_match else 60.0

    # Find all scene divs with data-start and data-duration
    # Pattern: <div ... data-composition-id="sX-..." data-start="..." data-duration="...">
    scenes = []
    for m in re.finditer(
        r'data-composition-id="(s\d+-[a-z_]+)"[^>]*\s+data-start="([\d.]+)"\s+data-duration="([\d.]+)"',
        content,
    ):
        scenes.append((m.group(1), float(m.group(2)), float(m.group(3))))

    # Sort by start time
    scenes.sort(key=lambda x: x[1])
    return scenes, root_dur

# ── Parse a composition HTML for content ────────────────────────────────────
def parse_composition(comp_path):
    """Extract scene content from a composition HTML file."""
    content = comp_path.read_text()

    data = {
        "field": "accent",
        "kicker": "",
        "hero": "",
        "chip": "",
        "card_body": "",
        "presenter": None,
        "archetype": "card-led",
    }

    m = re.search(r'<div[^>]*data-composition-id="[^"]*"[^>]*data-field="(\w+)"', content)
    if m:
        data["field"] = m.group(1)
    else:
        # Fallback: try reversed order
        m = re.search(r'data-field="(\w+)"[^>]*data-composition-id="[^"]*"', content)
        if m:
            data["field"] = m.group(1)

    m = re.search(r'id="\w+-kicker">([^<]+)', content)
    if m:
        data["kicker"] = m.group(1)

    m = re.search(r'id="\w+-hero">([^<]+)', content)
    if m:
        data["hero"] = m.group(1)

    m = re.search(r'id="\w+-chip"><b></b>([^<]+)', content)
    if m:
        data["chip"] = m.group(1)

    m = re.search(r'class="f">([^<]+)', content)
    if m:
        data["card_body"] = m.group(1)

    m = re.search(r'src="([^"]+presenter[^"]+)"', content)
    if m:
        data["presenter"] = str(ROOT / m.group(1))

    # Detect archetype
    if 'data-composition-id="\d+-animation"' in content:
        data["archetype"] = "animation"
    elif 'data-composition-id="\d+-cta"' in content:
        data["archetype"] = "cta"
    elif 'data-composition-id="\d+-end_screen"' in content:
        data["archetype"] = "end_screen"

    return data

# ── Text wrapping helper ────────────────────────────────────────────────────
def wrap_text(draw, text, font, max_width):
    """Wrap text to fit within max_width."""
    words = text.split()
    lines = []
    current = ""
    for word in words:
        test = (current + " " + word).strip()
        bbox = draw.textbbox((0, 0), test, font=font)
        if bbox[2] - bbox[0] <= max_width:
            current = test
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines

# ── Render a single frame ───────────────────────────────────────────────────
def render_frame(img, scene, progress):
    """Render one frame of a scene. progress is 0.0 to 1.0 within the scene."""
    draw = ImageDraw.Draw(img)
    field = scene["field"]
    colors = FIELDS[field]
    bg = colors["bg"]
    fg = colors["fg"]

    # Background
    draw.rectangle([0, 0, W, H], fill=bg)

    # Subtle halftone dots
    dot_r = 1
    dot_pitch = 7
    for y in range(0, H, dot_pitch):
        for x in range(0, W, dot_pitch):
            if (x // dot_pitch + y // dot_pitch) % 4 == 0:
                draw.ellipse([x, y, x + dot_r * 2, y + dot_r * 2], fill=fg)

    # Kicker (anchor 1)
    kicker = scene["kicker"]
    if kicker:
        font = get_font("SpaceMonoBold", TOKENS["size_kicker"])
        # Simple fade-in animation
        alpha = min(1.0, progress / 0.15)
        if alpha > 0:
            # Create overlay for alpha
            kicker_img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            kd = ImageDraw.Draw(kicker_img)
            bbox = kd.textbbox((0, 0), kicker, font=font)
            kh = bbox[3] - bbox[1]
            kx = TOKENS["margin_x"]
            ky = TOKENS["kicker_top"]
            # Dash
            dash_w = 46
            dash_h = 5
            kd.rectangle([kx, ky + (kh - dash_h) // 2, kx + dash_w, ky + (kh - dash_h) // 2 + dash_h], fill="#6F0017")
            # Text
            kd.text((kx + dash_w + 18, ky), kicker, font=font, fill=fg + f"{int(255 * alpha):02x}")
            img.alpha_composite(kicker_img)

    # Hero (anchor 2) - large text, up to 2 lines
    hero = scene["hero"]
    if hero:
        font = get_font("Anton", TOKENS["size_hero"])
        max_w = W - 2 * TOKENS["margin_x"] - 40
        lines = wrap_text(draw, hero, font, max_w)
        # Limit to 2 lines
        lines = lines[:2]
        line_h = TOKENS["size_hero"] * 0.88
        start_y = TOKENS["hero_top"]

        # Animation: scale down from 1.3, slide up from 44px
        scale = 1.3 - 0.3 * min(1.0, progress / 0.30)
        y_offset = 44 * (1.0 - min(1.0, progress / 0.30))
        alpha = min(1.0, progress / 0.30)

        for i, line in enumerate(lines):
            line_img = Image.new("RGBA", (W, int(line_h * 1.5)), (0, 0, 0, 0))
            ld = ImageDraw.Draw(line_img)
            bbox = ld.textbbox((0, 0), line, font=font)
            lw = bbox[2] - bbox[0]
            lx = TOKENS["margin_x"]
            ly = int(i * line_h + y_offset)
            ld.text((lx, ly), line, font=font, fill=fg + f"{int(255 * alpha):02x}")
            # Scale
            if scale != 1.0:
                line_img = line_img.resize(
                    (int(line_img.width * scale), int(line_img.height * scale)),
                    Image.LANCZOS,
                )
            img.alpha_composite(line_img, (0, int(start_y + i * line_h)))

    # Card (anchor 3A)
    card_body = scene["card_body"]
    if card_body:
        # Card background
        card_x = TOKENS["margin_x"]
        card_y = TOKENS["card_top"]
        card_w = TOKENS["card_w"]
        card_h = TOKENS["card_h"]

        # Animation: slide up from 56px, scale 0.95→1
        anim_progress = min(1.0, max(0.0, (progress - 0.45) / 0.32))
        card_y_offset = 56 * (1.0 - anim_progress)
        card_scale = 0.95 + 0.05 * anim_progress
        card_alpha = min(1.0, anim_progress)

        # Create card as separate image for scaling
        card_img = Image.new("RGBA", (int(card_w), int(card_h)), (0, 0, 0, 0))
        cd = ImageDraw.Draw(card_img)

        # Card background
        cd.rounded_rectangle([0, 0, card_w, card_h], radius=16, fill="#FFFDF8", outline="#0C0A0B", width=3)

        # Bar at top of card
        bar_h = 62
        cd.rounded_rectangle([0, 0, card_w, bar_h], radius=16, fill="#F1E9DC")
        cd.rectangle([0, bar_h - 3, card_w, bar_h], fill="#0C0A0B")

        # Bar text (left)
        bar_font = get_font("SpaceMonoBold", 28)
        cd.text((24, (bar_h - 28) // 2), card_body[:60], font=bar_font, fill="#16110F")
        # Bar text (right) - label
        cd.text((card_w - 200, (bar_h - 28) // 2), "TOR", font=bar_font, fill="#7A6B60")

        # Body text below bar
        body_font = get_font("SpaceMono", 28)
        body_lines = wrap_text(cd, card_body, body_font, card_w - 48)
        by = bar_h + 24
        for line in body_lines[:6]:  # limit lines
            cd.text((24, by), line, font=body_font, fill="#16110F")
            by += 28 * 1.5

        # Scale card
        if card_scale != 1.0:
            new_w = int(card_img.width * card_scale)
            new_h = int(card_img.height * card_scale)
            card_img = card_img.resize((new_w, new_h), Image.LANCZOS)

        # Alpha
        if card_alpha < 1.0:
            alpha = card_img.split()[-1]
            alpha = alpha.point(lambda p: int(p * card_alpha))
            card_img.putalpha(alpha)

        img.alpha_composite(card_img, (int(card_x), int(card_y + card_y_offset)))

    # Chip (anchor 4)
    chip = scene["chip"]
    if chip:
        chip_x = TOKENS["margin_x"]
        chip_y = TOKENS["chip_top"]
        chip_h = TOKENS["chip_h"]
        chip_pad = TOKENS["chip_pad"]

        # Animation: slide up from 30px
        anim_progress = min(1.0, progress / 0.26)
        chip_y_offset = 30 * (1.0 - anim_progress)
        chip_alpha = min(1.0, anim_progress)

        chip_img = Image.new("RGBA", (W, int(chip_h)), (0, 0, 0, 0))
        cd = ImageDraw.Draw(chip_img)

        # Chip background (rounded pill)
        cd.rounded_rectangle([0, 0, W, chip_h], radius=chip_h // 2, fill="#0C0A0B")
        # Dot
        dot_size = int(chip_h * 0.19)
        cd.ellipse([chip_pad, (chip_h - dot_size) // 2, chip_pad + dot_size, (chip_h + dot_size) // 2], fill="#6F0017")

        # Text
        chip_font = get_font("SpaceMonoBold", TOKENS["size_chip"])
        cd.text((chip_pad * 2 + dot_size, (chip_h - TOKENS["size_chip"]) // 2), chip, font=chip_font, fill="#EDE3D6")

        if chip_alpha < 1.0:
            alpha = chip_img.split()[-1]
            alpha = alpha.point(lambda p: int(p * chip_alpha))
            chip_img.putalpha(alpha)

        img.alpha_composite(chip_img, (0, int(chip_y + chip_y_offset)))

    # Presenter (anchor 5)
    presenter_path = scene["presenter"]
    if presenter_path and Path(presenter_path).exists():
        try:
            pres_img = Image.open(presenter_path).convert("RGBA")
            pres_w = W - TOKENS["presenter_x"]
            pres_h = TOKENS["presenter_h"]
            pres_img = pres_img.resize((int(pres_w), int(pres_h)), Image.LANCZOS)

            # Animation: slide up from 46px, scale 0.92→1
            anim_progress = min(1.0, max(0.0, (progress - 0.34) / 0.34))
            pres_y_offset = 46 * (1.0 - anim_progress)
            pres_scale = 0.92 + 0.08 * anim_progress
            pres_alpha = min(1.0, anim_progress)

            if pres_scale != 1.0:
                new_w = int(pres_w * pres_scale)
                new_h = int(pres_h * pres_scale)
                pres_img = pres_img.resize((new_w, new_h), Image.LANCZOS)

            if pres_alpha < 1.0:
                alpha = pres_img.split()[-1]
                alpha = alpha.point(lambda p: int(p * pres_alpha))
                pres_img.putalpha(alpha)

            img.alpha_composite(pres_img, (int(TOKENS["presenter_x"]), int(TOKENS["presenter_top"] + pres_y_offset)))
        except Exception as e:
            pass  # Skip presenter if image can't be loaded

    # Glow behind presenter
    if progress > 0.30:
        glow_alpha = min(1.0, progress / 0.45)
        glow_size = 699
        glow_x = TOKENS["presenter_x"] - (glow_size - (W - TOKENS["presenter_x"])) // 2
        glow_y = TOKENS["presenter_top"] - (glow_size - TOKENS["presenter_h"]) // 2
        glow_img = Image.new("RGBA", (glow_size, glow_size), (0, 0, 0, 0))
        gd = ImageDraw.Draw(glow_img)
        # Radial gradient approximation
        for r in range(glow_size // 2, 0, -4):
            a = int(255 * 0.20 * glow_alpha * (1.0 - r / (glow_size // 2)))
            gd.ellipse([glow_size // 2 - r, glow_size // 2 - r, glow_size // 2 + r, glow_size // 2 + r],
                       fill=(111, 0, 23, a))
        img.alpha_composite(glow_img, (int(glow_x), int(glow_y)))


# ── Main render ─────────────────────────────────────────────────────────────
def main():
    index_path = ROOT / "index.html"
    if not index_path.exists():
        print("ERROR: index.html not found. Run generate.py first.")
        sys.exit(1)

    scenes, root_dur = parse_index(index_path)
    print(f"Found {len(scenes)} scenes, total duration {root_dur:.2f}s")

    # Load compositions
    comp_dir = ROOT / "compositions"
    scene_data = {}
    for scene_id, start, dur in scenes:
        comp_file = comp_dir / f"{scene_id}.html"
        if comp_file.exists():
            scene_data[scene_id] = parse_composition(comp_file)
        else:
            scene_data[scene_id] = {"field": "accent", "kicker": "", "hero": "", "chip": "", "card_body": "", "presenter": None}

    # Set up ffmpeg pipe for raw video encoding
    ffmpeg_cmd = [
        str(FFMPEG),
        "-y",
        "-f", "rawvideo",
        "-pix_fmt", "rgba",
        "-s", f"{W}x{H}",
        "-r", str(FPS),
        "-i", "-",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-crf", "18",
        "-preset", "fast",
        str(ROOT / "renders" / "raw.mp4"),
    ]

    print("Starting ffmpeg video encoding...")
    proc = subprocess.Popen(ffmpeg_cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE)

    total_frames = int(root_dur * FPS)
    frame_count = 0

    try:
        for scene_id, start, dur in scenes:
            scene = scene_data[scene_id]
            scene_frames = int(dur * FPS)
            print(f"  Rendering {scene_id}: {start:.2f}s–{start + dur:.2f}s ({scene_frames} frames)")

            for i in range(scene_frames):
                progress = i / max(1, scene_frames - 1)
                img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
                render_frame(img, scene, progress)
                proc.stdin.write(img.tobytes())
                frame_count += 1

                if frame_count % 100 == 0:
                    print(f"    {frame_count}/{total_frames} frames...")

    finally:
        proc.stdin.close()
        stderr = proc.stderr.read().decode()
        proc.wait()

    print(f"Video rendered: {frame_count} frames → renders/raw.mp4")
    if stderr:
        print("ffmpeg stderr:", stderr[-500:])


if __name__ == "__main__":
    main()
