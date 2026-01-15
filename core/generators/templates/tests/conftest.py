"""Pytest 配置生成器"""
from core.decorators import Generator
from pathlib import Path
from ..base import BaseTemplateGenerator


@Generator(
    category="test",
    priority=110,
    requires=["DatabaseConnectionGenerator"],
    enabled_when=lambda c: c.has_testing(),
    description="生成 pytest 配置文件 (tests/conftest.py)"
)
class ConftestGenerator(BaseTemplateGenerator):
    """生成 pytest conftest.py 文件"""

    def generate(self) -> None:
        """生成 conftest.py"""
        if not self.config_reader.has_testing():
            return

        content = self._build_conftest()
        self.file_ops.create_file(
            file_path="tests/conftest.py",
            content=content,
            overwrite=True
        )

    def _build_conftest(self) -> str:
        """构建 conftest.py 内容"""
        imports = [
            "import pytest",
            "import asyncio",
            "from typing import AsyncGenerator, Generator",
            "from httpx import AsyncClient, ASGITransport",
            "from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker",
            "from app.main import app",
            "from app.core.config import settings",
            "from app.core.database import Base, get_db",
        ]

        content = f'''"""Pytest 配置和固件"""
{chr(10).join(imports)}


# 使用 SQLite 进行测试（基于文件的方式在异步环境下更可靠）
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """为异步测试创建事件循环"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def test_engine():
    """创建测试数据库引擎"""
    # 导入模型以将其注册到 SQLModel 元数据中
    from app.models.user import User  # noqa: F401
    
    # 使用基于文件的 SQLite 进行测试（比内存方式在异步环境下更可靠）
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        connect_args={{"check_same_thread": False}}
    )
    
    # 使用 SQLModel 元数据创建所有表
    async with engine.begin() as conn:
        from sqlmodel import SQLModel
        await conn.run_sync(SQLModel.metadata.create_all)
    
    yield engine
    
    # 删除所有表
    async with engine.begin() as conn:
        from sqlmodel import SQLModel
        await conn.run_sync(SQLModel.metadata.drop_all)
    
    await engine.dispose()
    
    # 清理测试数据库文件
    import os
    if os.path.exists("./test.db"):
        os.remove("./test.db")


@pytest.fixture(scope="function")
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """为测试创建数据库会话"""
    # 创建绑定到测试引擎的会话制造器
    async_session = async_sessionmaker(
        bind=test_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    
    async with async_session() as session:
        # 覆盖应用的数据库依赖
        async def override_get_db():
            yield session
        
        app.dependency_overrides[get_db] = override_get_db
        
        yield session
        
        # 清理：回滚任何未提交的更改
        await session.rollback()
        
        # 从表中删除所有数据（用于测试隔离）
        from sqlmodel import SQLModel
        for table in reversed(SQLModel.metadata.sorted_tables):
            await session.execute(table.delete())
        await session.commit()
        
        # 测试后清除覆盖
        app.dependency_overrides.clear()


@pytest.fixture(scope="function")
async def client(db_session) -> AsyncGenerator[AsyncClient, None]:
    """创建带有数据库会话覆盖的测试客户端"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
'''

        # 如果启用了身份验证，则添加认证固件
        if self.config_reader.has_auth():
            content += self._build_auth_fixtures()

        return content

    def _build_auth_fixtures(self) -> str:
        """构建身份验证固件"""
        return '''

@pytest.fixture
async def test_user_verified(db_session: AsyncSession):
    """创建已验证的测试用户用于登录/认证测试"""
    from app.models.user import User
    from app.core.security import get_password_hash
    
    user = User(
        email="test@example.com",
        username="testuser",
        hashed_password=get_password_hash("testpassword"),
        is_active=True,
        is_verified=True
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def test_user_unverified(db_session: AsyncSession):
    """创建未验证的测试用户用于邮箱验证测试"""
    from app.models.user import User
    from app.core.security import get_password_hash
    
    user = User(
        email="unverified@example.com",
        username="unverifieduser",
        hashed_password=get_password_hash("testpassword"),
        is_active=True,
        is_verified=False
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


# 向后兼容的别名
test_user = test_user_verified


@pytest.fixture
async def auth_headers(test_user_verified) -> dict:
    """获取身份验证请求头"""
    from app.core.security import security_manager
    
    access_token, _ = security_manager.create_access_token({"user_id": test_user_verified.id})
    return {"Authorization": f"Bearer {access_token}"}
'''
