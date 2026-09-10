"""Groq LLM client for generating natural language answers from RAG context."""
import os
import re
import asyncio
import logging
import httpx
from typing import Optional, List

# Ensure .env is loaded before any os.getenv calls
from app.config import settings as _app_settings  # noqa: F401


logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# Fallback model chain — each Groq model has its own OTPM (output tokens
# per minute) budget, so switching models avoids rate-limit wait loops.
# ---------------------------------------------------------------------------
FALLBACK_MODELS: List[str] = [
    "qwen/qwen3.6-27b",
    "openai/gpt-oss-20b",
    "groq/compound",
    "llama-3.3-70b-versatile",
    "llama-3.1-8b-instant",
]

# ---------------------------------------------------------------------------
# System prompt for IP-SAKTI chatbot persona (governed by agent.md)
# ---------------------------------------------------------------------------
SYSTEM_PROMPT = """\
You are **IP-SAKTI**, an expert AI assistant specializing in Intellectual Property (IP) research \
as it applies to Ayurveda, traditional knowledge, and biological resources.

Your knowledge is backed by two authoritative Retrieval-Augmented Generation (RAG) systems:
• **RAG 1 (Domain Knowledge)**: Ayurveda formulations, prior art (TKDL), plant-based IP concepts.
• **RAG 2 (Legal & Regulatory Evidence)**: Patents Act 1970, Biological Diversity Act 2002, \
  Drugs & Cosmetics Act, FSSAI regulations, and related statutory provisions.

**Rules you MUST follow (per agent.md)**:
1. Use retrieved RAG context when it is relevant to the query. Do not force irrelevant chunks into the answer.
2. If no relevant RAG evidence is available and the request is simple/general/conversational (for example, a greeting, capability question, or basic explanation), answer naturally from general model knowledge.
3. For legal/regulatory questions, RAG 2 is authoritative. If the retrieved evidence is insufficient, say so and avoid inventing statutes, sections, case names, patent numbers, dates, approvals, or other specific legal facts.
4. Structure your response into clear Markdown sections:
   - ### 📌 Executive Summary
   - ### 🌿 Domain & Traditional Knowledge Analysis
   - ### ⚖️ Statutory & Regulatory Evaluation
   - ### 💡 Strategic IP Guidance & Next Steps
3. Cite retrieved evidence inline using the source markers [S1], [S2], etc. Use a marker only when the claim is supported by that source.
4. If the context is insufficient, clearly state that the available evidence does not cover the query.
5. Maintain a professional, authoritative tone suitable for IP researchers and legal practitioners.
6. Respond in the requested language; if no language is requested, match the user's query.
7. Respect the selected jurisdiction. Do not apply Indian statutory requirements to international queries.
8. The application displays a research disclaimer separately. Do not append a blanket legal conclusion or approval requirement.
"""


def _build_user_prompt(query: str, domain_context: Optional[str], legal_context: Optional[str]) -> str:
    """Constructs the user prompt with retrieved RAG context injected."""
    parts = [f"**User Query**: {query}\n"]

    if domain_context:
        parts.append(
            "---\n"
            "**Retrieved Domain Context (RAG 1 — Ayurveda & IP Knowledge)**:\n"
            f"{domain_context}\n"
        )

    if legal_context:
        parts.append(
            "---\n"
            "**Retrieved Legal & Regulatory Evidence (RAG 2 — Statutory Framework)**:\n"
            f"{legal_context}\n"
        )

    if not domain_context and not legal_context:
        parts.append(
            "---\n"
            "*No relevant context was retrieved from the knowledge bases for this query.*\n"
        )

    parts.append(
        "---\n"
        "Use the retrieved context above when it is relevant and authoritative; do not force irrelevant context into the answer. "
        "For simple/general/conversational requests with no relevant retrieved evidence, answer naturally from general model knowledge. "
        "For legal or regulatory claims, do not invent unsupported specifics; explicitly identify when authoritative evidence is insufficient. "
        "Provide a well-structured answer following the framework in agent.md where applicable:\n"
        "### 📌 Executive Summary\n"
        "### 🌿 Domain & Traditional Knowledge Analysis\n"
        "### ⚖️ Statutory & Regulatory Evaluation\n"
        "### 💡 Strategic IP Guidance & Next Steps\n\n"
        "Use inline source markers [S1], [S2], etc. exactly as provided in the retrieved context. Do not invent source markers."
    )

    return "\n".join(parts)


