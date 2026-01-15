"""设置配置文件生成器"""
from core.decorators import Generator
from ..base import BaseTemplateGenerator


@Generator(
    category="app_config",
    priority=18,
    requires=["ConfigBaseGenerator"],
    description="生成配置聚合器 (app/core/config/settings.py)"
)
class ConfigSettingsGenerator(BaseTemplateGenerator):
    """生成 app/core/config/settings.py 文件"""

    def generate(self) -> None:
        """生成 Settings 配置文件"""
        imports = ["from functools import cached_property"]

        # 收集所有需要的配置模块
        config_modules = []

        # 基础配置（始终包含）
        config_modules.append({
            "import": "from app.core.config.modules.app import AppSettings",
            "property": "app",
            "class": "AppSettings"
        })

        config_modules.append({
            "import": "from app.core.config.modules.logger import LoggingSettings",
            "property": "logging",
            "class": "LoggingSettings"
        })

        # 数据库配置（当前为必选）
        config_modules.append({
            "import": "from app.core.config.modules.database import DatabaseSettings",
            "property": "database",
            "class": "DatabaseSettings"
        })

        # JWT 配置（启用认证时）
        if self.config_reader.has_auth():
            config_modules.append({
                "import": "from app.core.config.modules.jwt import JWTSettings",
                "property": "jwt",
                "class": "JWTSettings"
            })

        # 邮件配置（仅完整 JWT 认证）
        if self.config_reader.get_auth_type() == "complete":
            config_modules.append({
                "import": "from app.core.config.modules.email import EmailSettings",
                "property": "email",
                "class": "EmailSettings"
            })

        # CORS 配置（如启用）
        if self.config_reader.has_cors():
            config_modules.append({
                "import": "from app.core.config.modules.cors import CORSSettings",
                "property": "cors",
                "class": "CORSSettings"
            })

        # Redis 配置（如启用）
        if self.config_reader.has_redis():
            config_modules.append({
                "import": "from app.core.config.modules.redis import RedisSettings",
                "property": "redis",
                "class": "RedisSettings"
            })

        # Celery 配置（如启用）
        if self.config_reader.has_celery():
            config_modules.append({
                "import": "from app.core.config.modules.celery import CelerySettings",
                "property": "celery",
                "class": "CelerySettings"
            })

        # 构建 import 语句
        for module in config_modules:
            imports.append(module["import"])

        # 构建 Settings 类属性
        properties = []
        for module in config_modules:
            property_code = f'''    @cached_property
    def {module["property"]}(self) -> {module["class"]}:
        return {module["class"]}()'''
            properties.append(property_code)

        # 构建完整内容
        content = f'''class Settings:
    """全局配置类
    
    使用 cached_property 实现配置的惰性加载，以提升性能
    """

{chr(10).join(properties)}


# 创建全局 settings 实例
settings = Settings()
'''

        self.file_ops.create_python_file(
            file_path="app/core/config/settings.py",
            docstring="全局配置管理模块",
            imports=imports,
            content=content,
            overwrite=True
        )
