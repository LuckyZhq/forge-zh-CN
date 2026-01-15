#!/usr/bin/env python3
"""在所有必要的文件中更新版本号"""
import sys
import re
from pathlib import Path


def update_version(new_version: str):
    """更新 __version__.py 和 pyproject.toml 中的版本号"""
    project_root = Path(__file__).parent.parent

    # 更新 core/__version__.py
    version_file = project_root / "core" / "__version__.py"
    version_file.write_text(
        f'"""版本信息"""\n__version__ = "{new_version}"\n'
    )
    print(f"✅ 已更新 core/__version__.py，版本号为 {new_version}")

    # 更新 pyproject.toml
    pyproject_file = project_root / "pyproject.toml"
    content = pyproject_file.read_text()
    content = re.sub(
        r'version = "[^"]+"',
        f'version = "{new_version}"',
        content,
        count=1
    )
    pyproject_file.write_text(content)
    print(f"✅ 已更新 pyproject.toml，版本号为 {new_version}")

    print(f"\n🎉 版本已更新至 {new_version}")
    print("\n后续步骤：")
    print("1. 更新 CHANGELOG.md")
    print("2. git add -A")
    print(f"3. git commit -m 'Bump version to {new_version}'")
    print(f"4. git tag v{new_version}")
    print("5. git push && git push --tags")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("用法：python scripts/update_version.py <新版本号>")
        print("示例：python scripts/update_version.py 0.2.0")
        sys.exit(1)

    new_version = sys.argv[1]

    # 校验版本号格式
    if not re.match(r'^\d+\.\d+\.\d+$', new_version):
        print(f"❌ 无效的版本号格式：{new_version}")
        print("版本号格式应为：X.Y.Z（例如：0.2.0）")
        sys.exit(1)

    update_version(new_version)
