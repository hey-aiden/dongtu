"""
数据库连接管理
"""

from app.config import settings
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """全局统一的 ORM 模型基类"""


# 创建引擎和session的工厂函数
def create_async_engine_sessionmaker(
    db_url: str, **engine_kwargs
) -> tuple[object, async_sessionmaker[AsyncSession]]:
    engine = create_async_engine(db_url, **engine_kwargs)
    session_maker = async_sessionmaker(
        bind=engine, class_=AsyncSession, expire_on_commit=False, autoflush=False
    )
    return engine, session_maker


# 获取实例
engine, AsyncSessionLocal = create_async_engine_sessionmaker(
    settings.db_url, echo=False, pool_pre_ping=True, pool_size=10, max_overflow=20
)


# FastApi 依赖注入函数
async def get_db() -> AsyncSession:
    """FastAPI 依赖注入：为每个请求创建独立的数据库会话"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
