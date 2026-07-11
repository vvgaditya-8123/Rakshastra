import json
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional

# ── LLM Providers Wrapper ──────────────────────────────────────────────────

class LLMExplanationProvider(ABC):
    """Abstract base class for provider-agnostic AI explanation generation."""
    @abstractmethod
    def generate_explanation(self, prompt: str) -> str:
        pass


class GeminiProvider(LLMExplanationProvider):
    def __init__(self, api_key: str, model_name: str = "gemini-1.5-flash"):
        self.api_key = api_key
        self.model_name = model_name

    def generate_explanation(self, prompt: str) -> str:
        # Placeholder for real Gemini API call
        # In production: requests/google-genai client call
        return ""


class OpenAIProvider(LLMExplanationProvider):
    def __init__(self, api_key: str, model_name: str = "gpt-4-turbo"):
        self.api_key = api_key
        self.model_name = model_name

    def generate_explanation(self, prompt: str) -> str:
        # Placeholder for OpenAI client call
        return ""


class ClaudeProvider(LLMExplanationProvider):
    def __init__(self, api_key: str, model_name: str = "claude-3-5-sonnet"):
        self.api_key = api_key
        self.model_name = model_name

    def generate_explanation(self, prompt: str) -> str:
        # Placeholder for Anthropic client call
        return ""


class OllamaProvider(LLMExplanationProvider):
    def __init__(self, endpoint: str = "http://localhost:11434", model_name: str = "llama3"):
        self.endpoint = endpoint
        self.model_name = model_name

    def generate_explanation(self, prompt: str) -> str:
        # Placeholder for Ollama API call
        return ""


class MockLLMProvider(LLMExplanationProvider):
    """Simulates LLM response for offline testing or fallback validation."""
    def __init__(self, return_json: dict):
        self.return_json = return_json

    def generate_explanation(self, prompt: str) -> str:
        return json.dumps(self.return_json)


# ── Explainable Reasoning Engine ───────────────────────────────────────────

