"""README.md 生成器"""
from core.decorators import Generator
from ..templates.base import BaseTemplateGenerator


@Generator(
    category="config",
    priority=2,
    description="生成项目文档的 README.md"
)
class ReadmeGenerator(BaseTemplateGenerator):
    """README.md 文件生成器"""

    def generate(self) -> None:
        """生成 README.md 文件"""
        project_name = self.config_reader.get_project_name()

        content = self._build_header(project_name)
        content += self._build_features_section()
        content += self._build_installation_section()
        content += self._build_structure_section()
        content += self._build_configuration_section()
        content += self._build_api_docs_section()
        content += self._build_development_section()
        content += self._build_license_section()

        self.file_ops.create_markdown_file(
            file_path="README.md",
            title=None,
            content=content,
            overwrite=True
        )

    def _build_header(self, project_name: str) -> str:
        """构建标题"""
        return f'''# {project_name}

由 [Forge](https://github.com/ning3739/forge) 生成的 FastAPI 项目。

'''

    def _build_features_section(self) -> str:
        """构建功能列表部分"""
        features = []

        # 数据库(现在是必需的)
        db_type = self.config_reader.get_database_type()
        orm_type = self.config_reader.get_orm_type()
        features.append(f"- 🗄️ **数据库**: {db_type} 搭配 {orm_type}")

        # 迁移支持
        if self.config_reader.has_migration():
            features.append("- 📦 **数据库迁移**: Alembic 支持")

        if self.config_reader.has_auth():
            auth_type = self.config_reader.get_auth_type()
            features.append(f"- 🔐 **身份认证**: {auth_type}")
            if self.config_reader.has_refresh_token():
                features.append("- 🔄 **刷新令牌**: 安全的令牌刷新")

        # Redis 和 Celery
        if self.config_reader.has_redis():
            features.append("- 🔴 **Redis**: 缓存和会话管理")

        if self.config_reader.has_celery():
            features.append("- 📋 **后台任务**: 使用 Redis 代理的 Celery")
            features.append("- 💾 **数据库备份**: 自动备份任务(MySQL、PostgreSQL、SQLite)")

        if self.config_reader.has_cors():
            features.append("- 🌐 **CORS**: 已启用跨域资源共享")

        # 安全功能(始终包含)
        security_features = ["输入验证", "密码哈希", "速率限制"]
        features.append(f"- 🔒 **安全**: {', '.join(security_features)}")

        if self.config_reader.has_testing():
            features.append("- 🧪 **测试**: 支持异步和覆盖率的 pytest")

        if self.config_reader.has_docker():
            features.append("- 🐳 **Docker**: 生产就绪的容器化")

        if self.config_reader.has_dev_tools():
            features.append("- 🛠️ **开发工具**: Black、Ruff 代码质量工具")

        # 始终包含的功能
        features.append("- 📚 **API 文档**: Swagger UI 和 ReDoc")
        features.append("- 📊 **日志记录**: 使用 Loguru 的结构化日志")
        features.append("- 🏥 **健康检查**: 内置健康检查端点")

        return '## ✨ 功能特性\n\n' + '\n'.join(features) + '\n\n'

    def _build_installation_section(self) -> str:
        """构建安装说明部分"""
        return '''## 🚀 快速开始

### 前置要求

- Python 3.9+
- [uv](https://docs.astral.sh/uv/) (推荐)

### 安装

#### 使用 uv (推荐)

```bash
# 安装依赖
uv sync

# 运行应用程序
uv run uvicorn app.main:app --reload
````

### 访问你的 API

运行后,访问:

* **API 文档 (Swagger)**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
* **API 文档 (ReDoc)**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)
* **健康检查**: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)

'''


    def _build_structure_section(self) -> str:
        """构建项目结构部分"""
        content = '''## 项目结构


```
.
├── app/
│   ├── __init__.py
│   ├── main.py             # 应用程序入口点
│   ├── core/               # 核心配置
│   │   ├── config/         # 配置模块
│   │   │   ├── base.py
│   │   │   ├── settings.py
│   │   │   └── modules/    # 配置模块 (app、database、jwt、redis、celery 等)
│   │   ├── database/       # 数据库连接'''

        # 如果启用则添加 Redis 和 Celery 文件
        if self.config_reader.has_redis():
            content += '''
│   │   ├── redis.py        # Redis 连接管理器'''

        if self.config_reader.has_celery():
            content += '''
│   │   ├── celery.py       # Celery 配置'''

        content += '''
│   │   ├── deps.py         # 依赖项
│   │   ├── logger.py       # 日志配置
│   │   └── security.py     # 安全工具
│   ├── decorators/         # 自定义装饰器
│   │   └── rate_limit.py   # 速率限制装饰器
│   ├── models/             # 数据库模型
│   ├── schemas/            # Pydantic 模式
│   ├── crud/               # CRUD 操作
'''

        if self.config_reader.has_auth():
            content += '''│   ├── services/           # 业务逻辑
'''

        content += '''│   ├── routers/            # API 路由
│   │   └── v1/             # API 版本 1'''

        # 如果启用 Celery 则添加 tasks 目录
        if self.config_reader.has_celery():
            content += '''
│   ├── tasks/              # Celery 任务
│   │   ├── __init__.py     # 任务导出
│   │   └── backup_database_task.py   # 数据库备份任务'''

        content += '''
│   └── utils/              # 工具函数
'''

        if self.config_reader.has_migration():
            content += '''├── alembic/                # 数据库迁移
│   ├── versions/           # 迁移版本
│   └── env.py              # Alembic 配置
'''

        content += '''├── static/                 # 静态文件 (图片、CSS、JS 等)
'''

        if self.config_reader.has_testing():
            content += '''├── tests/                  # 测试文件
│   ├── conftest.py         # Pytest 配置
│   ├── test_main.py        # 主 API 测试
│   └── api/                # API 端点测试
'''

        if self.config_reader.has_docker():
            content += '''├── Dockerfile              # Docker 配置
├── docker-compose.yml      # Docker Compose 配置
├── .dockerignore           # Docker 忽略文件
'''

        content += '''├── script/                 # 自定义脚本 (shell 脚本等)
├── secret/                 # 环境文件
│   ├── .env.example        # 环境变量模板
│   ├── .env.development    # 开发环境
│   └── .env.production     # 生产环境
├── static/                 # 静态文件 (图片、CSS、JS 等)
├── pyproject.toml          # 项目依赖
├── .gitignore              # Git 忽略文件
└── README.md               # 本文件
```

'''
        return content

    def _build_configuration_section(self) -> str:
        """构建配置说明部分"""
        content = '''## 配置

将 `.env.example` 复制到 `.env` 并更新值:

```bash
cp .env.example .env
```

'''
        # 数据库配置(现在是必需的)
        content += self._build_database_config()

        return content

    def _build_database_config(self) -> str:
        """构建数据库配置说明"""
        content = '''### 数据库配置

在 `.env.development` 和 `.env.production` 中更新数据库连接字符串:

```
DATABASE_URL=postgresql://user:password@localhost:5432/dbname
```

'''


        if self.config_reader.has_migration():
            content += '''### 数据库迁移


```bash
# 创建新迁移
uv run alembic revision --autogenerate -m "描述"

# 应用迁移
uv run alembic upgrade head
```

'''

        return content

    def _build_api_docs_section(self) -> str:
        """构建 API 文档部分"""
        return '''## 📚 API 文档

应用程序运行后,访问:

* **Swagger UI**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
* **ReDoc**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)
* **健康检查**: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)

## 🔒 安全功能

### 速率限制

项目包含内置的速率限制装饰器来保护你的 API 端点:

```python
from app.decorators.rate_limit import rate_limit, rate_limit_strict

# 自定义速率限制
@router.get("/api/data")
@rate_limit(max_requests=100, window_seconds=60)
async def get_data(request: Request):
    return {"data": "value"}

# 预定义的严格限制(每分钟 10 个请求)
@router.post("/api/action")
@rate_limit_strict
async def perform_action(request: Request):
    return {"status": "success"}
```

**可用装饰器:**

* `@rate_limit_strict` - 每分钟 10 个请求
* `@rate_limit_moderate` - 每分钟 100 个请求
* `@rate_limit_relaxed` - 每小时 1000 个请求

**自定义标识符(例如基于用户):**

```python
@rate_limit(
    max_requests=50,
    window_seconds=3600,
    identifier_func=lambda req: req.state.user.id
)
async def user_endpoint(request: Request):
    return {"data": "user-specific"}
```

**注意:** 默认实现使用内存存储。对于具有多个实例的生产环境,请考虑使用基于 Redis 的速率限制。

'''

    def _build_development_section(self) -> str:
        """构建开发部分"""
        content = '## 🛠️ 开发\n\n'

        # 如果启用则添加 Celery 部分
        if self.config_reader.has_celery():
            content += self._build_celery_section()

        if self.config_reader.has_dev_tools():
            content += self._build_dev_tools_section()

        if self.config_reader.has_testing():
            content += self._build_testing_section()

        if self.config_reader.has_docker():
            content += self._build_docker_section()

        return content

    def _build_dev_tools_section(self) -> str:
        """构建开发工具部分"""
        return '''### 代码格式化

```bash
# 使用 Black 格式化代码
black .

# 使用 Ruff 进行代码检查
ruff check .

# 使用 MyPy 进行类型检查
mypy .
```

'''

    def _build_testing_section(self) -> str:
        """构建测试说明"""
        return '''### 运行测试

```bash
# 安装测试依赖
uv sync --extra dev

# 或安装特定的测试包
uv add --dev pytest pytest-asyncio httpx aiosqlite

# 运行所有测试
uv run pytest

# 运行并显示覆盖率
uv run pytest --cov=app tests/

# 运行特定测试文件
uv run pytest tests/api/test_auth.py -v
```

'''


    def _build_docker_section(self) -> str:
        """构建 Docker 说明"""
        project_name = self.config_reader.get_project_name()

        # 检查项目是否有多个服务(Redis、Celery 等)
        has_multiple_services = (
            self.config_reader.has_redis() or
            self.config_reader.has_celery() or
            self.config_reader.get_database_type() in ["MySQL", "PostgreSQL"]
        )

        if has_multiple_services:
            # 对于多服务设置使用 Docker Compose
            content = f'''### Docker

此项目包含完整的 Docker Compose 设置,包含所有必需的服务。

#### 生产部署

```bash
# 构建并启动所有服务
docker-compose up --build

# 在后台运行
docker-compose up -d --build

# 查看日志
docker-compose logs -f

# 停止所有服务
docker-compose down
```

#### 包含的服务

* **FastAPI 应用程序**: 主 API 服务器(端口 8000)
* **数据库**: {self.config_reader.get_database_type()} 数据库,带健康检查
* **数据库迁移**: 启动时自动进行模式迁移'''

            if self.config_reader.has_redis():
                content += '''

* **Redis**: 缓存和会话存储(端口 6379)'''

            if self.config_reader.has_celery():
                content += '''

* **Celery Worker**: 后台任务处理
* **Celery Beat**: 定时任务管理'''

            content += '''


#### 环境配置

Docker 设置使用来自 `./secret/.env.production` 的生产环境变量。
在部署前确保更新数据库凭据和其他敏感设置。

#### 开发 vs 生产

* **开发**: 使用 `uv run uvicorn app.main:app --reload` 进行本地开发
* **生产**: 使用 `docker-compose up` 进行完整的容器化部署

'''
            return content
        else:
            # 对于单服务设置使用简单的 Docker 命令
            return f'''### Docker

```bash
# 构建镜像
docker build -t {project_name} .

# 运行容器
docker run -p 8000:8000 {project_name}
```

'''

    def _build_license_section(self) -> str:
        """构建许可证部分"""
        return '''## 📝 许可证

此项目由 [Forge](https://github.com/ning3739/forge) 创建,采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件。

## 🙏 致谢

由 [Forge](https://github.com/ning3739/forge) 用 ❤️ 生成 - 一个强大的 FastAPI 项目脚手架工具。

构建工具:

* [FastAPI](https://fastapi.tiangolo.com/) - 现代、快速的 Web 框架
* [SQLModel](https://sqlmodel.tiangolo.com/) - 具有类型安全的 Python SQL 数据库
* [Pydantic](https://pydantic-docs.helpmanual.io/) - 使用 Python 类型提示进行数据验证
* [Alembic](https://alembic.sqlalchemy.org/) - 数据库迁移工具
* [pytest](https://pytest.org/) - 测试框架

---

**需要帮助?** 查看 [Forge 文档](https://github.com/ning3739/forge) 或提交 issue。
'''

    def _build_celery_section(self) -> str:
        """构建 Celery 部分"""
        return '''### 后台任务 (Celery)


此项目使用 Celery 进行后台任务处理,Redis 作为消息代理。

#### 启动 Celery 服务

**1. 启动主应用程序:**

```bash
uv run uvicorn app.main:app --reload
```

**2. 启动 Celery worker:**

```bash
uv run celery -A app.core.celery.celery_app worker --loglevel=info
```

**3. 启动 Flower 监控工具(可选):**

```bash
uv run celery -A app.core.celery.celery_app flower
# 在 http://localhost:5555 访问
```

#### 数据库备份任务

项目包含一个自动数据库备份任务,支持 MySQL、PostgreSQL 和 SQLite:

```python
from app.tasks.backup_database_task import backup_database_task

# 异步执行备份任务
result = backup_database_task.delay()

# 使用自定义参数
result = backup_database_task.delay(
    database_name="custom_db",
    retention_days=7,
    backup_dir="./custom_backups"
)

# 获取任务状态
print(f"任务 ID: {result.id}")
print(f"任务状态: {result.status}")

# 等待结果
task_result = result.get()
print(f"备份结果: {task_result}")
```

#### 定时任务(仅生产环境)

对于生产环境,你可以通过启动 Celery Beat 来启用自动调度:

```bash
# 仅生产环境 - 启动 Celery Beat 调度器
uv run celery -A app.core.celery.celery_app beat --loglevel=info
```

当 Beat 运行时,以下任务会自动调度:

* **数据库备份**: 每天凌晨 3:00 运行,保留备份 30 天
* 备份本地存储在 `./backups/database/` 目录中
* 支持 MySQL (mysqldump)、PostgreSQL (pg_dump) 和 SQLite (sqlite3)
* 自动压缩和清理旧备份

#### 配置

Celery 配置通过环境变量管理:

* `CELERY_BROKER_URL`: Redis 代理 URL (默认: redis://localhost:6379/1)
* `CELERY_RESULT_BACKEND`: 结果后端 URL (默认: redis://localhost:6379/2)

**Redis 设置:**

```bash
# 安装并启动 Redis
brew install redis  # macOS
sudo apt-get install redis-server  # Ubuntu
# 或使用 Docker: docker run -d -p 6379:6379 redis:alpine
```

'''

