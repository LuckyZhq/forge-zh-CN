"""邮件配置生成器"""
from pathlib import Path
from core.decorators import Generator
from core.utils import FileOperations
from core.config_reader import ConfigReader


@Generator(
    category="app_config",
    priority=17,
    requires=["ConfigBaseGenerator"],
    enabled_when=lambda c: c.get_auth_type() == 'complete',
    description="生成邮件配置"
)
class ConfigEmailGenerator:
    """邮件配置文件生成器"""

    def __init__(self, project_path: Path, config_reader: ConfigReader):
        """初始化配置生成器

        参数：
            project_path: 项目根目录路径
            config_reader: 配置读取生成器实例
        """
        self.project_path = Path(project_path)
        self.config_reader = config_reader
        self.file_ops = FileOperations(base_path=project_path)

    def generate(self) -> None:
        """生成邮件配置文件"""
        # 仅为完整 JWT 认证生成邮件配置
        if self.config_reader.get_auth_type() != "complete":
            return

        imports = [
            "from pydantic import Field, SecretStr",
            "from pydantic_settings import BaseSettings",
        ]

        content = '''class EmailSettings(BaseSettings):
    """邮件配置设置"""
    
    # SMTP 服务器配置
    EMAIL_HOST: str = Field(
        default="smtp.gmail.com",
        description="SMTP 服务器主机"
    )
    
    EMAIL_PORT: int = Field(
        default=587,
        description="SMTP 服务器端口"
    )
    
    EMAIL_HOST_USER: str = Field(
        default="",
        description="SMTP 用户名"
    )
    
    EMAIL_HOST_PASSWORD: SecretStr = Field(
        default="",
        description="SMTP 密码"
    )
    
    # SSL/TLS 配置
    EMAIL_USE_TLS: bool = Field(
        default=True,
        description="是否使用 TLS 连接 SMTP"
    )
    
    EMAIL_USE_SSL: bool = Field(
        default=False,
        description="是否使用 SSL 连接 SMTP"
    )
    
    EMAIL_SSL_CERT_REQS: str = Field(
        default="required",
        description="SSL 证书要求（required/optional/none）"
    )
    
    # 超时配置
    EMAIL_TIMEOUT: int = Field(
        default=30,
        description="SMTP 连接超时时间（秒）"
    )
    
    # 邮件过期时间
    EMAIL_EXPIRATION: int = Field(
        default=3600,
        description="邮件验证码过期时间（秒）"
    )
    
    # 邮件发件人配置
    EMAIL_FROM_NAME: str = Field(
        default="",
        description="邮件发件人名称"
    )
    
    EMAIL_FROM_EMAIL: str = Field(
        default="",
        description="邮件发件人地址"
    )
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"
'''

        self.file_ops.create_python_file(
            file_path="app/core/config/modules/email.py",
            docstring="邮件配置模块",
            imports=imports,
            content=content,
            overwrite=True
        )
