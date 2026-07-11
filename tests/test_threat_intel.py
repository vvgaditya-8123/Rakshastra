from rakshastra_core.intelligence import ThreatIntelligenceEngine, IntelligencePack

def test_normalization():
    engine = ThreatIntelligenceEngine()
    text = "   NEED MOLlY  \n  secure delivery  "
    normalized = engine.normalize_text(text)
    assert normalized == "need molly secure delivery"

def test_language_detection():
    engine = ThreatIntelligenceEngine()
    assert engine.detect_language("need molly secure delivery") == "en"
    assert engine.detect_language("pure quality ka maal ready hai") == "hinglish"

def test_entity_extraction():
    engine = ThreatIntelligenceEngine()
    text = "Contact telegram @NarcoFastBot or call +919893212345. Pay to drugdealer@upi and check https://scam-site.com or wallet 0xabc1234567890123456789012345678901234567"
    entities = engine.extract_entities(text)
    assert "@NarcoFastBot" in entities["usernames"]
    assert "+919893212345" in entities["phones"]
    assert "drugdealer@upi" in entities["upi_ids"]
    assert "https://scam-site.com" in entities["urls"]
    assert "0xabc1234567890123456789012345678901234567" in entities["crypto_wallets"]

def test_slang_and_emoji_expansion():
    engine = ThreatIntelligenceEngine()
    # Find drug pack
    drug_pack = next(p for p in engine.packs if p.name == "Drug Intelligence")
    
    text = "pure quality ka maal"
    expanded = engine.expand_slang(text, drug_pack)
    assert "maal (drug stock)" in expanded

    text_emoji = "need some 💊"
    expanded_emoji = engine.expand_emojis(text_emoji, drug_pack)
    assert "[pill/drug]" in expanded_emoji

def test_drug_pack_matching():
    engine = ThreatIntelligenceEngine()
    res = engine.analyze("need some Molly for the weekend")
    assert res["detected_threat"] == "Drug Intelligence"
    assert res["risk_score"] > 0.0
    assert "molly" in res["matched_indicators"]

def test_cyber_fraud_pack_matching():
    engine = ThreatIntelligenceEngine()
    res = engine.analyze("I have bank drop available for cashout")
    assert res["detected_threat"] == "Cyber Fraud"
    assert "bank drop available" in res["matched_indicators"]

def test_scam_detection_pack_matching():
    engine = ThreatIntelligenceEngine()
    res = engine.analyze("guaranteed returns on our new investment opportunity")
    assert res["detected_threat"] == "Scam Detection"
    assert "investment opportunity" in res["matched_indicators"]

def test_phishing_pack_matching():
    engine = ThreatIntelligenceEngine()
    res = engine.analyze("verify-your-identity at this secure login link")
    assert res["detected_threat"] == "Phishing Detection"
    assert "verify-your-identity" in res["matched_indicators"]

def test_credential_theft_pack_matching():
    engine = ThreatIntelligenceEngine()
    res = engine.analyze("selling stealer logs and database dump")
    assert res["detected_threat"] == "Credential Theft"
    assert "stealer log" in res["matched_indicators"] or "database dump" in res["matched_indicators"]

def test_money_mule_pack_matching():
    engine = ThreatIntelligenceEngine()
    res = engine.analyze("work from home as receiving agent with no experience required")
    assert res["detected_threat"] == "Money Mule Detection"
    assert "no experience required" in res["matched_indicators"] or "receiving agent" in res["matched_indicators"]

def test_human_trafficking_pack_matching():
    engine = ThreatIntelligenceEngine()
    res = engine.analyze("relocation assistance provided escort jobs fast work visa")
    assert res["detected_threat"] == "Human Trafficking"
    assert "escort" in res["matched_indicators"] or "relocation assistance provided" in res["matched_indicators"]

def test_dark_web_pack_matching():
    engine = ThreatIntelligenceEngine()
    res = engine.analyze("visit our marketplace hidden service at marketxyz.onion")
    assert res["detected_threat"] == "Dark Web Terminology"
    assert ".onion" in res["matched_indicators"] or "hidden service" in res["matched_indicators"]

def test_crypto_scam_pack_matching():
    engine = ThreatIntelligenceEngine()
    res = engine.analyze("join our presale for the next 100x gem to the moon")
    assert res["detected_threat"] == "Crypto Scam Language"
    assert "100x gem" in res["matched_indicators"] or "presale" in res["matched_indicators"]

def test_custom_pack_registration():
    engine = ThreatIntelligenceEngine()
    custom_pack = IntelligencePack(
        name="Custom Threat",
        keywords=["malware", "ransomware"],
        slang={},
        emojis={},
        patterns=[r"encrypted files"],
        weight=0.35,
        suggested_action="Isolate network host immediately."
    )
    engine.register_pack(custom_pack)
    res = engine.analyze("our system has encrypted files and ransomware threat")
    assert res["detected_threat"] == "Custom Threat"
    assert res["risk_score"] > 0.0
    assert res["suggested_action"] == "Isolate network host immediately."
