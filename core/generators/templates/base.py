"""基础模板生成器"""
from pathlib import Path
from core.config_reader import ConfigReader
from core.utils import FileOperations


class BaseTemplateGenerator:
    """所有代码生成器的基础生成器类"""

    def __init__(self, project_path: Path, config_reader: ConfigReader):
        """
        初始化基础生成器

        Args:
            project_path: 项目根目录路径
            config_reader: 配置读取器实例
        """
        self.project_path = Path(project_path)
        self.config_reader = config_reader
        self.file_ops = FileOperations(base_path=project_path)

    def generate(self) -> None:
        """生成文件 - 必须由子类实现"""
        raise NotImplementedError("子类必须实现 generate() 方法")
