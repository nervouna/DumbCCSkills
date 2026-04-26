---
name: python-scaffold
description: 快速搭建 Python 项目脚手架，支持 CLI 工具、Web 应用 (FastAPI)、Python 库三种类型。使用 uv + ruff + mypy + pytest 现代工具链。当用户说"创建 Python 项目"、"搭建项目脚手架"、"初始化 Python 项目"、"新建项目"、"scaffold a Python project"、"create a new Python project"时触发。
---

# Python 项目脚手架

快速创建符合社区最佳实践和用户开发习惯的 Python 项目。

## 输入收集

在执行前，必须收集以下信息。如果用户在消息中已经提供，直接使用；缺少的必须交互式询问：

1. **项目名称** (project_name): 目录名，使用 kebab-case（如 `my-cli-tool`）
2. **项目类型** (project_type): `cli` / `web` / `lib`
3. **简短描述** (description): 一句话说明项目用途

Python 包名 (project_name_snake) 由项目名自动转换：`my-cli-tool` → `my_cli_tool`。

## 工作流程

### 步骤 1: 确认参数

展示解析后的参数让用户确认：
- 项目名称 + Python 包名
- 项目类型
- 项目描述
- 创建路径

### 步骤 2: 创建目录结构

在指定路径（默认当前目录）下创建项目根目录，然后根据 project_type 创建对应的目录结构。

所有模板文件在 `templates/<type>/` 目录下。在开始生成前，先 Read 对应类型目录下的所有模板文件，了解文件列表。

### 步骤 3: 渲染模板

读取每个模板文件，替换以下占位符：
- `{{project_name}}` → kebab-case 项目名
- `{{project_name_snake}}` → snake_case Python 包名
- `{{description}}` → 项目描述
- `{{author}}` → 从 `git config user.name` 获取，失败则用 "TODO"
- `{{python_version}}` → "3.14"

将渲染后的内容写入对应的目标路径。模板文件路径映射规则：模板路径去掉 `templates/<type>/` 前缀后拼接到项目根目录。

### 步骤 4: 安装依赖

```bash
cd <project_dir> && uv sync
```

如果 uv 不可用，提示用户安装：`brew install uv`。

### 步骤 5: 初始化 Git

```bash
cd <project_dir> && git init && git add -A && git commit -m "chore: initial project scaffold"
```

提交信息遵循用户的 git commit 规范（`type: message` 格式）。

### 步骤 6: 配置 Claude Code 权限

在项目根目录创建 `.claude/settings.json`，预授权 Python 开发常用命令，避免后续每次手动批准：

```json
{
  "permissions": {
    "allow": [
      "Bash(uv *)",
      "Bash(python *)",
      "Bash(python3 *)",
      "Bash(uv run *)",
      "Bash(pytest *)",
      "Bash(ruff *)",
      "Bash(mypy *)",
      "Bash(mkdir *)",
      "Bash(find *)",
      "Bash(pip *)"
    ]
  }
}
```

创建命令：

```bash
mkdir -p <project_dir>/.claude
cat > <project_dir>/.claude/settings.json << 'EOF'
{
  "permissions": {
    "allow": [
      "Bash(uv *)",
      "Bash(python *)",
      "Bash(python3 *)",
      "Bash(uv run *)",
      "Bash(pytest *)",
      "Bash(ruff *)",
      "Bash(mypy *)",
      "Bash(mkdir *)",
      "Bash(find *)",
      "Bash(pip *)"
    ]
  }
}
EOF
```

如果项目已有 `.claude/settings.json`（比如在已有目录中创建），则合并 `permissions.allow` 数组，保留已有条目并追加新条目。如果已有条目覆盖了相同命令则跳过。

### 步骤 7: 完成报告

告知用户项目已就绪，列出关键文件路径和后续操作建议（如 `uv run pytest`、`uv run ruff check .`）。

## 模板渲染说明

### 变量替换表

| 占位符 | 来源 | 示例 |
|--------|------|------|
| `{{project_name}}` | 用户输入 | `my-cli-tool` |
| `{{project_name_snake}}` | 自动转换 | `my_cli_tool` |
| `{{description}}` | 用户输入 | `A CLI tool for data processing` |
| `{{author}}` | `git config user.name` | `Xiaoyu Guan` |
| `{{python_version}}` | 固定值 | `3.14` |

### 模板文件清单

#### CLI 类型 (`templates/cli/`)

```
pyproject.toml
.gitignore
.env.example
README.md
src/project_name/__init__.py
src/project_name/__main__.py
src/project_name/cli.py
tests/__init__.py
tests/test_cli.py
```

#### Web 类型 (`templates/web/`)

```
pyproject.toml
.gitignore
.env.example
README.md
src/project_name/__init__.py
src/project_name/__main__.py
src/project_name/app.py
src/project_name/config.py
src/project_name/routes/__init__.py
src/project_name/routes/health.py
src/project_name/models/__init__.py
tests/__init__.py
tests/conftest.py
tests/test_health.py
```

#### Lib 类型 (`templates/lib/`)

```
pyproject.toml
.gitignore
README.md
src/project_name/__init__.py
src/project_name/core.py
tests/__init__.py
tests/test_core.py
```

## 注意事项

- 不要生成 CI/CD 配置文件
- .env 文件不提交到 git（.gitignore 已包含）
- 代码文件简洁、不加多余注释
- 使用 `[dependency-groups]` 而非 `[tool.uv.dev-dependencies]`
- Git 用户设置代理：如果环境变量有 `ALL_PROXY`，提醒用户可能需要为 git 配置代理
