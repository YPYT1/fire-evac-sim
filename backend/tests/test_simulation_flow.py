"""端到端模拟流程测试：start → status → stop。"""

import os

from fastapi.testclient import TestClient

from backend.app.dependencies import get_session_manager
from backend.app.main import create_app
from backend.app.services.session_manager import SessionManager


def test_simulation_lifecycle():
    os.environ.setdefault("SIM_CONFIG_PATH", "backend/app/data/config/simulation.yaml")
    app = create_app()
    manager = SessionManager()
    app.dependency_overrides[get_session_manager] = lambda: manager

    client = TestClient(app)

    start_payload = {
        "mode": "floor1",
        "agents": {"count": 10, "speed_mean": 1.2, "speed_std": 0.1},
        "goals": ["north_door"],
    }
    start_response = client.post("/sim/start", json=start_payload)
    assert start_response.status_code == 200
    start_data = start_response.json()
    session_id = start_data["session_id"]
    assert session_id

    status_response = client.get("/sim/status", params={"session_id": session_id})
    assert status_response.status_code == 200
    status_data = status_response.json()
    assert status_data["session_id"] == session_id
    assert status_data["agent_count"] == 10
    assert status_data["tick_hz"] > 0
    assert "fire_decay" in status_data

    stop_response = client.post("/sim/stop", json={"session_id": session_id})
    assert stop_response.status_code == 204

    late_status = client.get("/sim/status", params={"session_id": session_id})
    assert late_status.status_code == 404

    app.dependency_overrides.clear()
