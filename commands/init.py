"""Init command module"""

import json
import time
import typer
import questionary
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any
from collections import OrderedDict
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.live import Live

from ui.logo import show_logo
from ui.components import (
    create_gradient_bar,
    create_highlighted_panel,
    create_questionary_style,
    console,
)
from ui.colors import get_colors
from core.utils.version_checker import check_for_updates
from core.version import __version__
from core.utils import ProjectConfig
from core.project_generator import ProjectGenerator

# ============================================================================
# 常量
# ============================================================================

DATABASE_CHOICES = ["PostgreSQL (推荐) ", "MySQL", "SQLite (开发环境 / 小型项目) "]

AUTH_CHOICES = ["完整 JWT 认证 (推荐) ", "基础 JWT 认证 (仅登录 / 注册) "]

DEFAULT_NON_INTERACTIVE_CONFIG = {
    "database": "MySQL",
    "orm": "SQLModel",
    "migration_tool": "Alembic",
    "features": {
        "auth": {
            "type": "complete",
            "refresh_token": True,
            "features": ["邮箱验证", "密码重置", "邮件服务"],
        },
        "cors": True,
        "dev_tools": True,
        "testing": True,
        "docker": True,
        "redis": True,
        "celery": True,
    },
}


# ============================================================================
# 辅助函数
# ============================================================================


def extract_choice(choice: str, default: str = "") -> str:
    """从选项文本中提取实际值 (移除括号中的描述)"""
    return choice.split(" (")[0] if choice else default


def get_auth_config(auth_type: str) -> Dict[str, Any]:
    """根据认证类型生成对应配置"""
    if "完整" in auth_type or "Complete" in auth_type:
        return {
            "type": "complete",
            "refresh_token": True,
            "features": ["邮箱验证", "密码重置", "邮件服务"],
        }
    else:
        return {"type": "basic", "refresh_token": False, "features": []}


# ============================================================================
# 配置收集
# ============================================================================


def collect_project_name(
    name: Optional[str], style: questionary.Style
) -> tuple[str, bool]:
    """收集项目名称

    如果用户输入 '.'，则使用当前目录名作为项目名。

    返回：
        (project_name, use_current_dir)
    """
    if name:
        if name == ".":
            return Path.cwd().name, True
        return name, False

    result = (
        questionary.text(
            "项目名称 (使用 '.' 表示当前目录) ：", default="forge-project", style=style
        ).ask()
        or "forge-project"
    )

    if result == ".":
        return Path.cwd().name, True
    return result, False


def collect_database_config(style: questionary.Style) -> tuple[str, str, Optional[str]]:
    """收集数据库相关配置

    返回：
        (database_type, orm_type, migration_tool)
    """
    database = extract_choice(
        questionary.select("数据库类型：", choices=DATABASE_CHOICES, style=style).ask(),
        "PostgreSQL",
    )

    orm = extract_choice("SQLModel")

    enable_migration = questionary.confirm(
        "是否启用数据库迁移 (Alembic) ？", default=True, auto_enter=True, style=style
    ).ask()

    migration_tool = "Alembic" if enable_migration else None
    return database, orm, migration_tool


def collect_features(style: questionary.Style) -> Dict[str, Any]:
    """收集功能模块配置"""
    auth_choice = questionary.select(
        "认证方式：", choices=AUTH_CHOICES, style=style
    ).ask()

    # Redis 配置
    enable_redis = questionary.confirm(
        "是否启用 Redis (缓存 / 会话 / 消息队列) ？",
        default=True,
        auto_enter=True,
        style=style,
    ).ask()

    # 仅在启用 Redis 时询问 Celery (Celery 依赖消息代理)
    enable_celery = False
    if enable_redis:
        enable_celery = questionary.confirm(
            "是否启用 Celery (后台任务 / 任务队列) ？",
            default=True,
            auto_enter=True,
            style=style,
        ).ask()

    # 在 Redis / Celery 选择完成后生成认证配置
    auth_config = get_auth_config(auth_choice)

    features = {
        "auth": auth_config,
        "cors": questionary.confirm(
            "是否启用 CORS？", default=True, auto_enter=True, style=style
        ).ask(),
        "dev_tools": questionary.confirm(
            "是否包含开发工具 (Black + Ruff) ？",
            default=True,
            auto_enter=True,
            style=style,
        ).ask(),
        "testing": questionary.confirm(
            "是否包含测试配置 (pytest) ？", default=True, auto_enter=True, style=style
        ).ask(),
        "docker": questionary.confirm(
            "是否包含 Docker 配置？", default=True, auto_enter=True, style=style
        ).ask(),
    }

    # 如果启用了 Redis / Celery，则加入功能列表
    if enable_redis:
        features["redis"] = True

    if enable_celery:
        features["celery"] = True

    return features


