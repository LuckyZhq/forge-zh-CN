"""CORS 配置文件生成器"""
from core.decorators import Generator
from ..base import BaseTemplateGenerator


@Generator(
    category="app_config",
    priority=14,
    requires=["ConfigBaseGenerator"],
    enabled_when=lambda c: c.has_cors(),
    description="生成 CORS 配置 (app/core/config/modules/cors.py)"
)
class ConfigCorsGenerator(BaseTemplateGenerator):
    """生成 app/core/config/modules/cors.py 文件"""

    def generate(self) -> None:
        """生成 CORS 配置文件"""
        # 仅在启用 CORS 时生成
        if not self.config_reader.has_cors():
            return

        imports = [
            "from pydantic import Field",
            "from app.core.config.base import EnvBaseSettings",
        ]

        content = '''class CORSSettings(EnvBaseSettings):
    """CORS（跨域资源共享）配置"""
    
    CORS_ALLOWED_ORIGINS: str = Field(
        default='https://heyxiaoli.com',
        description="允许的 CORS 来源（以逗号分隔）",
    )
    CORS_ALLOW_CREDENTIALS: bool = Field(
        default=True,
        description="是否允许携带凭证（cookies）"
    )
    CORS_ALLOW_METHODS: str = Field(
        default='GET,POST,PUT,DELETE,PATCH,OPTIONS,HEAD,TRACE,CONNECT',
        description="允许的 HTTP 方法（以逗号分隔）",
    )
    CORS_ALLOW_HEADERS: str = Field(
        default='Authorization,Content-Type,X-Language,Accept-Language',
        description="允许的 HTTP 头部（以逗号分隔）",
    )
    CORS_EXPOSE_HEADERS: str = Field(
        default='Content-Disposition,Content-Length,Content-Type,ETag,Last-Modified',
        description="暴露的 HTTP 头部（以逗号分隔）",
    )
'''

        self.file_ops.create_python_file(
            file_path="app/core/config/modules/cors.py",
            docstring="CORS 配置模块",
            imports=imports,
            content=content,
            overwrite=True
        )
