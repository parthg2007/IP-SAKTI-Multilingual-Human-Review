from fastapi import APIRouter, HTTPException

from app.config import settings
from app.core.escalation import create_case
from app.data.models import HumanEscalationRequest, HumanEscalationResponse

router = APIRouter(prefix="/api/v1/human", tags=["Human IP Facilitator"])


@router.post("/escalate", response_model=HumanEscalationResponse)
async def escalate_to_human(request: HumanEscalationRequest):
    if not settings.HUMAN_ESCALATION_ENABLED:
        raise HTTPException(status_code=503, detail="Human escalation is currently disabled.")
    return create_case(request)
