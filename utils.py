from functools import wraps
from fastapi import Request, HTTPException, Header
from typing import Callable

from models import ScrapeSettings


def authenticate(func: Callable):
    @wraps(func)
    async def wrapper(request: Request, settings: ScrapeSettings, token: str = Header(...), *args, **kwargs):
        if token != request.app.config["AUTH_TOKEN"]:
            raise HTTPException(status_code=401, detail="Invalid or missing authentication token")
        return await func(request, settings, token)
    
    return wrapper
