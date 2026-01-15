"""JWT 配置文件生成器"""
from core.decorators import Generator
from ..base import BaseTemplateGenerator


@Generator(
    category="app_config",
    priority=16,
    requires=["ConfigBaseGenerator"],
    enabled_when=lambda c: c.has_auth(),
    description="生成 JWT 配置 (app/core/config/modules/jwt.py)"
)
class ConfigJwtGenerator(BaseTemplateGenerator):
    """生成 app/core/config/modules/jwt.py 文件"""

    def generate(self) -> None:
        """生成 JWT 配置文件"""
        # 仅在启用认证时生成
        if not self.config_reader.has_auth():
            return

        imports = [
            "from typing import Optional",
            "from pydantic import Field, PositiveInt, SecretStr",
            "from app.core.config.base import EnvBaseSettings",
        ]

        auth_type = self.config_reader.get_auth_type()
        project_name = self.config_reader.get_project_name()

        # 生成项目标识（用于 issuer 和 audience）
        project_identifier = project_name.lower().replace('-', '_').replace(' ', '_')

        # JWT 基础配置（所有认证类型都需要）
        base_fields = f'''    JWT_SECRET_KEY: SecretStr = Field(
        ...,
        repr=False,
        description="JWT 密钥（请妥善保管）"
    )
    JWT_ALGORITHM: str = Field(
        default="HS256",
        description="JWT 加密算法"
    )
    JWT_ACCESS_TOKEN_EXPIRATION: PositiveInt = Field(
        default=1800,
        description="访问令牌有效期（秒）"
    )'''

        # 仅完整 JWT 认证包含 Refresh Token
        if auth_type == "complete":
            base_fields += f'''
    JWT_REFRESH_TOKEN_EXPIRATION: PositiveInt = Field(
        default=86400,
        description="刷新令牌有效期（秒）"
    )'''

        # 添加 issuer 与 audience
        base_fields += f'''
    JWT_ISSUER: Optional[str] = Field(
        default="{project_identifier}",
        description="JWT 签发方（issuer）"
    )
    JWT_AUDIENCE: Optional[str] = Field(
        default="{project_identifier}_users",
        description="JWT 接收方（audience）"
    )'''

        content = f'''class JWTSettings(EnvBaseSettings):
    """JWT 认证配置"""

{base_fields}
'''

        self.file_ops.create_python_file(
            file_path="app/core/config/modules/jwt.py",
            docstring="JWT 认证配置模块",
            imports=imports,
            content=content,
            overwrite=True
        )
