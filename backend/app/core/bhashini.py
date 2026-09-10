"""Optional BHASHINI translation adapter for multilingual IP-SAKTI."""
from __future__ import annotations

import logging
from typing import Any, Dict, Optional, Tuple

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

SUPPORTED_LANGUAGES = {
    "en": "English", "hi": "Hindi", "bn": "Bengali", "gu": "Gujarati",
    "kn": "Kannada", "ml": "Malayalam", "mr": "Marathi", "or": "Odia",
    "pa": "Punjabi", "ta": "Tamil", "te": "Telugu", "ur": "Urdu",
}


class BhashiniTranslator:
    def __init__(self) -> None:
        self._config_cache: Dict[Tuple[str, str], Dict[str, Any]] = {}

    @property
    def enabled(self) -> bool:
        return bool(
            settings.BHASHINI_ENABLED
            and settings.BHASHINI_USER_ID
            and settings.BHASHINI_API_KEY
            and settings.BHASHINI_PIPELINE_ID
        )

    async def _get_config(self, source: str, target: str) -> Optional[Dict[str, Any]]:
        key = (source, target)
        if key in self._config_cache:
            return self._config_cache[key]
        headers = {
            "userID": settings.BHASHINI_USER_ID or "",
            "ulcaApiKey": settings.BHASHINI_API_KEY or "",
        }
        payload = {
            "pipelineTasks": [{"taskType": "translation"}],
            "pipelineRequestConfig": {"pipelineId": settings.BHASHINI_PIPELINE_ID},
        }
        try:
            async with httpx.AsyncClient(timeout=settings.BHASHINI_TIMEOUT_SECONDS) as client:
                response = await client.post(settings.BHASHINI_CONFIG_URL, json=payload, headers=headers)
                response.raise_for_status()
                data = response.json()
            endpoint = data.get("pipelineInferenceAPIEndPoint") or {}
            callback_url = endpoint.get("callbackUrl") or settings.BHASHINI_INFERENCE_URL
            auth = endpoint.get("inferenceApiKey") or {}
            configs = []
            for task in data.get("pipelineResponseConfig", []):
                if task.get("taskType") == "translation":
                    configs.extend(task.get("config") or [])
            chosen = next((c for c in configs if (c.get("language") or {}).get("sourceLanguage") == source and (c.get("language") or {}).get("targetLanguage") == target), None)
            if not chosen or not callback_url or not auth.get("name") or not auth.get("value"):
                logger.warning("BHASHINI has no translation configuration for %s -> %s", source, target)
                return None
            cfg = {"callback_url": callback_url, "auth_name": auth["name"], "auth_value": auth["value"], "service_id": chosen.get("serviceId")}
            self._config_cache[key] = cfg
            return cfg
        except Exception as exc:
            logger.warning("BHASHINI config call failed for %s -> %s: %s", source, target, exc)
            return None

    async def translate(self, text: str, source: str, target: str) -> Tuple[str, bool]:
        if not text or source == target:
            return text, False
        if not self.enabled:
            return text, False
        cfg = await self._get_config(source, target)
        if not cfg:
            return text, False
        payload = {
            "pipelineTasks": [{
                "taskType": "translation",
                "config": {
                    "language": {"sourceLanguage": source, "targetLanguage": target},
                    "serviceId": cfg["service_id"],
                },
            }],
            "inputData": {"input": [{"source": text}], "audio": [{"audioContent": None}]},
        }
        try:
            async with httpx.AsyncClient(timeout=settings.BHASHINI_TIMEOUT_SECONDS) as client:
                response = await client.post(
                    cfg["callback_url"],
                    json=payload,
                    headers={cfg["auth_name"]: cfg["auth_value"]},
                )
                response.raise_for_status()
                data = response.json()
            output = (((data.get("pipelineResponse") or [{}])[0].get("output") or [{}])[0]).get("target")
            return (output.strip() if isinstance(output, str) and output.strip() else text), bool(output)
        except Exception as exc:
            logger.warning("BHASHINI translation failed for %s -> %s: %s", source, target, exc)
            return text, False


bhashini = BhashiniTranslator()
