"""Tasks __init__.py 生成器"""
from core.decorators import Generator
from pathlib import Path
from ..base import BaseTemplateGenerator


@Generator(
    category="task",
    priority=59,
    enabled_when=lambda c: c.has_celery(),
    description="生成 tasks __init__.py (app/tasks/__init__.py)"
)
class TasksInitGenerator(BaseTemplateGenerator):
    """Tasks __init__.py 生成器"""

    def generate(self) -> None:
        """生成 tasks __init__.py 文件"""

        imports = [
            "from .backup_database_task import backup_database_task",
        ]

        content = '''# 导出所有任务
__all__ = [
    "backup_database_task"
]
'''

        self.file_ops.create_python_file(
            file_path="app/tasks/__init__.py",
            docstring=(
                "Celery 任务模块\n\n"
                "该模块包含所有 Celery 异步任务的定义。\n\n"
                "用法示例：\n"
                "    from app.tasks.backup_database_task import backup_database_task\n"
                "    \n"
                "    # 异步执行任务\n"
                "    result = backup_database_task.delay()\n"
                "    \n"
                "    # 获取任务执行结果\n"
                "    task_result = result.get()"
            ),
            imports=imports,
            content=content,
            overwrite=True
        )
