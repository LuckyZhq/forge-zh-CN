"""Celery 应用生成器"""
from core.decorators import Generator
from pathlib import Path
from ..base import BaseTemplateGenerator


@Generator(
    category="app",
    priority=47,
    enabled_when=lambda c: c.has_celery(),
    requires=["CeleryConfigGenerator"],
    description="生成 Celery 应用实例 (app/core/celery.py)"
)
class CeleryAppGenerator(BaseTemplateGenerator):
    """Celery 应用实例生成器"""

    def generate(self) -> None:
        """生成 Celery 应用实例文件"""
        # 获取数据库类型以便正确导入
        db_type = self.config_reader.get_database_type().lower()

        imports = [
            "from celery import Celery",
            "from celery.schedules import crontab",
            "from app.core.config.settings import settings",
            "import asyncio",
            "from functools import wraps",
            f"from app.core.database.{db_type} import {db_type}_manager",
            "from app.core.logger import logger_manager",
        ]

        content = f'''def with_db_init(func):
    """装饰器：自动为 Celery 任务初始化数据库连接"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        logger = logger_manager.get_logger(__name__)
        
        # 初始化数据库连接（Celery 工作进程需要单独初始化）
        async def init_db():
            try:
                await {db_type}_manager.initialize()
                logger.debug("数据库已成功初始化，供 Celery 任务使用")
            except Exception as e:
                logger.error(f"Celery 任务数据库初始化失败: {{e}}")
                raise
        
        # 在 Celery 任务中运行异步初始化
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            # 如果没有事件循环，创建一个新的
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        try:
            loop.run_until_complete(init_db())
        except Exception as e:
            logger.error(f"Celery 任务中的数据库初始化失败: {{e}}")
            raise
        
        # 执行原始任务
        return func(*args, **kwargs)
    
    return wrapper


class CeleryManager:
    def __init__(self):
        self.celery_app = Celery(
            "app",
            broker=settings.celery.CELERY_BROKER_URL,
            backend=settings.celery.CELERY_RESULT_BACKEND,
        )
    
    def setup(self):
        self.celery_app.conf.update(
            broker_connection_retry_on_startup=True,
            accept_content=settings.celery.CELERY_ACCEPT_CONTENT,
            task_serializer=settings.celery.CELERY_TASK_SERIALIZER,
            result_serializer=settings.celery.CELERY_RESULT_SERIALIZER,
            timezone=settings.celery.CELERY_TIMEZONE,
            enable_utc=settings.celery.CELERY_ENABLE_UTC,
        )
    
    def autodiscovery(self):
        self.celery_app.autodiscover_tasks(
            packages=["app.tasks"],
            force=True,
        )
    
    def start(self):
        self.celery_app.start()
    
    def close(self):
        self.celery_app.close()


# 创建 Celery 应用实例
celery_app = Celery(
    "app",
    broker=settings.celery.CELERY_BROKER_URL,
    backend=settings.celery.CELERY_RESULT_BACKEND,
)

# 配置 Celery 应用
celery_app.conf.update(
    broker_connection_retry_on_startup=True,
    accept_content=settings.celery.CELERY_ACCEPT_CONTENT,
    task_serializer=settings.celery.CELERY_TASK_SERIALIZER,
    result_serializer=settings.celery.CELERY_RESULT_SERIALIZER,
    timezone=settings.celery.CELERY_TIMEZONE,
    enable_utc=settings.celery.CELERY_ENABLE_UTC,
    
    # 优化配置：适用于 2GB 内存服务器
    worker_concurrency=1,  # 1 个工作进程（节省内存）
    worker_prefetch_multiplier=1,  # 避免工作进程预取过多任务
    task_acks_late=True,  # 完成任务后才确认任务
    worker_max_tasks_per_child=100,  # 每处理 100 个任务后重启工作进程
    task_time_limit=3600,  # 任务超时：1 小时
    task_soft_time_limit=3000,  # 软超时：50 分钟
    
    # 防止重复任务执行的配置
    task_reject_on_worker_lost=True,  # 工作进程崩溃时拒绝任务，避免重复执行
    task_ignore_result=False,  # 保留任务结果以便追踪
    
    # 确保任务只执行一次
    task_always_eager=False,  # 确保任务异步执行
    worker_disable_rate_limits=False,  # 启用速率限制
    
    # 使用唯一标识符防止重复执行
    task_store_eager_result=True,  # 存储即时模式任务结果
)

# 自动发现任务
# 设置 force=False，避免重复任务注册
celery_app.autodiscover_tasks(
    packages=["app.tasks"],
    force=False,  # 设置为 False 以避免重复任务注册
)

# 配置 Celery Beat 定时任务
celery_app.conf.beat_schedule = {{
    'backup-database-daily': {{
        'task': 'app.tasks.backup_database_task.backup_database_task',
        'schedule': crontab(hour=3, minute=0),  # 每天 3:00 AM 执行
        'args': (),
        'kwargs': {{
            'retention_days': 30,  # 保留备份 30 天
        }},
        'options': {{
            'expires': 3600,  # 任务过期时间：1 小时
        }}
    }}
}}
'''

        self.file_ops.create_python_file(
            file_path="app/core/celery.py",
            docstring="Celery 配置与应用实例",
            imports=imports,
            content=content,
            overwrite=True
        )
