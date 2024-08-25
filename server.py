import logging
import os
import redis

from fastapi import FastAPI
from contextlib import asynccontextmanager

from configuration import from_envvar
from routes import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logger(app)
    app.logger.info("logger initialised")

    setup_config(app)
    app.logger.info("config added")

    setup_redis(app)
    app.logger.info("redis initialized")

    setup_routes(app)
    app.logger.info("routes registered")

    yield

    app.logger.info("shutting down...")

    redis_close()
    app.logger.info("redis closed")


app = FastAPI(lifespan=lifespan)

def setup_redis(app):
    app.redis = redis.Redis(host='localhost', port=6379, db=0)

async def redis_close():
    app.redis.close()

def setup_routes(app):
    app.include_router(router)

def setup_config(app):
    app.config = from_envvar()

def setup_logger(app):
    logging.basicConfig(level=logging.DEBUG)
    app.logger = logging.getLogger(__name__)

def make_directory():
    if not os.path.exists(app.config.IMAGE_DIR):
        os.makedirs(app.config.IMAGE_DIR)
