from typing import Dict, Any
from rakshastra_core.intelligence.keyword_engine import DrugSlangEngine

class DrugIntelligenceEngine:
    """Drug Intelligence Engine processing metadata, text, and OCR inputs to compute drug probability scores."""

    def __init__(self):
        self.slang_engine = DrugSlangEngine()

    def analyze_content(self, text: str, has_image: bool = False, ocr_text: str = "") -> Dict[str, Any]:
        """Compute the Drug Probability Score and return categorization insights."""
        score = 0.0
        reasons = []

        # 1. Slang Analysis
        matched_slang = self.slang_engine.detect_slang(text)
        if matched_slang:
            score += 0.4
            reasons.append(f"Matched drug slang categories: {list(matched_slang.keys())}")

        # 2. Emoji Analysis
        matched_emojis = self.slang_engine.detect_emojis(text)
        if matched_emojis:
            score += 0.2
            reasons.append(f"Matched drug advertisement emojis: {matched_emojis}")

        # 3. Hinglish context
        if self.slang_engine.contains_hinglish_context(text):
            score += 0.2
            reasons.append("Detected drug supply/delivery Hinglish keywords")

        # 4. Image / OCR text processing
        if has_image:
            score += 0.1
            if ocr_text:
                matched_ocr = self.slang_engine.detect_slang(ocr_text)
                if matched_ocr:
                    score += 0.2
                    reasons.append(f"Found drug slang in image OCR text: {list(matched_ocr.keys())}")

        # Cap probability score at 1.0
        final_score = min(score, 1.0)
        
        return {
            "drug_probability_score": final_score,
            "matched_slang": matched_slang,
            "matched_emojis": matched_emojis,
            "reasons": reasons,
            "requires_investigation": final_score >= 0.5
        }
