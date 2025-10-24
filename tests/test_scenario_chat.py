import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app

client = TestClient(app)

@patch("backend.assistants.run_assistant")
def test_scenario_chat_basic(mock_assistant):
    """Test basic scenario chat flow"""
    
    # Mock assistant responses
    def mock_responses(assistant_id, user_text):
        if "Finance" in user_text:
            return 'Financial analysis: You can afford 1-2 hires. Deltas: {"deltas": [{"lever":"headcount","delta_abs":2}]}'
        elif "Research" in user_text:
            return "No external signals needed."
        else:  # Orchestrator
            return '{"message": "Based on $28.5K monthly cash flow and 5.9 months runway, you can afford 1-2 new hires.", "propose_deltas": [{"lever":"headcount","delta_abs":2}], "horizon_days": 90}'
    
    mock_assistant.side_effect = mock_responses
    
    # Test request
    response = client.post(
        "/api/intent",
        json={
            "intent": "scenario_chat",
            "input": {"question": "Can we hire 2 techs next month?"},
            "company_id": "demo"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert "message" in data
    assert "assumptions_used" in data
    assert isinstance(data["message"], str)
    assert len(data["message"]) > 0
    
    # Simulation may or may not be present
    if "simulation" in data:
        assert "summary" in data["simulation"]


@patch("backend.assistants.run_assistant")
def test_scenario_chat_pricing(mock_assistant):
    """Test pricing question"""
    
    def mock_responses(assistant_id, user_text):
        if "Finance" in user_text:
            return 'Price analysis: 5% increase feasible. {"deltas": [{"lever":"price","delta_pct":5}]}'
        else:
            return '{"message": "A 5% price increase could boost margins by 1-2pp.", "propose_deltas": [{"lever":"price","delta_pct":5}], "horizon_days": 60}'
    
    mock_assistant.side_effect = mock_responses
    
    response = client.post(
        "/api/intent",
        json={
            "intent": "scenario_chat",
            "input": {"question": "Should we increase prices by 5%?"},
            "company_id": "demo"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "message" in data


@patch("backend.assistants.run_assistant")
def test_scenario_chat_no_question(mock_assistant):
    """Test with empty question"""
    
    response = client.post(
        "/api/intent",
        json={
            "intent": "scenario_chat",
            "input": {},
            "company_id": "demo"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "Please ask" in data["message"]
