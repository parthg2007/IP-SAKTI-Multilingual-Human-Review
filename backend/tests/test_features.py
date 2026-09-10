import json
from pathlib import Path

from fastapi.testclient import TestClient

from app.data.models import HumanEscalationRequest, MultiRAGQueryResponse
from app.main import app


def test_multirag_response_requires_confidence_contract():
    assert "confidence" in MultiRAGQueryResponse.model_fields


def test_human_escalation_creates_case(tmp_path, monkeypatch):
    monkeypatch.setattr("app.config.settings.ESCALATION_STORE_PATH", tmp_path / "cases.jsonl")
    monkeypatch.setattr("app.config.settings.HUMAN_ESCALATION_ENABLED", True)
    with TestClient(app) as client:
        response = client.post("/api/v1/human/escalate", json={"query": "Need help", "language": "en", "jurisdiction": "INDIA"})
    assert response.status_code == 200
    data = response.json()
    assert data["case_id"].startswith("IPF-")
    assert data["status"] == "queued_for_human_review"
    assert (tmp_path / "cases.jsonl").exists()
    record = json.loads((tmp_path / "cases.jsonl").read_text().strip())
    assert record["query"] == "Need help"


def test_languages_endpoint_lists_bhashini_languages():
    with TestClient(app) as client:
        response = client.get("/api/v1/languages")
    assert response.status_code == 200
    codes = {item["code"] for item in response.json()["languages"]}
    assert {"en", "hi", "bn", "ta", "te"}.issubset(codes)
