# FastAPI 数据库操作指南

> 适用项目:`ai-server`(FastAPI + SQLAlchemy 2.0 异步 + MySQL/aiomysql)

## 1. 依赖注入会话:`get_db`

数据库会话通过 FastAPI 的 `Depends` 注入,核心在 `src/app/db/core.py`:

```python
from collections.abc import AsyncGenerator

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI 依赖注入:为每个请求创建独立的数据库会话"""
    # async with 退出时 AsyncSession.__aexit__ 会自动调用 session.close(),
    # 因此无需再手动 finally: close();这里只负责 commit / rollback
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
```

### 生命周期契约

| 时机 | 动作 |
|------|------|
| 请求进入 | 创建独立 session,`yield` 注入接口 |
| 接口正常返回 | 自动 `commit()` |
| 接口抛异常 | 自动 `rollback()` 并重新抛出 |
| 无论成败 | `async with` 退出时自动 `close()` |

> 说明:`async with AsyncSessionLocal() as session` 退出时会自动调用
> `session.close()`(等价于内置的 `finally: close()`),所以不需要再手动写 close。

### 返回类型标注

有 `yield` 的函数是**异步生成器**,返回类型应标注为
`AsyncGenerator[AsyncSession, None]`(第一个参数是 yield 出的类型,第二个是 return 的类型),
**不能**写 `-> AsyncSession`。

## 2. 注入参数的类型别名:`DbSession`

在接口里用 `Annotated` 声明「注入的会话」:

```python
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db

# 类型别名:所有接口复用
DbSession = Annotated[AsyncSession, Depends(get_db)]
```

要点:

- `DbSession` 里的 `AsyncSession` 是「yield 出来的值」的类型,是**对的**,不要改成 `AsyncGenerator`。
- 用 `Annotated` 而非 `db=Depends(get_db)`,可避免 Ruff 的 **B008** 告警,且能拿到真实类型提示。

## 3. 读操作:`select()` 查询

```python
from sqlalchemy import select

@router.get("/conversations/{user_id}")
async def list_conversations(user_id: str, db: DbSession):
    result = await db.scalars(
        select(ConversationModel)
        .where(ConversationModel.user_id == user_id)
        .order_by(ConversationModel.created_at.desc())
    )
    return result.all()
```

## 4. 写操作:`add + flush + refresh`

```python
@router.post("/conversation", response_model=ConversationOut)
async def create_conversation(body: ConversationCreate, db: DbSession):
    conv = ConversationModel(
        conversation_id=uuid4().hex,
        user_id=body.user_id,
        title=body.title,
    )
    db.add(conv)
    await db.flush()        # 触发 INSERT,拿到自增 ID / Python 侧默认值(不 commit)
    await db.refresh(conv)  # 回读数据库侧生成的值(server_default / 触发器)
    return conv             # 不手动 commit,get_db 会在响应返回后统一 commit
```

## 5. `flush` / `commit` / `refresh` 的区别

| 操作 | 作用 | 事务状态 | 拿自增 ID | 拿 server_default/触发器值 |
|------|------|---------|:--------:|:-------------------------:|
| `flush()` | 把 SQL 发给 DB 执行 | 不提交 | ✅ | ❌ |
| `commit()` | 真正落库 | 提交、结束 | ✅ | ✅(刷新后) |
| `refresh()` | 发 `SELECT` 回读 | 不改变 | — | ✅ |

### 使用场景

- **`flush()`**:拿自增主键、拿 Python 侧 `default=` 的值、提前触发约束检查(外键/唯一键冲突可在业务侧捕获)。
- **`refresh()`**:拿 `server_default`、DB 触发器、DB 计算列生成的值。
- **`commit()`**:交给 `get_db` 末尾统一执行,业务侧不要手动 commit。

## 6. 关键配置(`async_sessionmaker`)

```python
session_maker = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,  # commit 后对象属性不失效
    autoflush=False,         # 查询不会自动 flush,需显式 flush
)
```

- **`expire_on_commit=False`**:commit 后 ORM 对象属性仍可读,不会触发「对象已过期」。
- **`autoflush=False`**:查询 / `refresh()` 不会自动 flush 未提交改动,所以 `flush()` 必须显式写。

## 7. 常见坑

1. **`refresh()` 前必须先 `flush()`**,否则报 `InvalidRequestError: Instance ... is not persisted`。
2. **别在业务侧手动 `commit()`**:事务职责交给 `get_db`,否则两处重叠、易混乱。
3. **`get_db` 返回类型是 `AsyncGenerator[AsyncSession, None]`**,不是 `AsyncSession`;但注入参数 `DbSession` 是 `AsyncSession`。两者别搞反。
4. **`Depends` 写在默认参数会触发 Ruff B008**:用 `Annotated` 写法规避(见第 2 节)。

## 8. 完整示例

见 `ai-server/src/app/api/demo.py`,包含读、写两个表的完整用例。
