"""配置基类文件生成器"""
from core.decorators import Generator
from ..base import BaseTemplateGenerator


@Generator(
    category="app_config",
    priority=10,
    description="生成 app/core/config/base.py"
)
class ConfigBaseGenerator(BaseTemplateGenerator):
    """生成 app/core/config/base.py 文件"""

    def generate(self) -> None:
        """生成配置基类文件"""
        imports = [
            "import os",
            "from pathlib import Path",
            "from dotenv import load_dotenv",
            "from pydantic_settings import BaseSettings",
        ]

        content = '''# 从 .env 文件加载环境变量
ENV = os.getenv("ENV", "development")

# 计算项目根目录路径（从 config/base.py 向上 4 层）
ENV_FILE = Path(__file__).resolve().parent.parent.parent.parent / f"secret/.env.{ENV}"

# 如果环境变量文件存在则加载，否则使用系统环境变量
if ENV_FILE.exists():
    load_dotenv(dotenv_path=ENV_FILE, override=True)
else:
    import warnings
    warnings.warn(
        f"环境变量文件 {ENV_FILE} 不存在。"
        "将使用系统环境变量。",
        UserWarning
    )


class EnvBaseSettings(BaseSettings):
    """环境配置基类
    
    所有配置类都应继承自该类。
    """
    
    class Config:
        env_file = ENV_FILE
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "allow"  # 允许模型中未定义的额外字段
'''

        self.file_ops.create_python_file(
            file_path="app/core/config/base.py",
            docstring="配置基类模块 —— 所有配置类的基类",
            imports=imports,
            content=content,
            overwrite=True
        )
