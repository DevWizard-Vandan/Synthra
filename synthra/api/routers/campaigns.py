"""Campaigns router — placeholder for future campaign CRUD operations."""

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/campaigns", tags=["campaigns"])


class CampaignsListResponse(BaseModel):
    """Response schema for the campaigns list endpoint."""

    campaigns: list[str]
    total: int


@router.get("", response_model=CampaignsListResponse)
async def list_campaigns() -> CampaignsListResponse:
    """List all campaigns. Placeholder — full CRUD in a future milestone."""
    return CampaignsListResponse(campaigns=[], total=0)
