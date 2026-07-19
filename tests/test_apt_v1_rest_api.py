import pytest
from fastapi.testclient import TestClient
from rakshastra_cli.web_server import app

client = TestClient(app)

def test_apt_get_groups():
    response = client.get("/api/v1/apt/groups")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    # Check shape
    group = data[0]
    assert "id" in group
    assert "name" in group

def test_apt_get_tactics():
    response = client.get("/api/v1/apt/tactics")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    tactic = data[0]
    assert "id" in tactic
    assert "name" in tactic

def test_apt_get_techniques():
    response = client.get("/api/v1/apt/techniques")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    tech = data[0]
    assert "id" in tech
    assert "name" in tech

def test_apt_attribute():
    payload = {
        "observed_ttps": ["T1566.001", "T1059.001"],
        "observed_iocs": ["avsvmcloud.com"],
        "target_sector": "government",
        "target_country": "India"
    }
    response = client.post("/api/v1/apt/attribute", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "candidate_groups" in data
    assert len(data["candidate_groups"]) > 0
    assert "group_name" in data["candidate_groups"][0]

def test_apt_predict():
    payload = {
        "observed_ttps": ["T1566.001", "T1059.001"],
        "top_k": 3
    }
    response = client.post("/api/v1/apt/predict", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "top_predictions" in data
    assert "current_phase" in data

def test_apt_full_analysis():
    payload = {
        "observed_ttps": ["T1566.001", "T1059.001"],
        "observed_iocs": ["avsvmcloud.com"],
        "target_sector": "government",
        "target_country": "India",
        "org_assets": [
            {"name": "workstation-01", "asset_type": "host", "properties": {"os": "Windows 11"}},
            {"name": "domain-controller", "asset_type": "host", "properties": {"os": "Windows Server 2022"}}
        ],
        "create_incident": True
    }
    response = client.post("/api/v1/apt/full-analysis", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "summary" in data
    assert "attribution" in data
    assert "predictions" in data
    assert "defensive_actions" in data
    assert "incident" in data

def test_threat_intel_search():
    payload = {
        "query": "Transparent Tribe Defense",
        "top_k": 3
    }
    response = client.post("/api/v1/threat-intel/search", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

def test_soar_playbooks():
    response = client.get("/api/v1/soar/playbooks")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    pb = data[0]
    assert "id" in pb
    assert "name" in pb

def test_attack_graph_chokepoints():
    response = client.get("/api/v1/attack-graph/chokepoints")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

def test_ueba_anomalies():
    payload = {
        "category": "APT_BEACONING",
        "limit": 10
    }
    response = client.post("/api/v1/ueba/anomalies", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
