import re
from typing import Dict, Any, List, Set, Tuple

class IntelligencePack:
    """Base class for Threat Intelligence Packs."""
    def __init__(
        self,
        name: str,
        keywords: List[str],
        slang: Dict[str, str],
        emojis: Dict[str, str],
        patterns: List[str],
        weight: float = 0.20,
        suggested_action: str = "Flag target for manual review."
    ):
        self.name = name
        self.keywords = [kw.lower() for kw in keywords]
        self.slang = {k.lower(): v.lower() for k, v in slang.items()}
        self.emojis = emojis
        self.patterns = patterns
        self.weight = weight
        self.suggested_action = suggested_action

    def match_indicators(self, text: str) -> List[str]:
        """Find matching keywords and regex patterns in normalized text."""
        matched = []
        text_lower = text.lower()
        
        # Keyword matching (word boundary checks where applicable)
        for kw in self.keywords:
            if re.search(r'\b' + re.escape(kw) + r'\b', text_lower) or kw in text_lower:
                matched.append(kw)
                
        # Regex patterns
        for pat in self.patterns:
            try:
                if re.search(pat, text_lower, re.IGNORECASE):
                    matched.append(pat)
            except re.error:
                pass
                
        return sorted(list(set(matched)))


# ── Threat Packs Implementation ──────────────────────────────────────────

class DrugIntelligencePack(IntelligencePack):
    def __init__(self):
        super().__init__(
            name="Drug Intelligence",
            keywords=["mdma", "molly", "ecstasy", "weed", "ganja", "charas", "cocaine", "heroin", "meth", "pills", "hash"],
            slang={"maal": "drug stock", "greens": "weed", "snow": "cocaine", "ice": "methamphetamine"},
            emojis={"💊": "pill/drug", "🌿": "weed", "❄️": "cocaine"},
            patterns=[r"maal ready hai", r"secure delivery", r"drop point"],
            weight=0.30,
            suggested_action="Report to LEA Narcotics division."
        )

class CyberFraudPack(IntelligencePack):
    def __init__(self):
        super().__init__(
            name="Cyber Fraud",
            keywords=["fraud", "carding", "refund", "chargeback", "bin list", "spoof", "bank drop", "wire transfer"],
            slang={"cvv": "card security code", "cc": "credit card", "fullz": "complete identity info"},
            emojis={"💳": "credit card", "💸": "money loss"},
            patterns=[r"bank drop available", r"carding method", r"cashout"],
            weight=0.25,
            suggested_action="Blacklist associated bank accounts and report suspicious activity."
        )

class ScamDetectionPack(IntelligencePack):
    def __init__(self):
        super().__init__(
            name="Scam Detection",
            keywords=["giveaway", "lottery", "prize", "jackpot", "earn quick", "double money", "investment plan"],
            slang={"easy money": "financial scam", "guaranteed returns": "ponzi scheme"},
            emojis={"🎁": "gift scam", "💰": "wealth scam"},
            patterns=[r"send \d+ to get \d+", r"make \d+ daily", r"investment opportunity"],
            weight=0.20,
            suggested_action="Flag for Ponzi / Advance Fee fraud investigation."
        )

class PhishingPack(IntelligencePack):
    def __init__(self):
        super().__init__(
            name="Phishing Detection",
            keywords=["verify account", "login verification", "update password", "suspicious login", "secure login link"],
            slang={"spoofed": "fake domain", "phish kit": "phishing templates"},
            emojis={"🎣": "phishing lure", "🔗": "suspicious link"},
            patterns=[r"verify-your-identity", r"login-security-update", r"bit\.ly/\w+"],
            weight=0.25,
            suggested_action="Block domain at firewall/DNS level and warn users."
        )

class CredentialTheftPack(IntelligencePack):
    def __init__(self):
        super().__init__(
            name="Credential Theft",
            keywords=["database dump", "leaked passwords", "combo list", "logs cloud", "stealer log", "keylogger"],
            slang={"combos": "email-password leaks", "db": "database leak"},
            emojis={"🔓": "unsecured credential", "🔑": "password"},
            patterns=[r"stealer logs?", r"combo file", r"dehashed"],
            weight=0.30,
            suggested_action="Trigger mandatory credential reset for impacted accounts."
        )

class MoneyMulePack(IntelligencePack):
    def __init__(self):
        super().__init__(
            name="Money Mule Detection",
            keywords=["work from home", "receiving agent", "transfer money", "remittance coordinator", "commission agent"],
            slang={"mule": "money laundering proxy", "cashout service": "mule network"},
            emojis={"💵": "cash", "🏦": "bank transfer"},
            patterns=[r"no experience required", r"keep \d+ percent", r"process payments"],
            weight=0.20,
            suggested_action="Forward details to AML (Anti-Money Laundering) compliance officer."
        )

class HumanTraffickingPack(IntelligencePack):
    def __init__(self):
        super().__init__(
            name="Human Trafficking",
            keywords=["escort", "massage", "no ID required", "work visa fast", "nanny offer", "hostess job"],
            slang={"companion": "trafficking victim", "relocate fast": "suspicious relocation"},
            emojis={"👤": "hidden identity", "✈️": "unverified transport"},
            patterns=[r"relocation assistance provided", r"passport held", r"immediate travel required"],
            weight=0.30,
            suggested_action="Alert human trafficking rescue hotline and law enforcement."
        )

