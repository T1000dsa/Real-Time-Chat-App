from fastapi import Depends
from typing import AsyncGenerator, Annotated
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncEngine,
    async_sessionmaker,
    AsyncSession,
    )
from contextlib import asynccontextmanager
from sqlalchemy.exc import SQLAlchemyError

from src.core.config.config import settings


class DbHelper:
    def __init__(
            self, 
            url:str, 
            echo:bool=True, 
            echo_pool:bool=False,
            pool_size:int=5,
            max_overflow:int=10,
            pool_pre_ping=True,
            pool_recycle=3600,
            ):
        
        self.engine:AsyncEngine = create_async_engine(
            url=url,
            echo=echo,
            echo_pool=echo_pool,
            pool_size=pool_size,
            max_overflow=max_overflow,
            pool_pre_ping=pool_pre_ping,
            pool_recycle=pool_recycle
        )
        
        self.session_factory:async_sessionmaker[AsyncSession] = async_sessionmaker(
            bind=self.engine,
            autoflush=False,
            expire_on_commit=False,
        )

    async def dispose(self) -> None:
        await self.engine.dispose()
    

    async def session_getter(self) -> AsyncGenerator[AsyncSession, None]:
        async with self.session_factory() as session:
            yield session


    @asynccontextmanager
    async def async_session(self):
        async with self.session_factory() as session:
            try:
                yield session
                await session.commit()
            except SQLAlchemyError:
                await session.rollback()
                raise
            finally:
                await session.close()


db_helper = DbHelper(
    url=str(settings.db.give_url),
    echo=settings.db.echo,
    echo_pool=settings.db.echo_pool,
    pool_size=settings.db.pool_size,
    max_overflow=settings.db.max_overflow
)
DBDI = Annotated[AsyncSession, Depends(db_helper.session_getter)]