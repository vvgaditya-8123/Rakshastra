import os
import tempfile
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

from rakshastra_core.models.behavior import (
    BehaviorBaseline,
    AnomalyEvent,
    EntityType,
    AnomalyCategory,
)
from rakshastra_core.engines.behavioral_analytics import BehavioralAnalyticsEngine
from tools.behavioral_anomaly_tool import (
    behavioral_ingest_handler,
    behavioral_collect_system_handler,
    behavioral_query_anomalies_handler,
    behavioral_get_baselines_handler,
    behavioral_summary_handler,
    behavioral_rebuild_baseline_handler,
)


@pytest.fixture
def temp_db():
    """Create a temporary SQLite database for testing."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    db_path = Path(path)
    yield db_path
    if db_path.exists():
        try:
            os.remove(db_path)
        except OSError:
            pass


def test_models_serialization():
    """Test BehaviorBaseline and AnomalyEvent serialization."""
    baseline = BehaviorBaseline(
        entity_id="test_user",
        entity_type=EntityType.USER,
        feature_name="login_hour",
        baseline_mean=9.5,
        baseline_std=0.5,
        sample_count=10,
    )
    serialized = baseline.to_dict()
    assert serialized["entity_id"] == "test_user"
    assert serialized["entity_type"] == "USER"
    assert serialized["baseline_mean"] == 9.5

    deserialized = BehaviorBaseline.from_dict(serialized)
    assert deserialized.entity_id == "test_user"
    assert deserialized.entity_type == EntityType.USER
    assert deserialized.baseline_mean == 9.5


def test_engine_ingestion_and_baselining(temp_db):
    """Test engine ingestion, baseline building, and online statistical updates."""
    engine = BehavioralAnalyticsEngine(temp_db)
    
    # Ingest initial observations to build baseline (minimum is 5 samples)
    # Let's ingest values around 10.0 (e.g. 9, 10, 11, 9, 11)
    for val in [9.0, 10.0, 11.0, 9.0, 11.0]:
        anomaly = engine.ingest_observation("user1", "USER", "login_hour", val)
        assert anomaly is None  # Not enough samples to score yet

    # Check baseline stats
    bl = engine._get_baseline("user1", "login_hour")
    assert bl is not None
    assert bl.sample_count == 5
    assert bl.baseline_mean == 10.0
    # Mean is 10.0. Std dev: values are [9, 10, 11, 9, 11]
    # Variance = (1+0+1+1+1)/5 = 0.8. Std = sqrt(0.8) ~= 0.894
    assert abs(bl.baseline_std - 0.894) < 0.05

    # 6th observation: Ingest an anomalous value (e.g. 24.0)
    # Z-score = (24 - 10) / 0.894 ~= 15.65 (very high)
    anomaly = engine.ingest_observation("user1", "USER", "login_hour", 24.0)
    assert anomaly is not None
    assert anomaly.deviation_score > 5.0
    assert anomaly.severity.value == "CRITICAL"
    assert anomaly.category == AnomalyCategory.LOGIN_TIME


def test_engine_queries_and_summary(temp_db):
    """Test engine query and summary statistics methods."""
    engine = BehavioralAnalyticsEngine(temp_db)
    
    # Ingest a baseline
    for val in [10.0] * 5:
        engine.ingest_observation("user2", "USER", "login_hour", val)
        
    # Trigger an anomaly
    engine.ingest_observation("user2", "USER", "login_hour", 20.0)
    
    anomalies = engine.get_anomalies(entity_id="user2")
    assert len(anomalies) == 1
    assert anomalies[0]["entity_id"] == "user2"
    assert anomalies[0]["observed_value"] == 20.0

    baselines = engine.get_baselines(entity_id="user2")
    assert len(baselines) == 1
    assert baselines[0]["feature_name"] == "login_hour"

    summary = engine.get_anomaly_summary()
    assert summary["total_anomalies"] == 1
    assert summary["total_baselines"] == 1
    assert summary["total_observations"] == 6


@patch("tools.behavioral_anomaly_tool._get_engine")
def test_tool_handlers(mock_get_engine, temp_db):
    """Test the behavioral anomaly detection tool handlers."""
    engine = BehavioralAnalyticsEngine(temp_db)
    mock_get_engine.return_value = engine

    # Ingest tool
    res_json = behavioral_ingest_handler({
        "entity_id": "device1",
        "entity_type": "DEVICE",
        "feature_name": "process_count",
        "value": 150.0,
    })
    import json
    res = json.loads(res_json)
    assert res["success"] is True
    assert res["anomaly_detected"] is False

    # Summary tool
    sum_json = behavioral_summary_handler({})
    summary = json.loads(sum_json)
    assert summary["success"] is True
    assert summary["total_observations"] == 1

    # Query anomalies tool
    q_json = behavioral_query_anomalies_handler({"entity_id": "device1"})
    q_res = json.loads(q_json)
    assert q_res["success"] is True
    assert q_res["count"] == 0

    # Get baselines tool
    b_json = behavioral_get_baselines_handler({"entity_id": "device1"})
    b_res = json.loads(b_json)
    assert b_res["success"] is True
    assert b_res["count"] == 1
    assert b_res["baselines"][0]["entity_id"] == "device1"
