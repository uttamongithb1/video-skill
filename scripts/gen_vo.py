#!/usr/bin/env python3
"""
Auto-generate voiceover MP3s from sections.json using gTTS (Google TTS).
Writes assets/vo/vo1.mp3 … voN.mp3 — no user-provided VO needed.
"""
import json
import sys
from pathlib import Path
from gtts import gTTS

ROOT = Path(__file__).resolve().parent.parent

SECTIONS_FILE = ROOT / "assets" / "vo" / "sections.json"
VO_DIR = ROOT / "assets" / "vo"

# Hinglish works best with Hindi language code; English portions are understood
# by gTTS's Hindi model well enough for short code-mixed phrases.
LANG = "hi"


def main():
    if not SECTIONS_FILE.exists():
        print(f"ERROR: {SECTIONS_FILE} not found")
        sys.exit(1)

    data = json.loads(SECTIONS_FILE.read_text())
    sections = data["sections"]
    VO_DIR.mkdir(parents=True, exist_ok=True)

    for i, section in enumerate(sections, start=1):
        vo_file = VO_DIR / f"vo{i}.mp3"
        if vo_file.exists():
            print(f"  [skip] vo{i}.mp3 already exists")
            continue
        text = section["say"]
        print(f"  [tts] vo{i}: {text[:60]}...")
        tts = gTTS(text=text, lang=LANG, slow=False)
        tts.save(str(vo_file))
        print(f"  [ok] vo{i}.mp3")

    print("== VO ready ==")


if __name__ == "__main__":
    main()
