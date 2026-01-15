"""路由聚合器生成器 - 生成 app/routers/v1/__init__.py"""
from core.decorators import Generator
from pathlib import Path
from ..base import BaseTemplateGenerator


@Generator(
    category="router",
    priority=82,
    requires=["AuthRouterGenerator", "UserRouterGenerator"],
    enabled_when=lambda c: c.has_auth(),
    description="生成路由聚合器文件 (app/routers/v1/__init__.py)"
)
class RouterAggregatorGenerator(BaseTemplateGenerator):
    """路由聚合器生成器 - 导出所有 v1 路由"""

    def generate(self) -> None:
        """生成路由聚合器文件"""
        # 仅在启用身份验证时生成
        if not self.config_reader.has_auth():
            return

        self._generate_router_aggregator()

    def _generate_router_aggregator(self) -> None:
        """生成 app/routers/v1/__init__.py"""
        imports = [
            "from .auth import router as auth_router",
            "from .users import router as user_router",
        ]

        exports = ["auth_router", "user_router"]

        content = f'''# 导出所有路由
__all__ = {exports}
'''

        self.file_ops.create_python_file(
            file_path="app/routers/v1/__init__.py",
            docstring="API v1 路由模块 - 聚合所有 v1 路由",
            imports=imports,
            content=content,
            overwrite=True
        )
