import sys
from pathlib import Path
import os
import shutil

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.apt_service import APTAttributionService
from rakshastra_core.engines.infrastructure_graph import InfrastructureGraph
from rakshastra_core.models.asset import Asset, AssetType, AssetRelation

def run_test():
    print("Initializing Temp DB Directory...")
    temp_dir = Path(__file__).parent / "temp_apt_test"
    if temp_dir.exists():
        shutil.rmtree(temp_dir)
    temp_dir.mkdir(parents=True, exist_ok=True)

    print("Initializing and Seeding Engines...")
    service = APTAttributionService(db_dir=str(temp_dir))
    
    # Let's verify we have techniques in the store
    groups = service.get_mitre_groups()
    techniques = service.get_mitre_techniques()
    print(f"Loaded {len(groups)} APT groups and {len(techniques)} techniques into MITRE store.")
    
    # Setup some assets in InfrastructureGraph (stored in security.db under temp_dir)
    print("Setting up infrastructure graph...")
    infra_db_path = temp_dir / "security.db"
    infra_graph = InfrastructureGraph(infra_db_path)
    
    # Add a network path: workstation-01 -> web-server-02 -> domain-controller
    w1 = Asset(id="workstation-01", name="workstation-01", asset_type=AssetType.HOST, properties={"os": "Windows 11", "EDR": True, "criticality": "low"})
    w2 = Asset(id="web-server-02", name="web-server-02", asset_type=AssetType.SERVICE, properties={"os": "Ubuntu 22.04", "WAF": True, "criticality": "medium"})
    dc = Asset(id="domain-controller", name="domain-controller", asset_type=AssetType.HOST, properties={"os": "Windows Server 2022", "mfa_enabled": False, "criticality": "critical"})
    
    infra_graph.add_asset(w1)
    infra_graph.add_asset(w2)
    infra_graph.add_asset(w3 := dc)
    
    infra_graph.add_relation(AssetRelation(source_id="workstation-01", target_id="web-server-02", relation_type="connects_to"))
    infra_graph.add_relation(AssetRelation(source_id="web-server-02", target_id="domain-controller", relation_type="connects_to"))

    # Execute full analysis pipeline
    print("\nExecuting Full APT Attribution & Prediction Pipeline...")
    observed_ttps = ["T1566.001", "T1059.001", "T1547.001"] # Spearphishing Attachment, PowerShell, Registry Run Keys
    observed_iocs = ["avsvmcloud.com", "badnews.dll"]
    
    # We pass org_assets to tailor defensive recommendations
    org_assets = [
        {"name": "workstation-01", "asset_type": "host", "properties": {"os": "Windows 11"}},
        {"name": "web-server-02", "asset_type": "web_server", "properties": {"os": "Ubuntu 22.04"}},
        {"name": "domain-controller", "asset_type": "host", "properties": {"os": "Windows Server 2022"}}
    ]
    
    result = service.full_analysis(
        observed_ttps=observed_ttps,
        observed_iocs=observed_iocs,
        target_sector="government",
        target_country="India",
        org_assets=org_assets,
        create_incident=True
    )
    
    print("\n--- ATTRIBUTION RESULT ---")
    print(f"Attributed Group: {result['summary']['attributed_group']}")
    print(f"Confidence Score: {result['summary']['attribution_confidence']:.1%}")
    print(f"Attribution Status: {result['summary']['attribution_status']}")
    print(f"Candidate Groups Evaluated: {len(result['attribution']['candidate_groups'])}")
    
    print("\n--- NEXT-STAGE PREDICTIONS ---")
    print(f"Current Phase: {result['summary']['current_attack_phase']}")
    print(f"Estimated Attack Stage: {result['summary']['attack_stage']}")
    print("Top 3 Predicted Next Techniques:")
    for pred in result['predictions']['top_predictions'][:3]:
        print(f"  - {pred['technique_id']} ({pred['technique_name']}) in Tactic {pred['tactic_name']} (Prob: {pred['probability']:.1%})")
        
    print("\n--- DEFENSIVE ACTIONS ---")
    print(f"Total Recommended Actions: {result['summary']['total_defensive_actions']}")
    print(f"Critical Priority Actions: {result['summary']['critical_actions']}")
    for plan in result['defensive_actions']['defensive_plan'][:2]:
        print(f"Tactic: {plan['tactic_name']} (Urgency: {plan['urgency']})")
        for act in plan['actions'][:2]:
            print(f"  - {act['action']}")
            if 'target_assets' in act:
                print(f"    Target Assets: {act['target_assets']}")

    print("\n--- SOAR INCIDENT CREATION ---")
    print(f"Incident ID: {result['summary']['incident_id']}")
    print(f"Playbook Selected: {result['incident']['playbook_name']} ({result['incident']['playbook_id']})")
    
    # Test playbook execution
    print("\nExecuting/Simulating Playbook Response...")
    exec_result = service.soar_engine.execute_playbook(result['summary']['incident_id'], mode="simulate")
    print(f"Actions Processed: {exec_result['actions_processed']}")
    for act in exec_result['actions'][:3]:
        print(f"  Step {act['step']}: {act['description']} -> {act['status']} ({act['result']})")

    # Clean up
    print("\nCleaning up temp database files...")
    shutil.rmtree(temp_dir)
    print("Verification pipeline test finished successfully!")

if __name__ == "__main__":
    run_test()
