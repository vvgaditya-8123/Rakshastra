import re
from typing import Dict, Any, List

class BotDetector:
    """Analyzes message patterns, command structures, and timestamps to identify automated spam bots."""

    def __init__(self):
        pass

    def detect_bot_behavior(self, messages: List[str]) -> Dict[str, Any]:
        """Assess the messages list and calculate an Automation Confidence Score."""
        if not messages:
            return {"automation_confidence": 0.0, "indicators": []}

        indicators = []
        confidence_points = 0.0

        # Check for typical bot command formats (e.g. /start, /help, /buy, /price)
        command_patterns = [r"^\/[a-zA-Z0-9_-]+$", r"^![a-zA-Z0-9_-]+$"]
        command_hits = 0

        # Identical messaging checks (repetition/spam)
        uniques = set()
        
        for msg in messages:
            msg_stripped = msg.strip()
            # Command matching
            if any(re.match(pat, msg_stripped) for pat in command_patterns):
                command_hits += 1
            uniques.add(msg_stripped)

        # Repetition index
        repetition_rate = 1.0 - (len(uniques) / len(messages))
        
        if command_hits / len(messages) >= 0.5:
            confidence_points += 0.4
            indicators.append("High ratio of command-formatted messages")
            
        if repetition_rate >= 0.5:
            confidence_points += 0.4
            indicators.append(f"High repetitive content rate: {repetition_rate * 100:.1f}%")
            
        # Detect typical bot advertising signatures
        ad_keywords = ["bot online", "click start to buy", "automated shop", "delivery instantly"]
        text_joined = " ".join(messages).lower()
        if any(kw in text_joined for kw in ad_keywords):
            confidence_points += 0.2
            indicators.append("Detected automated store/bot signature keywords")

        final_score = min(confidence_points, 1.0)
        
        return {
            "automation_confidence": final_score,
            "indicators": indicators,
            "is_automated": final_score >= 0.6
        }
