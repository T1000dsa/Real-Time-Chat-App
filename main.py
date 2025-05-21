from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from logging.config import dictConfig
import uvicorn
import logging

from src.core.config.config import settings
from src.core.config.logger import LOG_CONFIG
from src.core.dependencies.db_injection import db_helper

from src.api.v1.endpoints.healthcheck import router as heath_router
from src.api.v1.endpoints.main_router import router as main_router
from src.api.v1.auth.authentication import router as auth_router
from src.api.v1.endpoints.chat import router as chat_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    dictConfig(LOG_CONFIG)
    logger = logging.getLogger(__name__)
    logger.info(settings)
    
    yield  # FastAPI handles requests here

    try:
        await db_helper.dispose()
        logger.info("✅ Connection pool closed cleanly")
    except Exception as e:
        logger.warning(f"⚠️ Error closing connection pool: {e}")

app = FastAPI(lifespan=lifespan, title='real-time chat proj')

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # can alter with time
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(heath_router)
app.include_router(main_router)
app.include_router(auth_router)
app.include_router(chat_router)

if __name__ == '__main__':
    uvicorn.run(
        'main:app',
        host=settings.run.host,
        port=settings.run.port,
        reload=True,
        log_config=LOG_CONFIG
    )