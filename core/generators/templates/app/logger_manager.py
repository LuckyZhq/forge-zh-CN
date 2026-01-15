"""日志管理器生成器"""
from core.decorators import Generator
from ..base import BaseTemplateGenerator


@Generator(
    category="app_config",
    priority=13,
    requires=["ConfigLoggerGenerator"],
    description="生成日志管理器 (app/core/logger.py)"
)
class LoggerManagerGenerator(BaseTemplateGenerator):
    """生成 app/core/logger.py 文件 —— 日志管理器"""

    def generate(self) -> None:
        """生成日志管理器文件"""
        imports = [
            "import sys",
            "import logging",
            "from pathlib import Path",
            "from typing import Optional",
            "from loguru import logger",
            "",
            "from app.core.config.settings import settings",
        ]

        content = '''class LoggerManager:
    """日志管理器
    
    使用 Loguru 作为日志库，提供统一的日志管理接口
    """
    
    def __init__(self):
        self._initialized = False
        self._loggers = {}
    
    def setup(self) -> None:
        """初始化日志配置"""
        if self._initialized:
            return
        
        # 移除 Loguru 默认的 handler
        logger.remove()
        
        # 控制台输出
        if settings.logging.LOG_TO_CONSOLE:
            logger.add(
                sys.stdout,
                level=settings.logging.LOG_CONSOLE_LEVEL,
                format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
                       "<level>{level: <8}</level> | "
                       "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
                       "<level>{message}</level>",
                colorize=True,
            )
        
        # 文件输出
        if settings.logging.LOG_TO_FILE:
            log_path = Path(settings.logging.LOG_FILE_PATH)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            
            logger.add(
                settings.logging.LOG_FILE_PATH,
                level=settings.logging.LOG_LEVEL,
                format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
                rotation=settings.logging.LOG_ROTATION,
                retention=settings.logging.LOG_RETENTION_PERIOD,
                compression="zip",
                encoding="utf-8",
            )
        
        # 拦截标准库 logging
        self._intercept_standard_logging()
        
        self._initialized = True
        logger.info("日志系统初始化成功")
    
    def _intercept_standard_logging(self) -> None:
        """拦截标准库 logging，并重定向到 Loguru"""
        
        class InterceptHandler(logging.Handler):
            def emit(self, record: logging.LogRecord) -> None:
                # 获取对应的 Loguru 日志级别
                try:
                    level = logger.level(record.levelname).name
                except ValueError:
                    level = record.levelno
                
                # 查找调用栈位置
                frame, depth = logging.currentframe(), 2
                while frame.f_code.co_filename == logging.__file__:
                    frame = frame.f_back
                    depth += 1
                
                logger.opt(depth=depth, exception=record.exc_info).log(
                    level, record.getMessage()
                )
        
        # 拦截标准库 logging
        logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)
        
        # 拦截常见第三方库日志
        for logger_name in ["uvicorn", "uvicorn.access", "uvicorn.error", "fastapi"]:
            logging.getLogger(logger_name).handlers = [InterceptHandler()]
    
    def get_logger(self, name: Optional[str] = None):
        """获取日志实例
        
        参数：
            name: 日志名称，通常使用 __name__
        
        返回：
            Loguru logger 实例
        """
        if not self._initialized:
            self.setup()
        
        if name:
            return logger.bind(name=name)
        return logger


# 创建全局单例
logger_manager = LoggerManager()
'''

        self.file_ops.create_python_file(
            file_path="app/core/logger.py",
            docstring="日志管理模块",
            imports=imports,
            content=content,
            overwrite=True
        )
