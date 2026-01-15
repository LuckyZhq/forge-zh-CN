"""生成器编排器 - 自动发现和管理生成器"""
from pathlib import Path
from typing import List

from ..config_reader import ConfigReader
from ..decorators import GENERATORS, GeneratorDefinition


class GeneratorOrchestrator:
    """生成器编排器 - 使用装饰器自动发现和管理生成器"""

    def __init__(self, project_path: Path, config_reader: ConfigReader):
        """
        初始化编排器

        Args:
            project_path: 项目根目录路径
            config_reader: 配置读取器实例
        """
        self.project_path = Path(project_path)
        self.config_reader = config_reader
        self.generators = []
        self._initialize_generators()

    def _initialize_generators(self) -> None:
        """初始化生成器 - 自动发现、过滤和排序"""
        # 1. 导入所有生成器模块（触发装饰器注册）
        self._import_all_generators()

        # 2. 过滤已启用的生成器
        enabled_generators = self._filter_enabled_generators()

        # 3. 检查冲突
        self._check_conflicts(enabled_generators)

        # 4. 解析依赖并排序
        sorted_generators = self._resolve_dependencies(enabled_generators)

        # 5. 实例化生成器
        self.generators = self._instantiate_generators(sorted_generators)

        # 6. 记录生成器（用于调试）
        self._log_generators()

    def _import_all_generators(self) -> None:
        """导入所有生成器模块以触发装饰器注册"""
        # 配置文件生成器
        from core.generators.configs.pyproject import PyprojectGenerator
        from core.generators.configs.readme import ReadmeGenerator
        from core.generators.configs.gitignore import GitignoreGenerator
        from core.generators.configs.env import EnvGenerator
        from core.generators.configs.license import LicenseGenerator
        from core.generators.configs.redis import RedisConfigGenerator
        from core.generators.configs.celery import CeleryConfigGenerator

        # 部署配置生成器
        from core.generators.deployment.dockerfile import DockerfileGenerator
        from core.generators.deployment.docker_compose import DockerComposeGenerator
        from core.generators.deployment.dockerignore import DockerignoreGenerator

        # 应用代码生成器
        from core.generators.templates.app.security import SecurityGenerator
        from core.generators.templates.app.main import MainGenerator
        from core.generators.templates.app.base import ConfigBaseGenerator
        from core.generators.templates.app.app import ConfigAppGenerator
        from core.generators.templates.app.logger_config import ConfigLoggerGenerator
        from core.generators.templates.app.logger_manager import LoggerManagerGenerator
        from core.generators.templates.app.cors import ConfigCorsGenerator
        from core.generators.templates.app.database import ConfigDatabaseGenerator
        from core.generators.templates.app.jwt import ConfigJwtGenerator
        from core.generators.templates.app.email import ConfigEmailGenerator
        from core.generators.templates.app.settings import ConfigSettingsGenerator
        from core.generators.templates.app.deps import CoreDepsGenerator

        # 数据库生成器
        from core.generators.templates.database.connection import DatabaseConnectionGenerator
        from core.generators.templates.database.mysql import DatabaseMySQLGenerator
        from core.generators.templates.database.postgresql import DatabasePostgreSQLGenerator
        from core.generators.templates.database.sqlite import SQLiteGenerator
        from core.generators.templates.database.dependencies import DatabaseDependenciesGenerator

        # 模型生成器
        from core.generators.templates.models.user import UserModelGenerator
        from core.generators.templates.models.token import TokenModelGenerator

        # 模式生成器
        from core.generators.templates.schemas.user import UserSchemaGenerator
        from core.generators.templates.schemas.token import TokenSchemaGenerator

        # CRUD 生成器
        from core.generators.templates.crud.user import UserCRUDGenerator
        from core.generators.templates.crud.token import TokenCRUDGenerator

        # 服务生成器
        from core.generators.templates.services.auth import AuthServiceGenerator

        # 路由生成器
        from core.generators.templates.routers.auth import AuthRouterGenerator
        from core.generators.templates.routers.user import UserRouterGenerator
        from core.generators.templates.routers.router_aggregator import RouterAggregatorGenerator

        # 装饰器生成器
        from core.generators.templates.decorators.rate_limit import RateLimitDecoratorGenerator

        # 邮件生成器
        from core.generators.templates.email.email import EmailServiceGenerator
        from core.generators.templates.email.email_template import EmailTemplateGenerator

        # 任务生成器
        from core.generators.templates.tasks.backup_database_task import BackupDatabaseTaskGenerator
        from core.generators.templates.tasks.tasks_init import TasksInitGenerator

        # 应用核心生成器
        from core.generators.templates.app.celery import CeleryAppGenerator
        from core.generators.templates.app.redis import RedisAppGenerator

        # 测试生成器
        from core.generators.templates.tests.conftest import ConftestGenerator
        from core.generators.templates.tests.test_main import TestMainGenerator
        from core.generators.templates.tests.test_auth import TestAuthGenerator
        from core.generators.templates.tests.test_users import TestUsersGenerator

        # Alembic 生成器
        from core.generators.alembic import AlembicGenerator

    def _filter_enabled_generators(self) -> List[GeneratorDefinition]:
        """过滤已启用的生成器"""
        enabled = []

        for name, gen_def in GENERATORS.items():
            if self._is_enabled(gen_def):
                enabled.append(gen_def)

        return enabled

    def _is_enabled(self, gen_def: GeneratorDefinition) -> bool:
        """检查生成器是否应该启用"""
        if gen_def.enabled_when is None:
            return True

        try:
            return gen_def.enabled_when(self.config_reader)
        except Exception as e:
            print(f"警告: 检查 {gen_def.name} 是否启用时出错: {e}")
            return False

    def _check_conflicts(self, generators: List[GeneratorDefinition]) -> None:
        """检查生成器冲突"""
        enabled_names = {gen.name for gen in generators}

        for gen_def in generators:
            for conflict in gen_def.conflicts:
                if conflict in enabled_names:
                    raise ValueError(
                        f"生成器冲突: {gen_def.name} 与 {conflict} 冲突"
                    )

    def _resolve_dependencies(
        self,
        generators: List[GeneratorDefinition]
    ) -> List[GeneratorDefinition]:
        """
        解析依赖并排序（拓扑排序）

        Returns:
            排序后的生成器列表
        """
        # 创建名称到定义的映射
        gen_map = {gen.name: gen for gen in generators}

        # 拓扑排序
        sorted_gens = []
        visited = set()
        visiting = set()

        def visit(gen_def: GeneratorDefinition):
            if gen_def.name in visited:
                return

            if gen_def.name in visiting:
                raise ValueError(f"检测到循环依赖: {gen_def.name}")

            visiting.add(gen_def.name)

            # 先访问依赖项
            for req_name in gen_def.requires:
                req_gen = gen_map.get(req_name)
                if req_gen:
                    visit(req_gen)
                else:
                    print(f"警告: {gen_def.name} 需要 {req_name}，但它未启用")

            visiting.remove(gen_def.name)
            visited.add(gen_def.name)
            sorted_gens.append(gen_def)

        # 按优先级顺序访问
        for gen_def in sorted(generators, key=lambda g: g.priority):
            visit(gen_def)

        return sorted_gens

    def _instantiate_generators(
        self,
        gen_defs: List[GeneratorDefinition]
    ) -> List:
        """实例化生成器"""
        instances = []

        for gen_def in gen_defs:
            try:
                instance = gen_def.generator_class(
                    self.project_path,
                    self.config_reader
                )
                instances.append(instance)
            except Exception as e:
                print(f"错误: 实例化 {gen_def.name} 失败: {e}")
                raise

        return instances

    def _log_generators(self) -> None:
        """记录生成器信息（用于调试）"""
        # print(f"调试: 已注册生成器总数: {len(GENERATORS)}")
        # print(f"调试: 已启用生成器数: {len(self.generators)}")
        # for i, gen in enumerate(self.generators, 1):
        #     print(f"  {i}. {gen.__class__.__name__}")
        pass

    def generate(self) -> None:
        """生成所有项目文件"""
        # print(f"信息: 开始使用 {len(self.generators)} 个生成器进行生成")

        for generator in self.generators:
            try:
                # print(f"调试: 运行 {generator.__class__.__name__}")
                generator.generate()
            except Exception as e:
                print(f"{generator.__class__.__name__} 中出错: {e}")
                raise

        # print("信息: 生成成功完成")
