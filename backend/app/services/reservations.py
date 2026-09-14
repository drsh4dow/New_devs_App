from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP

from fastapi import HTTPException
from sqlalchemy import text

from app.core.database_pool import session_factory


async def calculate_total_revenue(
    property_id: str,
    tenant_id: str,
    month: int | None = None,
    year: int | None = None,
) -> dict:
    """Assign each reservation's full amount to its property-local check-in month."""
    parameters = {"property_id": property_id, "tenant_id": tenant_id}
    date_filter = ""
    if month is not None:
        parameters["start_date"] = datetime(year, month, 1)
        parameters["end_date"] = (
            datetime(year + 1, 1, 1) if month == 12 else datetime(year, month + 1, 1)
        )
        # Convert each local boundary separately: DST can change the UTC offset.
        date_filter = """
            AND r.check_in_date >= (CAST(:start_date AS timestamp) AT TIME ZONE p.timezone)
            AND r.check_in_date < (CAST(:end_date AS timestamp) AT TIME ZONE p.timezone)
        """

    async with session_factory() as session:
        result = await session.execute(
            text(
                f"""
                SELECT COALESCE(SUM(r.total_amount), 0) AS total,
                       COUNT(r.id) AS count,
                       MIN(r.currency) AS currency,
                       COUNT(DISTINCT r.currency) AS currency_count
                FROM properties p
                LEFT JOIN reservations r
                    ON r.property_id = p.id AND r.tenant_id = p.tenant_id
                    {date_filter}
                WHERE p.id = :property_id AND p.tenant_id = :tenant_id
                GROUP BY p.id
            """
            ),
            parameters,
        )
        row = result.one_or_none()

    if row is None:
        raise HTTPException(status_code=404, detail="Property not found")
    if row.currency_count > 1:
        raise HTTPException(
            status_code=422,
            detail="Cannot combine reservations with different currencies",
        )

    return {
        "property_id": property_id,
        "tenant_id": tenant_id,
        "total": str(row.total.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)),
        "currency": row.currency or "USD",
        "count": row.count,
    }
