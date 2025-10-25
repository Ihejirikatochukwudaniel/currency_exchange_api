from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone
from typing import List, Optional
import httpx
import os
import traceback

from app import crud, utils
from app.database import get_db

router = APIRouter(
    prefix="/countries",
    tags=["Countries"]
)

# ----------------------------------------------------------------
# 🔹 Helper function to refresh and cache countries
# ----------------------------------------------------------------
async def refresh_country_data(client: httpx.AsyncClient, session: AsyncSession, countries_data: List[dict]):
    """
    Process country data, fetch exchange rates, and store in database.
    
    Args:
        client: httpx AsyncClient for making API calls
        session: Database session (managed by get_db dependency)
        countries_data: List of country data from RestCountries API
    
    Returns:
        datetime: Timestamp of the refresh operation
    """
    try:
        rates = await utils.fetch_exchange_rates(client)
    except Exception as e:
        print(f"❌ Error fetching exchange rates: {str(e)}")
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
    
    # ✅ REMOVED: async with session.begin() - get_db() manages transactions
    # Just call the upsert function directly
    await crud.upsert_countries(session, payloads, refresh_ts)

    # Generate and cache summary image
    try:
        await utils.generate_summary_image(session, refresh_ts)
    except Exception as e:
        print(f"⚠️ Warning: Could not generate summary image: {str(e)}")
        # Don't fail the entire refresh if image generation fails

    return refresh_ts


# ----------------------------------------------------------------
# 🔹 Endpoints (specific → dynamic)
# ----------------------------------------------------------------

@router.post("/refresh")
async def refresh_countries(db: AsyncSession = Depends(get_db)):
    """
    Fetch countries + exchange rates, cache them in the database.
    
    This endpoint:
    1. Fetches country data from RestCountries API
    2. Fetches exchange rates
    3. Calculates estimated GDP
    4. Stores everything in the database
    5. Generates a summary image
    """
    # Check if database is ready (optional - remove if not needed)
    from app.main import db_ready, db_error
    if not db_ready:
        if db_error:
            raise HTTPException(
                status_code=503,
                detail={
                    "error": "Database not ready",
                    "details": f"Database initialization failed: {db_error}"
                }
            )
        raise HTTPException(
            status_code=503,
            detail={
                "error": "Database not ready",
                "details": "Database is still initializing. Please try again in a few seconds."
            }
        )
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                res = await client.get(
                    "https://restcountries.com/v2/all",
                    params={
                        "fields": "name,capital,region,population,flag,currencies"
                    }
                )
                res.raise_for_status()
                countries_data = res.json()
                
                if not countries_data:
                    raise HTTPException(
                        status_code=503,
                        detail={
                            "error": "External data source returned empty data",
                            "details": "RestCountries API returned no countries"
                        }
                    )
                
            except httpx.HTTPError as e:
                print(f"❌ HTTP Error fetching countries: {str(e)}")
                raise HTTPException(
                    status_code=503,
                    detail={
                        "error": "External data source unavailable",
                        "details": f"Could not fetch data from RestCountries API: {str(e)}"
                    }
                )
            except Exception as e:
                print(f"❌ Unexpected error fetching countries: {str(e)}")
                raise HTTPException(
                    status_code=503,
                    detail={
                        "error": "External data source unavailable",
                        "details": "Could not fetch data from RestCountries API"
                    }
                )

            # Process and store the data
            ts = await refresh_country_data(client, db, countries_data)

        return {
            "message": "Countries refreshed successfully",
            "last_refreshed_at": ts,
            "countries_processed": len(countries_data)
        }
    
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    
    except Exception as e:
        # Log and return 500 for unexpected errors
        error_detail = traceback.format_exc()
        print(f"❌ Error in /countries/refresh: {str(e)}")
        print(error_detail)
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Internal server error",
                "details": f"Failed to refresh countries: {str(e)}"
            }
        )


@router.get("")
async def get_countries(
    region: Optional[str] = Query(None, description="Filter by region (e.g. Africa)"),
    currency: Optional[str] = Query(None, description="Filter by currency code (e.g. NGN)"),
    sort: Optional[str] = Query(None, description="Sort by field, e.g. gdp_desc"),
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieve all countries with optional filters & sorting.
    
    Query Parameters:
    - region: Filter by region (e.g., "Africa", "Europe")
    - currency: Filter by currency code (e.g., "USD", "NGN")
    - sort: Sort results (e.g., "gdp_desc", "population_asc")
    """
    try:
        results = await crud.list_countries(db, region=region, currency=currency, sort=sort)
        return results
    except Exception as e:
        print(f"❌ Error in /countries: {str(e)}")
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail={"error": "Failed to retrieve countries", "details": str(e)}
        )


@router.get("/status")
async def get_status(db: AsyncSession = Depends(get_db)):
    """
    Show total number of countries and last refresh timestamp.
    
    Returns:
    - total_countries: Number of countries in the database
    - last_refreshed_at: Timestamp of the last data refresh
    """
    try:
        total, last_refreshed = await crud.get_status(db)
        return {
            "total_countries": total,
            "last_refreshed_at": last_refreshed
        }
    except Exception as e:
        print(f"❌ Error in /countries/status: {str(e)}")
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail={"error": "Failed to retrieve status", "details": str(e)}
        )


@router.get("/image")
async def get_summary_image():
    """
    Serve the generated summary image.
    
    Returns a PNG image showing country statistics.
    Returns 404 if the image hasn't been generated yet.
    """
    img_path = "cache/summary.png"
    if not os.path.exists(img_path):
        return JSONResponse(
            status_code=404,
            content={
                "error": "Summary image not found",
                "details": "Run POST /countries/refresh first to generate the image"
            }
        )
    return FileResponse(img_path, media_type="image/png")


@router.get("/{name}")
async def get_country(name: str, db: AsyncSession = Depends(get_db)):
    """
    Get a specific country by name.
    
    Path Parameters:
    - name: Country name (case-insensitive, e.g., "Nigeria", "United States")
    """
    try:
        country = await crud.get_country_by_name(db, name)
        if not country:
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "Country not found",
                    "details": f"No country found with name: {name}"
                }
            )
        return country
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error in /countries/{name}: {str(e)}")
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail={"error": "Failed to retrieve country", "details": str(e)}
        )


@router.delete("/{name}")
async def delete_country(name: str, db: AsyncSession = Depends(get_db)):
    """
    Delete a specific country record.
    
    Path Parameters:
    - name: Country name to delete
    """
    try:
        deleted = await crud.delete_country(db, name)
        if not deleted:
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "Country not found",
                    "details": f"No country found with name: {name}"
                }
            )
        return {
            "message": f"{name} deleted successfully",
            "deleted": True
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error in DELETE /countries/{name}: {str(e)}")
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail={"error": "Failed to delete country", "details": str(e)}
        )
