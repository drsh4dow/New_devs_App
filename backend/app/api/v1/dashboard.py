from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text

from app.core.auth import authenticate_request
from app.core.database_pool import session_factory
from app.models.auth import AuthenticatedUser
from app.services.cache import get_revenue_summary

router = APIRouter()


def get_tenant_id(
    current_user: AuthenticatedUser = Depends(authenticate_request),
) -> str:
    if not current_user.tenant_id:
        raise HTTPException(status_code=403, detail="Client identity required")
    return current_user.tenant_id


@router.get("/dashboard/properties")
async def get_dashboard_properties(
    tenant_id: str = Depends(get_tenant_id),
) -> list[dict]:
    async with session_factory() as session:
        result = await session.execute(
            text(
                "SELECT id, name FROM properties WHERE tenant_id = :tenant_id ORDER BY id"
            ),
            {"tenant_id": tenant_id},
        )
        return [dict(row) for row in result.mappings()]


@router.get("/dashboard/summary")
async def get_dashboard_summary(
    property_id: str,
    month: int | None = Query(default=None, ge=1, le=12),
    year: int | None = Query(default=None, ge=1, le=9998),
    tenant_id: str = Depends(get_tenant_id),
) -> dict:
    if (month is None) != (year is None):
        raise HTTPException(status_code=422, detail="Supply both month and year")

    revenue_data = await get_revenue_summary(property_id, tenant_id, month, year)
    return {
        "property_id": revenue_data["property_id"],
        "total_revenue": float(revenue_data["total"]),
        "currency": revenue_data["currency"],
        "reservations_count": revenue_data["count"],
    }
