"""pyproject.toml 生成器"""
from core.decorators import Generator
from ..templates.base import BaseTemplateGenerator


@Generator(
    category="config",
    priority=1,
    description="生成包含依赖的 pyproject.toml 文件"
)
class PyprojectGenerator(BaseTemplateGenerator):
    """pyproject.toml 文件生成器"""

    def generate(self) -> None:
        """生成 pyproject.toml 文件"""
        project_name = self.config_reader.get_project_name()

        content = self._build_project_section(project_name)
        content += self._build_dependencies_section()
        content += self._build_dev_dependencies_section()
        content += self._build_build_system_section()
        content += self._build_tool_configs_section()

        self.file_ops.create_file(
            file_path="pyproject.toml",
            content=content,
            overwrite=True
        )

    def _build_project_section(self, project_name: str) -> str:
        """构建项目基础信息配置段"""
        return f'''[project]
name = "{project_name}"
version = "0.1.0"
description = "由 Forge 生成的 FastAPI 项目"
readme = "README.md"
requires-python = ">=3.10"
'''

    def _build_dependencies_section(self) -> str:
        """构建项目依赖配置段"""
        dependencies = self._get_dependencies()

        content = 'dependencies = [\n'
        for dep in dependencies:
            content += f'    "{dep}",\n'
        content += ']\n\n'

        return content

    def _build_dev_dependencies_section(self) -> str:
        """构建开发环境依赖配置段"""
        dev_dependencies = self._get_dev_dependencies()

        if not dev_dependencies:
            return ''

        content = '[project.optional-dependencies]\n'
        content += 'dev = [\n'
        for dep in dev_dependencies:
            content += f'    "{dep}",\n'
        content += ']\n\n'

        return content

    def _build_build_system_section(self) -> str:
        """构建构建系统（Build System）配置段"""
        return '''[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["app"]
'''

    def _build_tool_configs_section(self) -> str:
        """构建开发工具相关配置段"""
        content = ''

        if self.config_reader.has_testing():
            content += self._build_pytest_config()

        if self.config_reader.has_dev_tools():
            content += self._build_black_config()
            content += self._build_ruff_config()
            content += self._build_mypy_config()

        return content

    def _get_dependencies(self) -> list:
        """获取项目运行所需的依赖列表"""
        dependencies = [
            'fastapi>=0.104.0',
            'uvicorn[standard]>=0.24.0',
            'pydantic>=2.5.0',
            'pydantic-settings>=2.1.0',
            'loguru>=0.7.0',  # 日志库
        ]

        # 数据库相关依赖（当前为必需）
        dependencies.extend(self._get_database_dependencies())

        # 认证鉴权相关依赖
        if self.config_reader.has_auth():
            dependencies.extend(self._get_auth_dependencies())

        # Redis 相关依赖
        if self.config_reader.has_redis():
            dependencies.extend(self._get_redis_dependencies())

        # Celery 相关依赖
        if self.config_reader.has_celery():
            dependencies.extend(self._get_celery_dependencies())

        return dependencies

    def _get_database_dependencies(self) -> list:
        """获取数据库相关依赖列表"""
        deps = []

        db_type = self.config_reader.get_database_type()
        orm_type = self.config_reader.get_orm_type()

        # ORM 框架依赖
        if orm_type == "SQLModel":
            deps.append("sqlmodel>=0.0.14")
        elif orm_type == "SQLAlchemy":
            deps.append("sqlalchemy>=2.0.0")

        # 异步 SQLAlchemy 需要 greenlet
        deps.append("greenlet>=3.0.0")

        # 数据库驱动依赖
        if db_type == "PostgreSQL":
            deps.extend(["psycopg2-binary>=2.9.9", "asyncpg>=0.29.0"])
        elif db_type == "MySQL":
            deps.extend(["pymysql>=1.1.0", "aiomysql>=0.2.0"])
        elif db_type == "SQLite":
            deps.extend(["aiosqlite>=0.19.0"])

        # 数据库迁移工具依赖
        if self.config_reader.has_migration():
            deps.append("alembic>=1.13.0")

        return deps

    def _get_auth_dependencies(self) -> list:
        """获取认证与鉴权相关依赖列表"""
        deps = [
            "python-jose[cryptography]>=3.3.0",
            "argon2-cffi>=23.1.0",  # Argon2 密码哈希算法
            "python-multipart>=0.0.6",
            "email-validator>=2.1.0",  # 邮箱地址校验
        ]

        # 完整 JWT 认证模式需要邮件服务相关依赖
        if self.config_reader.get_auth_type() == "complete":
            deps.extend(
                [
                    "jinja2>=3.1.0",
                    "aiosmtplib>=3.0.0",  # 异步 SMTP 客户端
                ]
            )

        return deps

    def _get_dev_dependencies(self) -> list:
        """获取开发环境依赖列表"""
        dev_deps = []

        if self.config_reader.has_testing():
            dev_deps.extend(
                [
                    "pytest>=7.4.0",
                    "pytest-asyncio>=0.21.0",
                    "httpx>=0.25.0",
                    "aiosqlite>=0.19.0",  # 测试环境使用的 SQLite
                ]
            )

        if self.config_reader.has_dev_tools():
            dev_deps.extend(
                [
                    "black>=23.12.0",
                    "ruff>=0.1.0",
                    "mypy>=1.7.0",
                ]
            )

        return dev_deps

    def _get_redis_dependencies(self) -> list:
        """获取 Redis 相关依赖"""
        return [
            "redis>=5.0.0",  # Redis 客户端
        ]

    def _get_celery_dependencies(self) -> list:
        """获取 Celery 相关依赖"""
        return [
            "celery>=5.3.0",  # Celery 任务队列
            "flower>=2.0.0",  # Celery 监控工具
        ]

    def _build_pytest_config(self) -> str:
        """构建 pytest 配置"""
        return """
[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"
"""

    def _build_black_config(self) -> str:
        """构建 Black 代码格式化工具配置"""
        return """
[tool.black]
line-length = 88
target-version = ['py310']
include = '\\.pyi?$'
"""

    def _build_ruff_config(self) -> str:
        """构建 Ruff 代码检查工具配置"""
        return """
[tool.ruff]
line-length = 88
target-version = "py310"
select = ["E", "F", "I", "N", "W"]
ignore = []
"""

    def _build_mypy_config(self) -> str:
        """构建 MyPy 类型检查工具配置"""
        return '''
[tool.mypy]
python_version = "3.10"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = false
'''
