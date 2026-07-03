import re
from typing import Dict, Any, List

class DrugSlangEngine:
    """Matches drug-related slang, emojis, code words, Hindi/Hinglish terms, and hashtags."""
    
    # Common slang words for illicit substances
    SLANG_DATABASE = {
        "mdma": ["ecstasy", "molly", "mandy", "md", "mumbai rolling"],
        "weed": ["ganja", "stuff", "greens", "maal", "bhang", "hash", "charas"],
        "cocaine": ["coke", "blow", "snow", "white", "didi"],
        "meth": ["ice", "glass", "crystal", "meth", "speed"],
        "heroin": ["chitta", "smack", "brown sugar"]
    }

    # Emojis commonly associated with drug advertisements online
    DRUG_EMOJIS = {"💊", "🌿", "🚬", "❄️", "🍀", "🍬", "🦄", "⚡"}

    def __init__(self):
        pass

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
        hinglish_patterns = [
            r"maal ready hai",
            r"chahiye to dm karo",
            r"delivery mil jayegi",
            r"stock available hai",
            r"pure quality ka maal"
        ]
        text_lower = text.lower()
        return any(re.search(pat, text_lower) for pat in hinglish_patterns)
