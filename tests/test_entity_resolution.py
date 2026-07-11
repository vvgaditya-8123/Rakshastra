from rakshastra_core.intelligence.entity_resolution import EntityResolutionEngine

def test_entity_extraction_from_text():
    engine = EntityResolutionEngine()
    text = "Call me at +919893212345 or email target@scam.com. Check wallet 0xabc1234567890123456789012345678901234567 and telegram @DirectMeds."
    extracted = engine.extract_entities_from_text(text)
    
    tokens = [item[0] for item in extracted]
    assert "+919893212345" in tokens
    assert "target@scam.com" in tokens
    assert "0xabc1234567890123456789012345678901234567" in tokens
    assert "@DirectMeds" in tokens

def test_input_payload_processing():
    engine = EntityResolutionEngine()
    payload = {
        "text": "Telegram handler @DirectMeds is active.",
        "chat": ["Call +919893212345 for help.", "Send money to dealer@upi"],
        "ocr": "Screenshot OCR text: Wallet 0xabc1234567890123456789012345678901234567",
        "url": "https://scamdomain.com/index.html",
        "url_content": "Visit us at discord:scam_moderator."
    }
    
    result = engine.process_input(payload)
    assert "resolved_profiles" in result
    assert "graph" in result
    
    # Assert nodes and edges are populated
    graph = result["graph"]
    assert len(graph["nodes"]) > 0
    assert len(graph["edges"]) > 0
    
    # Check that all entities are linked to the same operator profile
    operators = [n for n in graph["nodes"] if n["type"] == "operator"]
    assert len(operators) == 1

def test_alias_merging():
    engine = EntityResolutionEngine()
    # Explicitly link handles
    engine.link_entities("@DirectMeds", "+919893212345")
    engine.link_entities("+919893212345", "dealer@upi")
    
    # Register metadata for finding them
    engine.entity_metadata["@DirectMeds"] = {"type": "telegram", "confidence": 0.9}
    engine.entity_metadata["+919893212345"] = {"type": "phone", "confidence": 0.9}
    engine.entity_metadata["dealer@upi"] = {"type": "upi", "confidence": 0.9}
    
    result = engine.resolve_graph()
    profiles = result["resolved_profiles"]
    assert len(profiles) == 1
    
    # Check members in profile
    profile = list(profiles.values())[0]
    assert "@DirectMeds" in profile["raw_members"]
    assert "+919893212345" in profile["raw_members"]
    assert "dealer@upi" in profile["raw_members"]
