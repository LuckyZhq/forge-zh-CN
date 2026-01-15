
# 使用 forge-zh-CN 构建 FastAPI 项目

`forge-zh-CN` 是一个 FastAPI 项目脚手架工具，可用于快速生成结构规范的 FastAPI 项目。

## 一、克隆项目

```bash
git clone https://github.com/LuckyZhq/forge-zh-CN.git
cd forge-zh-CN
```

---

## 二、构建并安装 forge

在项目根目录执行：

```bash
pip install .
```


安装完成后，可通过以下命令验证是否成功：

```bash
forge --help
```

---

## 三、创建 FastAPI 项目

在任意你希望创建项目的目录中执行：

```bash
forge init
```

---

## 五、启动 FastAPI 项目

进入生成的项目目录：

```bash
cd your_project_name
```

安装依赖并启动服务：

```bash
uv sync
uv run uvicorn app.main:app --reload
```

浏览器访问：

* [http://127.0.0.1:8000](http://127.0.0.1:8000)
* [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

---

## 六、说明

* `forge init` 会基于内置模板生成 FastAPI 项目
* 可通过修改 `templates/` 目录来自定义项目结构和默认代码
* 适合用于个人项目或团队统一 FastAPI 工程规范
