"""Keep the default test suite independent of paid external providers."""
import pytest
from app.core.llm import groq_llm
from app.core.bhashini import bhashini


@pytest.fixture(autouse=True)
def offline_providers(monkeypatch):
    monkeypatch.setattr(groq_llm, "_enabled", False)
    monkeypatch.setattr(type(bhashini), "enabled", property(lambda self: False))
