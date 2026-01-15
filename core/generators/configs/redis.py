"""Redis 配置生成器"""
from pathlib import Path
from core.decorators import Generator
from core.utils import FileOperations
from core.config_reader import ConfigReader


@Generator(
    category="config",
    priority=45,
    enabled_when=lambda c: c.has_redis(),
    description="生成 Redis 配置"
)
class RedisConfigGenerator:
    """Redis 配置生成器"""

    def __init__(self, project_path: Path, config_reader: ConfigReader):
        """初始化 Redis 配置生成器

        参数：
            project_path: 项目根目录路径
            config_reader: 配置读取器实例
        """
        self.project_path = Path(project_path)
        self.config_reader = config_reader
        self.file_ops = FileOperations(base_path=project_path)

    def generate(self) -> None:
        """生成 Redis 配置"""
        if not self.config_reader.has_redis():
            return

        # 生成 Redis 配置模块
        self._generate_redis_config()

        # 说明：Redis 连接管理器由 RedisAppGenerator 负责生成

    def _generate_redis_config(self) -> None:
        """生成 Redis 配置设置"""
        content = '''"""Redis 配置模块"""

from app.core.config.base import EnvBaseSettings
from pydantic import Field


class RedisSettings(EnvBaseSettings):
    """Redis 配置"""
    
    REDIS_CONNECTION_URL: str = Field(
        default="redis://localhost:6379",
        description=(
            "Redis 连接地址。支持带密码的格式："
            "redis://:password@host:port 或 redis://username:password@host:port"
        ),
    )
    
    REDIS_POOL_SIZE: int = Field(
        default=5,
        description=(
            "Redis 连接池的最大连接数（保守策略："
            "适用于 2 核 CPU、2GB 内存的服务器）"
        ),
    )
    
    REDIS_SOCKET_TIMEOUT: int = Field(
        default=10, 
        description="Redis socket 超时时间（秒）"
    )
    
    REDIS_DEFAULT_TTL: int = Field(
        default=3600, 
        description="缓存的默认生存时间（秒）"
    )
'''

        self.file_ops.create_python_file(
            file_path="app/core/config/modules/redis.py",
            content=content,
            overwrite=True
        )
