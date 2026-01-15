"""Main.py generator"""

from core.decorators import Generator
from pathlib import Path
from .base import BaseTemplateGenerator


@Generator(
    category="app",
    priority=90,
    requires=[
        "ConfigSettingsGenerator",
        "LoggerManagerGenerator",
        "DatabaseConnectionGenerator",
    ],
    description="Generate main application entry point (app/main.py)",
)
class MainGenerator(BaseTemplateGenerator):
    """Main.py File generator"""

    def generate(self) -> None:
        """generate main.py file"""
        auth_type = (
            self.config_reader.get_auth_type()
            if self.config_reader.has_auth()
            else None
        )

        if auth_type:
            self._generate_main_with_auth()
        else:
            self._generate_basic_main()

    def _generate_basic_main(self) -> None:
        """generate base main.py (no authentication)"""
        imports = [
            "import os",
            "import uvicorn",
            "from fastapi import FastAPI, HTTPException, Request",
            "from fastapi.responses import JSONResponse",
            "from fastapi.openapi.utils import get_openapi",
            "from fastapi.middleware.cors import CORSMiddleware",
            "from fastapi.staticfiles import StaticFiles",
            "",
            "from app.core.config.settings import settings",
            "from app.core.logger import logger_manager",
            "from app.core.database import db_manager",
        ]

        # Add Redis import if enabled
        if self.config_reader.has_redis():
            imports.append("from app.core.redis import redis_manager")

        # 构建 lifespan 函数
        lifespan_content = '''# 创建 LoggerManager 实例
logger_manager.setup()

# 创建 Logger 实例
logger = logger_manager.get_logger(__name__)


# 创建 lifespan
async def lifespan(_app: FastAPI):
    """应用生命周期管理"""
    logger.info("🚩 应用正在启动...")
    logger.info(f"🚧 当前运行环境：{os.getenv('ENV', 'development')}")

    try:
        # 初始化数据库连接
        await db_manager.initialize()
        logger.info("🎉 数据库连接初始化成功")
        await db_manager.test_connections()
        logger.info("🎉 数据库连接测试成功")
    except Exception as e:
        logger.error(f"❌ 数据库连接失败：{e}")
        logger.warning("⚠️ 应用将在未建立数据库连接的情况下启动")'''

        # 如果启用了 Redis，则添加 Redis 初始化逻辑
        if self.config_reader.has_redis():
            lifespan_content += """

    try:
        # 初始化 Redis 连接
        await redis_manager.initialize_async()
        logger.info("🎉 Redis 连接初始化成功")
        await redis_manager.async_test_connection()
        logger.info("🎉 Redis 连接测试成功")
    except Exception as e:
        logger.error(f"❌ Redis 连接失败：{e}")
        logger.warning("⚠️ 应用将在未建立 Redis 连接的情况下启动")"""

        lifespan_content += """

    yield

    # 关闭数据库连接
    try:
        await db_manager.close()
        logger.info("🎉 数据库连接已成功关闭")
    except Exception as e:
        logger.error(f"❌ 数据库连接关闭失败：{e}")
        logger.warning("⚠️ 数据库连接关闭失败")"""

        # 如果启用了 Redis，则添加 Redis 清理逻辑
        if self.config_reader.has_redis():
            lifespan_content += """

    # 关闭 Redis 连接
    try:
        await redis_manager.close()
        logger.info("🎉 Redis 连接已成功关闭")
    except Exception as e:
        logger.error(f"❌ Redis 连接关闭失败：{e}")
        logger.warning("⚠️ Redis 连接关闭失败")"""

        # 构建主应用内容
        app_content = '''

# 创建 FastAPI 实例
app = FastAPI(
    lifespan=lifespan,
    title=settings.app.APP_NAME,
    version=settings.app.APP_VERSION,
    description=settings.app.APP_DESCRIPTION,
)


# 全局异常处理器
@app.exception_handler(HTTPException)
async def http_exception_handler(_request: Request, exc: HTTPException):
    """HTTP 异常处理器"""
    logger.error(f"HTTPException: {exc}")
    error_detail = exc.detail

    if isinstance(error_detail, dict):
        error_message = error_detail.get("error", str(error_detail))
    else:
        error_message = str(error_detail)

    return JSONResponse(
        status_code=exc.status_code,
        content={"status": exc.status_code, "error": error_message},
    )


@app.exception_handler(Exception)
async def general_exception_handler(_request: Request, exc: Exception):
    """通用异常处理器"""
    logger.error(f"Exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"status": 500, "error": "服务器内部错误"},
    )


# CORS 中间件'''

        # Add CORS configuration if enabled
        if self.config_reader.has_cors():
            app_content += """
allow_origins = [x.strip() for x in settings.cors.CORS_ALLOWED_ORIGINS.split(',') if x.strip()]
allow_methods = [x.strip() for x in settings.cors.CORS_ALLOW_METHODS.split(',') if x.strip()]
allow_headers = [x.strip() for x in settings.cors.CORS_ALLOW_HEADERS.split(',') if x.strip()]
allow_credentials = settings.cors.CORS_ALLOW_CREDENTIALS
expose_headers = [x.strip() for x in settings.cors.CORS_EXPOSE_HEADERS.split(',') if x.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_methods=allow_methods,
    allow_headers=allow_headers,
    allow_credentials=allow_credentials,
    expose_headers=expose_headers,
)"""

        app_content += '''


# 静态文件
static_dir = os.path.join(os.path.dirname(__file__), "..", "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")


# 健康检查接口
@app.get("/health", tags=["Health"])
async def health_check():
    """健康检查接口"""
    return {"status": "healthy"}


# OpenAPI 文档
def custom_openapi():
    """自定义 OpenAPI 文档"""
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title=settings.app.APP_NAME,
        version=settings.app.APP_VERSION,
        description=settings.app.APP_DESCRIPTION,
        routes=app.routes,
    )

    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi


# 启动应用
if __name__ == "__main__":
    if os.getenv("ENV") == "development":
        logger.info("🚩 正在以开发模式启动应用...")
        uvicorn.run(
            app="app.main:app",
            host="127.0.0.1",
            port=8000,
            reload=True,
        )'''

        content = lifespan_content + app_content

        self.file_ops.create_python_file(
            file_path="app/main.py",
            docstring="FastAPI 应用主入口",
            imports=imports,
            content=content,
            overwrite=True,
        )

    def _generate_main_with_auth(self) -> None:
        """生成包含认证功能的 main.py"""
        imports = [
            "import os",
            "import uvicorn",
            "from fastapi import FastAPI, HTTPException, Request",
            "from fastapi.responses import JSONResponse",
            "from fastapi.openapi.utils import get_openapi",
            "from fastapi.middleware.cors import CORSMiddleware",
            "from fastapi.staticfiles import StaticFiles",
            "",
            "from app.core.config.settings import settings",
            "from app.core.logger import logger_manager",
            "from app.core.database import db_manager",
        ]

        # 如果启用了 Redis，则添加 Redis 导入
        if self.config_reader.has_redis():
            imports.append("from app.core.redis import redis_manager")

        # 添加路由导入
        router_imports = [
            "    auth_router,",
            "    user_router,",
        ]

        imports.extend(
            [
                "",
                "from app.routers.v1 import (",
            ]
            + router_imports
            + [
                ")",
            ]
        )

        # 构建 lifespan 函数
        lifespan_content = '''# 创建 LoggerManager 实例
logger_manager.setup()

# 创建 Logger 实例
logger = logger_manager.get_logger(__name__)


# 创建 lifespan
async def lifespan(_app: FastAPI):
    """应用生命周期管理"""
    logger.info("🚩 应用正在启动...")
    logger.info(f"🚧 当前运行环境：{os.getenv('ENV', 'development')}")

    try:
        # 初始化数据库连接
        await db_manager.initialize()
        logger.info("🎉 数据库连接初始化成功")
        await db_manager.test_connections()
        logger.info("🎉 数据库连接测试成功")
    except Exception as e:
        logger.error(f"❌ 数据库连接失败：{e}")
        logger.warning("⚠️ 应用将在未建立数据库连接的情况下启动")'''

        # 如果启用了 Redis，则添加 Redis 初始化逻辑
        if self.config_reader.has_redis():
            lifespan_content += """

    try:
        # 初始化 Redis 连接
        await redis_manager.initialize_async()
        logger.info("🎉 Redis 连接初始化成功")
        await redis_manager.async_test_connection()
        logger.info("🎉 Redis 连接测试成功")
    except Exception as e:
        logger.error(f"❌ Redis 连接失败：{e}")
        logger.warning("⚠️ 应用将在未建立 Redis 连接的情况下启动")"""

        lifespan_content += """

    yield

    # 关闭数据库连接
    try:
        await db_manager.close()
        logger.info("🎉 数据库连接已成功关闭")
    except Exception as e:
        logger.error(f"❌ 数据库连接关闭失败：{e}")
        logger.warning("⚠️ 数据库连接关闭失败")"""

        # 如果启用了 Redis，则添加 Redis 清理逻辑
        if self.config_reader.has_redis():
            lifespan_content += """

    # 关闭 Redis 连接
    try:
        await redis_manager.close()
        logger.info("🎉 Redis 连接已成功关闭")
    except Exception as e:
        logger.error(f"❌ Redis 连接关闭失败：{e}")
        logger.warning("⚠️ Redis 连接关闭失败")"""

        # 构建主应用内容
        app_content = '''

# 创建 FastAPI 实例
app = FastAPI(
    lifespan=lifespan,
    title=settings.app.APP_NAME,
    version=settings.app.APP_VERSION,
    description=settings.app.APP_DESCRIPTION,
)


# 全局异常处理器
@app.exception_handler(HTTPException)
async def http_exception_handler(_request: Request, exc: HTTPException):
    """HTTP 异常处理器"""
    logger.error(f"HTTPException: {exc}")
    error_detail = exc.detail

    if isinstance(error_detail, dict):
        error_message = error_detail.get("error", str(error_detail))
    else:
        error_message = str(error_detail)

    return JSONResponse(
        status_code=exc.status_code,
        content={"status": exc.status_code, "error": error_message},
    )


@app.exception_handler(Exception)
async def general_exception_handler(_request: Request, exc: Exception):
    """通用异常处理器"""
    logger.error(f"Exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"status": 500, "error": "服务器内部错误"},
    )


# CORS 中间件'''

        # Add CORS configuration if enabled
        if self.config_reader.has_cors():
            app_content += """
allow_origins = [x.strip() for x in settings.cors.CORS_ALLOWED_ORIGINS.split(',') if x.strip()]
allow_methods = [x.strip() for x in settings.cors.CORS_ALLOW_METHODS.split(',') if x.strip()]
allow_headers = [x.strip() for x in settings.cors.CORS_ALLOW_HEADERS.split(',') if x.strip()]
allow_credentials = settings.cors.CORS_ALLOW_CREDENTIALS
expose_headers = [x.strip() for x in settings.cors.CORS_EXPOSE_HEADERS.split(',') if x.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_methods=allow_methods,
    allow_headers=allow_headers,
    allow_credentials=allow_credentials,
    expose_headers=expose_headers,
)"""

        app_content += """


# Static files
static_dir = os.path.join(os.path.dirname(__file__), "..", "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")


# Include routers
app.include_router(auth_router, prefix="/api/v1")
app.include_router(user_router, prefix="/api/v1")"""

        app_content += '''


# 健康检查接口
@app.get("/health", tags=["Health"])
async def health_check():
    """健康检查接口"""
    return {"status": "healthy"}


# OpenAPI 文档
def custom_openapi():
    """自定义 OpenAPI 文档"""
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title=settings.app.APP_NAME,
        version=settings.app.APP_VERSION,
        description=settings.app.APP_DESCRIPTION,
        routes=app.routes,
    )

    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi


# 启动应用
if __name__ == "__main__":
    if os.getenv("ENV") == "development":
        logger.info("🚩 正在以开发模式启动应用...")
        uvicorn.run(
            app="app.main:app",
            host="127.0.0.1",
            port=8000,
            reload=True,
        )'''


        content = lifespan_content + app_content

        self.file_ops.create_python_file(
            file_path="app/main.py",
            docstring="FastAPI 应用主入口",
            imports=imports,
            content=content,
            overwrite=True
        )
