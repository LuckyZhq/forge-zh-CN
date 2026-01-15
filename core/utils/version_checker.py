"""版本检查工具"""
import json
import urllib.request
import urllib.error
import subprocess
import sys
from typing import Optional, Tuple
from packaging import version
from core.version import __version__
from ui.colors import get_colors, console
import questionary


def get_latest_version() -> Optional[str]:
    """从 PyPI 获取最新版本号"""
    try:
        with urllib.request.urlopen(
            "https://pypi.org/pypi/ningfastforge/json",
            timeout=3
        ) as response:
            data = json.loads(response.read().decode())
            return data["info"]["version"]
    except (urllib.error.URLError, json.JSONDecodeError, KeyError, TimeoutError):
        return None


def compare_versions(current: str, latest: str) -> Tuple[bool, str]:
    """比较当前版本与最新版本

    返回：
        (是否需要更新, 版本比较结果说明)
    """
    try:
        current_ver = version.parse(current.lstrip('v'))
        latest_ver = version.parse(latest.lstrip('v'))

        if current_ver < latest_ver:
            return True, f"{current} < {latest}"
        elif current_ver > latest_ver:
            return False, f"{current} > {latest}（开发版本）"
        else:
            return False, f"{current} = {latest}（已是最新）"
    except Exception:
        return False, "无法比较版本号"


def auto_update() -> bool:
    """尝试自动更新当前包

    返回：
        更新成功返回 True，否则返回 False
    """
    try:
        console.print("[yellow]🔄 正在更新 Forge...[/yellow]")

        # 根据不同的安装方式尝试不同的更新命令
        update_commands = [
            [sys.executable, "-m", "pip", "install", "--upgrade", "ningfastforge"],
            ["pip", "install", "--upgrade", "ningfastforge"],
            ["pip3", "install", "--upgrade", "ningfastforge"],
        ]

        for cmd in update_commands:
            try:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                if result.returncode == 0:
                    console.print("[green]✅ 更新成功！[/green]")
                    console.print("[dim]请重新运行命令以使用新版本。[/dim]")
                    return True
            except (subprocess.TimeoutExpired, FileNotFoundError):
                continue

        console.print("[red]❌ 自动更新失败，请手动更新：[/red]")
        console.print("[bold]pip install --upgrade ningfastforge[/bold]")
        return False

    except Exception as e:
        console.print(f"[red]❌ 更新出错：{e}[/red]")
        return False


def check_for_updates(silent: bool = False, interactive: bool = True) -> bool:
    """检查是否有可用更新，并根据配置显示提示

    参数：
        silent: 为 True 时不输出任何提示
        interactive: 为 True 时提供交互式自动更新选项

    返回：
        如果有新版本可用则返回 True，否则返回 False
    """
    latest = get_latest_version()
    if not latest:
        if not silent:
            console.print("[dim yellow]⚠️  无法检查更新[/dim yellow]")
        return False

    is_outdated, comparison = compare_versions(__version__, latest)

    if is_outdated and not silent:
        if interactive:
            show_interactive_update_prompt(latest)
        else:
            show_update_notification(latest)

    return is_outdated


def show_interactive_update_prompt(latest_version: str) -> None:
    """显示带有自动更新选项的交互式更新提示"""
    colors = get_colors()

    console.print()
    console.print(f"[bold {colors.warning}]📦 发现新版本！[/bold {colors.warning}]")
    console.print(f"[{colors.text_secondary}]当前版本：[/{colors.text_secondary}] [bold]{__version__}[/bold]")
    console.print(f"[{colors.text_secondary}]最新版本：[/{colors.text_secondary}] [bold {colors.success}]{latest_version}[/bold {colors.success}]")
    console.print()

    # 先显示手动更新命令
    console.print(f"[{colors.text_secondary}]手动更新请执行：[/{colors.text_secondary}]")
    console.print(f"[bold {colors.primary}]pip install --upgrade ningfastforge[/bold {colors.primary}]")
    console.print()

    try:
        # 询问用户是否现在更新
        choice = questionary.select(
            "是否现在更新？",
            choices=[
                "✅ 是，自动更新",
                "⏭️  否，继续使用当前版本"
            ],
            style=questionary.Style([
                ('question', 'bold'),
                ('pointer', 'fg:#8B5CF6 bold'),
                ('highlighted', 'fg:#8B5CF6 bold'),
                ('selected', 'fg:#A855F7'),
                ('answer', 'fg:#C084FC bold')
            ])
        ).ask()

        if choice == "✅ 是，自动更新":
            success = auto_update()
            if success:
                console.print("[bold green]🎉 更新完成！请重新运行命令。[/bold green]")
                sys.exit(0)
        # 如果选择“不更新”，则继续执行后续逻辑

    except (KeyboardInterrupt, EOFError):
        # 用户按下 Ctrl+C，直接继续
        console.print()


def show_update_notification(latest_version: str) -> None:
    """显示非交互式更新提示"""
    colors = get_colors()

    console.print(f"[{colors.text_secondary}]更新命令：[/{colors.text_secondary}]")
    console.print(f"[bold {colors.primary}]pip install --upgrade ningfastforge[/bold {colors.primary}]")
    console.print()