class GroqLLMClient:
    """
    Lightweight Groq API client using httpx (no external Groq SDK needed).
    Calls the Groq chat completions endpoint which is OpenAI-compatible.

    Rate-limit strategy: instead of retrying the same model with long waits,
    immediately try the next model in the fallback chain (each model has its
    own OTPM budget on Groq).  A short timed retry on the primary model is
    only attempted as a last resort.
    """

    BASE_URL = "https://api.groq.com/openai/v1/chat/completions"

    def __init__(self):
        self.api_key: Optional[str] = os.getenv("GROQ_API_KEY") or _app_settings.GROQ_API_KEY
        self.model: str = os.getenv("GROQ_MODEL", _app_settings.GROQ_MODEL)
        self.max_tokens: int = int(os.getenv("GROQ_MAX_TOKENS", str(_app_settings.GROQ_MAX_TOKENS)))
        self.temperature: float = float(os.getenv("GROQ_TEMPERATURE", str(_app_settings.GROQ_TEMPERATURE)))
        self._enabled: bool = bool(self.api_key)

        # Build ordered model chain: primary first, then fallbacks (deduplicated)
        self._model_chain: List[str] = [self.model]
        for fb in FALLBACK_MODELS:
            if fb != self.model and fb not in self._model_chain:
                self._model_chain.append(fb)

        if self._enabled:
            logger.info(
                f"Groq LLM client initialized (primary={self.model}, "
                f"fallbacks={[m for m in self._model_chain[1:]]})."
            )
        else:
            logger.warning(
                "GROQ_API_KEY not set. LLM synthesis disabled — falling back to template-based answers."
            )

    @property
    def is_enabled(self) -> bool:
        # Dynamically check if key was added to env
        key = os.getenv("GROQ_API_KEY") or self.api_key
        return self._enabled and bool(key)

    async def translate_query_to_english(self, query: str, source_language: str = "auto") -> str:
        """Fast translation of non-English query to English for accurate RAG retrieval."""
        key = os.getenv("GROQ_API_KEY") or self.api_key
        if not self.is_enabled or not query.strip():
            return query

        prompt = (
            "You are a translation assistant specializing in Intellectual Property, Ayurveda, and legal concepts.\n"
            f"Translate the following user question from {source_language} into English for technical search retrieval.\n"
            "Keep technical Ayurvedic terms, botanical names, and legal terms accurately represented in English.\n"
            "Output ONLY the translated English query text, nothing else.\n\n"
            f"Query: {query}"
        )

        headers = {
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 120,
            "temperature": 0.1,
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(self.BASE_URL, json=payload, headers=headers)
                if resp.status_code == 200:
                    text = resp.json()["choices"][0]["message"]["content"].strip().strip('"')
                    if text:
                        logger.info(f"Groq translated query '{query}' -> '{text}'")
                        return text
        except Exception as e:
            logger.warning(f"Groq query translation failed: {e}")
        return query

    # ------------------------------------------------------------------
    # Internal: single-shot request to one model
    # ------------------------------------------------------------------
    async def _try_model(
        self, model_id: str, payload: dict, headers: dict
    ) -> tuple[Optional[str], Optional[httpx.HTTPStatusError]]:
        """Attempt a single LLM call.  Returns (answer, None) on success
        or (None, error) on a 429 rate-limit.  Raises on other errors."""
        payload_copy = {**payload, "model": model_id}
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(self.BASE_URL, json=payload_copy, headers=headers)
                response.raise_for_status()
                data = response.json()
                answer = data["choices"][0]["message"]["content"]
                if "<think>" in answer and "</think>" in answer:
                    answer = re.sub(r"<think>.*?</think>", "", answer, flags=re.DOTALL).strip()
                logger.info(
                    f"Groq LLM generation successful on model={model_id} "
                    f"(tokens used: {data.get('usage', {})})."
                )
                return answer, None
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                logger.warning(f"Groq 429 on model={model_id}: {e.response.text[:200]}")
                return None, e
            raise  # propagate non-429 HTTP errors

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    async def generate_answer(
        self,
        query: str,
        domain_context: Optional[str] = None,
        legal_context: Optional[str] = None,
        jurisdiction: str = "INDIA",
        language: Optional[str] = None,
    ) -> str:
        """
        Sends retrieved RAG context + user query to Groq and returns the
        LLM-generated answer.

        Rate-limit handling:
          1. Try the primary model.
          2. On 429, immediately try each fallback model (no waiting).
          3. If every model is rate-limited, wait once using the retry-after
             header and retry the primary model.
          4. If that also fails, return a template-based fallback answer.
        """
        key = os.getenv("GROQ_API_KEY") or self.api_key
        if not self.is_enabled:
            return self._fallback_answer(query, domain_context, legal_context)

        # Trim context to avoid exceeding token limits on free tier
        trimmed_domain = domain_context[:3000] if domain_context else None
        trimmed_legal = legal_context[:3000] if legal_context else None
        user_prompt = _build_user_prompt(query, trimmed_domain, trimmed_legal)

        lang_instruction = ""
        if language and language.lower() not in ("en", "english"):
            lang_instruction = (
                f"\n\n**CRITICAL MULTILINGUAL INSTRUCTION**: You must respond fluently and naturally in the requested language ({language}). "
                "Keep the standard Markdown section headers (### 📌 Executive Summary, ### 🌿 Domain & Traditional Knowledge Analysis, "
                "### ⚖️ Statutory & Regulatory Evaluation, ### 💡 Strategic IP Guidance & Next Steps) intact. "
                "Retain all source citation markers [S1], [S2] exactly where applicable in the text. "
                "Translate technical IP and Ayurvedic explanations accurately and naturally into this language."
            )

        user_prompt = (
            f"Selected jurisdiction: {jurisdiction}. "
            f"Response language: {language or 'match the query'}.\n\n"
            + user_prompt
            + lang_instruction
        )

        payload = {
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "top_p": 0.9,
            "stream": False,
        }

        headers = {
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        }

        last_429_error: Optional[httpx.HTTPStatusError] = None

        # --- Phase 1: try each model in the chain (no waiting) -----------
        for model_id in self._model_chain:
            try:
                answer, err = await self._try_model(model_id, payload, headers)
                if answer is not None:
                    return answer
                last_429_error = err  # 429 — try next model
            except httpx.HTTPStatusError as e:
                logger.error(f"Groq API HTTP error {e.response.status_code}: {e.response.text}")
                return self._fallback_answer(query, domain_context, legal_context)
            except Exception as e:
                logger.error(f"Groq LLM generation failed: {e}")
                return self._fallback_answer(query, domain_context, legal_context)

        # --- Phase 2: all models rate-limited — one timed retry ----------
        if last_429_error is not None:
            retry_header = last_429_error.response.headers.get("retry-after")
            try:
                wait_time = min(5.0, max(0.5, float(retry_header))) if retry_header else 2.0
            except (ValueError, TypeError):
                wait_time = 2.0

            logger.info(
                f"All models rate-limited. Waiting {wait_time:.1f}s before final retry on {self.model}..."
            )
            await asyncio.sleep(wait_time)

            try:
                answer, err = await self._try_model(self.model, payload, headers)
                if answer is not None:
                    return answer
                logger.warning("Final retry also rate-limited; returning template fallback.")
            except Exception as e:
                logger.error(f"Final retry failed: {e}")

        return self._fallback_answer(query, domain_context, legal_context)

    @staticmethod
    def _fallback_answer(
        query: str,
        domain_context: Optional[str],
        legal_context: Optional[str],
    ) -> str:
        """Template-based fallback when LLM is unavailable."""
        parts = []
        if domain_context:
            parts.append(f"### 🌿 Domain Context (RAG 1: Ayurveda & IP Knowledge)\n{domain_context}")
        if legal_context:
            parts.append(f"### ⚖️ Legal & Regulatory Stance (RAG 2: Statutory Evidence)\n{legal_context}")
        if parts:
            return "\n\n---\n\n".join(parts)
        return "Could not synthesize answer from connected RAG instances."


# ---------------------------------------------------------------------------
# Global singleton
# ---------------------------------------------------------------------------
groq_llm = GroqLLMClient()
