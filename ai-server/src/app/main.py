from contextlib import asynccontextmanager

import app.model  # 导入即注册,注册 ORM 模型到 Base.metadata
from app.api.index import index_router
from app.db import Base, engine
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


app = FastAPI(title="ai-server", version="0.0.1", lifespan=lifespan)

# 允许前端(dev 跑在 3000 端口)跨域访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(index_router, prefix="/dongtu")


def main():

    from .config import settings

    print("start", settings)
    """开发服务器入口，启动前自动释放 8000 端口"""
    import os
    import signal
    import subprocess

    result = subprocess.run(
        ["lsof", "-ti:8000"], capture_output=True, text=True, check=False
    )

    for pid in result.stdout.strip().split():
        try:
            os.kill(int(pid), signal.SIGKILL)
            print(f"[dev] killed old process on port 8000 (pid={pid})")
        except ProcessLookupError:
            pass

    import uvicorn

    uvicorn.run("app.main:app", reload=True)
