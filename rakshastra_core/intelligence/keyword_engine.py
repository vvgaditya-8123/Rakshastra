import re
import json
import os
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


class DrugSlangEngine:
    """Matches drug-related slang, emojis, code words, Hindi/Hinglish terms,
    and hashtags.  Loads learned vocabulary from training artifacts when
    available."""

    # Hardcoded baseline slang (always present)
    _BASE_SLANG = {
        "mdma": ["ecstasy", "molly", "mandy", "md", "mumbai rolling"],
        "weed": ["ganja", "stuff", "greens", "maal", "bhang", "hash", "charas"],
        "cocaine": ["coke", "blow", "snow", "white", "didi"],
        "meth": ["ice", "glass", "crystal", "meth", "speed"],
        "heroin": ["chitta", "smack", "brown sugar"],
    }

    # Hardcoded baseline emojis
    _BASE_EMOJIS = {"\U0001f48a", "\U0001f33f", "\U0001f6ac", "\u2744\ufe0f",
                    "\U0001f340", "\U0001f36c", "\U0001f984", "\u26a1"}

    # Hardcoded baseline Hinglish patterns
    _BASE_HINGLISH = [
        r"maal ready hai",
        r"chahiye to dm karo",
        r"delivery mil jayegi",
        r"stock available hai",
        r"pure quality ka maal",
    ]

    def __init__(self):
        curr_dir = os.path.dirname(os.path.abspath(__file__))

        # ── Build the live slang database ────────────────────────────
        self.SLANG_DATABASE: Dict[str, List[str]] = {}
        for cat, terms in self._BASE_SLANG.items():
            self.SLANG_DATABASE[cat] = list(terms)

        self.learned_words: set[str] = set()

        # ── Build the live emoji set ─────────────────────────────────
        self.DRUG_EMOJIS = set(self._BASE_EMOJIS)

        # ── Build the live Hinglish patterns ─────────────────────────
        self.hinglish_patterns: List[str] = list(self._BASE_HINGLISH)

        # ── Build the live transaction patterns ──────────────────────
        self.transaction_patterns: List[str] = []

        # ── Load learned vocabulary ──────────────────────────────────
        self._learned_vocab_count = 0
        self._load_learned_vocabulary(curr_dir)

        # ── Load learned patterns ────────────────────────────────────
        self._learned_patterns_count = 0
        self._load_learned_patterns(curr_dir)

        # ── Load flagged handles ─────────────────────────────────────
        self.flagged_handles: set = set()
        self._load_flagged_handles(curr_dir)

    # ── Loaders ──────────────────────────────────────────────────────

    def _load_learned_vocabulary(self, base_dir: str):
        """Merge learned_drug_vocab.json into the live SLANG_DATABASE."""
        vocab_path = os.path.join(base_dir, "learned_drug_vocab.json")
        if not os.path.exists(vocab_path):
            return
        try:
            with open(vocab_path, "r", encoding="utf-8") as f:
                vocab = json.load(f)
            for term, info in vocab.items():
                cat = info.get("category", "other")
                conf = info.get("confidence", 0.5)
                if conf < 0.4:
                    continue  # skip low-confidence terms
                if cat not in self.SLANG_DATABASE:
                    self.SLANG_DATABASE[cat] = []
                if term not in self.SLANG_DATABASE[cat]:
                    self.SLANG_DATABASE[cat].append(term)
                    self._learned_vocab_count += 1
                self.learned_words.add(term)
            logger.debug("Loaded %d learned vocabulary terms", self._learned_vocab_count)
        except Exception as e:
            logger.warning("Failed to load learned vocabulary: %s", e)

    def _load_learned_patterns(self, base_dir: str):
        """Merge learned_drug_patterns.json into live pattern lists."""
        pat_path = os.path.join(base_dir, "learned_drug_patterns.json")
        if not os.path.exists(pat_path):
            return
        try:
            with open(pat_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Hinglish patterns
            for p in data.get("hinglish_patterns", []):
                if p not in self.hinglish_patterns:
                    self.hinglish_patterns.append(p)
                    self._learned_patterns_count += 1

            # Transaction patterns
            for p in data.get("transaction_phrases", []):
                if p not in self.transaction_patterns:
                    self.transaction_patterns.append(p)
                    self._learned_patterns_count += 1

            # Emojis
            for e in data.get("drug_emojis", []):
                self.DRUG_EMOJIS.add(e)

            logger.debug("Loaded %d learned patterns", self._learned_patterns_count)
        except Exception as e:
            logger.warning("Failed to load learned patterns: %s", e)

    def _load_flagged_handles(self, base_dir: str):
        """Load the flagged handles dataset."""
        handles_path = os.path.join(base_dir, "flagged_handles.json")
        if not os.path.exists(handles_path):
            return
        try:
            with open(handles_path, "r", encoding="utf-8") as f:
                self.flagged_handles = set(json.load(f))
            logger.debug("Loaded %d flagged handles", len(self.flagged_handles))
        except Exception as e:
            logger.warning("Failed to load flagged handles: %s", e)

    # ── Detection Methods ────────────────────────────────────────────

    def detect_slang(self, text: str) -> Dict[str, List[str]]:
        """Scan text and identify matching slang categories."""
        matches = {}
        text_lower = text.lower()
        for category, keywords in self.SLANG_DATABASE.items():
            found = []
            for kw in keywords:
                if re.search(r'\b' + re.escape(kw) + r'\b', text_lower):
                    found.append(kw)
            if found:
                matches[category] = found
        return matches

    def detect_emojis(self, text: str) -> List[str]:
        """Extract matched drug-related emojis from text."""
        return [char for char in text if char in self.DRUG_EMOJIS]

    def contains_hinglish_context(self, text: str) -> bool:
        """Heuristics to check for drug-related Hinglish/Hindi phrases."""
        text_lower = text.lower()
        return any(re.search(pat, text_lower) for pat in self.hinglish_patterns)

    def detect_transaction_patterns(self, text: str) -> List[str]:
        """Detect drug transaction / delivery phrases."""
        matches = []
        text_lower = text.lower()
        for pat in self.transaction_patterns:
            try:
                if re.search(pat, text_lower):
                    matches.append(pat)
            except re.error:
                if pat in text_lower:
                    matches.append(pat)
        return matches

    def detect_flagged_handles(self, text: str) -> List[str]:
        """Extract social media handles and check against the flagged list."""
        matches = []
        if not self.flagged_handles:
            return matches

        patterns = [
            r"@([a-zA-Z0-9_]{3,15})",
            r"(?:instagram\.com|t\.me|twitter\.com|twitter\.com\/status)\/([a-zA-Z0-9_]{3,15})",
        ]
        for pattern in patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                handle = match.group(1).strip()
                if handle in self.flagged_handles:
                    matches.append(handle)
        return sorted(list(set(matches)))

    # ── Stats ────────────────────────────────────────────────────────

    def get_vocabulary_stats(self) -> Dict[str, Any]:
        """Return statistics about loaded vocabulary and patterns."""
        total_terms = sum(len(v) for v in self.SLANG_DATABASE.values())
        base_terms = sum(len(v) for v in self._BASE_SLANG.values())
        return {
            "total_slang_terms": total_terms,
            "base_slang_terms": base_terms,
            "learned_slang_terms": self._learned_vocab_count,
            "categories": list(self.SLANG_DATABASE.keys()),
            "drug_emojis": len(self.DRUG_EMOJIS),
            "hinglish_patterns": len(self.hinglish_patterns),
            "transaction_patterns": len(self.transaction_patterns),
            "flagged_handles": len(self.flagged_handles),
            "learned_patterns": self._learned_patterns_count,
        }
