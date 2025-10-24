import httpx
from typing import Tuple, Dict, List, Optional
from datetime import datetime
import random
import os
from PIL import Image, ImageDraw
from sqlalchemy import select
from app import models


COUNTRIES_API = 'https://restcountries.com/v2/all?fields=name,capital,region,population,flag,currencies'
EXCHANGE_API = 'https://open.er-api.com/v6/latest/USD'


async def fetch_countries(client: httpx.AsyncClient) -> List[dict]:
    r = await client.get(COUNTRIES_API, timeout=30.0)
    r.raise_for_status()
    return r.json()


async def fetch_exchange_rates(client: httpx.AsyncClient) -> Dict[str, float]:
    r = await client.get(EXCHANGE_API, timeout=30.0)
    r.raise_for_status()
    body = r.json()
    rates = body.get('rates') or {}
    return rates


def extract_currency_code(country_obj: dict) -> Optional[str]:
    currencies = country_obj.get('currencies') or []
    if not currencies:
        return None
    first = currencies[0]
    return first.get('code')


def compute_estimated_gdp(population: int, exchange_rate: Optional[float]) -> Optional[float]:
    if population is None:
        return None
    if exchange_rate in (None, 0):
        return 0 if exchange_rate is None else None
    multiplier = random.uniform(1000, 2000)
    return (population * multiplier) / exchange_rate


# 🧩 NEW FUNCTION: generate_summary_image()
async def generate_summary_image(session, refresh_ts):
    """
    Generate a simple summary image showing:
    - Total number of countries
    - Top 5 by estimated GDP
    - Last refresh timestamp
    """
    # Query all countries
    result = await session.execute(select(models.Country))
    countries = result.scalars().all()
    total_countries = len(countries)

    # Sort by GDP and get top 5
    top_countries = sorted(
        [c for c in countries if c.estimated_gdp],
        key=lambda x: x.estimated_gdp,
        reverse=True
    )[:5]

    # Ensure cache folder exists
    os.makedirs("cache", exist_ok=True)

    # Create image canvas
    width, height = 600, 400
    img = Image.new("RGB", (width, height), color=(240, 240, 240))
    draw = ImageDraw.Draw(img)

    # Write summary text
    draw.text((20, 20), "🌍 Country Summary", fill=(0, 0, 0))
    draw.text((20, 60), f"Total Countries: {total_countries}", fill=(0, 0, 0))
    draw.text((20, 90), f"Last Refresh: {refresh_ts.strftime('%Y-%m-%d %H:%M:%S UTC')}", fill=(0, 0, 0))

    # Top 5 list
    y = 130
    draw.text((20, y), "Top 5 by Estimated GDP:", fill=(0, 0, 0))
    y += 30
    for c in top_countries:
        line = f"{c.name} — {round(c.estimated_gdp, 2):,}"
        draw.text((40, y), line, fill=(0, 0, 0))
        y += 25

    # Save image
    img_path = "cache/summary.png"
    img.save(img_path)
    return img_path