class ExplainableReasoningEngine:
    """Combines threat, entity, graph, and correlation inputs to generate explainable AI reasoning."""

    def __init__(self, provider: Optional[LLMExplanationProvider] = None):
        self.provider = provider

    def analyze_investigation(
        self,
        session_id: str,
        threat_output: Dict[str, Any],
        entity_output: Dict[str, Any],
        graph_output: Dict[str, Any],
        correlation_output: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Automatically synthesize inputs into structured explainable outputs."""
        
        # Build prompt containing full structured metadata context
        context_data = {
            "session_id": session_id,
            "threat_intelligence": {
                "score": threat_output.get("risk_score", 0.0),
                "category": threat_output.get("detected_threat", "Unknown"),
                "matched_indicators": threat_output.get("matched_indicators", []),
                "reasons": threat_output.get("reasons", []),
                "language": threat_output.get("language", "en")
            },
            "entities": entity_output.get("resolved_profiles", {}),
            "graph": {
                "nodes_count": len(graph_output.get("nodes", [])),
                "edges_count": len(graph_output.get("edges", []))
            },
            "correlation": {
                "matches": correlation_output.get("matched_evidence", []),
                "suggested_merge": correlation_output.get("suggested_merge")
            }
        }
        
        prompt = f"""
        Analyze the following Cyber Threat Investigation metadata and generate explainable intelligence:
        {json.dumps(context_data, indent=2)}

        Return a JSON object containing the following keys:
        - "threat_summary": Natural language summary detailing what was found, why it matters, confidence, and threat level.
        - "reasoning_chain": Step-by-step reasoning list from raw indicators to conclusion.
        - "evidence_explanation": Bullet points explaining trigger rules, producing engine, and graph coordinates.
        - "counter_evidence": Points explaining why confidence is not 100% (e.g. missing reuses/indicators).
        - "recommendations": Actions list (e.g. monitor channels, preserve data, MLAT).
        - "investigation_narrative": Chronological text narrative of how the threat unfolded across sources.
        - "risk_explanation": Breakdown of risk contribution (Content, Graph, Correlation, History).
        """

        # If provider is configured and returns a valid result, use it
        if self.provider:
            try:
                raw_resp = self.provider.generate_explanation(prompt)
                if raw_resp:
                    parsed = json.loads(raw_resp)
                    # Add Markdown report
                    parsed["markdown_report"] = self.generate_markdown_report(parsed)
                    return parsed
            except Exception:
                pass # Fallback to deterministic engine on any LLM parser failures

        # Heuristic/Deterministic Fallback Generation
        fallback_data = self._generate_fallback(session_id, context_data)
        fallback_data["markdown_report"] = self.generate_markdown_report(fallback_data)
        return fallback_data

    def _generate_fallback(self, session_id: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Deterministic fallback engine when LLM is unavailable or fails."""
        threat_data = context["threat_intelligence"]
        risk_score = threat_data["score"]
        category = threat_data["category"]
        indicators = threat_data["matched_indicators"]
        corr = context["correlation"]

        # 1. Threat Summary
        threat_level = "LOW"
        if risk_score >= 0.75:
            threat_level = "CRITICAL"
        elif risk_score >= 0.50:
            threat_level = "HIGH"
        elif risk_score >= 0.25:
            threat_level = "MEDIUM"

        threat_summary = {
            "what_was_found": f"Detected operational indicators matching {category}.",
            "why_it_matters": "Indicates active coordinated threat distribution or infrastructure reuse.",
            "confidence": f"System is {int(risk_score * 100)}% confident based on matches.",
            "overall_threat_level": threat_level
        }

        # 2. Reasoning Chain
        steps = []
        steps.append("Step 1: Input text normalized and scanned.")
        if indicators:
            steps.append(f"Step 2: Threat keywords matched: {indicators}.")
        if context["entities"]:
            steps.append(f"Step 3: Disparate entity footprints resolved into operator groups.")
        if corr["matches"]:
            steps.append(f"Step 4: Multi-source correlation identified {len(corr['matches'])} matching historical cases.")
        steps.append(f"Conclusion: Resolved active {category} network with {threat_level} severity.")

        # 3. Evidence Explanation
        ev_explanation = []
        if indicators:
            ev_explanation.append(f"Rule triggered: Keyword/slang density. Produced by: ThreatIntelligenceEngine. Contributed: {indicators}.")
        if corr["matches"]:
            ev_explanation.append(f"Rule triggered: Identifier reuse. Produced by: MultiSourceCorrelationEngine. Relates to: {[m['matching_session_id'] for m in corr['matches']]}.")

        # 4. Counter Evidence
        counter_ev = []
        has_phone = any(etype == "phone" for p in context["entities"].values() for etype in p.get("entities", {}))
        has_wallet = any(etype == "wallet" for p in context["entities"].values() for etype in p.get("entities", {}))
        
        if not has_phone:
            counter_ev.append("Confidence not 100%: Reused phone number footprint was not detected in this session.")
        if not has_wallet:
            counter_ev.append("Confidence not 100%: Reused cryptocurrency wallet was not detected in this session.")
        if not corr["matches"]:
            counter_ev.append("Confidence not 100%: No historical investigation correlation matched these footprints.")

        # 5. Recommendations
        recs = ["Collect metadata and network logs."]
        if "Telegram" in str(context):
            recs.append("Monitor associated Telegram channel/invite link.")
        if "wallet" in str(context):
            recs.append("Track crypto wallet transactions and execute blockchain analysis.")
        if risk_score >= 0.50:
            recs.append("Request data preservation order from corresponding service providers.")
            recs.append("Draft formal MLAT (Mutal Legal Assistance Treaty) request.")

        # 6. Investigation Narrative
        narrative = f"Investigation {session_id} commenced with raw content analysis. "
        if indicators:
            narrative += f"The threat actor employed specific {category} language. "
        if corr["matches"]:
            narrative += f"Cross-platform correlation linked these activities to historical cases: {[m['matching_session_id'] for m in corr['matches']]}."
        else:
            narrative += "No prior cases matched this actor footprint yet."

        # 7. Risk Explanation
        risk_exp = {
            "content_risk": round(risk_score * 0.40, 3),
            "graph_risk": round(min(context["graph"]["nodes_count"] * 0.05, 0.20), 3),
            "correlation_risk": round(0.30 if corr["matches"] else 0.0, 3),
            "history_risk": round(0.10 if corr["suggested_merge"] else 0.0, 3),
            "threat_pack": category
        }

        return {
            "threat_summary": threat_summary,
            "reasoning_chain": steps,
            "evidence_explanation": ev_explanation,
            "counter_evidence": counter_ev,
            "recommendations": recs,
            "investigation_narrative": narrative,
            "risk_explanation": risk_exp
        }

    def generate_markdown_report(self, data: Dict[str, Any]) -> str:
        """Formulate a human-readable investigation report from structured analysis."""
        summary = data["threat_summary"]
        recs = data["recommendations"]
        chain = data["reasoning_chain"]
        risk = data["risk_explanation"]

        md = []
        md.append("# Explainable AI Security Investigation Report")
        md.append(f"**Threat Level**: `{summary['overall_threat_level']}` | **Confidence**: `{summary['confidence']}`")
        md.append("\n---\n")

        md.append("## Executive Threat Summary")
        md.append(f"- **What was found**: {summary['what_was_found']}")
        md.append(f"- **Why it matters**: {summary['why_it_matters']}")
        md.append("\n---\n")

        md.append("## Reasoning Chain")
        for step in chain:
            md.append(f"- {step}")
        md.append("\n---\n")

        md.append("## Chronological Narrative")
        md.append(data["investigation_narrative"])
        md.append("\n---\n")

        md.append("## Risk Score Breakdown")
        for k, v in risk.items():
            md.append(f"- **{k.replace('_', ' ').title()}**: {v}")
        md.append("\n---\n")

        if data["counter_evidence"]:
            md.append("## Counter Evidence / Gaps")
            for gap in data["counter_evidence"]:
                md.append(f"- {gap}")
            md.append("\n---\n")

        md.append("## Recommended Investigator Actions")
        for rec in recs:
            md.append(f"- [ ] {rec}")

        return "\n".join(md)
