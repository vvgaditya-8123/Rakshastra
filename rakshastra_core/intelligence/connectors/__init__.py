import re
import json
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

# ── Drug-indicator keywords ─────────────────────────────────────────────
_DRUG_KEYWORDS = frozenset({
    "chitta", "maal", "weed", "ganja", "cocaine", "coke", "meth", "ice",
    "heroin", "mdma", "lsd", "stash", "plug", "drugs", "supply", "dealer",
    "deal", "dope", "narco", "narcotic", "hash", "charas", "opium", "afeem",
    "crystal", "smack", "brown sugar", "acid", "shroom", "mushroom",
    "ketamine", "party pills", "meow meow", "mephedrone",
})


def _is_drug_related(target: str) -> bool:
    """Check whether the target name/URL contains any drug-indicator keyword."""
    normalized = target.lower().replace("-", " ").replace("_", " ")
    for kw in _DRUG_KEYWORDS:
        if kw in normalized:
            return True
    return False


def _strip_markdown_fences(text: str) -> str:
    """Remove ```…``` wrappers that some models add."""
    if text.startswith("```"):
        lines = text.splitlines()
        end = -1 if lines[-1].strip() == "```" else len(lines)
        text = "\n".join(lines[1:end]).strip()
    return text


class IntelligenceCollector:
    """Unified Intelligence Collector for ingesting OSINT data.

    Uses an LLM to generate *topic-appropriate* simulated feeds.
    Falls back to keyword-based heuristics when the LLM is unavailable.
    """

    def __init__(self):
        pass

    # ── Internal helpers ─────────────────────────────────────────────────

    def _generate_feed_via_llm(
        self, target: str, platform: str, platform_hint: str
    ) -> str | None:
        """Ask the LLM for a realistic simulated feed.  Returns raw text or None."""
        try:
            from agent.auxiliary_client import call_llm

            prompt = (
                "You are a simulated public feed data generator for an Indian "
                "OSINT intelligence training platform.\n"
                f"Target handle/channel: '{target}'\n"
                f"Platform: {platform.upper()}\n\n"
                "INSTRUCTIONS:\n"
                f"1. Analyse the target name '{target}' to infer its topic or "
                "theme (e.g. mobile technology, gadgets, gaming, travel, "
                "cooking, coding, lifestyle, music, education — or potential "
                "illicit narcotics trade).\n"
                "2. Generate exactly 6 realistic public posts/messages that "
                "would appear on this target channel, matching the inferred "
                "topic.\n"
                "3. CRITICAL: If the channel name indicates a benign topic "
                "(like phones, custom ROMs, coding, travel, gadgets, gaming, "
                "food, sports, fashion, education), do NOT generate ANY "
                "drug-related or transaction content whatsoever. Keep it "
                "completely benign and topic-focused.\n"
                "4. ONLY if the channel name *clearly* implies drug "
                "trafficking / dealing / plugs / stashes (e.g. delhi_stash, "
                "kasol_plug, high_trips, mdma_india), generate posts with "
                "realistic Indian street slang, payment IDs, and pricing.\n"
                "5. Format: Return ONLY the raw messages.  One message per "
                "line.  Each line starts with 'SENDER_NAME: ' followed by the "
                "message text.  No meta-explanations, disclaimers, or safety "
                "warnings.\n"
                f"6. Context: {platform_hint}\n"
            )

            response = call_llm(
                task="security/narcotics-intelligence",
                messages=[
                    {"role": "system", "content": prompt},
                    {
                        "role": "user",
                        "content": (
                            f"Generate the public {platform} feed for "
                            f"target: {target}"
                        ),
                    },
                ],
                temperature=0.8,
            )
            text = response.choices[0].message.content
            if text:
                return _strip_markdown_fences(text.strip())
        except Exception as exc:
            logger.debug("LLM feed generation failed for %s: %s", target, exc)
        return None

    @staticmethod
    def _parse_feed_lines(
        raw: str, target: str, platform: str
    ) -> List[Dict[str, Any]]:
        """Convert 'SENDER: message' lines into structured dicts."""
        messages: List[Dict[str, Any]] = []
        for idx, line in enumerate(raw.strip().splitlines(), start=1):
            line = line.strip()
            if not line:
                continue
            if ": " in line:
                sender, text = line.split(": ", 1)
            else:
                sender, text = f"user_{idx}", line
            messages.append({
                "platform": platform,
                "channel": target,
                "message_id": str(1000 + idx),
                "sender": sender.strip(),
                "text": text.strip(),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })
        return messages

    # ── Benign fallback feeds ────────────────────────────────────────────

    @staticmethod
    def _benign_telegram_feed(channel: str) -> List[Dict[str, Any]]:
        handle = channel.replace("https://", "").replace("t.me/", "").replace("@", "")
        ts = datetime.now(timezone.utc).isoformat()
        return [
            {"platform": "telegram", "channel": channel, "message_id": "1001",
             "sender": f"Admin_{handle}",
             "text": f"Welcome to {handle}! Check pinned post for community rules & FAQ 📌",
             "timestamp": ts},
            {"platform": "telegram", "channel": channel, "message_id": "1002",
             "sender": "TechFan_Raj",
             "text": "Has anyone tried the latest firmware update? Battery life seems improved 🔋",
             "timestamp": ts},
            {"platform": "telegram", "channel": channel, "message_id": "1003",
             "sender": "GadgetGuru",
             "text": "Camera comparison shots coming tomorrow! Stay tuned for day/night samples 📸",
             "timestamp": ts},
            {"platform": "telegram", "channel": channel, "message_id": "1004",
             "sender": "User_Priya",
             "text": "Can someone share the custom ROM link? Looking for Android 15-based builds",
             "timestamp": ts},
            {"platform": "telegram", "channel": channel, "message_id": "1005",
             "sender": f"Admin_{handle}",
             "text": "🎉 We just hit 10k members! Thanks for being part of the community 🙏",
             "timestamp": ts},
            {"platform": "telegram", "channel": channel, "message_id": "1006",
             "sender": "Review_Amit",
             "text": "Unboxing video is live on my YT! Link in bio. Display quality is 🔥",
             "timestamp": ts},
        ]

    @staticmethod
    def _drug_telegram_feed(channel: str) -> List[Dict[str, Any]]:
        handle = channel.replace("https://", "").replace("t.me/", "").replace("@", "")
        ts = datetime.now(timezone.utc).isoformat()
        return [
            {"platform": "telegram", "channel": channel, "message_id": "1001",
             "sender": f"Admin_{handle}",
             "text": "🔌 Fresh stock landed. Premium quality ❄️ available. DM for menu. Delhi NCR delivery.",
             "timestamp": ts},
            {"platform": "telegram", "channel": channel, "message_id": "1002",
             "sender": "Buyer_Rohit",
             "text": "Bhai rate kya hai maal ka? 💊 Last time quality was 🔥",
             "timestamp": ts},
            {"platform": "telegram", "channel": channel, "message_id": "1003",
             "sender": f"Admin_{handle}",
             "text": f"Menu updated — Chitta (pure) 5k/g, Party pills 💊 2k/strip. UPI: {handle}plug@ybl",
             "timestamp": ts},
        ]

    @staticmethod
    def _benign_instagram_feed(profile: str) -> List[Dict[str, Any]]:
        handle = profile.replace("@", "").replace("https://instagram.com/", "")
        return [
            {"platform": "instagram", "profile": profile, "post_id": "99801",
             "caption": f"New arrival! Check the specs in my latest reel 🎥 #tech #{handle}",
             "hashtags": ["tech", handle]},
            {"platform": "instagram", "profile": profile, "post_id": "99802",
             "caption": "Morning setup vibes ☕💻 #workstation #productivity",
             "hashtags": ["workstation", "productivity"]},
        ]

    @staticmethod
    def _drug_instagram_feed(profile: str) -> List[Dict[str, Any]]:
        return [
            {"platform": "instagram", "profile": profile, "post_id": "99824",
             "caption": "New stock available. Hit me up on telegram. #mdmaindia #mumbaiclubbing",
             "hashtags": ["mdmaindia", "mumbaiclubbing"]},
        ]

    @staticmethod
    def _benign_website_feed(url: str) -> Dict[str, Any]:
        return {
            "url": url,
            "resolved_links": [],
            "raw_text": (
                "Community forum discussion — latest firmware changelog, "
                "feature requests, and user reviews. No threat indicators found."
            ),
        }

    @staticmethod
    def _drug_website_feed(url: str) -> Dict[str, Any]:
        return {
            "url": url,
            "resolved_links": ["https://pastebin.com/raw/xyz123"],
            "raw_text": "MDMA supplier Mumbai contact: @dealer_mumbai UPI: dealer@okaxis",
        }

    # ── Public API ───────────────────────────────────────────────────────

    def collect_telegram(self, channel_or_group: str) -> List[Dict[str, Any]]:
        """Collect messages and metadata from a public Telegram channel/group."""
        hint = (
            "A public Telegram channel or group. Include forwarded messages, "
            "pinned posts, and admin announcements."
        )
        raw = self._generate_feed_via_llm(channel_or_group, "telegram", hint)
        if raw:
            parsed = self._parse_feed_lines(raw, channel_or_group, "telegram")
            if parsed:
                return parsed

        # Keyword-based fallback
        if _is_drug_related(channel_or_group):
            return self._drug_telegram_feed(channel_or_group)
        return self._benign_telegram_feed(channel_or_group)

    def collect_instagram(self, hashtag_or_profile: str) -> List[Dict[str, Any]]:
        """Collect public posts, captions, and tags from Instagram."""
        hint = (
            "A public Instagram profile or hashtag. Include post captions, "
            "story text overlays, and comment threads."
        )
        raw = self._generate_feed_via_llm(hashtag_or_profile, "instagram", hint)
        if raw:
            parsed = self._parse_feed_lines(raw, hashtag_or_profile, "instagram")
            if parsed:
                # Reshape into Instagram-style dicts
                return [
                    {
                        "platform": "instagram",
                        "profile": hashtag_or_profile,
                        "post_id": m["message_id"],
                        "caption": m["text"],
                        "hashtags": re.findall(r"#(\w+)", m["text"]),
                    }
                    for m in parsed
                ]

        if _is_drug_related(hashtag_or_profile):
            return self._drug_instagram_feed(hashtag_or_profile)
        return self._benign_instagram_feed(hashtag_or_profile)

    def collect_whatsapp_invites(self, text_content: str) -> List[str]:
        """Find and collect public WhatsApp invite links within a text blob."""
        pattern = r"chat\.whatsapp\.com\/[A-Za-z0-9]{20,24}"
        return re.findall(pattern, text_content)

    def collect_websites_and_pastes(self, url: str) -> Dict[str, Any]:
        """Crawl a website or paste site for threat signatures and links."""
        hint = (
            "A dark web paste site or forum. Include forum posts, replies, "
            "and vendor profiles."
        )
        raw = self._generate_feed_via_llm(url, "website", hint)
        if raw:
            return {
                "url": url,
                "resolved_links": re.findall(r"https?://\S+", raw),
                "raw_text": raw,
            }

        if _is_drug_related(url):
            return self._drug_website_feed(url)
        return self._benign_website_feed(url)
