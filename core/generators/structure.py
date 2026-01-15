"""项目结构生成模块"""
from pathlib import Path
from core.utils import FileOperations
from .alembic import AlembicGenerator


class StructureGenerator:
    """项目结构生成器 —— 创建目录结构及初始化文件"""

    def __init__(self, project_path: Path, config_reader: 'ConfigReader'):
        """初始化结构生成器

        参数：
            project_path: 项目根目录路径
            config_reader: 配置读取器实例
        """
        self.project_path = Path(project_path)
        self.config_reader = config_reader
        self.file_ops = FileOperations(base_path=project_path)

    def create_project_structure(self) -> None:
        """创建项目目录结构"""
        self._create_directories()
        self._create_init_files()
        # 说明：项目文件现在由 DynamicGeneratorOrchestrator
        # 在 ProjectGenerator.generate() 中生成
        self._init_alembic()

    def _create_directories(self) -> None:
        """创建所有必需的目录"""
        directories = [
            "app", "app/core", "app/core/config", "app/core/config/modules",
            "app/core/database", "app/decorators", "app/schemas", "app/utils",
            "app/crud", "app/models", "app/services", "app/routers", "app/routers/v1",
            "script", "static",
        ]

        if self.config_reader.has_migration():
            directories.append("alembic")

        if self.config_reader.has_testing():
            directories.extend(["tests", "tests/api", "tests/unit"])

        for directory in directories:
            (self.project_path / directory).mkdir(parents=True, exist_ok=True)

    def _create_init_files(self) -> None:
        """创建所有必需的 __init__.py 文件"""
        init_files = [
            "app/__init__.py", "app/core/__init__.py", "app/decorators/__init__.py",
            "app/schemas/__init__.py", "app/utils/__init__.py", "app/crud/__init__.py",
            "app/models/__init__.py", "app/services/__init__.py", "app/routers/__init__.py",
            "app/routers/v1/__init__.py",
        ]

        if self.config_reader.has_testing():
            init_files.extend([
                "tests/__init__.py", "tests/api/__init__.py", "tests/unit/__init__.py",
            ])

        # 创建特殊的 __init__.py 文件
        self._create_config_init()
        self._create_config_modules_init()
        self._create_database_init()

        # 批量创建普通的 __init__.py 文件
        for init_file in init_files:
            self.file_ops.create_file(init_file, content="", overwrite=False)

    def _create_config_init(self) -> None:
        """创建 app/core/config/__init__.py"""
        content = '''"""配置模块"""
from .settings import settings

__all__ = ["settings"]
'''
        self.file_ops.create_file(
            "app/core/config/__init__.py",
            content,
            overwrite=True
        )

    def _create_config_modules_init(self) -> None:
        """创建 app/core/config/modules/__init__.py"""
        imports = [
            "from .app import AppSettings",
            "from .logger import LoggingSettings",
            "from .database import DatabaseSettings",
            "from .jwt import JWTSettings",
        ]
        exports = ["AppSettings", "LoggingSettings", "DatabaseSettings", "JWTSettings"]

        if self.config_reader.get_auth_type() == "complete":
            imports.append("from .email import EmailSettings")
            exports.append("EmailSettings")

        if self.config_reader.has_cors():
            imports.append("from .cors import CORSSettings")
            exports.append("CORSSettings")

        content = f'''"""配置模块"""
{chr(10).join(imports)}

__all__ = [{', '.join([f'"{exp}"' for exp in exports])}]
'''
        self.file_ops.create_file(
            "app/core/config/modules/__init__.py",
            content,
            overwrite=True
        )

    def _create_database_init(self) -> None:
        """创建 app/core/database/__init__.py"""
        db_type = self.config_reader.get_database_type()

        if db_type == "SQLite":
            # SQLite 使用更简单的结构
            content = '''"""数据库模块"""
from .connection import db_manager, get_database_session

async def get_db():
    """获取数据库会话（异步）"""
    async for session in get_database_session():
        yield session

__all__ = ["db_manager", "get_db"]
'''
        else:
            # PostgreSQL 和 MySQL 使用管理器模式
            db_manager = (
                "postgresql_manager"
                if db_type == "PostgreSQL"
                else "mysql_manager"
            )
            content = f'''"""数据库模块"""
from .connection import db_manager
from .{db_type.lower()} import {db_manager}, Base

async def get_db():
    """获取数据库会话（异步）"""
    async for session in {db_manager}.get_db():
        yield session

__all__ = ["db_manager", "{db_manager}", "Base", "get_db"]
'''

        self.file_ops.create_file(
            "app/core/database/__init__.py",
            content,
            overwrite=True
        )

    def _init_alembic(self) -> None:
        """初始化 Alembic 数据库迁移工具"""
        if self.config_reader.has_migration():
            alembic_gen = AlembicGenerator(
                self.project_path,
                self.config_reader
            )
            alembic_gen.generate()
