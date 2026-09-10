import asyncio
import json
from unittest.mock import AsyncMock, patch

import httpx
import pytest
from fastapi.testclient import TestClient

from app.config import settings
from app.core.knowledge_graph import knowledge_graph
from app.core.llm import groq_llm
from app.core.voice import voice_service
from app.data.models import MultiRAGQueryRequest, RAGEvidence
from app.main import app, _get_frontend_dist
from app.orchestrator.http_connector import HTTPRAGConnector
from app.orchestrator.registry import rag_registry
from app.orchestrator.service import orchestrator_service


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as test_client:
        yield test_client


def test_search_filters_and_document_roundtrip(client):
    for corpus in ("knowledge", "legal"):
        health = client.get(f"/api/v1/rag/{corpus}/health").json()
        for mode in ("bm25", "vector", "hybrid"):
            response = client.post(f"/api/v1/rag/{corpus}/search", json={
                "query": "patent traditional knowledge", "mode": mode, "top_k": 3,
                "domain": health["domains_indexed"][0],
            })
            assert response.status_code == 200
            data = response.json()
            assert data["total_hits"] <= 3
            assert all(item["domain"] == health["domains_indexed"][0] for item in data["results"])
    response = client.post("/api/v1/rag/legal/search", json={"query": "TRIPS", "jurisdiction": "INTERNATIONAL"})
    assert response.status_code == 200
    hits = response.json()["results"]
    assert hits
    document = client.get(f"/api/v1/rag/legal/documents/{hits[0]['document_id']}").json()
    assert document["jurisdiction"] == "INTERNATIONAL"


def test_invalid_historical_dates_are_rejected(client):
    for value in ("yesterday", "2026-02-30", ""):
        assert client.post("/api/v1/rag/legal/historical", json={"query": "patents", "requested_date": value}).status_code == 422
        assert client.post("/api/v1/rag/legal/query", json={"query": "patents", "as_of_date": value}).status_code == 422


def test_voice_multipart_contract_and_unavailable_error(client):
    with patch.object(voice_service, "transcribe_audio", new_callable=AsyncMock, return_value=("A question", "ta", {"provider": "test"})) as transcribe:
        response = client.post("/api/v1/voice/transcribe", files={"file": ("recording.m4a", b"audio" * 100, "audio/mp4")}, data={"language": "ta"})
        assert response.status_code == 200
        assert response.json()["text"] == "A question"
        assert transcribe.call_args.kwargs["language"] == "ta"
        assert transcribe.call_args.kwargs["content_type"] == "audio/mp4"
    with patch.object(voice_service, "transcribe_audio", new_callable=AsyncMock, side_effect=RuntimeError("Unavailable")):
        assert client.post("/api/v1/voice/transcribe", files={"file": ("audio.webm", b"audio" * 100)}).status_code == 503


def test_review_preserves_full_answer_and_evidence(client, tmp_path, monkeypatch):
    destination = tmp_path / "review.jsonl"
    monkeypatch.setattr(settings, "ESCALATION_STORE_PATH", destination)
    monkeypatch.setattr(settings, "HUMAN_ESCALATION_ENABLED", True)
    payload = {"query": "A research question", "answer": "a" * 13000, "language": "ta", "jurisdiction": "INTERNATIONAL", "confidence": 0.5,
               "citations": [{"document_id": "DOC", "chunk_id": str(index), "title": "Source", "source_name": "Authority", "rag_source": "RAG2"} for index in range(20)]}
    response = client.post("/api/v1/human/escalate", json=payload)
    assert response.status_code == 200
    stored = json.loads(destination.read_text(encoding="utf-8"))
    assert stored["answer"] == payload["answer"]
    assert len(stored["citations"]) == 20
    assert stored["language"] == "ta"
    assert stored["jurisdiction"] == "INTERNATIONAL"


def test_international_trace_excludes_domestic_graph_and_rules(client):
    data = client.post("/api/v1/orchestrator/query", json={"query": "patent formulation", "jurisdiction": "INTERNATIONAL"}).json()
    assert data["graph"]["nodes"] == []
    assert data["agentic_reasoning"]["statutory_checks"] == []
    assert data["agentic_reasoning"]["action_plan"] == []


def test_graph_selection_is_deterministic_and_does_not_default_unrelated_questions():
    assert knowledge_graph.extract_relevant_subgraph("hello", [])["nodes"] == []
    graph = knowledge_graph.extract_relevant_subgraph("turmeric", [])
    assert graph == knowledge_graph.extract_relevant_subgraph("turmeric", [])
    assert any(node["id"] == "bio_turmeric" for node in graph["nodes"])


def test_remote_failure_raises_instead_of_reporting_a_response():
    connector = HTTPRAGConnector("test", "https://example.test")
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock, return_value=httpx.Response(503)):
        with pytest.raises(RuntimeError):
            asyncio.run(connector.query("query"))


def test_registered_prior_art_service_participates_in_synthesis():
    connector = HTTPRAGConnector("test_prior_art", "https://example.test", role="prior_art")
    evidence = RAGEvidence(document_id="DOC", chunk_id="same-id", title="Prior art", source_name="Remote", text="Remote passage", rag_source=connector.rag_id)
    connector.query = AsyncMock(return_value=("Prior art context", [evidence], 0.8))
    rag_registry.register(connector)
    try:
        with patch.object(groq_llm, "generate_answer", new_callable=AsyncMock, return_value="Answer") as generate:
            result = asyncio.run(orchestrator_service.execute_query(MultiRAGQueryRequest(query="prior art", target_rags=[connector.rag_id])))
        assert "[S1]" in generate.call_args.kwargs["domain_context"]
        assert "Remote passage" in generate.call_args.kwargs["domain_context"]
        assert result.connected_rags_responded == [connector.rag_id]
    finally:
        rag_registry.unregister(connector.rag_id)


def test_root_frontend_build_is_preferred_over_packaged_fallback(tmp_path, monkeypatch):
    backend = tmp_path / "backend"
    root_dist = tmp_path / "frontend" / "dist"
    bundled_dist = backend / "frontend" / "dist"
    for directory in (root_dist, bundled_dist):
        directory.mkdir(parents=True)
        (directory / "index.html").write_text("test", encoding="utf-8")
    monkeypatch.setattr(settings, "BASE_DIR", backend)
    assert _get_frontend_dist() == root_dist