# ============================================================================
# 项目处理
# ============================================================================


def handle_existing_project(
    name: str, style: questionary.Style, use_current_dir: bool = False
) -> bool:
    """处理已存在的项目

    参数：
        name: 项目名称
        style: Questionary 样式
        use_current_dir: 是否使用当前目录作为项目根目录

    返回：
        True 表示继续，False 表示取消
    """
    colors = get_colors()
    console.print()
    console.print(
        f"[bold {colors.warning}]⚠️  项目 '{name}' 已存在！[/bold {colors.warning}]"
    )

    # 加载已有配置
    user_cwd = Path.cwd()
    if use_current_dir:
        project_path = user_cwd
    else:
        project_path = user_cwd / name

    existing_config = ProjectConfig.load(project_path)
    if existing_config:
        console.print(
            f"[{colors.text_muted}]发现已有配置，创建时间："
            f"{existing_config.get('metadata', {}).get('created_at', '未知时间')}[/{colors.text_muted}]"
        )

    console.print()

    # 询问用户如何处理
    action = questionary.select(
        "你想如何处理这个已存在的项目？",
        choices=["取消 —— 保留现有项目", "覆盖 —— 重新生成整个项目"],
        style=style,
    ).ask()

    if not action or "取消" in action or "Cancel" in action:
        console.print(f"\n[{colors.info}]操作已取消。[/ {colors.info}]")
        raise typer.Exit(code=0)

    elif "覆盖" in action or "Overwrite" in action:
        import shutil

        try:
            console.print(
                f"\n[{colors.warning}]正在删除已有项目文件...[/ {colors.warning}]"
            )

            if use_current_dir:
                # 使用当前目录时，仅删除 Forge 生成的内容
                forge_dir = project_path / ".forge"
                app_dir = project_path / "app"

                if forge_dir.exists():
                    shutil.rmtree(forge_dir)
                if app_dir.exists():
                    shutil.rmtree(app_dir)

                # 同时删除其他常见的生成文件 / 目录
                for item in [
                    "alembic",
                    "tests",
                    "static",
                    "secret",
                    "script",
                    "pyproject.toml",
                    "alembic.ini",
                    "README.md",
                    "Dockerfile",
                    "docker-compose.yml",
                    ".dockerignore",
                    ".gitignore",
                    "LICENSE",
                    "uv.lock",
                ]:
                    item_path = project_path / item
                    if item_path.exists():
                        if item_path.is_dir():
                            shutil.rmtree(item_path)
                        else:
                            item_path.unlink()
            else:
                # 子目录模式下，直接删除整个项目目录
                shutil.rmtree(project_path)

            console.print(
                f"[{colors.success}]✅ 已成功删除现有项目。[/ {colors.success}]"
            )
        except Exception as e:
            console.print(f"\n[bold red]删除现有项目时发生错误：[/bold red] {str(e)}")
            raise typer.Exit(code=1)

    return True  # 继续项目生成


def build_project_config(
    name: str,
    database: str,
    orm: str,
    migration_tool: Optional[str],
    features: Dict[str, Any],
) -> Dict[str, Any]:
    """构建项目配置字典"""
    return {
        "project_name": name,
        "database": {"type": database, "orm": orm, "migration_tool": migration_tool},
        "features": features,
    }


def save_config_file(project_path: Path, config: Dict[str, Any]) -> None:
    """将配置文件保存到 .forge/config.json"""
    # 创建 .forge 目录
    forge_dir = project_path / ".forge"
    forge_dir.mkdir(parents=True, exist_ok=True)

    # 按初始化交互顺序构建配置
    ordered_config = OrderedDict()
    ordered_config["project_name"] = config.get("project_name")

    if "database" in config:
        ordered_config["database"] = config["database"]

    ordered_config["features"] = config.get("features")

    # 添加元数据
    ordered_config["metadata"] = {
        "created_at": datetime.now().isoformat(),
        "forge_version": __version__,
    }

    # 保存配置文件
    config_file = forge_dir / "config.json"
    with open(config_file, "w", encoding="utf-8") as f:
        json.dump(ordered_config, f, indent=2, ensure_ascii=False)


