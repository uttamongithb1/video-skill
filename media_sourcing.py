"""
Premium Media Sourcing — v3.0
==============================

Production-ready media pipeline for evidence and B-roll:
  • Per-platform search query templates (YouTube, Instagram, forums, websites, images)
  • yt-dlp download commands for video/audio
  • Image download placeholders
  • Evidence card HTML structure with citation
  • Fair-use / rights verification reminders

The agent executes searches and downloads; this module generates the strategy
and the exact shell commands.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Dict


@dataclass
class MediaSource:
    platform: str          # youtube | instagram | forum | website | image | music
    query: str
    url: str = ""
    caption: str = ""
    license_note: str = "Verify rights / fair use before publishing"
    download_cmd: str = ""


@dataclass
class EvidenceBlock:
    timestamp: str
    claim: str
    sources: List[MediaSource]
    html_block: str = ""


# ─── Premium search query templates ──────────────────────────────────────
SEARCH_TEMPLATES: Dict[str, Dict[str, List[str]]] = {
    "tor": {
        "youtube": [
            "Tor network how it works entry middle exit relay animation",
            "Tor Browser anonymous routing explained visual",
            "Tor Project official architecture diagram",
        ],
        "instagram": [
            "Tor network explained infographic",
            "how Tor relays work animation",
        ],
        "forum": [
            "site:reddit.com/r/tor how Tor entry middle exit relay works",
            "site:torproject.org documentation relay architecture",
        ],
        "website": [
            "https://www.torproject.org/about/ Tor overview",
            "https://2019.www.torproject.org/docs/ Tor documentation",
        ],
        "image": [
            "Tor network diagram entry middle exit relay",
            "Tor circuit animation GIF",
        ],
    },
    "vpn": {
        "youtube": [
            "How VPN works encryption tunnel explained animation",
            "VPN vs proxy vs Tor difference visual",
        ],
        "website": [
            "https://www.eff.org/deeplinks VPN explained",
        ],
        "image": [
            "VPN tunnel encryption diagram",
        ],
    },
    "ai": {
        "youtube": [
            "How large language models work animation",
            "Neural network explained visual",
        ],
        "website": [
            "https://openai.com/ AI overview",
        ],
        "image": [
            "Neural network architecture diagram",
            "Transformer model attention diagram",
        ],
    },
    "generic_technical": {
        "youtube": [
            "{topic} explained animation",
            "{topic} how it works visual guide",
        ],
        "instagram": [
            "{topic} infographic explained",
        ],
        "forum": [
            "site:reddit.com {topic} explained",
            "site:stackoverflow.com {topic} how it works",
        ],
        "website": [
            "{topic} official documentation",
            "{topic} Wikipedia overview",
        ],
        "image": [
            "{topic} diagram infographic",
            "{topic} architecture illustration",
        ],
    },
}


def build_search_queries(topic: str, category: str = "generic_technical") -> dict:
    """Return platform → list of search queries. Agent executes these."""
    templates = SEARCH_TEMPLATES.get(category, SEARCH_TEMPLATES["generic_technical"])
    return {
        platform: [t.format(topic=topic) for t in template_list]
        for platform, template_list in templates.items()
    }


def yt_dlp_command(query: str, output_dir: str = "assets/media") -> str:
    """Generate a yt-dlp command to download the best quality video."""
    return (
        f'yt-dlp -f "bestvideo[height<=1080]+bestaudio/best" '
        f'--merge-output-format mp4 --write-thumbnail --write-sub --sub-lang en '
        f'"ytsearch1:{query}" -o "{output_dir}/%(title)s.%(ext)s"'
    )


def audio_download_command(query: str, output_dir: str = "assets/audio") -> str:
    """Generate a yt-dlp command to download audio only (voiceover/music)."""
    return (
        f'yt-dlp -x --audio-format mp3 --audio-quality 0 '
        f'"ytsearch1:{query}" -o "{output_dir}/%(title)s.%(ext)s"'
    )


def evidence_card_structure(
    timestamp: str,
    claim: str,
    sources: List[dict],
) -> dict:
    """
    Return a structured evidence block dict for the orchestrator.
    Includes the HTML block placeholder and download commands.
    """
    dl_cmds = []
    for s in sources:
        if s.get("platform") == "youtube" and s.get("query"):
            dl_cmds.append(yt_dlp_command(s["query"]))
        elif s.get("platform") == "image" and s.get("query"):
            dl_cmds.append(f'# Image download: {s["query"]}')

    return {
        "timestamp": timestamp,
        "claim": claim,
        "sources": sources,
        "download_commands": dl_cmds,
        "rights_note": "All media must be rights-cleared or fair-use verified before publishing.",
    }


__all__ = [
    "MediaSource", "EvidenceBlock", "build_search_queries",
    "yt_dlp_command", "audio_download_command", "evidence_card_structure",
    "SEARCH_TEMPLATES",
]
