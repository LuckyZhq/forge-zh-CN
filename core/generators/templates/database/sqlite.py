"""SQLite 数据库配置生成器"""
from core.decorators import Generator
from ..base import BaseTemplateGenerator


@Generator(
    category="database",
    priority=35,
    description="生成 SQLite 数据库配置"
)
class SQLiteGenerator(BaseTemplateGenerator):
    """SQLite 数据库配置生成器"""

    def generate(self) -> None:
        """生成 SQLite 数据库配置"""
        if self.config_reader.get_database_type() != "SQLite":
            return

        # 生成数据库连接模块
        self._generate_database_connection()

        # 生成数据库依赖
        self._generate_database_dependencies()

    def _generate_database_connection(self) -> None:
        """生成数据库连接模块"""
        content = '''"""SQLite 数据库连接配置"""
import os
from typing import Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config.modules.database import DatabaseSettings
from app.core.logger import logger_manager

# 获取数据库配置
db_config = DatabaseSettings()
logger = logger_manager.get_logger(__name__)

# 创建 SQLite 异步引擎
engine = create_async_engine(
    db_config.DATABASE_URL,
    echo=db_config.ECHO,
    poolclass=StaticPool,
    connect_args={
        "check_same_thread": False,  # SQLite 特有配置
    },
)

# 创建异步 Session 工厂
AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_database_session() -> AsyncSession:
    """获取数据库会话
    
    返回：
        AsyncSession: 数据库会话
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_database():
    """初始化数据库表"""
    from sqlmodel import SQLModel
    
    async with engine.begin() as conn:
        # 创建所有表
        await conn.run_sync(SQLModel.metadata.create_all)


async def close_database():
    """关闭数据库连接"""
    await engine.dispose()


class DatabaseConnectionManager:
    """SQLite 数据库连接管理器"""
    
    def __init__(self):
        pass
    
    async def initialize(self) -> None:
        """初始化数据库连接"""
        await init_database()
        logger.info("✅ SQLite 数据库初始化完成")
    
    async def test_connections(self) -> bool:
        """测试数据库连接"""
        try:
            from sqlalchemy import text
            async with AsyncSessionLocal() as session:
                # 简单测试查询
                await session.execute(text("SELECT 1"))
            logger.info("✅ SQLite 数据库连接测试成功")
            return True
        except Exception as e:
            logger.error(f"❌ SQLite 数据库连接测试失败: {e}")
            raise
    
    async def close(self) -> None:
        """关闭数据库连接"""
        await close_database()
        logger.info("✅ SQLite 数据库连接已关闭")
    
    async def __aenter__(self) -> "DatabaseConnectionManager":
        """进入异步上下文管理器"""
        await self.initialize()
        return self
    
    async def __aexit__(
        self,
        exc_type: Optional[type],
        exc_value: Optional[Exception],
        traceback: Optional[Any],
    ) -> None:
        """退出异步上下文管理器"""
        if exc_type is not None:
            logger.error(
                f"❌ DatabaseConnectionManager 上下文中发生异常: "
                f"{exc_type.__name__}: {exc_value}"
            )
        await self.close()
        return False


db_manager = DatabaseConnectionManager()
'''

        self.file_ops.create_python_file(
            file_path="app/core/database/connection.py",
            content=content,
            overwrite=True
        )

    def _generate_database_dependencies(self) -> None:
        """生成数据库依赖"""
        content = '''"""SQLite 数据库依赖"""
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends

from app.core.database.connection import get_database_session


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """获取数据库会话依赖
    
    产出：
        AsyncSession: 数据库会话
    """
    async for session in get_database_session():
        yield session


# 数据库依赖
DatabaseDep = Depends(get_db)
'''

        self.file_ops.create_python_file(
            file_path="app/core/database/dependencies.py",
            content=content,
            overwrite=True
        )
