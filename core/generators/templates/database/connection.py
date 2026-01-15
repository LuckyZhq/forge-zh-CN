"""数据库连接文件生成器"""
from core.decorators import Generator
from pathlib import Path
from ..base import BaseTemplateGenerator


@Generator(
    category="database",
    priority=30,
    requires=["ConfigDatabaseGenerator"],
    description="生成数据库连接管理器 (app/core/database/connection.py)"
)
class DatabaseConnectionGenerator(BaseTemplateGenerator):
    """数据库连接管理器生成器"""

    def generate(self) -> None:
        """生成 app/core/database/connection.py"""
        db_type = self.config_reader.get_database_type()

        # SQLite 使用独立的连接模式，跳过该生成器
        if db_type == "SQLite":
            return

        # 根据数据库类型确定对应的管理器名称
        if db_type == "PostgreSQL":
            db_manager = "postgresql_manager"
        elif db_type == "MySQL":
            db_manager = "mysql_manager"
        else:  # SQLite（理论上不会进入）
            db_manager = "sqlite_manager"

        imports = [
            "from typing import Any, Optional",
            "from app.core.logger import logger_manager",
            f"from app.core.database.{db_type.lower()} import {db_manager}",
        ]

        content = f'''logger = logger_manager.get_logger(__name__)


class DatabaseConnectionManager:
    """数据库连接管理器 —— 统一管理数据库连接"""
    
    def __init__(self):
        self.{db_type.lower()}_manager = {db_manager}
    
    async def initialize(self) -> None:
        """初始化数据库连接"""
        await self.{db_type.lower()}_manager.initialize()
    
    async def test_connections(self) -> bool:
        """测试数据库连接"""
        try:
            # 测试数据库连接
            await self.{db_type.lower()}_manager.test_connection()
            logger.info("✅ 数据库连接测试成功")
            return True
        except Exception as e:
            logger.error(f"❌ 数据库连接测试失败: {{e}}")
            raise
    
    async def close(self) -> None:
        """关闭数据库连接"""
        await self.{db_type.lower()}_manager.close()
    
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
                f"{{exc_type.__name__}}: {{exc_value}}"
            )
        await self.close()
        # 返回 False 表示不吞掉异常，继续向外抛出
        return False


db_manager = DatabaseConnectionManager()
'''

        self.file_ops.create_python_file(
            file_path="app/core/database/connection.py",
            docstring="数据库连接管理模块",
            imports=imports,
            content=content,
            overwrite=True
        )
