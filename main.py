"""Forge CLI 主入口点"""
import typer
from typing import Optional

from ui.logo import show_logo
from commands.init import init_command
from core.version import __version__
from core.utils.version_checker import check_for_updates

# 创建主应用
app = typer.Typer(
    name="forge",
    help="Forge - 现代化的 FastAPI 项目脚手架 CLI 工具",
    rich_markup_mode="rich",
    add_completion=False
)

# 注册命令
app.command(name="init", help="初始化一个新的 FastAPI 项目")(init_command)


def version_callback(value: bool) -> None:
    """版本信息回调"""
    if value:
        typer.echo(f"Forge CLI v{__version__}")
        raise typer.Exit()


@app.callback(invoke_without_command=True)
def main_callback(
    ctx: typer.Context,
    version: Optional[bool] = typer.Option(
        None,
        "--version",
        "-v",
        help="显示版本信息",
        callback=version_callback,
        is_eager=True
    )
):
    """
    Forge CLI 工具

    强大的 FastAPI 项目脚手架生成器
    """
    if ctx.invoked_subcommand is None:
        show_logo()
        typer.echo()  # 空行
        typer.echo(ctx.get_help())  # 显示帮助信息

        # 显示帮助时检查更新（非交互式）
        check_for_updates(silent=False, interactive=False)


def main():
    """主入口函数"""
    app()


if __name__ == "__main__":
    main()
