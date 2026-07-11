from typing import Dict, Any, List
from rakshastra_core.intelligence.keyword_engine import DrugSlangEngine


class DrugIntelligenceEngine:
    """Drug Intelligence Engine processing metadata, text, and OCR inputs
    to compute drug probability scores.

    Scoring weights (total possible = 1.0+):
        Slang match (hardcoded):        0.30
        Learned vocabulary match:       0.25
        Emoji match:                    0.15
        Hinglish context:               0.15
        Transaction patterns:           0.15
        Flagged handle detection:       0.25
        Image present:                  0.05
        OCR text slang match:           0.15
    """

    def __init__(self):
        self.slang_engine = DrugSlangEngine()

    def analyze_content(
        self,
        text: str,
        has_image: bool = False,
        ocr_text: str = "",
    ) -> Dict[str, Any]:
        """Compute the Drug Probability Score and return categorization insights."""
        score = 0.0
        reasons: List[str] = []

        # 1. Core slang analysis (hardcoded baseline terms)
        matched_slang = self.slang_engine.detect_slang(text)
        if matched_slang:
            # Count how many categories matched for graduated scoring
            cat_count = len(matched_slang)
            base_slang_score = min(0.30, 0.15 * cat_count)
            score += base_slang_score
            reasons.append(
                f"Matched drug slang ({cat_count} categories): "
                f"{list(matched_slang.keys())}"
            )

        # 2. Emoji analysis
        matched_emojis = self.slang_engine.detect_emojis(text)
        if matched_emojis:
            emoji_score = min(0.15, 0.05 * len(matched_emojis))
            score += emoji_score
            reasons.append(f"Matched {len(matched_emojis)} drug emojis")

        # 3. Hinglish context
        if self.slang_engine.contains_hinglish_context(text):
            score += 0.15
            reasons.append("Detected drug supply/delivery Hinglish keywords")

        # 4. Transaction patterns (from learned patterns)
        matched_tx = self.slang_engine.detect_transaction_patterns(text)
        if matched_tx:
            tx_score = min(0.15, 0.05 * len(matched_tx))
            score += tx_score
            reasons.append(
                f"Matched {len(matched_tx)} transaction patterns: "
                f"{matched_tx[:3]}"
            )

        # 5. Flagged handle detection
        matched_handles = self.slang_engine.detect_flagged_handles(text)
        if matched_handles:
            handle_score = min(0.25, 0.10 * len(matched_handles))
            score += handle_score
            reasons.append(
                f"Detected {len(matched_handles)} flagged handles: "
                f"{matched_handles[:5]}"
            )

        # 6. Image / OCR text processing
        if has_image:
            score += 0.05
            reasons.append("Image attachment present")
            if ocr_text:
                matched_ocr = self.slang_engine.detect_slang(ocr_text)
                if matched_ocr:
                    score += 0.15
                    reasons.append(
                        f"Found drug slang in image OCR text: "
                        f"{list(matched_ocr.keys())}"
                    )

        # Cap probability score at 1.0
        final_score = round(min(score, 1.0), 3)

        return {
            "drug_probability_score": final_score,
            "matched_slang": matched_slang,
            "matched_emojis": matched_emojis,
            "matched_handles": matched_handles,
            "matched_transaction_patterns": matched_tx,
            "reasons": reasons,
            "requires_investigation": final_score >= 0.5,
            "vocabulary_stats": self.slang_engine.get_vocabulary_stats(),
        }
