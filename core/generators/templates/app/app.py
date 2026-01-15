"""应用配置文件生成器"""
from core.decorators import Generator
from ..base import BaseTemplateGenerator


@Generator(
    category="app_config",
    priority=11,
    requires=["ConfigBaseGenerator"],
    description="生成应用配置 (app/core/config/modules/app.py)"
)
class ConfigAppGenerator(BaseTemplateGenerator):
    """生成 app/core/config/modules/app.py 文件"""

    def generate(self) -> None:
        """生成应用配置文件"""
        project_name = self.config_reader.get_project_name()

        imports = [
            "from pydantic import Field",
            "from app.core.config.base import EnvBaseSettings",
        ]

        content = f'''class AppSettings(EnvBaseSettings):
    """应用元数据配置"""
    
    APP_NAME: str = Field(
        default="{project_name}",
        description="应用名称"
    )
    APP_DESCRIPTION: str = Field(
        default="{project_name} 是一个 FastAPI 应用。",
        description="应用描述",
    )
    APP_VERSION: str = Field(
        default="0.1.0",
        description="应用版本"
    )
'''

        self.file_ops.create_python_file(
            file_path="app/core/config/modules/app.py",
            docstring="应用配置模块",
            imports=imports,
            content=content,
            overwrite=True
        )
