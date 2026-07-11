from rakshastra_core.intelligence.explainable_reasoning import ExplainableReasoningEngine, MockLLMProvider

def test_fallback_reasoning_generation():
    engine = ExplainableReasoningEngine()
    
    session_id = "INV-TEST-001"
    threat_output = {
        "risk_score": 0.85,
        "detected_threat": "Drug Intelligence",
        "matched_indicators": ["mdma", "molly"],
        "reasons": ["Matched drug slang"],
        "language": "en"
    }
    entity_output = {
        "resolved_profiles": {
            "OP-ABC123XYZ": {
                "operator_id": "OP-ABC123XYZ",
                "entities": {"telegram": ["@DirectMeds"], "phone": ["+919893212345"]}
            }
        }
    }
    graph_output = {
        "nodes": [{"id": "INV-TEST-001"}, {"id": "@DirectMeds"}],
        "edges": [{"source": "INV-TEST-001", "target": "@DirectMeds"}]
    }
    correlation_output = {
        "matched_evidence": [{"matching_session_id": "INV-HIST-099", "confidence": 0.95}],
        "suggested_merge": {"session_a": "INV-TEST-001", "session_b": "INV-HIST-099", "confidence": 0.95}
    }

    res = engine.analyze_investigation(
        session_id=session_id,
        threat_output=threat_output,
        entity_output=entity_output,
        graph_output=graph_output,
        correlation_output=correlation_output
    )

    # 1. Assert required JSON keys are present
    assert "threat_summary" in res
    assert "reasoning_chain" in res
    assert "evidence_explanation" in res
    assert "counter_evidence" in res
    assert "recommendations" in res
    assert "investigation_narrative" in res
    assert "risk_explanation" in res
    assert "markdown_report" in res

    # 2. Check content of specific fields
    assert res["threat_summary"]["overall_threat_level"] == "CRITICAL"
    assert "Step 4: Multi-source correlation" in res["reasoning_chain"][3]
    assert len(res["recommendations"]) > 0
    assert "INV-HIST-099" in res["investigation_narrative"]
    assert res["risk_explanation"]["threat_pack"] == "Drug Intelligence"
    assert "# Explainable AI Security Investigation Report" in res["markdown_report"]


def test_mock_llm_provider_generation():
    mock_data = {
        "threat_summary": {"overall_threat_level": "HIGH", "confidence": "95%", "what_was_found": "A", "why_it_matters": "B"},
        "reasoning_chain": ["Step 1", "Step 2"],
        "evidence_explanation": ["Engine X triggered"],
        "counter_evidence": ["No phone match"],
        "recommendations": ["Expand graph"],
        "investigation_narrative": "Narrative text",
        "risk_explanation": {"content_risk": 0.5}
    }
    provider = MockLLMProvider(mock_data)
    engine = ExplainableReasoningEngine(provider)
    
    res = engine.analyze_investigation(
        session_id="INV-TEST-002",
        threat_output={},
        entity_output={},
        graph_output={},
        correlation_output={}
    )
    
    assert res["threat_summary"]["overall_threat_level"] == "HIGH"
    assert res["recommendations"] == ["Expand graph"]
    assert "# Explainable AI Security Investigation Report" in res["markdown_report"]