class DarkWebPack(IntelligencePack):
    def __init__(self):
        super().__init__(
            name="Dark Web Terminology",
            keywords=["onion link", "tor browser", "hidden service", "dread forum", "escrow", "vendor pgp"],
            slang={"markets": "darknet marketplaces", "exit node": "tor router"},
            emojis={"🧅": "onion / tor"},
            patterns=[r"\.onion\b", r"pgp public key", r"tor hidden service"],
            weight=0.20,
            suggested_action="Correlate onion addresses with active dark web monitoring databases."
        )

class CryptoScamPack(IntelligencePack):
    def __init__(self):
        super().__init__(
            name="Crypto Scam Language",
            keywords=["airdrop", "presale", "rugpull", "token launch", "100x gem", "to the moon", "liquidity locked"],
            slang={"pump": "market manipulation", "rekt": "major financial loss"},
            emojis={"🚀": "hype / pump", "💎": "crypto hold"},
            patterns=[r"whitelist open", r"connect wallet", r"guaranteed airdrop"],
            weight=0.20,
            suggested_action="Flag smart contract address and report fraudulent dApp."
        )


# ── Threat Intelligence Engine ───────────────────────────────────────────

class ThreatIntelligenceEngine:
    def __init__(self):
        # Register standard packs
        self.packs: List[IntelligencePack] = [
            DrugIntelligencePack(),
            CyberFraudPack(),
            ScamDetectionPack(),
            PhishingPack(),
            CredentialTheftPack(),
            MoneyMulePack(),
            HumanTraffickingPack(),
            DarkWebPack(),
            CryptoScamPack()
        ]

    def register_pack(self, pack: IntelligencePack):
        """Allow dynamic addition of new intelligence packs."""
        self.packs.append(pack)

    def normalize_text(self, text: str) -> str:
        """Lowercase, strip excess whitespaces, and normalize characters."""
        if not text:
            return ""
        # Basic character lookalike cleanups (e.g. Cyrillic/homoglyph cleanups if needed)
        norm = text.lower().strip()
        norm = re.sub(r'\s+', ' ', norm)
        return norm

    def detect_language(self, text: str) -> str:
        """Simple heuristic to detect Hinglish, Hindi, or English."""
        hinglish_words = {"maal", "hai", "chahiye", "karo", "milega", "bhai", "sab", "ho", "ka"}
        text_words = set(re.findall(r'\b\w+\b', text.lower()))
        
        if text_words.intersection(hinglish_words):
            return "hinglish"
        return "en"

    def expand_slang(self, text: str, pack: IntelligencePack) -> str:
        """Replace slang terms with their expanded explanations."""
        expanded = text
        for slang_term, replacement in pack.slang.items():
            pattern = r'\b' + re.escape(slang_term) + r'\b'
            expanded = re.sub(pattern, f"{slang_term} ({replacement})", expanded, flags=re.IGNORECASE)
        return expanded

    def expand_emojis(self, text: str, pack: IntelligencePack) -> str:
        """Replace matching emojis with their textual meanings."""
        expanded = text
        for emoji, representation in pack.emojis.items():
            if emoji in expanded:
                expanded = expanded.replace(emoji, f" [{representation}] ")
        return expanded

    def extract_entities(self, text: str) -> Dict[str, List[str]]:
        """Extract URLs, UPI IDs, Crypto Wallets, Usernames, and Phones."""
        entities = {
            "urls": re.findall(r'https?://[^\s/$.?#].[^\s]*', text),
            "upi_ids": re.findall(r'[a-zA-Z0-9.\-_]+@[a-zA-Z0-9.\-_]+', text),
            "crypto_wallets": re.findall(r'\b(?:0x[a-fA-F0-9]{40}|bc1[a-zA-Z0-9]{39,59})\b', text),
            "usernames": re.findall(r'@\w+', text),
            "phones": re.findall(r'\+?\d{10,15}', text)
        }
        # Unique/clean
        for key in entities:
            entities[key] = sorted(list(set(entities[key])))
        return entities

    def analyze(self, text: str) -> Dict[str, Any]:
        """Runs the normalized text against registered intelligence packs."""
        normalized = self.normalize_text(text)
        language = self.detect_language(normalized)
        entities = self.extract_entities(text)

        highest_risk_score = 0.0
        primary_threat = "None"
        reasoning = "No threat detected."
        suggested_action = "Routine monitoring."
        matched_indicators = []
        confidence = 0.0

        for pack in self.packs:
            # Expand slang & emojis for matches
            expanded = self.expand_slang(normalized, pack)
            expanded = self.expand_emojis(expanded, pack)

            indicators = pack.match_indicators(expanded)
            if indicators:
                # Calculate confidence score for this pack
                # Match density (number of matched indicators / total keywords & patterns)
                total_density = len(indicators) / max(len(pack.keywords) + len(pack.patterns), 1)
                pack_confidence = min(0.40 + (total_density * 0.60), 1.0)
                
                # Risk score contribution
                risk_contrib = pack.weight * pack_confidence
                
                if risk_contrib > highest_risk_score:
                    highest_risk_score = risk_contrib
                    primary_threat = pack.name
                    reasoning = f"Matched {len(indicators)} indicators for {pack.name}: {indicators[:5]}."
                    suggested_action = pack.suggested_action
                    matched_indicators = indicators
                    confidence = pack_confidence

        # Format and return final response
        return {
            "risk_score": round(min(highest_risk_score, 1.0), 3),
            "detected_threat": primary_threat,
            "reasoning": reasoning,
            "matched_indicators": matched_indicators,
            "suggested_action": suggested_action,
            "confidence": round(confidence, 3),
            "entities": entities,
            "language": language
        }
