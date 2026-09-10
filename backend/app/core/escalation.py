"""Human IP facilitator escalation persistence."""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from app.config import settings
from app.data.models import HumanEscalationRequest, HumanEscalationResponse

logger = logging.getLogger(__name__)


def create_case(request: HumanEscalationRequest) -> HumanEscalationResponse:
    case_id = f"IPF-{datetime.now(timezone.utc):%Y%m%d}-{uuid4().hex[:8].upper()}"
    path: Path = settings.ESCALATION_STORE_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "case_id": case_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": "queued_for_human_review",
        **request.model_dump(),
    }
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")
    logger.info("Human IP facilitator case created: %s", case_id)
    return HumanEscalationResponse(
        case_id=case_id,
        status="queued_for_human_review",
        message="Your question, answer context, confidence assessment, and source trail have been queued for human IP facilitator review.",
        facilitator_email=settings.IP_FACILITATOR_EMAIL,
    )
