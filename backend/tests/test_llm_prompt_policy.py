from app.core.llm import _build_user_prompt, SYSTEM_PROMPT


def test_system_prompt_allows_general_fallback_without_retrieved_context():
    assert "simple/general/conversational" in SYSTEM_PROMPT
    assert "general model knowledge" in SYSTEM_PROMPT
    assert "do not force irrelevant" in SYSTEM_PROMPT.lower()


def test_user_prompt_allows_general_fallback_without_rag():
    prompt = _build_user_prompt("hello", None, None)
    assert "No relevant context was retrieved" in prompt
    assert "answer naturally from general model knowledge" in prompt
    assert "do not force irrelevant context" in prompt.lower()