def generate_project(project_path: Path, config: Dict[str, Any]) -> None:
    """生成项目结构和代码"""
    try:
        # 保存配置文件到 .forge/config.json
        save_config_file(project_path, config)

        # 调用 ProjectGenerator 生成项目结构
        generator = ProjectGenerator(project_path)
        generator.config_reader.load_config()
        generator.config_reader.validate_config()
        generator.generate()

    except Exception as e:
        console.print(f"\n[bold red]错误：[/bold red] {str(e)}")
        raise typer.Exit(code=1)


# ============================================================================
# 进度与展示
# ============================================================================


def show_saving_progress(name: str) -> None:
    """显示配置保存与项目生成的进度"""
    colors = get_colors()
    create_gradient_bar("rainbow")

    progress = Progress(
        SpinnerColumn(style=colors.primary_light, spinner_name="dots12"),
        TextColumn(
            f"[bold {colors.primary}]▸[/bold {colors.primary}] "
            f"[bold {colors.text_primary}]{{task.description}}"
        ),
        BarColumn(
            complete_style=colors.neon_green,
            finished_style=colors.neon_green,
            pulse_style=colors.primary_light,
            bar_width=None,
        ),
        console=console,
        transient=True,
    )

    steps = ["创建项目目录", "保存配置", "创建项目结构", "生成代码文件", "生成配置文件"]

    with Live(progress, refresh_per_second=10):
        for step in steps:
            task = progress.add_task(step, total=100)
            for _ in range(100):
                progress.update(task, advance=1)
                time.sleep(0.008)
            progress.remove_task(task)


def build_config_summary_lines(
    name: str,
    database: str,
    orm: str,
    migration_tool: Optional[str],
    features: Dict[str, Any],
) -> list[str]:
    """构建配置摘要展示内容"""
    colors = get_colors()
    lines = [
        f"[bold {colors.primary_light}]项目：[/bold {colors.primary_light}] "
        f"[bold {colors.text_primary}]{name}[/bold {colors.text_primary}]",
        f"[bold {colors.primary_light}]数据库：[/bold {colors.primary_light}] "
        f"[{colors.secondary}]{database} + {orm}[/{colors.secondary}]",
    ]

    if migration_tool:
        lines.append(
            f"[bold {colors.primary_light}]数据库迁移：[/bold {colors.primary_light}] "
            f"[{colors.secondary}]{migration_tool}[/{colors.secondary}]"
        )

    # 认证配置
    auth_config = features.get("auth", {})
    auth_type = (
        "完整 JWT 认证" if auth_config.get("type") == "complete" else "基础 JWT 认证"
    )
    refresh_token = " (包含 Refresh Token) " if auth_config.get("refresh_token") else ""
    lines.append(
        f"[bold {colors.primary}]认证方式：[/bold {colors.primary}] "
        f"[dim]{auth_type}{refresh_token}[/dim]"
    )

    if auth_config.get("type") == "complete":
        auth_features = auth_config.get("features", [])
        if auth_features:
            lines.append(
                f"[{colors.text_muted}]  • {', '.join(auth_features)}[/{colors.text_muted}]"
            )

    # Redis 与 Celery 配置
    redis_enabled = features.get("redis", False)
    celery_enabled = features.get("celery", False)

    if redis_enabled or celery_enabled:
        cache_queue_items = []
        if redis_enabled:
            cache_queue_items.append("Redis")
        if celery_enabled:
            cache_queue_items.append("Celery")

        lines.append(
            f"[bold {colors.warning}]缓存与队列：[/bold {colors.warning}] "
            f"[dim]{', '.join(cache_queue_items)}[/dim]"
        )

    # 安全配置
    security_items = ["参数校验", "密码加密"]
    if features.get("cors"):
        security_items.insert(0, "CORS")

    lines.append(
        f"[bold {colors.neon_green}]安全特性：[/bold {colors.neon_green}] "
        f"[dim]{', '.join(security_items)}[/dim]"
    )

    # 开发工具
    if features.get("dev_tools"):
        lines.append(
            f"[bold {colors.secondary}]开发工具：[/bold {colors.secondary}] "
            f"[dim]API 文档, Black, Ruff[/dim]"
        )

    # 测试
    if features.get("testing"):
        lines.append(
            f"[bold {colors.info}]测试：[/bold {colors.info}] "
            f"[dim]pytest, httpx, 覆盖率[/dim]"
        )

    # 部署
    if features.get("docker"):
        lines.append(
            f"[bold {colors.accent}]部署方式：[/bold {colors.accent}] "
            f"[dim]Docker, Docker Compose[/dim]"
        )

    return lines


