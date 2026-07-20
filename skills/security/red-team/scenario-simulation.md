# Cyber Resilience Digital Twin & Red-Team Scenario Simulation Playbook

Playbook for autonomous Graph AI infrastructure topology modeling, Red-Team cyber attack scenario simulation, blast radius analysis, and What-If defensive counter-measure validation.

---

## Overview

Traditional penetration testing and vulnerability scans provide static snapshots of individual systems, missing complex multi-hop attack propagation paths across enterprise and government infrastructure. 

The **Digital Twin Engine** constructs a virtual graph representation of your infrastructure (Nodes: Hosts, Firewalls, Routers, Databases, Domain Controllers; Edges: Network connections, Protocol trust, Active Directory paths) to simulate adversarial campaigns, quantify potential damage before an actual incident occurs, and validate defensive interventions.

---

## Key Metrics & Formulas

### 1. Blast Radius Percentage
$$\text{Blast Radius} = \left(\frac{\text{Compromised Nodes Count}}{\text{Total Network Nodes Count}}\right) \times 100\%$$

### 2. Probability of Compromise (PoC)
$$\text{PoC} = \frac{\sum_{i \in \text{Compromised}} w_i \times P(i)}{\sum_{j \in \text{Total}} w_j}$$
Where $w_i$ is the asset criticality weight (1.0 to 3.0) and $P(i)$ is the infection probability.

### 3. Quantitative Resilience Score (0 - 100)
$$\text{Resilience Score} = \max\left(0.0, 100.0 - (0.6 \times \text{Blast Radius \%} + 40.0 \times \text{PoC})\right)$$

---

## Attack Scenario Templates

| Scenario Key | Attack Name | Initial Vector | Primary Target Assets |
|---|---|---|---|
| `RANSOMWARE_CASCADE` | Ransomware Propagation & Encryption | Phishing Email / SMB Worm | Workstations, File Shares, DBs |
| `APT_LATERAL_MOVEMENT` | Nation-State Stealth Lateral Movement | Compromised Credentials | Domain Controllers, IAM Roles, DBs |
| `ZERO_DAY_CASCADE` | Unpatched RCE Perimeter Cascade | VPN Gateway Exploit | Edge Firewalls, DMZ App Servers |
| `DATA_EXFILTRATION` | Unauthorized Data Exfiltration | Insider / Compromised Service | Primary Databases, Cloud Storage |

---

## Agent Operational Workflow

### Phase 1: Build / Inspect Infrastructure Topology
View existing topology or add new critical infrastructure assets:
```json
{
  "name": "dt_add_node",
  "args": {
    "name": "Primary Core Database",
    "node_type": "DATABASE",
    "department": "FINANCE",
    "ip_address": "10.0.3.50",
    "security_controls": ["ENCRYPTION", "EDR"],
    "vulnerability_count": 1,
    "criticality_weight": 2.5
  }
}
```

Add network connectivity edges between nodes:
```json
{
  "name": "dt_add_edge",
  "args": {
    "source_id": "NODE-APP-01",
    "target_id": "NODE-DB-PRIMARY",
    "protocol": "POSTGRESQL",
    "port": 5432,
    "trust_level": 0.8
  }
}
```

### Phase 2: Execute Red-Team Cyber Attack Simulation
Simulate a Ransomware or APT Lateral Movement campaign starting from a compromised host:
```json
{
  "name": "dt_simulate_attack",
  "args": {
    "scenario_key": "RANSOMWARE_CASCADE",
    "entry_node_id": "NODE-WORKSTATION-42"
  }
}
```

### Phase 3: Validate What-If Defensive Counter-Measures
Test virtual security interventions without risking live operations:
```json
{
  "name": "dt_apply_defense_whatif",
  "args": {
    "sim_id": "SIM-8F3A29B1",
    "defense_actions": [
      {
        "action_type": "MICROSEGMENTATION",
        "source_id": "NODE-WORKSTATION-42",
        "target_id": "NODE-APP-01"
      },
      {
        "action_type": "ENFORCE_MFA",
        "node_id": "NODE-DC-01"
      }
    ]
  }
}
```

### Phase 4: Monitor Digital Twin Resilience Dashboard
Check aggregate network resilience score improvements:
```json
{
  "name": "dt_dashboard_summary",
  "args": {}
}
```
