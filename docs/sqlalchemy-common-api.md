# SQLAlchemy 常用 API 使用文档

> 适用:`ai-server` 项目,SQLAlchemy 2.0 异步(AsyncSession)+ `Mapped` / `mapped_column` 声明式模型。

## 0. 异步要点(先记住)

- 会话是 `AsyncSession`,所有 DB 操作都要 `await`。
- **异步下没有懒加载**:访问 `relationship` 关联属性会抛 `MissingGreenlet`,必须用 `selectinload()` 等**预加载**(见第 8 节)。
- 结果要 `await` 后再取:先 `await db.scalars(...)` 拿到 `ScalarResult`,再 `.all()` / `.first()`。

---

## 1. 查询构建:`select`

```python
from sqlalchemy import select

# 查整表
stmt = select(User)

# 只查某几列(返回元组)
stmt = select(User.id, User.name)

# 给列起别名
stmt = select(User.name.label("username"))

# 子查询
sub = select(Order.user_id).where(Order.amount > 100).subquery()
stmt = select(User).where(User.id.in_(select(sub.c.user_id)))
```

## 2. 过滤条件:`where` + 操作符

```python
from sqlalchemy import and_, or_, not_, func, select

stmt = select(User).where(
    User.age >= 18,                 # 比较
    User.name.like("%张%"),         # LIKE
    User.status.in_(["a", "b"]),    # IN
)

# 常用操作符速查
User.age == 18          # 等于
User.age != 18          # 不等于
User.age > 18           # 大于 / >= / < / <=
User.name.like("%x%")   # 模糊(通配 %)
User.name.ilike("%x%")  # 模糊(忽略大小写)
User.status.in_([...])  # IN
User.status.not_in([...])  # NOT IN
User.age.between(18, 30)   # BETWEEN
User.email.is_(None)       # IS NULL
User.email.is_not(None)    # IS NOT NULL

# 逻辑组合
or_(User.age < 18, User.age > 60)          # OR
and_(User.age >= 18, User.active == True)  # AND(多个 where 参数默认就是 and)
not_(User.deleted == True)                 # NOT
```

## 3. 排序与分页

```python
stmt = (
    select(User)
    .order_by(User.created_at.desc())   # 倒序
    .order_by(User.age)                 # 正序
    .limit(20)                          # 每页条数
    .offset(40)                         # 偏移
)

# 多字段排序:先按 created_at 倒序,再按 id 正序
stmt = select(User).order_by(User.created_at.desc(), User.id.asc())
```

## 4. 聚合与分组:`func` + `group_by` / `having`

```python
from sqlalchemy import func

# 计数(最常用)
total = await db.scalar(
    select(func.count(User.id)).where(User.status == "active")
)

# 其他聚合
func.sum(Order.amount)   # 求和
func.avg(Order.amount)   # 平均
func.max(User.age)       # 最大
func.min(User.age)       # 最小
func.count()             # COUNT(*)

# 分组 + 过滤
stmt = (
    select(Order.user_id, func.count(Order.id).label("cnt"))
    .group_by(Order.user_id)
    .having(func.count(Order.id) > 5)
)
rows = (await db.execute(stmt)).all()  # [(user_id, cnt), ...]
```

## 5. 结果获取:`execute` / `scalars` / `scalar` / `get` / `first` / `one`

```python
# 拿 ORM 对象列表(最常用)
rows = (await db.scalars(select(User))).all()

# execute 返回 Result,可 .scalars() 转 ORM 对象,或直接取列
result = await db.execute(select(User.id, User.name))
rows = result.all()                 # 元组列表 [(id, name), ...]

# 拿单个标量(聚合/count)
count = await db.scalar(select(func.count(User.id)))

# 按主键拿单条,不存在返回 None
user = await db.get(User, 123)

# 单条结果的三种取法
first = (await db.scalars(select(User).where(...))).first()        # 第一条,无则 None
one = (await db.scalars(select(User).where(...))).one()            # 恰好一条,0/多条报错
one_or_none = (await db.scalars(select(User).where(...))).one_or_none()  # 0/1 条,多条报错
```

## 6. 写操作:`add` / `add_all` / `delete` / `flush` / `refresh`

```python
# 新增单条
user = User(name="张三", age=18)
db.add(user)

# 新增多条
db.add_all([User(name="a"), User(name="b")])

# 删除(ORM 实例)
await db.delete(user)

# flush:把 SQL 发给数据库执行(不提交),拿到自增 ID / Python 侧 default
await db.flush()

# refresh:再 SELECT 回读,拿 server_default / 触发器生成的值
await db.refresh(user)

# commit / rollback 通常交给 get_db 依赖(见 fastapi-db-operations.md),业务侧别手动 commit
```

## 7. 批量更新 / 删除(核心式,绕过 ORM)

```python
from sqlalchemy import update, delete

# 批量更新
await db.execute(
    update(User)
    .where(User.status == "inactive")
    .values(status="deleted", updated_at=now)
)

# 批量删除
await db.execute(delete(User).where(User.id < 100))

# 自增/自减
await db.execute(update(User).where(User.id == 1).values(age=User.age + 1))
```

## 8. 关系与预加载(异步重点)

```python
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

class User(Base):
    __tablename__ = "user"
    id: Mapped[int] = mapped_column(primary_key=True)
    orders: Mapped[list["Order"]] = relationship(back_populates="user")

class Order(Base):
    __tablename__ = "order"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"))
    user: Mapped["User"] = relationship(back_populates="orders")
```

查询时预加载关联对象(异步下必须,不能懒加载):

