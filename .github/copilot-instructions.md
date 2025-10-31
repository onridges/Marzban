## 快速说明 — 给 AI 代码助手的要点

以下内容帮助自动化编码代理（Copilot / agents）快速在本仓库中变得有用。重点针对本项目的真实、可发现模式与命令 —— 非通用建议。

### 项目概览（大局）
- 后端：Python，入口为 `main.py`，使用 Uvicorn/Starlette/FastAPI 风格（通过环境变量 `UVICORN_HOST`/`UVICORN_PORT` 控制）。
- 数据层：SQLAlchemy，数据库 URL 由 `SQLALCHEMY_DATABASE_URL` 控制；迁移在 `db/migrations/`（alembic）下。
- 前端：位于 `app/dashboard/`，基于 React + Vite（`yarn dev` / `yarn build`）。构建产物放到 `app/dashboard/build/`。
- 辅助：`marzban-cli.py` 提供管理命令（见 `cli/README.md`），以及多个 background jobs 在 `jobs/`。
- Xray 集成：xray 配置模板 `xray_config.json`；运行时路径由 `XRAY_EXECUTABLE_PATH`、`XRAY_ASSETS_PATH` 等 env 控制；模板位于 `app/templates/`（如 `v2ray/`, `clash/`, `singbox/`）。

### 立刻可运行（开发者常用命令 & 例子）
- 启动后端（开发）：在项目根，先复制并编辑 `.env`（见 `.env.example`），然后：

```bash
python3 main.py   # 或使用项目文档中配置的 uvicorn 方式
```

- 数据库迁移：

```bash
alembic upgrade head   # 在仓库根运行，迁移位于 db/migrations/
```

- 安装并运行前端：

```bash
cd app/dashboard
yarn install
yarn dev     # 本地热重载
yarn build   # 产出到 app/dashboard/build/
```

- 使用 CLI 生成订阅示例：

```bash
python3 marzban-cli.py subscription get-config -u alice -f v2ray
# 或安装为全局命令后： marzban-cli subscription get-config ...
```

### 项目特有约定 / 可看到的模式
- 模板目录：`CUSTOM_TEMPLATES_DIRECTORY` env 指向模板根，`app/templates/` 提供示例模板。修改模板通常不需重启服务（README 中有说明）。
- 订阅链接生成依赖 `XRAY_SUBSCRIPTION_URL_PREFIX` 环境变量；CLI 的 `get-link` 需要该值存在。
- Webhook / 通知：`WEBHOOK_ADDRESS` + `WEBHOOK_SECRET`（header 为 `x-webhook-secret`）。相关代码在 `utils/notification.py`、`jobs/` 与 `telegram/`、`discord/` handlers 下实现。
- Xray 多节点与多入站（inbounds）逻辑：查看 `xray/` 目录与 `subscription/` 里的生成器（`v2ray.py`, `clash.py`, `singbox.py`）以理解数据流与占位符替换。
- 后端路由组织：`app/routers/` 下按功能分文件（user, admin, node, subscription, system...），首选在那里寻找 API 行为。

### 集成点与外部依赖（必须显式处理的东西）
- Xray 二进制与 JSON：`XRAY_EXECUTABLE_PATH` 与 `XRAY_JSON`。修改或模拟 Xray 时，优先使用这些 env 变量而非硬编码路径。
- Telegram Bot：`TELEGRAM_API_TOKEN` 和 `TELEGRAM_ADMIN_ID`；相关事件处理在 `telegram/handlers/`。
- 可选：Discord webhook（在 `discord/handlers/`）。

### 常见改动所在文件（快速索引）
- 启动/配置： `main.py`, `config.py`, `.env.example`
- 数据模型/CRUD： `db/models.py`, `db/crud.py`, `models/`（高层 domain models）
- Migrations： `db/migrations/` + `alembic.ini`
- 前端： `app/dashboard/`（Vite/React）
- Xray & subscription templates： `xray/`, `subscription/`, `app/templates/`
- CLI： `marzban-cli.py`, `cli/README.md`

### 不要做（安全与互操作）
- 不要把真实密钥或 token 写入仓库；在修改示例 `.env` 时请保持敏感信息只在本地或 CI secret 中。
- 修改 Xray 相关路径时，务必保持 env 名称一致并在 README 中同步说明。

---
如果需要，我可以把上述内容合并为英文版或按 CI（GitHub Actions）/Docker 用例扩展入具体命令。请告诉我是否需要添加：CI 构建、Docker 本地调试或更多代码位置的示例片段（例如 `app/routers/user.py` 的典型请求-响应样例）。
