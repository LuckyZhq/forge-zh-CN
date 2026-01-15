"""环境变量文件生成器"""
from core.decorators import Generator
from ..templates.base import BaseTemplateGenerator


@Generator(
    category="config",
    priority=4,
    description="生成 .env.example 文件"
)
class EnvGenerator(BaseTemplateGenerator):
    """环境变量文件生成器"""

    def generate(self) -> None:
        """生成环境变量文件"""
        # 生成 .env.example
        self._generate_env_example()

        # 生成 .env.development
        self._generate_env_development()

        # 生成 .env.production
        self._generate_env_production()

    def _generate_env_example(self) -> None:
        """生成 .env.example 文件（示例配置）"""
        content = self._build_header("示例环境变量")
        content += self._build_app_section(example=True)
        content += self._build_database_section(example=True)  # 数据库现在是必需的

        if self.config_reader.has_auth():
            content += self._build_auth_section(example=True)

        # 完整 JWT 认证需要邮件配置
        if self.config_reader.get_auth_type() == "complete":
            content += self._build_email_section(example=True)

        if self.config_reader.has_cors():
            content += self._build_cors_section(example=True)

        if self.config_reader.has_redis():
            content += self._build_redis_section(example=True)

        if self.config_reader.has_celery():
            content += self._build_celery_section(example=True)

        content += self._build_logging_section(example=True)

        self.file_ops.create_file(
            file_path="secret/.env.example",
            content=content,
            overwrite=True
        )

    def _generate_env_development(self) -> None:
        """生成 .env.development 文件（开发环境配置）"""
        content = self._build_header("开发环境变量")
        content += self._build_app_section(env="development")
        content += self._build_database_section(env="development")  # 数据库现在是必需的

        if self.config_reader.has_auth():
            content += self._build_auth_section(env="development")

        # 完整 JWT 认证需要邮件配置
        if self.config_reader.get_auth_type() == "complete":
            content += self._build_email_section(env="development")

        if self.config_reader.has_cors():
            content += self._build_cors_section(env="development")

        if self.config_reader.has_redis():
            content += self._build_redis_section(env="development")

        if self.config_reader.has_celery():
            content += self._build_celery_section(env="development")

        content += self._build_logging_section(env="development")

        self.file_ops.create_file(
            file_path="secret/.env.development",
            content=content,
            overwrite=True
        )

    def _generate_env_production(self) -> None:
        """生成 .env.production 文件（生产环境配置）"""
        content = self._build_header("生产环境变量")
        content += "# ⚠ 警告：此文件包含生产环境密钥信息\n"
        content += "# 请勿将该文件提交到版本控制系统\n"
        content += "# 部署前请务必更新所有密码和密钥\n\n"
        content += self._build_app_section(env="production")

        content += self._build_database_section(env="production")  # 数据库现在是必需的

        if self.config_reader.has_auth():
            content += self._build_auth_section(env="production")

        # 完整 JWT 认证需要邮件配置
        if self.config_reader.get_auth_type() == "complete":
            content += self._build_email_section(env="production")

        if self.config_reader.has_cors():
            content += self._build_cors_section(env="production")

        if self.config_reader.has_redis():
            content += self._build_redis_section(env="production")

        if self.config_reader.has_celery():
            content += self._build_celery_section(env="production")

        content += self._build_logging_section(env="production")

        self.file_ops.create_file(
            file_path="secret/.env.production", content=content, overwrite=True
        )

    def _build_header(self, title: str) -> str:
        """构建文件头部"""
        return f"""# ============================================
# {title}
# ============================================
# 由 Forge 自动生成
# 请勿将该文件提交到版本控制系统
# ============================================

"""

    def _build_app_section(
        self, example: bool = False, env: str = "development"
    ) -> str:
        """构建应用配置部分"""
        project_name = self.config_reader.get_project_name()

        return f'''# ============================================
# 应用配置
# ============================================
APP_NAME="{project_name}"
APP_VERSION="1.0.0"
APP_DESCRIPTION="{project_name} API"

'''

    def _build_server_section(
        self, example: bool = False, env: str = "development"
    ) -> str:
        """构建服务配置部分（已移除，服务配置通过命令行参数传入）"""
        return ""

    def _build_database_section(
        self, example: bool = False, env: str = "development"
    ) -> str:
        """构建数据库配置部分"""
        db_type = self.config_reader.get_database_type()
        project_name = self.config_reader.get_project_name()

        if example:
            if db_type == "PostgreSQL":
                return """# ============================================
# 数据库配置（PostgreSQL）
# ============================================
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/dbname

# 连接池配置
ECHO=false
POOL_PRE_PING=true
POOL_TIMEOUT=30
POOL_SIZE=6
POOL_MAX_OVERFLOW=2

"""
            elif db_type == "MySQL":
                return """# ============================================
# 数据库配置（MySQL）
# ============================================
DATABASE_URL=mysql+aiomysql://user:password@localhost:3306/dbname

# 连接池配置
ECHO=false
POOL_PRE_PING=true
POOL_TIMEOUT=30
POOL_SIZE=6
POOL_MAX_OVERFLOW=2

"""
            elif db_type == "SQLite":
                return """# ============================================
# 数据库配置（SQLite）
# ============================================
DATABASE_URL=sqlite+aiosqlite:///./database.db

# 连接池配置
ECHO=false
POOL_PRE_PING=false
POOL_TIMEOUT=30

"""

        # 开发 / 生产环境专用配置
        db_name = project_name  # 使用项目名作为数据库名，与 Docker 配置保持一致
        echo = "true" if env == "development" else "false"

        if db_type == "PostgreSQL":
            if env == "production":
                # 生产环境使用 Docker 服务名
                return f"""# ============================================
# 数据库配置（PostgreSQL）
# ============================================
DATABASE_URL=postgresql+asyncpg://postgres:postgres@db:5432/{db_name}

# 连接池配置
ECHO={echo}
POOL_PRE_PING=true
POOL_TIMEOUT=30
POOL_SIZE=6
POOL_MAX_OVERFLOW=2

"""
            else:
                # 开发环境使用 localhost
                return f"""# ============================================
# 数据库配置（PostgreSQL）
# ============================================
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/{db_name}

# 连接池配置
ECHO={echo}
POOL_PRE_PING=true
POOL_TIMEOUT=30
POOL_SIZE=6
POOL_MAX_OVERFLOW=2

"""
        elif db_type == "MySQL":
            if env == "production":
                # 生产环境使用 Docker 服务名
                return f"""# ============================================
# 数据库配置（MySQL）
# ============================================
DATABASE_URL=mysql+aiomysql://root:mysql@db:3306/{db_name}

# 连接池配置
ECHO={echo}
POOL_PRE_PING=true
POOL_TIMEOUT=30
POOL_SIZE=6
POOL_MAX_OVERFLOW=2

"""
            else:
                # 开发环境使用 localhost
                return f"""# ============================================
# 数据库配置（MySQL）
# ============================================
DATABASE_URL=mysql+aiomysql://root:mysql@localhost:3306/{db_name}

# 连接池配置
ECHO={echo}
POOL_PRE_PING=true
POOL_TIMEOUT=30
POOL_SIZE=6
POOL_MAX_OVERFLOW=2

"""
        elif db_type == "SQLite":
            db_file = (
                f"{project_name}_{env}.db"
                if env != "development"
                else f"{project_name}.db"
            )
            return f"""# ============================================
# 数据库配置（SQLite）
# ============================================
DATABASE_URL=sqlite+aiosqlite:///./{db_file}

# 连接池配置
ECHO={echo}
POOL_PRE_PING=false
POOL_TIMEOUT=30

"""

        return ""

    def _build_auth_section(
        self, example: bool = False, env: str = "development"
    ) -> str:
        """构建认证配置部分"""
        if example:
            content = """# ============================================
# 认证配置
# ============================================
JWT_SECRET_KEY=your-secret-key-here-change-in-production-min-32-chars
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRATION=1800
"""

            if self.config_reader.has_refresh_token():
                content += """JWT_REFRESH_TOKEN_EXPIRATION=86400
"""

            content += """JWT_ISSUER=demo
JWT_AUDIENCE=demo_users

"""
            return content

        # 为开发环境生成随机密钥
        import secrets

        secret_key = secrets.token_urlsafe(32)
        project_name = self.config_reader.get_project_name()

        content = f"""# ============================================
# 认证配置
# ============================================
JWT_SECRET_KEY={secret_key}
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRATION=1800
"""

        if self.config_reader.has_refresh_token():
            content += """JWT_REFRESH_TOKEN_EXPIRATION=86400
"""

        content += f"""JWT_ISSUER={project_name}
JWT_AUDIENCE={project_name}_users

"""
        return content

    def _build_cors_section(
        self, example: bool = False, env: str = "development"
    ) -> str:
        """构建 CORS 配置部分"""
        if example:
            return """# ============================================
# CORS 配置
# ============================================
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8080
CORS_ALLOW_CREDENTIALS=true
CORS_ALLOW_METHODS=GET,POST,PUT,DELETE,PATCH,OPTIONS
CORS_ALLOW_HEADERS=*
CORS_EXPOSE_HEADERS=

"""

        if env == "development":
            return """# ============================================
# CORS 配置
# ============================================
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8080,http://127.0.0.1:3000
CORS_ALLOW_CREDENTIALS=true
CORS_ALLOW_METHODS=GET,POST,PUT,DELETE,PATCH,OPTIONS
CORS_ALLOW_HEADERS=*
CORS_EXPOSE_HEADERS=

"""
        else:
            return """# ============================================
# CORS 配置
# ============================================
CORS_ALLOWED_ORIGINS=https://yourdomain.com
CORS_ALLOW_CREDENTIALS=true
CORS_ALLOW_METHODS=GET,POST,PUT,DELETE,PATCH,OPTIONS
CORS_ALLOW_HEADERS=*
CORS_EXPOSE_HEADERS=

"""

    def _build_email_section(
        self, example: bool = False, env: str = "development"
    ) -> str:
        """构建邮件配置部分"""
        project_name = self.config_reader.get_project_name()

        if example:
            return f'''# ============================================
# 邮件配置（SMTP）
# ============================================
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
EMAIL_USE_TLS=true
EMAIL_USE_SSL=false
EMAIL_SSL_CERT_REQS=required
EMAIL_TIMEOUT=30
EMAIL_EXPIRATION=3600

# 发件人配置
EMAIL_FROM_NAME="{project_name}"
EMAIL_FROM_EMAIL=noreply@yourdomain.com

'''

        return f'''# ============================================
# 邮件配置（SMTP）
# ============================================
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
EMAIL_USE_TLS=true
EMAIL_USE_SSL=false
EMAIL_SSL_CERT_REQS=required
EMAIL_TIMEOUT=30
EMAIL_EXPIRATION=3600

# 发件人配置
EMAIL_FROM_NAME="{project_name}"
EMAIL_FROM_EMAIL=noreply@yourdomain.com

'''

    def _build_logging_section(
        self, example: bool = False, env: str = "development"
    ) -> str:
        """构建日志配置部分"""
        if example:
            return """# ============================================
# 日志配置
# ============================================
LOG_LEVEL=INFO
LOG_TO_FILE=true
LOG_FILE_PATH=logs/app.log
LOG_TO_CONSOLE=true
LOG_CONSOLE_LEVEL=INFO
LOG_ROTATION=1 day
LOG_RETENTION_PERIOD=7 days

"""

        log_level = "DEBUG" if env == "development" else "INFO"
        log_file_path = f"logs/app_{env}.log"

        return f"""# ============================================
# 日志配置
# ============================================
LOG_LEVEL={log_level}
LOG_TO_FILE=true
LOG_FILE_PATH={log_file_path}
LOG_TO_CONSOLE=true
LOG_CONSOLE_LEVEL={log_level}
LOG_ROTATION=1 day
LOG_RETENTION_PERIOD=7 days

"""

    def _build_redis_section(
        self, example: bool = False, env: str = "development"
    ) -> str:
        """构建 Redis 配置部分"""
        if example:
            return """# ============================================
# Redis 配置
# ============================================
REDIS_CONNECTION_URL=redis://localhost:6379
REDIS_POOL_SIZE=5
REDIS_SOCKET_TIMEOUT=10
REDIS_DEFAULT_TTL=3600

"""

        # 不同环境的 Redis 配置
        if env == "development":
            redis_url = "redis://localhost:6379"
            pool_size = "3"
        else:  # production
            redis_url = "redis://redis:6379"  # 生产环境使用 Docker 服务名
            pool_size = "5"

        return f"""# ============================================
# Redis 配置
# ============================================
REDIS_CONNECTION_URL={redis_url}
REDIS_POOL_SIZE={pool_size}
REDIS_SOCKET_TIMEOUT=10
REDIS_DEFAULT_TTL=3600

"""

    def _build_celery_section(
        self, example: bool = False, env: str = "development"
    ) -> str:
        """构建 Celery 配置部分"""
        if example:
            return """# ============================================
# Celery 配置
# ============================================
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2
CELERY_TASK_SERIALIZER=json
CELERY_RESULT_SERIALIZER=json
CELERY_ACCEPT_CONTENT=["json"]
CELERY_TIMEZONE=UTC
CELERY_ENABLE_UTC=true
CELERY_TASK_ALWAYS_EAGER=false
CELERY_TASK_EAGER_PROPAGATES=true
CELERY_WORKER_CONCURRENCY=4
CELERY_WORKER_PREFETCH_MULTIPLIER=1
CELERY_RESULT_EXPIRES=3600

# 任务路由（JSON 格式）
CELERY_TASK_ROUTES={}

# 周期性任务调度（在代码中配置）
# CELERY_BEAT_SCHEDULE 在 app/core/celery.py 中配置

"""

        # 不同环境下的 Celery 配置
        if env == "development":
            broker_url = "redis://localhost:6379/1"
            result_backend = "redis://localhost:6379/2"
            task_always_eager = "false"
            worker_concurrency = "2"
        else:  # production
            broker_url = "redis://redis:6379/1"  # 生产环境使用 Docker 服务名
            result_backend = "redis://redis:6379/2"  # 生产环境使用 Docker 服务名
            task_always_eager = "false"
            worker_concurrency = "4"

        return f"""# ============================================
# Celery 配置
# ============================================
CELERY_BROKER_URL={broker_url}
CELERY_RESULT_BACKEND={result_backend}
CELERY_TASK_SERIALIZER=json
CELERY_RESULT_SERIALIZER=json
CELERY_ACCEPT_CONTENT=["json"]
CELERY_TIMEZONE=UTC
CELERY_ENABLE_UTC=true
CELERY_TASK_ALWAYS_EAGER={task_always_eager}
CELERY_TASK_EAGER_PROPAGATES=true
CELERY_WORKER_CONCURRENCY={worker_concurrency}
CELERY_WORKER_PREFETCH_MULTIPLIER=1
CELERY_RESULT_EXPIRES=3600

# 任务路由（JSON 格式）
CELERY_TASK_ROUTES={{}}

# 周期性任务调度（在代码中配置）
# CELERY_BEAT_SCHEDULE 在 app/core/celery.py 中配置

"""
