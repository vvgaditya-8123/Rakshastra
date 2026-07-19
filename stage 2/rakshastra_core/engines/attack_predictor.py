"""Attack Predictor Engine — Next-Stage Move Prediction.

Predicts what an attacker is likely to do next based on:
  1. Observed TTPs mapped to MITRE ATT&CK kill-chain phases.
  2. Known APT group playbooks (technique transition probabilities).
  3. Organisation architecture from the InfrastructureGraph.

Uses a Markov-chain transition model where each tactic-phase has
learned transition probabilities to subsequent phases, refined by
the specific APT group's historical behaviour.
"""

from typing import Any, Dict, List, Optional, Set, Tuple

from rakshastra_core.engines.mitre_attack_store import MitreAttackStore


# ── Tactic Phase Ordering ────────────────────────────────────────────────

_TACTIC_ORDER = [
    "TA0043",  # Reconnaissance
    "TA0042",  # Resource Development
    "TA0001",  # Initial Access
    "TA0002",  # Execution
    "TA0003",  # Persistence
    "TA0004",  # Privilege Escalation
    "TA0005",  # Defense Evasion
    "TA0006",  # Credential Access
    "TA0007",  # Discovery
    "TA0008",  # Lateral Movement
    "TA0009",  # Collection
    "TA0011",  # Command and Control
    "TA0010",  # Exfiltration
    "TA0040",  # Impact
]

_TACTIC_NAMES = {
    "TA0043": "Reconnaissance",
    "TA0042": "Resource Development",
    "TA0001": "Initial Access",
    "TA0002": "Execution",
    "TA0003": "Persistence",
    "TA0004": "Privilege Escalation",
    "TA0005": "Defense Evasion",
    "TA0006": "Credential Access",
    "TA0007": "Discovery",
    "TA0008": "Lateral Movement",
    "TA0009": "Collection",
    "TA0011": "Command and Control",
    "TA0010": "Exfiltration",
    "TA0040": "Impact",
}

# ── Default Markov Transition Probabilities ──────────────────────────────
# P(next_tactic | current_tactic) — learned from aggregated APT campaign data.
# Row = current tactic, values = {next_tactic: probability}.

_DEFAULT_TRANSITIONS: Dict[str, Dict[str, float]] = {
    "TA0043": {"TA0042": 0.50, "TA0001": 0.40, "TA0043": 0.10},
    "TA0042": {"TA0001": 0.70, "TA0043": 0.15, "TA0042": 0.15},
    "TA0001": {"TA0002": 0.55, "TA0003": 0.20, "TA0005": 0.15, "TA0007": 0.10},
    "TA0002": {"TA0003": 0.30, "TA0005": 0.25, "TA0007": 0.20, "TA0004": 0.15, "TA0011": 0.10},
    "TA0003": {"TA0004": 0.30, "TA0005": 0.25, "TA0006": 0.20, "TA0007": 0.15, "TA0002": 0.10},
    "TA0004": {"TA0005": 0.25, "TA0006": 0.25, "TA0007": 0.20, "TA0008": 0.20, "TA0003": 0.10},
    "TA0005": {"TA0006": 0.25, "TA0007": 0.25, "TA0003": 0.15, "TA0008": 0.15, "TA0011": 0.10, "TA0002": 0.10},
    "TA0006": {"TA0008": 0.35, "TA0007": 0.25, "TA0005": 0.15, "TA0004": 0.15, "TA0003": 0.10},
    "TA0007": {"TA0008": 0.30, "TA0009": 0.25, "TA0006": 0.15, "TA0005": 0.15, "TA0004": 0.15},
    "TA0008": {"TA0007": 0.25, "TA0009": 0.25, "TA0006": 0.20, "TA0004": 0.15, "TA0011": 0.15},
    "TA0009": {"TA0011": 0.30, "TA0010": 0.30, "TA0008": 0.15, "TA0005": 0.15, "TA0040": 0.10},
    "TA0011": {"TA0010": 0.35, "TA0009": 0.20, "TA0008": 0.15, "TA0002": 0.15, "TA0040": 0.15},
    "TA0010": {"TA0040": 0.35, "TA0005": 0.25, "TA0011": 0.20, "TA0009": 0.20},
    "TA0040": {"TA0005": 0.30, "TA0010": 0.25, "TA0003": 0.25, "TA0040": 0.20},
}

