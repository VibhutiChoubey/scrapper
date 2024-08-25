from fastapi import APIRouter, Depends, Request

from models import ScrapeSettings, ScrapingTool
from utils import authenticate

router = APIRouter()


@router.post("/scrape")
@authenticate
async def scrape(request: Request, settings: ScrapeSettings, token: str):
    scraper = ScrapingTool(settings=settings)
    message = scraper.scrape(request)
    return {"status": message}