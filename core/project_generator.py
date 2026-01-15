"""项目生成器模块"""
from pathlib import Path
from core.config_reader import ConfigReader
from .generators.structure import StructureGenerator
from .generators.orchestrator import GeneratorOrchestrator


class ProjectGenerator:
    """项目生成器 - 基于配置生成 FastAPI 项目"""

    def __init__(self, project_path: Path):
        """初始化项目生成器

        Args:
            project_path: 项目根目录路径
        """
        self.project_path = Path(project_path)
        self.config_reader = ConfigReader(project_path)
        self.structure_generator = StructureGenerator(project_path, self.config_reader)
        self.orchestrator = None  # 延迟初始化直到配置加载完成

    def generate(self) -> None:
        """生成项目结构和代码"""
        # 1. 创建目录结构
        self.structure_generator.create_project_structure()

        # 2. 配置加载后初始化编排器
        self.orchestrator = GeneratorOrchestrator(self.project_path, self.config_reader)

        # 3. 使用编排器生成所有文件
        self.orchestrator.generate()
