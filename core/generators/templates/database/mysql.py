"""MySQL 数据库管理器生成器"""
from core.decorators import Generator
from pathlib import Path
from ..base import BaseTemplateGenerator


@Generator(
    category="database",
    priority=31,
    requires=["DatabaseConnectionGenerator"],
    enabled_when=lambda c: c.get_database_type() == 'MySQL',
    description="生成 MySQL 数据库管理器 (app/core/database/mysql.py)"
)
class DatabaseMySQLGenerator(BaseTemplateGenerator):
    """MySQL 数据库管理器生成器"""

    def generate(self) -> None:
        """生成 app/core/database/mysql.py"""
        db_type = self.config_reader.get_database_type()
        if db_type != "MySQL":
            return

        orm_type = self.config_reader.get_orm_type()

        imports = [
            "from collections.abc import AsyncGenerator",
            "from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession",
            "from sqlalchemy import create_engine, text",
            "from sqlalchemy.orm import sessionmaker, Session, declarative_base",
            "from app.core.logger import logger_manager",
            "from app.core.config.settings import settings",
        ]

        # 定义 SQLAlchemy Declarative Base
        base_definition = '''# SQLAlchemy 声明式基类
Base = declarative_base()

'''

        content = base_definition + '''class MySQLManager:
    """MySQL 连接管理器 —— 使用 SQLAlchemy / SQLModel ORM"""
    
    def __init__(self):
        self.logger = logger_manager.get_logger(__name__)
        self.async_engine: create_async_engine | None = None
        self.async_session_maker: async_sessionmaker | None = None
        self.sync_engine: create_engine | None = None
        self.sync_session_maker: sessionmaker | None = None
    
    def get_sqlalchemy_url(self) -> str:
        """构建 SQLAlchemy 异步连接 URL"""
        url = settings.database.DATABASE_URL
        # 确保使用 aiomysql 驱动
        if url.startswith("mysql://"):
            return url.replace("mysql://", "mysql+aiomysql://", 1)
        elif url.startswith("mysql+pymysql://"):
            return url.replace("mysql+pymysql://", "mysql+aiomysql://", 1)
        return url
    
    def get_sync_sqlalchemy_url(self) -> str:
        """构建 SQLAlchemy 同步连接 URL"""
        url = settings.database.DATABASE_URL
        # 确保使用 pymysql 驱动
        if url.startswith("mysql://"):
            return url.replace("mysql://", "mysql+pymysql://", 1)
        elif url.startswith("mysql+aiomysql://"):
            return url.replace("mysql+aiomysql://", "mysql+pymysql://", 1)
        return url
    
    async def initialize(self) -> None:
        """初始化异步与同步连接（幂等）"""
        if self.async_engine:
            self.logger.debug("MySQLManager 已经初始化，无需重复初始化。")
            return
        
        try:
            db = settings.database
            
            # 初始化异步引擎
            self.async_engine = create_async_engine(
                self.get_sqlalchemy_url(),
                echo=db.ECHO,
                pool_pre_ping=db.POOL_PRE_PING,
                pool_timeout=db.POOL_TIMEOUT,
                pool_size=db.POOL_SIZE,
                max_overflow=db.POOL_MAX_OVERFLOW,
                # 设置 MySQL 会话级时区为 UTC
                connect_args={
                    "init_command": "SET SESSION time_zone = '+00:00'",
                },
            )
            
            self.async_session_maker = async_sessionmaker(
                self.async_engine,
                class_=AsyncSession,
                expire_on_commit=False,
            )
            
            # 初始化同步引擎（用于后台任务）
            self.sync_engine = create_engine(
                self.get_sync_sqlalchemy_url(),
                echo=db.ECHO,
                pool_pre_ping=db.POOL_PRE_PING,
                pool_timeout=db.POOL_TIMEOUT,
                pool_size=db.POOL_SIZE,
                max_overflow=db.POOL_MAX_OVERFLOW,
                connect_args={
                    "init_command": "SET SESSION time_zone = '+00:00'",
                },
            )
            
            self.sync_session_maker = sessionmaker(
                self.sync_engine,
                class_=Session,
                expire_on_commit=False,
            )
            
            self.logger.info("✅ MySQL 初始化成功（异步 + 同步）。")
        except Exception:
            self.logger.exception("❌ MySQL 初始化失败。")
            raise
    
    async def get_db(self) -> AsyncGenerator[AsyncSession, None]:
        """FastAPI 依赖注入：返回异步数据库会话"""
        if not self.async_session_maker:
            raise RuntimeError("数据库尚未初始化，请先调用 initialize()。")
        
        async with self.async_session_maker() as session:
            yield session
    
    def get_sync_db(self) -> Session:
        """后台任务使用：返回同步数据库会话"""
        if not self.sync_session_maker:
            raise RuntimeError("数据库尚未初始化，请先调用 initialize()。")
        return self.sync_session_maker()
    
    async def test_connection(self) -> bool:
        """测试数据库连接"""
        if not self.async_session_maker:
            raise RuntimeError("数据库尚未初始化。")
        
        try:
            async with self.async_session_maker() as session:
                result = await session.execute(text("SELECT 1"))
                if result.scalar() != 1:
                    raise RuntimeError("❌ MySQL 连接测试失败。")
                self.logger.info("✅ MySQL 连接测试通过。")
                return True
        except Exception:
            self.logger.exception("❌ MySQL 连接测试失败。")
            raise
    
    async def close(self) -> None:
        """关闭连接池并释放资源"""
        if self.async_engine:
            try:
                await self.async_engine.dispose()
                self.async_engine = None
                self.async_session_maker = None
                self.logger.info("✅ MySQL 异步引擎已成功释放。")
            except Exception:
                self.logger.exception("❌ 释放 MySQL 异步引擎失败。")
                raise
        
        if self.sync_engine:
            try:
                self.sync_engine.dispose()
                self.sync_engine = None
                self.sync_session_maker = None
                self.logger.info("✅ MySQL 同步引擎已成功释放。")
            except Exception:
                self.logger.exception("❌ 释放 MySQL 同步引擎失败。")
                raise
    
    async def __aenter__(self) -> "MySQLManager":
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_value, traceback) -> None:
        await self.close()


# 单例实例
mysql_manager = MySQLManager()
'''

        self.file_ops.create_python_file(
            file_path="app/core/database/mysql.py",
            docstring="MySQL 数据库连接管理模块",
            imports=imports,
            content=content,
            overwrite=True
        )
