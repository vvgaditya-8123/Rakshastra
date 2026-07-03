from typing import Dict, Any, List
from rakshastra_core.models.workflow import WorkflowState
from rakshastra_core.engines.workflow import SecurityWorkflowEngine

class SecurityReasoningEngine:
    """Orchestrates security reasoning by recommending next phases and actions based on context."""

    GUIDANCE_TEMPLATES = {
        WorkflowState.RECON: {
            "action": "Perform host discovery and initial scope mapping.",
            "skills": ["network-scan"],
            "message": "Start by identifying target hosts, active subnets, and mapping out the scope of the investigation. Run initial ping sweeps or basic scans."
        },
        WorkflowState.ENUMERATION: {
            "action": "Enumerate active ports and services on identified hosts.",
            "skills": ["network-scan", "linux-audit", "windows-audit"],
            "message": "Scan discovered hosts for open ports, determine what services are running, and identify versions/protocols. Build service dependencies."
        },
        WorkflowState.COLLECTION: {
            "action": "Collect system configurations, logs, and process states.",
            "skills": ["linux-audit", "docker-audit", "windows-audit", "forensics", "credential-audit"],
            "message": "Gather configurations, container privileges, file permissions, or credential files from target hosts to identify potential exposures."
        },
        WorkflowState.EVIDENCE: {
            "action": "Record validated findings as structured evidence.",
            "skills": ["incident-response", "forensics"],
            "message": "Examine collected configurations and logs. Record any confirmed vulnerabilities, exposed secrets, or misconfigurations as formal Evidence records."
        },
        WorkflowState.ANALYSIS: {
            "action": "Analyze root causes and build attack paths.",
            "skills": ["incident-response", "forensics"],
            "message": "Correlate recorded evidence. Traverse the Infrastructure Graph to identify lateral movement opportunities and construct potential attack paths."
        },
        WorkflowState.PRIORITIZATION: {
            "action": "Run threat engine to prioritize risks using 6-factor scoring.",
            "skills": ["compliance-check"],
            "message": "Calculate composite risk scores using the six-factor threat engine. Prioritize vulnerabilities from critical down to low severity."
        },
        WorkflowState.RECOMMENDATION: {
            "action": "Compile remediation playbooks and specific fix commands.",
            "skills": ["incident-response", "compliance-check"],
            "message": "Prepare clear, prioritized recommended actions. Specify the exact commands or configuration files that need patching/remediating."
        },
        WorkflowState.VERIFICATION: {
            "action": "Verify that applied fixes are active and correct.",
            "skills": ["compliance-check", "network-scan"],
            "message": "Re-run checks, scan ports, or read back configurations to verify that the remediation has successfully mitigated the vulnerability."
        },
        WorkflowState.REPORT: {
            "action": "Generate and present the final security report.",
            "skills": ["compliance-check"],
            "message": "Compile findings, prioritized risks, recommendations, and evidence citations into a structured security report."
        }
    }

    def get_guidance(self, session_id: str, workflow_engine: SecurityWorkflowEngine) -> Dict[str, Any]:
        """Get optimal workflow guidance based on the current active phase."""
        current_phase = workflow_engine.get_active_phase(session_id)
        template = self.GUIDANCE_TEMPLATES.get(current_phase, self.GUIDANCE_TEMPLATES[WorkflowState.RECON])
        
        # Determine next logical phase in the sequence
        current_index = workflow_engine.PHASE_SEQUENCE.index(current_phase)
        next_phase = None
        if current_index + 1 < len(workflow_engine.PHASE_SEQUENCE):
            next_phase = workflow_engine.PHASE_SEQUENCE[current_index + 1]

        return {
            "current_phase": current_phase.value,
            "recommended_action": template["action"],
            "recommended_skills": template["skills"],
            "guidance_message": template["message"],
            "next_logical_phase": next_phase.value if next_phase else None
        }