def show_config_summary(
    name: str,
    database: str,
    orm: str,
    migration_tool: Optional[str],
    features: Dict[str, Any],
) -> None:
    """显示配置摘要"""
    colors = get_colors()
    console.print()

    lines = build_config_summary_lines(name, database, orm, migration_tool, features)
    panel = create_highlighted_panel(
        "\n".join(lines),
        title="配置摘要",
        accent_color=colors.neon_pink,
        icon=":package:",
    )
    console.print(panel)

    # 若启用完整 JWT 认证，则显示邮件配置提醒
    auth_config = features.get("auth", {})
    if auth_config.get("type") == "complete":
        show_email_config_warning()


def show_email_config_warning() -> None:
    """显示邮件服务配置提醒"""
    colors = get_colors()
    console.print()
    warning_content = (
        f"[bold {colors.warning}]⚠️  重要提示：请配置邮件服务[/bold {colors.warning}]\n\n"
        f"[{colors.text_muted}]在运行应用之前，请在 .env 文件中更新以下配置：[/{colors.text_muted}]\n\n"
        f"[{colors.secondary}]  SMTP_HOST=smtp.gmail.com[/{colors.secondary}]\n"
        f"[{colors.secondary}]  SMTP_PORT=587[/{colors.secondary}]\n"
        f"[{colors.secondary}]  SMTP_USER=your-email@gmail.com[/{colors.secondary}]\n"
        f"[{colors.secondary}]  SMTP_PASSWORD=your-app-password[/{colors.secondary}]\n"
        f"[{colors.secondary}]  EMAILS_FROM_EMAIL=noreply@yourdomain.com[/{colors.secondary}]\n\n"
        f"[{colors.text_muted}]Gmail 配置说明： https://support.google.com/accounts/answer/185833[/{colors.text_muted}]"
    )
    warning_panel = create_highlighted_panel(
        warning_content, title="邮件配置", accent_color=colors.warning, icon="⚠️"
    )
    console.print(warning_panel)


