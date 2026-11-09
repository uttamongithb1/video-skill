#!/usr/bin/env python3
"""
Auto-download all required external assets so the skill runs end-to-end
without asking the user for anything.
- Font TTFs from Google Fonts
- Presenter pose PNGs (generated programmatically)
- Music bed MP3 (generated programmatically)
"""
import os
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent

FONTS = {
    "Anton-Regular.ttf": "https://github.com/google/fonts/raw/main/ofl/anton/Anton-Regular.ttf",
    "ArchivoBlack-Regular.ttf": "https://github.com/google/fonts/raw/main/ofl/archivoblack/ArchivoBlack-Regular.ttf",
    "SpaceMono-Regular.ttf": "https://github.com/google/fonts/raw/main/ofl/spacemono/SpaceMono-Regular.ttf",
    "SpaceMono-Bold.ttf": "https://github.com/google/fonts/raw/main/ofl/spacemono/SpaceMono-Bold.ttf",
}

POSES = {
    "p1_shrug.png": "SHRUG",
    "p2_facepalm.png": "FACEPALM",
    "p3_present.png": "PRESENT",
    "p4_chin.png": "CHIN",
    "p5_memory.png": "MEMORY",
    "p6_thumbs.png": "THUMBS",
    "p7_cta.png": "CTA",
    "p8_point.png": "POINT",
    "p9_idea.png": "IDEA",
}

COLORS = ["#6C0013", "#4A001E", "#8B0030", "#A52A4A", "#C04060",
          "#D96070", "#E88080", "#F2A0A0", "#FFC0C0"]


def download_fonts():
    font_dir = ROOT / "assets" / "fonts"
    font_dir.mkdir(parents=True, exist_ok=True)
    import urllib.request
    for name, url in FONTS.items():
        dest = font_dir / name
        if dest.exists():
            print(f"  [skip] {name} already exists")
            continue
        try:
            print(f"  [dl] {name}...")
            urllib.request.urlretrieve(url, str(dest))
            print(f"  [ok] {name} ({dest.stat().st_size} bytes)")
        except Exception as e:
            print(f"  [fail] {name}: {e}")


def generate_presenter_poses():
    pose_dir = ROOT / "assets" / "presenter" / "cut"
    pose_dir.mkdir(parents=True, exist_ok=True)
    for i, (filename, label) in enumerate(POSES.items()):
        dest = pose_dir / filename
        if dest.exists():
            print(f"  [skip] {filename} already exists")
            continue
        img = Image.new("RGBA", (240, 320), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        cx, cy = 120, 140
        r = 60
        color = COLORS[i % len(COLORS)]
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=color, outline="#FFFFFF", width=4)
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 24)
        except Exception:
            font = ImageFont.load_default()
        bbox = draw.textbbox((0, 0), label, font=font)
        tw = bbox[2] - bbox[0]
        draw.text((cx - tw / 2, cy + r + 20), label, font=font, fill=color)
        img.save(str(dest))
        print(f"  [ok] {filename}")


def generate_music_bed():
    import numpy as np
    import wave
    bed_dir = ROOT / "assets" / "music"
    bed_dir.mkdir(parents=True, exist_ok=True)
    dest = bed_dir / "bed.mp3"
    if dest.exists():
        print(f"  [skip] bed.mp3 already exists")
        return

    sample_rate = 44100
    duration = 62
    t = np.linspace(0, duration, int(sample_rate * duration), False)

    drone = 0.05 * np.sin(2 * np.pi * 110 * t) + 0.03 * np.sin(2 * np.pi * 110 * 1.5 * t)

    chords = [
        (220, 329.63, 392.00),
        (174.61, 220, 261.63),
        (130.81, 164.81, 196.00),
        (98.00, 123.47, 146.83),
    ]
    chord_audio = np.zeros_like(t)
    chord_duration = duration / len(chords)
    for i, (f1, f2, f3) in enumerate(chords):
        start = int(i * chord_duration * sample_rate)
        end = min(int((i + 1) * chord_duration * sample_rate), len(t))
        t_seg = t[start:end]
        seg = (0.04 * np.sin(2 * np.pi * f1 * t_seg) +
               0.04 * np.sin(2 * np.pi * f2 * t_seg) +
               0.04 * np.sin(2 * np.pi * f3 * t_seg))
        fade = int(0.5 * sample_rate)
        seg[:fade] *= np.linspace(0, 1, fade)
        seg[-fade:] *= np.linspace(1, 0, fade)
        chord_audio[start:end] += seg

    percussion = np.zeros_like(t)
    bpm = 70
    beat_interval = 60 / bpm
    for beat in np.arange(0, duration, beat_interval):
        idx = int(beat * sample_rate)
        if idx < len(t):
            seg_len = int(0.1 * sample_rate)
            seg = np.exp(-np.linspace(0, 10, seg_len)) * 0.03
            end_idx = min(idx + seg_len, len(t))
            percussion[idx:end_idx] += seg[:end_idx - idx]

    mix = drone + chord_audio + percussion
    mix = mix / np.max(np.abs(mix)) * 0.25
    mix_int = (mix * 32767).astype(np.int16)

    wav_path = bed_dir / "bed_temp.wav"
    with wave.open(str(wav_path), 'w') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(mix_int.tobytes())

    import subprocess
    ffmpeg = ROOT / "tools" / "ffmpeg"
    subprocess.run([str(ffmpeg), "-y", "-i", str(wav_path),
                    "-codec:a", "libmp3lame", "-q:a", "4", str(dest)],
                   capture_output=True)
    wav_path.unlink()
    print(f"  [ok] bed.mp3 ({dest.stat().st_size} bytes)")


def main():
    print("== Auto-downloading/generating assets ==")
    download_fonts()
    generate_presenter_poses()
    generate_music_bed()
    print("== Assets ready ==")


if __name__ == "__main__":
    main()
