# 发布到 PyPI 指南

使用 GitHub Actions 将 Forge 发布到 PyPI 的完整指南。

## 目录

- [快速开始](#快速开始)
- [前置条件](#前置条件)
- [设置步骤](#设置步骤)
- [发布](#发布)
- [私有仓库](#私有仓库)
- [故障排除](#故障排除)

## 快速开始

给急性子的人：

```bash
# 1. 更新 pyproject.toml（名称、版本、作者、URL）
# 2. 本地测试构建
./scripts/test_build.sh

# 3. 在以下地址配置 PyPI 可信发布：
https://pypi.org/manage/account/publishing/

# 4. 创建 GitHub 环境：Settings → Environments → "pypi"

# 5. 创建 GitHub Release → 自动发布！
````

## 前置条件

### 1. 账户

* **PyPI 账户**：[https://pypi.org（用于生产环境）](https://pypi.org（用于生产环境）)
* **Test PyPI 账户**：[https://test.pypi.org（可选，用于测试）](https://test.pypi.org（可选，用于测试）)

### 2. GitHub 仓库

你的代码必须在 GitHub 仓库中（公开或私有）。

**仓库可见性对比：**

| 类型 | 优点                                  | 缺点                                                |
| -- | ----------------------------------- | ------------------------------------------------- |
| 公开 | ✅ 无限 Actions 时长<br>✅ 社区贡献<br>✅ 完全透明 | ❌ 源代码可见                                           |
| 私有 | ✅ 源代码私有<br>✅ 发布流程相同                 | ⚠️ Actions 时长有限（免费 2,000 分钟/月）<br>⚠️ PyPI 上的包仍然公开 |

**重要提示**：PyPI 上的包始终是公开的，即使来自私有仓库。

### 3. 包名称

检查你想要的名称是否可用：

* 访问：[https://pypi.org/project/your-package-name/](https://pypi.org/project/your-package-name/)
* 如果已被占用，选择替代方案：`fastapi-forge`、`forge-cli` 等

## 设置步骤

### 步骤 1：更新包元数据

编辑 `pyproject.toml`：

```toml
[project]
name = "ningfastforge"  # ⚠️ 必须在 PyPI 上唯一
version = "0.1.0"       # ⚠️ 每次发布都要更新
authors = [
    {name = "Ning", email = "ning3739@gmail.com"}  # ⚠️ 更新
]

[project.urls]
Homepage = "https://github.com/ning3739/forge"      # ⚠️ 更新
Repository = "https://github.com/ning3739/forge"    # ⚠️ 更新
Issues = "https://github.com/ning3739/forge/issues" # ⚠️ 更新
```

### 步骤 2：更新 LICENSE

编辑 LICENSE 文件，将 `[Your Name]` 替换为你的真实姓名。

### 步骤 3：本地测试构建

```bash
# 运行测试脚本
./scripts/test_build.sh

# 或手动执行：
pip install build twine
python -m build
twine check dist/*
```

### 步骤 4：配置 PyPI 可信发布

可信发布是安全、现代的发布方式（无需 API 令牌）。

#### 可视化指南

```
你的仓库结构：
├── .github/
│   └── workflows/
│       └── publish.yml  ← 工作流名称："publish.yml"
├── pyproject.toml       ← 包名称："ningfastforge"
└── ...

PyPI 表单字段：
┌─────────────────────────────────────────┐
│ PyPI Project Name: ningfastforge        │ ← 来自 pyproject.toml
│ Owner: yourusername                     │ ← 你的 GitHub 用户名
│ Repository name: forge                  │ ← 只需仓库名
│ Workflow name: publish.yml              │ ← 只需文件名！
│ Environment name: pypi                  │ ← 来自工作流
└─────────────────────────────────────────┘
```

#### 生产环境配置（PyPI）：

1. 访问：[https://pypi.org/manage/account/publishing/](https://pypi.org/manage/account/publishing/)
2. 点击 "Add a new pending publisher"
3. 填写表单：

   * **PyPI Project Name**：`ningfastforge`（来自你的 `pyproject.toml`）
   * **Owner**：`ning3739`（你的 GitHub 用户名）
   * **Repository name**：`forge`（只需仓库名，不是完整 URL）
   * **Workflow name**：`publish.yml` ⚠️ 只需文件名，不是路径！
   * **Environment name**：`pypi` ⚠️ 必须与工作流文件匹配
4. 点击 "Add"

**重要提示**：

* 工作流名称只需填写 `publish.yml`（不是 `.github/workflows/publish.yml`）
* 文件必须存在于仓库的 `.github/workflows/publish.yml` 位置
* 在配置 PyPI 之前，先将工作流文件推送到 GitHub

#### 常见错误

| 错误                          | 解决方案                                              |
| --------------------------- | ------------------------------------------------- |
| "Workflow name not found"   | 确保 `.github/workflows/publish.yml` 存在并已推送到 GitHub |
| "Environment name mismatch" | 检查环境名称完全匹配（区分大小写）                                 |
| "Repository not found"      | 只使用仓库名（如 `forge`），不是完整 URL                        |

#### 测试环境配置（Test PyPI）：

在 [https://test.pypi.org/manage/account/publishing/](https://test.pypi.org/manage/account/publishing/) 执行相同步骤，但使用：

* **Environment name**：`testpypi` ⚠️ 必须与工作流文件匹配

#### 配置示例

**生产环境 PyPI：**

```
PyPI Project Name:    ningfastforge
Owner:                ning3739
Repository name:      forge
Workflow name:        publish.yml
Environment name:     pypi
```

**测试环境 Test PyPI：**

```
PyPI Project Name:    ningfastforge
Owner:                ning3739
Repository name:      forge
Workflow name:        publish.yml
Environment name:     testpypi
```

### 发布前检查清单

发布前使用此检查清单：

#### 配置

* [ ] 已更新 `pyproject.toml`（名称、版本、作者、URL）
* [ ] 已更新 LICENSE 文件中的姓名
* [ ] 已更新 CHANGELOG.md 中的变更记录

#### 测试

* [ ] 已本地测试构建：`./scripts/test_build.sh`
* [ ] 已验证包内容：`tar -tzf dist/*.tar.gz | less`
* [ ] 已测试安装：`pip install dist/*.whl && forge --version`

#### PyPI 设置

* [ ] 已创建 PyPI 账户
* [ ] 已使用正确的值配置可信发布
* [ ] 已创建 GitHub 环境：`pypi` 或 `testpypi`

#### 发布

* [ ] 已将所有更改推送到 GitHub
* [ ] 已创建 GitHub Release（或触发手动工作流）
* [ ] 已验证从 PyPI 安装：`pip install ningfastforge`

### 步骤 5：配置 GitHub 环境

1. 进入你的 GitHub 仓库
2. 导航到：Settings → Environments
3. 点击 "New environment"
4. 命名为：`pypi`（或用于测试的 `testpypi`）
5. （可选）添加保护规则：

   * 必需的审核者
   * 等待计时器
   * 部署分支限制

## 发布

### 自动化发布流程

项目使用全自动 CI/CD：

1. **更新 `pyproject.toml` 中的版本**：

   ```toml
   version = "0.1.2"
   ```

2. **更新 CHANGELOG.md 中的变更记录**：

   ```markdown
   ## [0.1.2] - 2025-01-06

   ### 新增
   - 新功能

   ### 修复
   - Bug 修复
   ```

3. **提交并推送到 main 分支**：

   ```bash
   git add pyproject.toml CHANGELOG.md
   git commit -m "Bump version to 0.1.2"
   git push origin main
   ```

4. **自动流程（无需手动操作）**：

   * ✅ 在 Python 3.9-3.13 上运行 CI 测试
   * ✅ 构建并验证包
   * ✅ 自动发布到 PyPI
   * ✅ 自动创建 Git 标签
   * ✅ 自动创建 GitHub Release 并附带更新日志

就这样！只需推送到 main 分支，一切都会自动完成。

### 版本管理

工作流自动执行：

* 从 `pyproject.toml` 检测版本
* 检查版本是否已发布
* 如果版本标签已存在则跳过
* 成功发布后创建标签和发布

### 监控

观察进度：

* **Actions**：[https://github.com/ning3739/forge/actions](https://github.com/ning3739/forge/actions)
* **PyPI**：[https://pypi.org/project/ningfastforge/](https://pypi.org/project/ningfastforge/)
* **Releases**：[https://github.com/ning3739/forge/releases](https://github.com/ning3739/forge/releases)

## 版本管理

遵循语义化版本控制（MAJOR.MINOR.PATCH）：

* **PATCH**（0.1.0 → 0.1.1）：Bug 修复
* **MINOR**（0.1.0 → 0.2.0）：新功能（向后兼容）
* **MAJOR**（0.1.0 → 1.0.0）：破坏性变更

每次发布前：

1. 更新 `pyproject.toml` 中的版本
2. 更新 CHANGELOG.md 中的变更记录
3. 提交更改
4. 创建匹配标签的发布

## 私有仓库

### 使用私有仓库配合公开 PyPI

✅ 完全支持！你的设置已经适用于私有仓库。

**私有部分：**

* GitHub 上的源代码
* Git 历史和提交记录
* Issues 和讨论

**公开部分：**

* PyPI 上的包（始终公开）
* 包元数据
* 编译后的代码（可被反编译）

**私有仓库的 GitHub Actions 限制：**

* 免费版：2,000 分钟/月
* Pro 版：3,000 分钟/月
* 典型用量：每次发布约 2-3 分钟

### 替代方案：保持包私有

如果你也需要包私有：

**选项 1：从 GitHub 安装**

```bash
# 公开仓库
pip install git+https://github.com/username/forge.git

# 私有仓库（需要认证）
pip install git+https://github.com/username/forge.git@v0.1.0
```

**选项 2：私有 PyPI 服务器**

* Gemfury - $45/月
* AWS CodeArtifact
* devpi - 自托管，免费

## 故障排除

### 包名称已被占用

**错误**：包名称在 PyPI 上已存在

**解决方案**：选择不同的名称

* 尝试：`fastapi-forge`、`forge-cli`、`fastapi-scaffold-cli`
* 在 `pyproject.toml` 中更新
* 在 PyPI 可信发布者设置中更新

### 本地构建失败

**错误**：构建命令失败

**解决方案**：

```bash
# 检查 Python 版本
python --version  # 应该是 3.9+

# 重新安装构建工具
pip install --upgrade build twine

# 检查语法错误
python -m py_compile main.py

# 查看构建输出中的错误消息
```

### 发布失败

**错误**：GitHub Actions 发布步骤失败

**常见原因：**

1. **未配置可信发布者**

   * 在 PyPI 验证设置
   * 检查环境名称是否匹配（`pypi` 或 `testpypi`）

2. **包名称不匹配**

   * `pyproject.toml` 中的名称必须与 PyPI 项目名称匹配
   * 区分大小写！

3. **版本已存在**

   * 无法重新发布相同版本
   * 增加版本号

4. **GitHub 环境未创建**

   * 在仓库设置中创建环境
   * 名称必须与工作流匹配（`pypi` 或 `testpypi`）

### 安装后导入错误

**错误**：`pip install` 后出现 `ModuleNotFoundError`

**解决方案**：

```bash
# 检查包结构
tar -tzf dist/*.tar.gz | grep ".py$"

# 验证 pyproject.toml 中的包配置
[tool.setuptools]
packages = ["commands", "core", "ui"]
py-modules = ["main"]

# 重新构建和测试
python -m build
pip install dist/*.whl --force-reinstall
```

## 添加 PyPI 徽章到 README

发布后，将这些徽章添加到 README.md：

```markdown
[![PyPI version](https://badge.fury.io/py/ningfastforge.svg)](https://badge.fury.io/py/ningfastforge)
[![Python Versions](https://img.shields.io/pypi/pyversions/ningfastforge.svg)](https://pypi.org/project/ningfastforge/)
[![Downloads](https://pepy.tech/badge/ningfastforge)](https://pepy.tech/project/ningfastforge)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
```

将 `ningfastforge` 替换为你的实际包名称。

## 检查清单

**发布前：**

* [ ] 已更新 `pyproject.toml`（名称、版本、作者、URL）
* [ ] 已更新 LICENSE 文件中的姓名
* [ ] 已更新 CHANGELOG.md 中的变更记录
* [ ] 已本地测试构建：`./scripts/test_build.sh`
* [ ] 已配置 PyPI 可信发布
* [ ] 已创建 GitHub 环境（`pypi` 或 `testpypi`）
* [ ] 已先在 Test PyPI 上测试（推荐）
* [ ] 已创建带有正确标签的 GitHub release
* [ ] 已验证安装：`pip install ningfastforge`
* [ ] 已测试 CLI：`forge --version`

## 资源

* **PyPI**：[https://pypi.org](https://pypi.org)
* **Test PyPI**：[https://test.pypi.org](https://test.pypi.org)
* **可信发布指南**：[https://docs.pypi.org/trusted-publishers/](https://docs.pypi.org/trusted-publishers/)
* **Python 打包指南**：[https://packaging.python.org/](https://packaging.python.org/)
* **语义化版本控制**：[https://semver.org/](https://semver.org/)

## 需要帮助？

* 检查 GitHub Actions 日志以获取详细错误消息
* 查看 PyPI 文档
* 在你的仓库中开启 issue
* 查看 Python Packaging Discourse
