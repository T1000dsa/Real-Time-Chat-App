from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from logging.config import dictConfig
import uvicorn
import logging

from src.core.config.config import settings, media_root, static_root
from src.core.config.logger import LOG_CONFIG
from src.core.dependencies.db_injection import db_helper
from src.core.middleware.middleware import init_token_refresh_middleware
from src.core.services.cache.redis import ConnectionManager as redis_conmanager
from src.core.services.chat.infrastructure.services.RoomService import RoomService
from src.core.services.chat.infrastructure.services.ConnectionManager import ConnectionManager

from src.api.v1.endpoints.healthcheck import router as heath_router
from src.api.v1.endpoints.main_router import router as main_router
from src.api.v1.auth.authentication import router as auth_router
from src.api.v1.endpoints.chat import router as chat_router
from src.api.v1.endpoints.direct_messages import router as direct_msg_router
from src.api.v1.auth.profile_managment import router as profile_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings.create_directories()
    dictConfig(LOG_CONFIG)
    logger = logging.getLogger(__name__)
    app.mount("/media", StaticFiles(directory=media_root), name="media")
    app.mount("/static", StaticFiles(directory=static_root), name="static")

    app.state.room_service = RoomService()
    app.state.con_manager = ConnectionManager()

    redis_manager = redis_conmanager()
    app.state.redis_manager = redis_manager

    try:
        await redis_manager.redis.flushdb()
        logger.info("🧹 Redis database flushed successfully")
    except Exception as e:
        logger.error(f"❌ Failed to flush Redis database: {e}")
    
    yield  # FastAPI handles requests here

    try:
        await redis_manager.pubsub.close()
        await redis_manager.redis.close()
        await db_helper.dispose()
        redis_manager.redis.close()

        logger.info("✅ Connection pool closed cleanly")
    except Exception as e:
        logger.warning(f"⚠️ Error closing connection pool: {e}")

app = FastAPI(lifespan=lifespan, title=settings.run.title)

app.add_middleware(
    SessionMiddleware,
    secret_key=settings.jwt.key.get_secret_value(),
    session_cookie="session_cookie",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # can alter with time
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
init_token_refresh_middleware(app)

app.include_router(heath_router)
app.include_router(main_router)
app.include_router(auth_router)
app.include_router(profile_router)
app.include_router(chat_router)
app.include_router(direct_msg_router)

if __name__ == '__main__':
    uvicorn.run(
        'main:app',
        host=settings.run.host,
        port=settings.run.port,
        reload=not settings.is_prod(),
        log_config=LOG_CONFIG
    )