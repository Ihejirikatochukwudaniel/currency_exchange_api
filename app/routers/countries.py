from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone
from typing import List, Optional
import httpx, os

from app import crud, utils
from app.database import get_db

router = APIRouter(
    prefix="/countries",
    tags=["Countries"]
)

# ----------------------------------------------------------------
# 🔹 Helper function to refresh and cache countries
# ----------------------------------------------------------------
async def refresh_country_data(client, session: AsyncSession, countries_data: List[dict]):
    try:
        rates = await utils.fetch_exchange_rates(client)
    except Exception:
        raise HTTPException(
            status_code=503,
            detail={
                "error": "External data source unavailable",
                "details": "Could not fetch data from Exchange Rates API"
            }
        )

    payloads = []
    for c in countries_data:
        name = c.get("name")
        population = c.get("population")
        capital = c.get("capital")
        region = c.get("region")
        flag = c.get("flag")
        currency_code = utils.extract_currency_code(c)
        exchange_rate = None
        estimated_gdp = None

        if currency_code:
            erate = rates.get(currency_code)
            if erate is not None:
                exchange_rate = float(erate)
                estimated_gdp = utils.compute_estimated_gdp(population, exchange_rate)
        else:
            currency_code = None
            estimated_gdp = 0

        payloads.append({
            "name": name,
            "capital": capital,
            "region": region,
            "population": population or 0,
            "currency_code": currency_code,
            "exchange_rate": exchange_rate,
            "estimated_gdp": estimated_gdp,
            "flag_url": flag,
        })

    refresh_ts = datetime.now(timezone.utc)
    async with session.begin():
        await crud.upsert_countries(session, payloads, refresh_ts)

    # Generate and cache summary image
    await utils.generate_summary_image(session, refresh_ts)

    return refresh_ts


# ----------------------------------------------------------------
# 🔹 Endpoints (specific → dynamic)
# ----------------------------------------------------------------

@router.post("/refresh")
async def refresh_countries(db: AsyncSession = Depends(get_db)):
    """Fetch countries + exchange rates, cache them in the database."""
    async with httpx.AsyncClient(timeout=30) as client:
        try:
            res = await client.get(
                "https://restcountries.com/v2/all?fields=name,capital,region,population,flag,currencies"
            )
            res.raise_for_status()
            countries_data = res.json()
        except Exception:
            raise HTTPException(
                status_code=503,
                detail={
                    "error": "External data source unavailable",
                    "details": "Could not fetch data from RestCountries API"
                }
            )

        ts = await refresh_country_data(client, db, countries_data)

    return {"message": "Countries refreshed successfully", "last_refreshed_at": ts}


@router.get("")
async def get_countries(
    region: Optional[str] = Query(None, description="Filter by region (e.g. Africa)"),
    currency: Optional[str] = Query(None, description="Filter by currency code (e.g. NGN)"),
    sort: Optional[str] = Query(None, description="Sort by field, e.g. gdp_desc"),
    db: AsyncSession = Depends(get_db)
):
    """Retrieve all countries with optional filters & sorting."""
    results = await crud.list_countries(db, region=region, currency=currency, sort=sort)
    return results


@router.get("/status")
async def get_status(db: AsyncSession = Depends(get_db)):
    """Show total number of countries and last refresh timestamp."""
    total, last_refreshed = await crud.get_status(db)
    return {
        "total_countries": total,
        "last_refreshed_at": last_refreshed
    }


@router.get("/image")
async def get_summary_image():
    """Serve the generated summary image."""
    img_path = "cache/summary.png"
    if not os.path.exists(img_path):
        return JSONResponse(status_code=404, content={"error": "Summary image not found"})
    return FileResponse(img_path, media_type="image/png")


@router.get("/{name}")
async def get_country(name: str, db: AsyncSession = Depends(get_db)):
    """Get a specific country by name."""
    country = await crud.get_country_by_name(db, name)
    if not country:
        raise HTTPException(status_code=404, detail={"error": "Country not found"})
    return country


@router.delete("/{name}")
async def delete_country(name: str, db: AsyncSession = Depends(get_db)):
    """Delete a specific country record."""
    deleted = await crud.delete_country(db, name)
    if not deleted:
        raise HTTPException(status_code=404, detail={"error": "Country not found"})
    return {"message": f"{name} deleted successfully"}
