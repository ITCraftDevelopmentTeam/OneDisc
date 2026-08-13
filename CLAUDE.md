# CLAUDE.md

本文件为在 OneDisc 仓库中工作的 AI 编程助手（及人类开发者）提供指南。

## 项目简介

OneDisc 是一个基于 Discord 的 OneBot 实现，支持 OneBot V11 / V12 协议，可对接
NoneBot2、koishi 等 OneBot 框架。v1.0 起使用 Poetry 管理依赖，并使用 Nuitka
将程序编译为各平台可执行文件发布。

## 环境要求

- Python >= 3.12
- Poetry（`poetry install --all-groups` 安装全部依赖，含 dev 组的 nuitka）

## 仓库结构

```
main.py                  程序入口（读取配置 → 初始化日志 → 导入插件 → 连接 Discord）
version.py               从 pyproject.toml 读取版本号
pyproject.toml           项目元数据 + 依赖（版本号唯一权威来源，发版前必须修改）
call_action.py           动作分发（根据 OneBot 协议类型调用对应 action）
actions/                 OneBot 动作实现
  v11/                   OneBot V11 动作
  v12/                   OneBot V12 动作
network/                 各协议版本的网络服务（HTTP / WS / WS 反向）
utils/                   工具模块（配置、日志、数据库、事件、消息解析等）
docs/                    VitePress 文档（独立发布到 GitHub Pages）
.github/workflows/       CI 定义（见下文）
```

## 常用命令

```bash
poetry install --all-groups          # 安装全部依赖
python main.py                       # 运行（需先有 config.json，缺失时进入创建向导）
poetry run python -m nuitka ...      # 编译（参数见 .github/workflows/ci.yml）
```

## 编码规范与注意事项

1. **日志**：使用 `utils/logger.py` 的 `get_logger()`，每个模块在模块级调用
   `logger = get_logger()` 即可获得以本模块命名的 logger。
   ⚠️ **禁止在 get_logger 中使用 `inspect.stack()`/`inspect.getmodule()` 获取调用方**：
   程序使用 Nuitka 编译发布，编译模块没有真实源码文件，inspect 会抛
   `AttributeError: 'dict' object has no attribute 'endswith'` 导致程序无法启动
   （见 issue #106）。现在通过 `sys._getframe(1).f_globals["__name__"]` 实现。
2. **版本号**：唯一权威来源是 `pyproject.toml` 的 `project.version`。`version.py`
   运行时读取它（打包后从可执行文件同目录的数据文件中读取）。
   **发版前必须先修改 pyproject.toml 中的版本号**，否则发布的可执行文件会显示
   旧版本号（v0.2.10 发布时显示 0.2.9.0 的错误曾真实发生过）。
3. **配置文件**：程序从当前工作目录读取 `config.json`，缺失时进入创建向导并退出。
4. **类型标注**：项目使用较新的类型标注语法（`str | None`），保持风格一致。

## CI / 构建

- `.github/workflows/ci.yml`（Build (Dev)）：push 到 master 或手动触发，构建
  Windows / Linux / macOS 三平台 onefile 可执行文件并上传 artifact，同时构建并
  部署文档到 GitHub Pages。
- `.github/workflows/build-release.yml`（Build (Release)）：创建 Release 时触发，
  构建并直接把可执行文件上传到 Release 资产。
- 每个构建任务都包含**冒烟测试**：用临时 config.json 启动产物，检查是否打印
  「OneDisc (By: IT Craft Development Team)」和「当前版本」后正常存活，防止发布
  无法启动的产物（如缺少 websockets 等库）。
- 本地验证构建产物：`./build/onedisc --version` 不可用，请按冒烟测试步骤运行并
  观察启动日志。

## 发版流程

1. 修改 `pyproject.toml` 中的 `version`（如 `1.0.0`）。
2. 合并 PR 到 master。
3. 创建 tag（`v1.0.0`）并发布 Release → 自动触发 build-release.yml 构建并上传资产。
4. 下载 Release 资产做冒烟测试确认可运行。

## 其他

- Docker 部署见 `Dockerfile`（python:3.12-slim + poetry + wkhtmltopdf）。
- 文档使用 VitePress（`docs/`），本地预览：`npm install && npm run docs:dev`。