```python
from sqlalchemy.orm import selectinload, joinedload

# 查用户同时带上他们的订单
users = (await db.scalars(
    select(User).options(selectinload(User.orders))
)).all()

# selectinload:先查主表,再 IN 查关联表(推荐,多对多/一对多用)
# joinedload:一条 LEFT JOIN 查出(适合一对一/多对一)
```

> 异步里直接访问 `user.orders` 会报 `MissingGreenlet`,一定要在查询时用 `options(selectinload(...))` 预加载。

## 9. 常用模式

### 9.1 动态过滤(条件拼接)

```python
stmt = select(User)
if name:
    stmt = stmt.where(User.name.like(f"%{name}%"))
if status:
    stmt = stmt.where(User.status == status)
rows = (await db.scalars(stmt)).all()
```

### 9.2 分页封装(配合 count)

```python
async def paginate(db, stmt, limit, offset):
    total = await db.scalar(select(func.count()).select_from(stmt.subquery()))
    items = (await db.scalars(stmt.limit(limit).offset(offset))).all()
    return {"total": total, "items": items}
```

### 9.3 存在性检查

```python
from sqlalchemy import exists

has = await db.scalar(select(exists().where(User.name == "张三")))
if has:
    ...
```

### 9.4 去重

```python
rows = (await db.scalars(select(User.city).distinct())).all()
```

---

## 10. 模型字段:`mapped_column` 参数大全

```python
from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

class User(Base):
    __tablename__ = "user"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(64), nullable=False, comment="用户名")
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    age: Mapped[int] = mapped_column(Integer, default=18)
    score: Mapped[float] = mapped_column(Float, default=0.0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=beijing_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, onupdate=beijing_now)
```

### 常用参数

| 参数 | 作用 | 备注 |
|------|------|------|
| `primary_key=True` | 主键 | |
| `autoincrement=True` | 自增 | 主键默认自动开 |
| `nullable=False` | 非空 | |
| `default=` | Python 侧默认值 | flush 时填到对象上 |
| `server_default=` | 数据库侧默认值 | 需 refresh 才能拿到 |
| `onupdate=` | 更新时 Python 侧自动填 | 配合更新时间戳 |
| `index=True` | 建单列索引 | |
| `unique=True` | 唯一约束 | |
| `comment="..."` | 字段注释 | |

### 常用 SQL 类型

| 类型 | 用途 |
|------|------|
| `String(n)` | 定长字符串 |
| `Text` | 长文本 |
| `Integer` / `BigInteger` | 整数(大表主键用 BigInteger) |
| `Boolean` | 布尔 |
| `DateTime` / `Date` / `Time` | 时间 |
| `Numeric(p, s)` | 精确小数(金额用它,返回 `Decimal`,别用 Float) |
| `Float` | 浮点 |
| `JSON` | JSON |

### 联合索引 / 联合唯一约束

```python
from sqlalchemy import Index, UniqueConstraint

class Message(Base):
    __tablename__ = "message"
    __table_args__ = (
        Index("idx_user_created", "user_id", "created_at"),          # 联合索引
        UniqueConstraint("user_id", "name", name="uq_user_name"),    # 联合唯一
    )
    ...
```

### default vs server_default 的区别

| | `default=` | `server_default=` |
|--|-----------|-------------------|
| 值在哪算 | Python 侧,flush 时填 | 数据库侧,INSERT 时填 |
| 拿值时机 | `flush()` 后就有 | 需 `refresh()` 回读 |
| 适用 | 业务默认值、`beijing_now` | 数据库函数如 `CURRENT_TIMESTAMP` |

```python
# server_default 要用 text() 包一下
from sqlalchemy import text
mapped_column(DateTime, server_default=text("CURRENT_TIMESTAMP"))
```

## 11. 建表与迁移:`create_all` vs Alembic

### 11.1 create_all(开发够用)

你 `main.py` 的 lifespan 里已经用了 `Base.metadata.create_all`:

- 只**建新表**,不**改已有表**(加列/改类型不生效)。
- 适合开发期、原型、空库初始化。
- 生产环境别用它做 schema 变更。

### 11.2 Alembic(生产迁移)

```bash
# 1. 安装
uv add alembic

# 2. 初始化(异步项目用 async 模板)
alembic init -t async alembic

# 3. 生成迁移(自动对比模型与数据库的差异)
alembic revision --autogenerate -m "create conversation tables"

# 4. 应用迁移
alembic upgrade head
```

配置要点(`alembic/env.py`):

1. `target_metadata = Base.metadata`(指向你的模型基类)。
2. `sqlalchemy.url` 用 `settings.db_url`。
3. 迁移脚本会自动 import 模型,保证 `Base.metadata` 注册了所有表。

常用命令:

| 命令 | 作用 |
|------|------|
| `alembic revision --autogenerate -m "msg"` | 对比模型和库,生成迁移 |
| `alembic upgrade head` | 升级到最新 |
| `alembic downgrade -1` | 回退一个版本 |
| `alembic current` | 看当前版本 |
| `alembic history` | 看迁移历史 |

> 上了 Alembic 之后,记得把 lifespan 里的 `create_all` 删掉,否则两者会打架。

## 速查:最常用的 10 个

| 场景 | 写法 |
|------|------|
| 查列表 | `(await db.scalars(select(Model))).all()` |
| 查单条 | `(await db.scalars(select(Model).where(...))).first()` |
| 按主键查 | `await db.get(Model, id)` |
| 计数 | `await db.scalar(select(func.count(Model.id)))` |
| 新增 | `db.add(obj)` + `await db.flush()` |
| 删除 | `await db.delete(obj)` |
| 批量更新 | `await db.execute(update(Model).where(...).values(...))` |
| 分页 | `.order_by(...).limit(n).offset(m)` |
| 模糊查 | `.where(Model.name.like("%x%"))` |
| 预加载关联 | `.options(selectinload(Model.rel))` |
