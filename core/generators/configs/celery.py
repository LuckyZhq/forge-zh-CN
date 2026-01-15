"""Celery 配置生成器"""
from pathlib import Path
from core.decorators import Generator
from core.utils import FileOperations
from core.config_reader import ConfigReader


@Generator(
    category="config",
    priority=46,
    enabled_when=lambda c: c.has_celery(),
    requires=["RedisConfigGenerator"],
    description="生成 Celery 配置"
)
class CeleryConfigGenerator:
    """Celery 配置生成器"""

    def __init__(self, project_path: Path, config_reader: ConfigReader):
        """初始化 Celery 配置生成器

        参数：
            project_path: 项目根目录路径
            config_reader: 配置读取器实例
        """
        self.project_path = Path(project_path)
        self.config_reader = config_reader
        self.file_ops = FileOperations(base_path=project_path)

    def generate(self) -> None:
        """生成 Celery 配置"""
        if not self.config_reader.has_celery():
            return

        # 生成 Celery 配置模块
        self._generate_celery_config()

        # 说明：
        # Celery 应用实例由 CeleryAppGenerator 生成
        # 具体任务由各自的任务生成器负责生成

    def _generate_celery_config(self) -> None:
        """生成 Celery 配置设置"""
        # Celery 使用 Redis 作为消息代理（启用 Celery 时 Redis 必然可用）
        content = '''"""Celery 配置模块"""

from app.core.config.base import EnvBaseSettings
from pydantic import Field


class CelerySettings(EnvBaseSettings):
    """Celery 配置"""
    
    CELERY_BROKER_URL: str = Field(
        default="redis://localhost:6379/1",
        description="Celery 消息代理地址（Redis 数据库 1）",
    )
    
    CELERY_RESULT_BACKEND: str = Field(
        default="redis://localhost:6379/2",
        description="Celery 结果后端地址（Redis 数据库 2）",
    )
    
    CELERY_ACCEPT_CONTENT: list[str] = Field(
        default=["json"],
        description="Celery 接受的消息内容类型",
    )
    
    CELERY_TASK_SERIALIZER: str = Field(
        default="json",
        description="Celery 任务序列化方式",
    )
    
    CELERY_RESULT_SERIALIZER: str = Field(
        default="json",
        description="Celery 结果序列化方式",
    )
    
    CELERY_TIMEZONE: str = Field(
        default="UTC",
        description="Celery 使用的时区",
    )
    
    CELERY_ENABLE_UTC: bool = Field(
        default=True,
        description="是否启用 UTC 时间",
    )
'''

        self.file_ops.create_python_file(
            file_path="app/core/config/modules/celery.py",
            content=content,
            overwrite=True
        )
