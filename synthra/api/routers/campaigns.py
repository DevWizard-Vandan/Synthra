"""Campaigns router — listing and details about campaigns."""

from typing import Any, List
from fastapi import APIRouter, Request
from pydantic import BaseModel

router = APIRouter(prefix="/campaigns", tags=["campaigns"])


class CampaignInfo(BaseModel):
    """Detailed summary of a campaign."""

    id: str
    name: str
    region: str
    universe: str
    budget_limit: float
    budget_spent: float
    target_alpha_count: int
    max_simulations: int
    status: str
    state: str


class CampaignsListResponse(BaseModel):
    """Response schema for the campaigns list endpoint."""

    campaigns: List[CampaignInfo]
    total: int


@router.get("", response_model=CampaignsListResponse)
async def list_campaigns(request: Request) -> CampaignsListResponse:
    """List all campaigns from the database."""
    service = getattr(request.app.state, "service", None)
    if not service or not service.governor:
        return CampaignsListResponse(campaigns=[], total=0)

    gov = service.governor
    campaigns = []
    with gov.db_manager.connection() as conn:
        cursor = conn.execute(
            "SELECT c.id, c.name, c.region, c.universe, c.budget_limit, "
            "c.budget_spent, c.target_alpha_count, c.max_simulations, c.status, "
            "COALESCE(s.state, 'DRAFT') as state "
            "FROM campaigns c "
            "LEFT JOIN campaign_states s ON c.id = s.campaign_id"
        )
        rows = cursor.fetchall()
        for r in rows:
            campaigns.append(
                CampaignInfo(
                    id=r[0],
                    name=r[1],
                    region=r[2],
                    universe=r[3],
                    budget_limit=r[4],
                    budget_spent=r[5],
                    target_alpha_count=r[6],
                    max_simulations=r[7],
                    status=r[8],
                    state=r[9],
                )
            )
    return CampaignsListResponse(campaigns=campaigns, total=len(campaigns))


@router.post("/{campaign_id}/run")
async def run_campaign_endpoint(campaign_id: str, request: Request) -> dict[str, Any]:
    """Trigger autonomous execution for a campaign."""
    service = getattr(request.app.state, "service", None)
    if not service or not service.governor:
        return {"status": "error", "message": "Governor service not initialized"}

    try:
        service.governor.run_campaign(campaign_id)
        return {
            "status": "success",
            "message": f"Campaign {campaign_id} queued for execution",
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}
