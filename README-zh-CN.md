<div align="center">
  <img src="https://github.com/ning3739/forge/blob/main/assets/logo.svg?raw=true" alt="Forge Logo" width="480"/>
</div>

<br/>

<div align="center">

[![PyPI version](https://badge.fury.io/py/ningfastforge.svg)](https://badge.fury.io/py/ningfastforge)
[![Python Versions](https://img.shields.io/pypi/pyversions/ningfastforge.svg)](https://pypi.org/project/ningfastforge/)
[![Downloads](https://static.pepy.tech/badge/ningfastforge)](https://pepy.tech/project/ningfastforge)
[![Downloads per month](https://static.pepy.tech/badge/ningfastforge/month)](https://pepy.tech/project/ningfastforge)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

</div>

---

**Forge** 是一个强大的命令行工具，帮助你通过最佳实践、智能默认配置以及精美的交互式界面，快速构建**可直接用于生产环境的 FastAPI 项目**。

## ✨ 功能特性

- 🎨 **精美的交互式 UI** —— 带渐变色和流畅动画的终端界面
- 🚀 **智能预设** —— 为测试、开发工具、部署和监控精心设计的默认配置
- 🔐 **即开即用的认证系统** —— 内置 JWT 认证支持（基础版 & 完整版）
- 🗄️ **灵活的数据库支持** —— 支持 PostgreSQL、MySQL、SQLite，基于 SQLModel / SQLAlchemy
- 🔴 **Redis 集成** —— 内置 Redis，用于缓存、会话和消息队列
- 📋 **后台任务** —— 集成 Celery + Redis Broker 进行异步任务处理
- 💾 **数据库备份** —— 自动化数据库备份任务，支持所有数据库类型
- 📦 **模块化架构** —— 只生成你真正需要的功能
- 🧪 **内置测试体系** —— 预配置 pytest，支持异步测试和覆盖率统计
- 🐳 **Docker 就绪** —— 生产级 Docker / Docker Compose 配置
- 🔍 **类型安全** —— 生成代码全量类型注解
- ⚡ **Async 优先** —— 针对 FastAPI 异步能力进行深度优化

## 📋 环境要求

- Python 3.9+
- [uv](https://docs.astral.sh/uv/)（推荐）或 pip

## 🚀 快速开始

### 安装

[自行构建](install.md)

#### 从 PyPI 安装（推荐）

```bash
pip install ningfastforge
````

#### 升级到最新版本

如果你已经安装过 Forge，可以执行：

```bash
pip install --upgrade ningfastforge
```

> 💡 **提示**：始终使用最新版本以获得新功能、Bug 修复和安全更新。

#### 从源码安装

```bash
# 克隆仓库
git clone https://github.com/ning3739/forge.git
cd forge

# 使用 uv（推荐）
uv sync

# 或使用 pip
pip install -e .
```

### 验证安装

```bash
forge --version
```

### 创建你的第一个项目

```bash
# 交互式模式（推荐）
forge init

# 指定项目名
forge init forge-project

# 非交互模式（使用默认配置）
forge init forge-project --no-interactive
```

### 运行项目

```bash
cd forge-project
uv sync
uv run uvicorn app.main:app --reload

# 访问：
http://127.0.0.1:8000/docs   # Swagger 文档
http://127.0.0.1:8000/redoc  # ReDoc 文档
```

## 🏗️ 架构设计

Forge 采用 **“配置优先（Configuration-First）”** 的设计理念，并结合 **动态生成器系统**：

1. `forge init` 通过交互式命令收集用户选择
2. 首先生成配置文件 `.forge/config.json`
3. 动态生成器系统根据配置自动发现并执行对应生成器

### 动态生成器系统

Forge 使用基于装饰器的生成器自动注册与调度机制：

```python
@Generator(
    category="model",
    priority=40,
    requires=["DatabaseConnectionGenerator"],
    enabled_when=lambda c: c.has_auth()
)
class UserModelGenerator:
    def generate(self):
        # 生成用户模型代码
```

**优势：**

* ✅ 自动发现生成器（无需手动注册）
* ✅ 依赖解析（按正确顺序执行）
* ✅ 条件执行（仅启用必要生成器）
* ✅ 易扩展（新增功能只需新增文件）

这种设计确保了：

* ✅ 配置可追溯、可复现
* ✅ 职责清晰、解耦良好
* ✅ 项目可重复生成和升级
* ✅ 支持配置共享与模板化
* ✅ 模块化、易维护的代码结构

## 🎯 配置选项

### 数据库

* **PostgreSQL（推荐）** —— 功能强大，适合生产环境
* **MySQL** —— 流行、广泛支持
* **SQLite** —— 轻量级，适合开发和小型项目

### ORM 支持

* **SQLModel（推荐）** —— 基于 SQLAlchemy + Pydantic，现代、类型安全
* **SQLAlchemy** —— 成熟稳定、功能强大

### 认证与安全

#### 认证模式

* **完整 JWT 认证（推荐）**

  * 登录 / 注册
  * 邮箱验证
  * 找回密码
  * SMTP 邮件服务
  * Refresh Token
* **基础 JWT 认证**

  * 仅登录 / 注册
  * 可选 Refresh Token

#### 安全特性

* CORS（可配置）
* 接口限流（装饰器，自动集成）
* 参数校验（Pydantic）
* 密码加密（bcrypt）
* SQL 注入防护（ORM）
* XSS 防护（FastAPI 内置）

### 核心功能（默认包含）

* **日志系统** —— Loguru 结构化日志
* **API 文档** —— Swagger UI + ReDoc
* **健康检查接口**
* **接口限流支持**

### 后台任务与缓存

* **Redis** —— 缓存 / 会话 / 消息队列
* **Celery** —— 分布式任务队列
* **数据库备份** —— 支持 MySQL / PostgreSQL / SQLite
* **定时任务** —— Celery Beat（生产环境）

### 开发工具

* **标准（推荐）** —— Black + Ruff
* **无** —— 不生成开发工具

### 测试支持

启用测试后，Forge 会生成：

* pytest（支持 async）
* httpx
* pytest-cov
* pytest-asyncio

#### 运行测试

```bash
pytest
pytest --cov=app tests/
pytest tests/test_main.py
pytest -v
```

## 📁 生成的项目结构

```
forge-project/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI 应用入口点
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config/          # 配置管理
│   │   │   ├── __init__.py
│   │   │   ├── base.py      # 基础配置
│   │   │   ├── settings.py  # 设置聚合器
│   │   │   └── modules/     # 配置模块 (app, database, jwt, cors, email, logger, redis, celery)
│   │   │       ├── __init__.py
│   │   │       ├── app.py
│   │   │       ├── celery.py
│   │   │       ├── cors.py
│   │   │       ├── database.py
│   │   │       ├── email.py
│   │   │       ├── jwt.py
│   │   │       ├── logger.py
│   │   │       └── redis.py
│   │   ├── database/        # 数据库连接
│   │   │   ├── __init__.py
│   │   │   ├── connection.py
│   │   │   ├── dependencies.py
│   │   │   └── mysql.py     # 数据库特定连接 (mysql/postgresql/sqlite)
│   │   ├── redis.py         # Redis 连接管理器 (如果启用 Redis)
│   │   ├── celery.py        # Celery 配置 (如果启用 Celery)
│   │   ├── deps.py          # 全局依赖项
│   │   ├── logger.py        # 日志配置
│   │   └── security.py      # 安全工具 (密码哈希, JWT)
│   ├── decorators/          # 自定义装饰器
│   │   ├── __init__.py
│   │   └── rate_limit.py    # 速率限制装饰器
│   ├── models/              # 数据库模型
│   │   ├── __init__.py
│   │   ├── user.py
│   │   └── token.py         # (如果启用刷新令牌)
│   ├── schemas/             # Pydantic 模式
│   │   ├── __init__.py
│   │   ├── user.py
│   │   └── token.py
│   ├── crud/                # CRUD 操作
│   │   ├── __init__.py
│   │   ├── user.py
│   │   └── token.py         # (如果启用刷新令牌)
│   ├── services/            # 业务逻辑
│   │   ├── __init__.py
│   │   └── auth.py
│   ├── tasks/               # Celery 任务 (如果启用 Celery)
│   │   ├── __init__.py      # 任务导出
│   │   └── backup_database_task.py  # 数据库备份任务
│   ├── routers/             # API 路由
│   │   ├── __init__.py
│   │   └── v1/              # API 版本 1
│   │       ├── __init__.py  # 路由聚合器
│   │       ├── auth.py
│   │       └── users.py
│   └── utils/               # 工具函数
│       ├── __init__.py
│       └── email.py         # (如果启用完整认证)
├── tests/                   # 测试文件 (如果启用)
│   ├── __init__.py
│   ├── conftest.py          # Pytest 配置和固件
│   ├── test_main.py         # 主 API 端点测试
│   ├── api/
│   │   ├── __init__.py
│   │   ├── test_auth.py     # 认证测试
│   │   └── test_users.py    # 用户端点测试
│   └── unit/                # 单元测试目录
│       └── __init__.py
├── alembic/                 # 数据库迁移 (如果启用)
│   ├── versions/            # 迁移版本
│   │   └── .gitkeep
│   ├── env.py               # Alembic 环境
│   ├── script.py.mako       # 迁移模板
│   └── README.md
├── static/                  # 静态文件
│   └── email_template/      # 邮件模板 (如果启用完整认证)
│       ├── base.html
│       ├── verification.html
│       ├── password_reset.html
│       └── welcome.html
├── script/                  # 自定义脚本目录
├── secret/                  # 环境文件
│   ├── .env.example         # 环境变量模板
│   ├── .env.development     # 开发环境
│   └── .env.production      # 生产环境
├── .forge/                  # Forge 配置
│   └── config.json          # 项目配置
├── docker-compose.yml       # Docker Compose 配置 (如果启用)
├── Dockerfile               # Docker 配置 (如果启用)
├── .dockerignore            # Docker 忽略文件 (如果启用)
├── .gitignore               # Git 忽略文件
├── alembic.ini              # Alembic 配置 (如果启用迁移)
├── pyproject.toml           # 项目依赖
├── uv.lock                  # UV 锁文件
├── LICENSE                  # MIT 许可证
└── README.md                # 项目文档
```



## 🎨 智能默认配置

* PostgreSQL + SQLModel
* Alembic 迁移
* 完整 JWT 认证
* Redis + Celery
* CORS 启用
* Black + Ruff
* pytest + 覆盖率
* Docker + Docker Compose

## 🛠️ 常用命令

### `forge init`

初始化 FastAPI 项目：

```bash
forge init
forge init forge-project
forge init forge-project --no-interactive
```

### `forge --version`

查看版本号：

```bash
forge --version
forge -v
```

## 🎯 最佳实践建议

### API 项目（推荐）

```
PostgreSQL + SQLModel
完整 JWT 认证
Redis + Celery
启用 CORS
Black + Ruff
pytest + 覆盖率
Docker 部署
```

### 简单项目

```
SQLite + SQLModel
基础 JWT 或无认证
启用 CORS
Docker 部署
```

## 🤝 参与贡献

欢迎提交 Pull Request！

### 开发环境搭建

```bash
git clone https://github.com/ning3739/forge.git
cd forge
uv sync
./scripts/test_build.sh
```

## 📝 许可证

MIT License

## 🎉 更新日志

请查看 [CHANGELOG.md](CHANGELOG.md)

## 🙏 致谢

本项目基于以下优秀开源项目构建：

* FastAPI
* Typer
* Rich
* Questionary

## 📧 支持

如有问题或建议，请在 GitHub 提交 Issue。

---

❤️ 为 FastAPI 社区而生

