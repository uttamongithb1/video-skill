"""
Media Sourcing — Evidence & Internet Media Discovery Interface.

Helps the agent find and cite high-quality evidence for technical explainers:
  • Search query templates per platform (YouTube, Instagram, forums, websites)
  • Evidence card HTML blocks with citation placeholders
  • Media URL placeholders (data-var-src) for HyperFrames variable injection
  • Consistency rules for evidence citation format

The agent is responsible for executing searches and filling in real URLs.
This module generates the *structure* and *search strategy*.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List


@dataclass
class MediaSource:
    platform: str          # youtube | instagram | forum | website | image
    query: str
    url: str = ""          # filled by agent after search
    caption: str = ""
    license_note: str = "Verify rights before use"


@dataclass
class EvidenceBlock:
    timestamp: str         # e.g. "12-18s"
    claim: str             # what the evidence supports
    sources: List[MediaSource]
    html_block: str = ""


# ─── Search query templates per topic category ───────────────────────────
SEARCH_TEMPLATES = {
    "tor": {
        "youtube": [
            "Tor network how it works entry middle exit relay animation",
            "Tor browser anonymous routing explained visual",
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
    """
    Return a dict of platform -> list of search queries for the given topic.
    The agent should run these searches and collect high-quality media URLs.
    """
    templates = SEARCH_TEMPLATES.get(category, SEARCH_TEMPLATES["generic_technical"])
    queries = {}
    for platform, template_list in templates.items():
        queries[platform] = [t.format(topic=topic) for t in template_list]
    return queries


def evidence_card_html(timestamp: str, claim: str, sources: list,
                       design: dict) -> str:
    """
    Generate a HyperFrames-compatible evidence card block.
    sources: list of MediaSource dicts with platform, url, caption.
    """
    bg = design.get("evidence_bg", "var(--lavender_bg)")
    text = design.get("evidence_text", "var(--ink)")
    border = design.get("evidence_border", "var(--evidence_border)")

    source_html = ""
    for s in sources:
        source_html += f"""
    <div class="evidence-source" style="margin-top:12px; font-size:20px;
         color: var(--ink_soft); font-weight:500;">
      <span style="color: var(--maroon_bg); font-weight:700;">[{s['platform'].upper()}]</span>
      {s.get('caption', s.get('url', 'source'))}
    </div>"""

    return f"""
  <div class="scene evidence" data-start="{timestamp.split('-')[0]}"
       data-duration="{_dur(timestamp)}" data-track-index="50">
    <div class="evidence-card" style="
        background: {bg}; color: {text}; border-left: 6px solid {border};
        padding: {design.get('card_padding','40px')}; max-width: 1100px;
        font-family: var(--font_stack);">
      <div class="evidence-claim" style="
          font-size: 40px; font-weight: 700; line-height: 1.35;
          margin-bottom: 24px;">{claim}</div>
      <div class="evidence-media" style="
          margin-bottom: 20px; min-height: 200px;
          background: var(--maroon_near_black);
          display: flex; align-items: center; justify-content: center;
          color: var(--cream_text); font-size: 28px; font-weight: 600;">
        [MEDIA PLACEHOLDER — insert {sources[0]['platform'] if sources else 'image/video'} here]
        <div style="font-size:20px; margin-top:10px; opacity:0.7;">
          data-var-src="{sources[0]['url'] if sources else ''}"
        </div>
      </div>
      {source_html}
      <div class="evidence-cite" style="
          margin-top: 20px; font-size: 20px; font-weight: 500;
          opacity: 0.7; border-top: 1px solid {border}; padding-top: 12px;">
        Sources: {', '.join(s['platform'] for s in sources)}
      </div>
    </div>
  </div>"""


def _dur(timestamp: str) -> float:
    """Parse '12-18s' -> 6.0 duration."""
    try:
        parts = timestamp.replace("s", "").split("-")
        return float(parts[1]) - float(parts[0])
    except Exception:
        return 4.0


def citation_footer(sources: list, design: dict) -> str:
    """Lower-third citation strip for evidence scenes."""
    text = design.get("evidence_text", "var(--ink)")
    return f"""
  <div class="citation-strip" style="
      position: absolute; bottom: 40px; left: 90px; right: 90px;
      background: rgba(26, 21, 21, 0.85); color: {text};
      padding: 14px 24px; font-family: var(--font_stack);
      font-size: 20px; font-weight: 500; border-radius: 8px;
      backdrop-filter: blur(4px);">
    Sources: {' • '.join(s.get('platform','') for s in sources)}
  </div>"""


__all__ = ["MediaSource", "EvidenceBlock", "build_search_queries",
           "evidence_card_html", "citation_footer"]