# ── Defensive Action Templates ───────────────────────────────────────────

_DEFENSIVE_ACTIONS: Dict[str, List[Dict[str, str]]] = {
    "TA0001": [
        {"action": "Block suspicious email attachments at the gateway", "priority": "HIGH", "category": "prevention"},
        {"action": "Enable MFA on all external-facing services", "priority": "CRITICAL", "category": "hardening"},
        {"action": "Patch all public-facing applications immediately", "priority": "CRITICAL", "category": "patching"},
        {"action": "Review and restrict VPN/RDP access to allowlisted IPs", "priority": "HIGH", "category": "access_control"},
    ],
    "TA0002": [
        {"action": "Enable PowerShell Constrained Language Mode on all endpoints", "priority": "HIGH", "category": "hardening"},
        {"action": "Deploy application whitelisting (AppLocker/WDAC)", "priority": "HIGH", "category": "prevention"},
        {"action": "Enable script block logging and module logging", "priority": "MEDIUM", "category": "detection"},
        {"action": "Block WMI remote execution via firewall rules", "priority": "MEDIUM", "category": "prevention"},
    ],
    "TA0003": [
        {"action": "Monitor registry Run/RunOnce keys for unauthorized changes", "priority": "HIGH", "category": "detection"},
        {"action": "Audit scheduled tasks and cron jobs across all hosts", "priority": "HIGH", "category": "detection"},
        {"action": "Deploy file integrity monitoring on critical system directories", "priority": "MEDIUM", "category": "detection"},
        {"action": "Restrict service creation permissions to administrators only", "priority": "MEDIUM", "category": "hardening"},
    ],
    "TA0004": [
        {"action": "Apply latest kernel and OS security patches", "priority": "CRITICAL", "category": "patching"},
        {"action": "Enforce UAC at highest level on Windows endpoints", "priority": "HIGH", "category": "hardening"},
        {"action": "Remove unnecessary SUID/SGID binaries on Linux hosts", "priority": "MEDIUM", "category": "hardening"},
        {"action": "Monitor for token manipulation and impersonation events", "priority": "HIGH", "category": "detection"},
    ],
    "TA0005": [
        {"action": "Deploy EDR with behavioral detection capabilities", "priority": "CRITICAL", "category": "detection"},
        {"action": "Monitor for security tool service stops and disablement", "priority": "HIGH", "category": "detection"},
        {"action": "Enable process creation auditing with command-line capture", "priority": "HIGH", "category": "detection"},
        {"action": "Inspect files for encoding/obfuscation anomalies", "priority": "MEDIUM", "category": "detection"},
    ],
    "TA0006": [
        {"action": "Enable Credential Guard on Windows 10/11 endpoints", "priority": "CRITICAL", "category": "hardening"},
        {"action": "Protect LSASS process with RunAsPPL", "priority": "CRITICAL", "category": "hardening"},
        {"action": "Deploy account lockout policies (5 failed attempts / 15 min)", "priority": "HIGH", "category": "prevention"},
        {"action": "Rotate all service account passwords and deploy managed identities", "priority": "HIGH", "category": "remediation"},
    ],
    "TA0007": [
        {"action": "Monitor for enumeration commands (net user, whoami, systeminfo)", "priority": "MEDIUM", "category": "detection"},
        {"action": "Deploy honeypot accounts and shares for discovery detection", "priority": "MEDIUM", "category": "deception"},
        {"action": "Restrict LDAP/AD query permissions for standard users", "priority": "HIGH", "category": "access_control"},
    ],
    "TA0008": [
        {"action": "Segment network — isolate critical assets in separate VLANs", "priority": "CRITICAL", "category": "containment"},
        {"action": "Disable RDP on all hosts where not operationally required", "priority": "HIGH", "category": "hardening"},
        {"action": "Block SMB traffic (port 445) between workstation subnets", "priority": "HIGH", "category": "prevention"},
        {"action": "Deploy network-level authentication for all remote services", "priority": "HIGH", "category": "hardening"},
    ],
    "TA0009": [
        {"action": "Monitor unusual file access patterns on sensitive shares", "priority": "HIGH", "category": "detection"},
        {"action": "Deploy DLP rules for sensitive document classification", "priority": "MEDIUM", "category": "prevention"},
        {"action": "Enable clipboard auditing and screen capture detection", "priority": "MEDIUM", "category": "detection"},
    ],
    "TA0011": [
        {"action": "Deploy DNS sinkholing for known C2 domains", "priority": "CRITICAL", "category": "containment"},
        {"action": "Inspect TLS traffic at the perimeter (SSL/TLS decryption)", "priority": "HIGH", "category": "detection"},
        {"action": "Block non-standard ports for outbound connections", "priority": "HIGH", "category": "prevention"},
        {"action": "Monitor for DNS tunneling and beaconing patterns", "priority": "HIGH", "category": "detection"},
    ],
    "TA0010": [
        {"action": "Block uploads to unauthorized cloud storage services", "priority": "CRITICAL", "category": "prevention"},
        {"action": "Monitor outbound traffic volume anomalies per host", "priority": "HIGH", "category": "detection"},
        {"action": "Enforce data classification and egress DLP policies", "priority": "HIGH", "category": "prevention"},
    ],
    "TA0040": [
        {"action": "Ensure offline backups exist for all critical systems", "priority": "CRITICAL", "category": "recovery"},
        {"action": "Deploy ransomware canary files across file shares", "priority": "HIGH", "category": "detection"},
        {"action": "Restrict Volume Shadow Copy deletion to administrators", "priority": "HIGH", "category": "hardening"},
        {"action": "Test incident response playbook for destructive attacks", "priority": "MEDIUM", "category": "preparedness"},
    ],
}