def show_next_steps(
    name: str, features: Dict[str, Any], use_current_dir: bool = False
) -> None:
    """显示后续操作步骤

    参数：
        name: 项目名称
        features: 项目功能配置
        use_current_dir: 是否在当前目录创建项目
    """
    colors = get_colors()
    console.print()

    # 确定项目路径与 cd 命令
    if use_current_dir:
        project_location = Path.cwd()
        cd_line = ""  # 无需切换目录
    else:
        project_location = Path.cwd() / name
        cd_line = f"[bold {colors.primary}]cd {name}[/bold {colors.primary}]\n"

    content = (
        f"[bold {colors.neon_green}]:white_check_mark:[/bold {colors.neon_green}]  "
        f"[bold {colors.text_primary}]项目创建成功！"
        f"[/bold {colors.text_primary}]\n\n"
        f"[{colors.text_muted}]项目位置：[/{colors.text_muted}]\n"
        f"[bold {colors.secondary}]{project_location}[/bold {colors.secondary}]\n\n"
        f"[{colors.text_muted}]接下来你可以执行以下步骤：[/{colors.text_muted}]\n"
        f"{cd_line}"
        f"[bold {colors.secondary}]uv sync[/bold {colors.secondary}]  "
        f"[{colors.text_muted}]# 安装依赖[/{colors.text_muted}]\n"
        f"[bold {colors.neon_green}]uv run uvicorn app.main:app --reload[/bold {colors.neon_green}]  "
        f"[{colors.text_muted}]# 启动服务[/{colors.text_muted}]"
    )

    # 如果启用了 Celery，显示后台任务说明
    celery_enabled = features.get("celery", False)
    if isinstance(celery_enabled, bool) and celery_enabled:
        content += (
            f"\n\n[{colors.text_muted}]后台任务 (Celery) ：[/{colors.text_muted}]\n"
            f"[bold {colors.warning}]uv run celery -A app.core.celery.celery_app worker --loglevel=info[/bold {colors.warning}]  "
            f"[{colors.text_muted}]# 启动 Celery Worker[/{colors.text_muted}]\n"
            f"[bold {colors.secondary}]uv run celery -A app.core.celery.celery_app flower[/bold {colors.secondary}]  "
            f"[{colors.text_muted}]# 启动监控面板 (可选) [/{colors.text_muted}]"
        )
    elif isinstance(celery_enabled, dict) and celery_enabled.get("enabled", False):
        # 兼容旧格式
        content += (
            f"\n\n[{colors.text_muted}]后台任务 (Celery) ：[/{colors.text_muted}]\n"
            f"[bold {colors.warning}]uv run celery -A app.core.celery.celery_app worker --loglevel=info[/bold {colors.warning}]  "
            f"[{colors.text_muted}]# 启动 Celery Worker[/{colors.text_muted}]\n"
            f"[bold {colors.secondary}]uv run celery -A app.core.celery.celery_app flower[/bold {colors.secondary}]  "
            f"[{colors.text_muted}]# 启动监控面板 (可选) [/{colors.text_muted}]"
        )

    panel = create_highlighted_panel(
        content, title="🚀  下一步操作", accent_color=colors.neon_pink, icon=":rocket:"
    )
    console.print(panel)
    console.print()


# ============================================================================
# 主执行流程
# ============================================================================


def execute_init(
    name: Optional[str] = None, interactive: bool = True
) -> Dict[str, Any]:
    """执行 init 初始化命令"""
    show_logo()

    # 在 init 命令开始时检查更新 (交互模式)
    check_for_updates(silent=False, interactive=interactive)

    style = create_questionary_style()

    if interactive:
        # 交互模式
        name, use_current_dir = collect_project_name(name, style)

        # 检查项目是否已存在
        user_cwd = Path.cwd()
        if use_current_dir:
            project_path = user_cwd
        else:
            project_path = user_cwd / name

        if ProjectConfig.exists(project_path):
            handle_existing_project(name, style, use_current_dir=use_current_dir)

        database, orm, migration_tool = collect_database_config(style)
        features = collect_features(style)

    else:
        # 非交互模式，使用默认配置
        name = name or "my-fastapi-project"
        use_current_dir = name == "."
        if name == ".":
            name = Path.cwd().name

        database = DEFAULT_NON_INTERACTIVE_CONFIG["database"]
        orm = DEFAULT_NON_INTERACTIVE_CONFIG["orm"]
        migration_tool = DEFAULT_NON_INTERACTIVE_CONFIG["migration_tool"]
        features = DEFAULT_NON_INTERACTIVE_CONFIG["features"]
        user_cwd = Path.cwd()

    # 构建项目配置
    project_config = build_project_config(name, database, orm, migration_tool, features)

    # 显示保存与生成进度
    show_saving_progress(name)

    # 确定项目路径 (是否使用当前目录)
    if use_current_dir:
        project_path = user_cwd  # 直接使用当前目录
    else:
        project_path = user_cwd / name
        project_path.mkdir(parents=True, exist_ok=True)

    generate_project(project_path, project_config)

    # 显示配置摘要与后续步骤
    show_config_summary(name, database, orm, migration_tool, features)
    show_next_steps(name, features, use_current_dir=use_current_dir)

    return {
        "project_name": name,
        "database": database,
        "orm": orm,
        "migration_tool": migration_tool,
        "features": features
    }


def init_command(
    name: Optional[str] = typer.Argument(
        None,
        help="项目名称"
    ),
    interactive: bool = typer.Option(
        True,
        "--interactive/--no-interactive",
        "-i/-I",
        help="是否启用交互模式"
    )
):
    """初始化一个新的 FastAPI 项目"""
    execute_init(name=name, interactive=interactive)
