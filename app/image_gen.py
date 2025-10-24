from PIL import Image, ImageDraw, ImageFont
from typing import List, Tuple
import os


CACHE_DIR = os.path.join(os.getcwd(), 'cache')
if not os.path.exists(CACHE_DIR):
    os.makedirs(CACHE_DIR, exist_ok=True)


SUMMARY_PATH = os.path.join(CACHE_DIR, 'summary.png')


def generate_summary_image(total: int, top5: List[Tuple[str, float]], timestamp: str) -> str:
    width, height = 1200, 800
    img = Image.new('RGB', (width, height), color=(255, 255, 255))
    d = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype('DejaVuSans.ttf', 28)
    except Exception:
        font = ImageFont.load_default()

    y = 40
    d.text((40, y), f'Total Countries: {total}', font=font, align='left')
    y += 50
    d.text((40, y), f'Last Refresh: {timestamp}', font=font)
    y += 70
    d.text((40, y), 'Top 5 countries by estimated GDP:', font=font)
    y += 40
    for i, (name, gdp) in enumerate(top5, start=1):
        d.text((60, y), f'{i}. {name} — {gdp:,.2f}', font=font)
        y += 36

    img.save(SUMMARY_PATH)
    return SUMMARY_PATH