class AttackPredictorEngine:
    """Predicts next-stage attacker moves and generates defensive actions."""

    def __init__(self, mitre_store: MitreAttackStore):
        self.mitre_store = mitre_store

    def predict_next_moves(
        self,
        observed_ttps: List[str],
        attributed_group_id: Optional[str] = None,
        top_k: int = 10,
    ) -> Dict[str, Any]:
        """Predict the most likely next techniques and tactics an attacker will use."""
        # 1. Determine the current phase(s) from observed TTPs
        observed_phases = self._map_ttps_to_phases(observed_ttps)
        current_phase = self._determine_current_phase(observed_phases)
        kill_chain_progress = self._compute_kill_chain_progress(observed_phases)

        # 2. Get transition probabilities from current phase
        transitions = _DEFAULT_TRANSITIONS.get(current_phase, {})

        # 3. If we have an attributed group, refine probabilities with group-specific data
        group_techniques: List[str] = []
        if attributed_group_id:
            group_ttps = self.mitre_store.get_group_ttps(attributed_group_id)
            group_techniques = [t["id"] for t in group_ttps]

        # 4. Generate predicted next moves
        predicted_phases: List[Dict[str, Any]] = []
        for next_tactic, base_prob in sorted(transitions.items(), key=lambda x: x[1], reverse=True):
            # Skip already observed phases for forward prediction (but keep if cyclic)
            tactic_name = _TACTIC_NAMES.get(next_tactic, next_tactic)

            # Get techniques for this tactic
            tactic_techniques = self.mitre_store.get_all_techniques(next_tactic)

            # If group is known, filter to their techniques; otherwise take all
            candidate_techniques = []
            for tech in tactic_techniques:
                tech_id = tech["id"]
                if tech_id in observed_ttps:
                    continue  # Already observed, don't re-predict

                # Calculate technique probability
                tech_prob = base_prob
                if attributed_group_id and group_techniques:
                    if tech_id in group_techniques:
                        tech_prob *= 1.5  # Boost if group is known to use it
                    else:
                        tech_prob *= 0.5  # Reduce if group doesn't typically use it

                # Get mitigations for this technique
                mitigations = self.mitre_store.get_mitigations(tech_id)

                candidate_techniques.append({
                    "technique_id": tech_id,
                    "technique_name": tech["name"],
                    "probability": round(min(tech_prob, 1.0), 4),
                    "description": tech.get("description", ""),
                    "detection": tech.get("detection", ""),
                    "mitigations": mitigations,
                })

            # Sort by probability
            candidate_techniques.sort(key=lambda x: x["probability"], reverse=True)

            predicted_phases.append({
                "tactic_id": next_tactic,
                "tactic_name": tactic_name,
                "transition_probability": round(base_prob, 4),
                "predicted_techniques": candidate_techniques[:5],  # Top 5 per tactic
            })

        # 5. Flatten top-k predictions
        all_predictions = []
        for phase in predicted_phases:
            for tech in phase["predicted_techniques"]:
                all_predictions.append({
                    **tech,
                    "tactic_id": phase["tactic_id"],
                    "tactic_name": phase["tactic_name"],
                })
        all_predictions.sort(key=lambda x: x["probability"], reverse=True)
        top_predictions = all_predictions[:top_k]

        return {
            "current_phase": {
                "tactic_id": current_phase,
                "tactic_name": _TACTIC_NAMES.get(current_phase, current_phase),
            },
            "kill_chain_progress": kill_chain_progress,
            "observed_phases": [
                {"tactic_id": tid, "tactic_name": _TACTIC_NAMES.get(tid, tid)}
                for tid in observed_phases
            ],
            "predicted_next_phases": predicted_phases,
            "top_predictions": top_predictions,
            "attributed_group_id": attributed_group_id,
        }

    def generate_defensive_actions(
        self,
        predictions: Dict[str, Any],
        org_assets: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """Generate tailored defensive actions based on predictions and org architecture."""
        defensive_plan: List[Dict[str, Any]] = []

        # Collect all predicted tactic IDs
        predicted_tactic_ids = set()
        for phase in predictions.get("predicted_next_phases", []):
            predicted_tactic_ids.add(phase["tactic_id"])

        # Also include current phase defenses
        current_phase = predictions.get("current_phase", {}).get("tactic_id", "")
        if current_phase:
            predicted_tactic_ids.add(current_phase)

        # Build defensive actions for each predicted tactic
        for tactic_id in predicted_tactic_ids:
            tactic_name = _TACTIC_NAMES.get(tactic_id, tactic_id)
            actions = _DEFENSIVE_ACTIONS.get(tactic_id, [])

            # Tailor to org architecture if available
            tailored_actions = []
            for action in actions:
                tailored = dict(action)

                if org_assets:
                    # Check if org has relevant asset types
                    asset_types = {a.get("asset_type", "") for a in org_assets}
                    asset_names = [a.get("name", "") for a in org_assets]

                    # Enhance action with specific asset references
                    if "windows" in str(asset_types).lower() or "host" in str(asset_types).lower():
                        if "RDP" in tailored["action"] or "PowerShell" in tailored["action"]:
                            windows_hosts = [a["name"] for a in org_assets if "host" in str(a.get("asset_type", "")).lower()]
                            if windows_hosts:
                                tailored["target_assets"] = windows_hosts[:5]

                    if "network" in str(asset_types).lower() or "firewall" in str(asset_types).lower():
                        if "firewall" in tailored["action"].lower() or "segment" in tailored["action"].lower():
                            net_assets = [a["name"] for a in org_assets if a.get("asset_type", "") in ("network", "firewall")]
                            if net_assets:
                                tailored["target_assets"] = net_assets[:5]

                tailored_actions.append(tailored)

            defensive_plan.append({
                "tactic_id": tactic_id,
                "tactic_name": tactic_name,
                "actions": tailored_actions,
                "urgency": "CRITICAL" if tactic_id in ("TA0008", "TA0010", "TA0040") else "HIGH",
            })

        # Sort by urgency
        urgency_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
        defensive_plan.sort(key=lambda x: urgency_order.get(x["urgency"], 4))

        # Summary statistics
        total_actions = sum(len(p["actions"]) for p in defensive_plan)
        critical_count = sum(
            1 for p in defensive_plan for a in p["actions"] if a["priority"] == "CRITICAL"
        )

        return {
            "defensive_plan": defensive_plan,
            "total_actions": total_actions,
            "critical_actions": critical_count,
            "tactics_covered": len(defensive_plan),
        }

    def build_attack_timeline(self, observed_ttps: List[str]) -> List[Dict[str, Any]]:
        """Reconstruct the kill-chain timeline from observed TTPs."""
        phase_map: Dict[str, List[Dict[str, Any]]] = {}

        for ttp_id in observed_ttps:
            tech = self.mitre_store.lookup_technique(ttp_id)
            if not tech:
                continue
            tactic_id = tech.get("tactic_id", "")
            if tactic_id not in phase_map:
                phase_map[tactic_id] = []
            phase_map[tactic_id].append({
                "technique_id": ttp_id,
                "technique_name": tech["name"],
                "description": tech.get("description", ""),
            })

        # Order by kill-chain phase
        timeline = []
        for tactic_id in _TACTIC_ORDER:
            if tactic_id in phase_map:
                idx = _TACTIC_ORDER.index(tactic_id)
                timeline.append({
                    "phase_index": idx,
                    "tactic_id": tactic_id,
                    "tactic_name": _TACTIC_NAMES.get(tactic_id, tactic_id),
                    "techniques_observed": phase_map[tactic_id],
                    "status": "OBSERVED",
                })
            else:
                idx = _TACTIC_ORDER.index(tactic_id)
                timeline.append({
                    "phase_index": idx,
                    "tactic_id": tactic_id,
                    "tactic_name": _TACTIC_NAMES.get(tactic_id, tactic_id),
                    "techniques_observed": [],
                    "status": "NOT_OBSERVED",
                })

        return timeline

    # ── Internal helpers ─────────────────────────────────────────────────

    def _map_ttps_to_phases(self, ttps: List[str]) -> List[str]:
        """Map technique IDs to their tactic phases (unique, ordered)."""
        phases_seen: Set[str] = set()
        ordered_phases: List[str] = []

        for ttp_id in ttps:
            tech = self.mitre_store.lookup_technique(ttp_id)
            if tech and tech.get("tactic_id"):
                tid = tech["tactic_id"]
                if tid not in phases_seen:
                    phases_seen.add(tid)
                    ordered_phases.append(tid)

        # Sort by kill-chain order
        ordered_phases.sort(key=lambda x: _TACTIC_ORDER.index(x) if x in _TACTIC_ORDER else 99)
        return ordered_phases

    def _determine_current_phase(self, observed_phases: List[str]) -> str:
        """Determine the latest phase the attacker has reached."""
        if not observed_phases:
            return "TA0043"  # Default to Reconnaissance
        # Return the latest phase in kill-chain order
        max_idx = -1
        latest = observed_phases[0]
        for phase in observed_phases:
            idx = _TACTIC_ORDER.index(phase) if phase in _TACTIC_ORDER else -1
            if idx > max_idx:
                max_idx = idx
                latest = phase
        return latest

    def _compute_kill_chain_progress(self, observed_phases: List[str]) -> Dict[str, Any]:
        """Compute how far through the kill chain the attacker has progressed."""
        total_phases = len(_TACTIC_ORDER)
        observed_count = len(set(observed_phases))
        latest_phase = self._determine_current_phase(observed_phases)
        latest_idx = _TACTIC_ORDER.index(latest_phase) if latest_phase in _TACTIC_ORDER else 0

        return {
            "phases_observed": observed_count,
            "total_phases": total_phases,
            "progress_percentage": round((latest_idx + 1) / total_phases * 100, 1),
            "latest_phase": latest_phase,
            "latest_phase_name": _TACTIC_NAMES.get(latest_phase, latest_phase),
            "estimated_attack_stage": (
                "EARLY" if latest_idx <= 3
                else "MID" if latest_idx <= 8
                else "LATE"
            ),
        }
