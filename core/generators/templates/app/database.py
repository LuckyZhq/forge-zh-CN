"""数据库配置文件生成器"""
from core.decorators import Generator
from ..base import BaseTemplateGenerator


@Generator(
    category="app_config",
    priority=15,
    requires=["ConfigBaseGenerator"],
    description="生成数据库配置 (app/core/config/modules/database.py)"
)
class ConfigDatabaseGenerator(BaseTemplateGenerator):
    """生成 app/core/config/modules/database.py 文件"""

    def generate(self) -> None:
        """生成数据库配置文件"""
        imports = [
            "from pydantic import Field, PositiveInt",
            "from app.core.config.base import EnvBaseSettings",
        ]

        # 根据数据库类型生成默认的连接 URL
        db_type = self.config_reader.get_database_type()
        project_name = self.config_reader.get_project_name()

        # 生成数据库名称（将项目名称转换为有效的数据库名称）
        db_name = project_name.lower().replace('-', '_').replace(' ', '_')

        if db_type == "PostgreSQL":
            default_url = f"postgresql://user:password@localhost:5432/{db_name}_dev"
        elif db_type == "MySQL":
            default_url = f"mysql://user:password@localhost:3306/{db_name}_dev"
        elif db_type == "SQLite":
            default_url = f"sqlite:///./{db_name}.db"
        else:
            raise ValueError(f"不支持的数据库类型: {db_type}")

        content = f'''class DatabaseSettings(EnvBaseSettings):
    """数据库配置"""
    
    # 数据库连接 URL
    DATABASE_URL: str = Field(
        default="{default_url}",
        description="数据库连接 URL",
    )
    
    # 连接池配置
    ECHO: bool = Field(
        default=False,
        description="是否启用 SQL 语句回显"
    )
    POOL_PRE_PING: bool = Field(
        default=True,
        description="是否在获取连接前进行预先 Ping 检测"
    )
    POOL_TIMEOUT: PositiveInt = Field(
        default=30,
        description="连接池超时时间（秒）"
    )
    POOL_SIZE: PositiveInt = Field(
        default=6,
        description="数据库连接池大小（保守策略：适用于 2 核心 2GB 服务器）",
    )
    POOL_MAX_OVERFLOW: PositiveInt = Field(
        default=2,
        description="数据库连接池最大溢出数量（保守策略：减少溢出连接）",
    )
'''

        self.file_ops.create_python_file(
            file_path="app/core/config/modules/database.py",
            docstring="数据库配置模块",
            imports=imports,
            content=content,
            overwrite=True
        )
