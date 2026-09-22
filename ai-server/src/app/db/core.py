"""
数据库连接管理
"""

from collections.abc import AsyncGenerator
from typing import Annotated

from app.config import settings
from fastapi import Depends
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
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI 依赖注入：为每个请求创建独立的数据库会话"""
    # async with 退出时 AsyncSession.__aexit__ 会自动调用 session.close()，
    # 因此无需再手动 finally: close()；这里只负责 commit / rollback
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


# 注入的数据库会话类型别名：所有接口复用，等价于 Annotated[AsyncSession, Depends(get_db)]
# 为什么能抽成模块变量复用：这里只是「类型标注」，不产生任何运行时对象。
# 真正的 session 由 Depends(get_db) 在每个请求到来时才创建（结束后自动 commit/close），
# 所以共享这个别名是安全的——和「模块级 session 单例」那种会串数据、泄漏连接的做法是两回事。
DbSession = Annotated[AsyncSession, Depends(get_db)]
