from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete
from app import models
from datetime import datetime
from typing import List, Optional


# ----------------------------------------------------------------
# 🔹 Get one country by name
# ----------------------------------------------------------------
async def get_country_by_name(session: AsyncSession, name: str):
    q = select(models.Country).where(func.lower(models.Country.name) == name.lower())
    res = await session.execute(q)
    return res.scalars().first()


# ----------------------------------------------------------------
# 🔹 List countries with filters/sorting
# ----------------------------------------------------------------
async def list_countries(
    session: AsyncSession,
    region: Optional[str] = None,
    currency: Optional[str] = None,
    sort: Optional[str] = None
) -> List[models.Country]:
    q = select(models.Country)

    if region:
        q = q.where(models.Country.region == region)
    if currency:
        q = q.where(models.Country.currency_code == currency)

    if sort == "gdp_desc":
        q = q.order_by(models.Country.estimated_gdp.desc().nullslast())
    elif sort == "name_asc":
        q = q.order_by(models.Country.name.asc())

    res = await session.execute(q)
    return res.scalars().all()


# ----------------------------------------------------------------
# 🔹 Delete country by name
# ----------------------------------------------------------------
async def delete_country(session: AsyncSession, name: str) -> int:
    q = delete(models.Country).where(func.lower(models.Country.name) == name.lower())
    res = await session.execute(q)
    return res.rowcount


# ----------------------------------------------------------------
# 🔹 Upsert countries (insert or update)
# ----------------------------------------------------------------
async def upsert_countries(session: AsyncSession, country_dicts: List[dict], refresh_timestamp: datetime):
    """
    country_dicts: list of dicts with keys matching Country model fields.
    Insert or update each country (case-insensitive).
    """
    for c in country_dicts:
        existing = await get_country_by_name(session, c["name"])
        if existing:
            for k, v in c.items():
                setattr(existing, k, v)
            existing.last_refreshed_at = refresh_timestamp
        else:
            db_obj = models.Country(**c)
            db_obj.last_refreshed_at = refresh_timestamp
            session.add(db_obj)
    await session.flush()


# ----------------------------------------------------------------
# 🔹 Get total countries and last refresh timestamp
# ----------------------------------------------------------------
async def total_countries_and_last_refresh(session: AsyncSession):
    q = select(func.count(models.Country.id), func.max(models.Country.last_refreshed_at))
    res = await session.execute(q)
    count, last = res.first()
    return count or 0, last


# ----------------------------------------------------------------
# 🔹 Wrapper for /status endpoint
# ----------------------------------------------------------------
async def get_status(session: AsyncSession):
    """
    Returns total number of countries and last refresh time.
    """
    total, last_refreshed = await total_countries_and_last_refresh(session)
    return total, last_refreshed
