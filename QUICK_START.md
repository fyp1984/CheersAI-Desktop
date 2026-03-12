# CheersAI 项目启动说明

## 环境要求

| 工具 | 版本 | 用途 |
|------|------|------|
| Docker Desktop | 最新版 | 运行 PostgreSQL、Redis、Weaviate、Plugin Daemon |
| Node.js | >= 24 | 前端运行环境 |
| pnpm | >= 10 | 前端包管理 |
| Python | 3.12 | 后端运行环境 |
| uv | 最新版 | Python 包管理（`pip install uv`） |
| Rust + Cargo | 最新版 | Tauri 桌面应用打包（可选） |

---

## 首次安装

```bash
# 1. 安装后端依赖
cd api
uv sync

# 2. 安装前端依赖
cd web
pnpm install
```

---

## 启动项目

### 方式一：一键启动脚本（推荐）

脚本自动完成：启动 Docker 服务 → 等待数据库就绪 → 数据库迁移 → 启动 Flask API。

```powershell
# PowerShell
.\start-backend.ps1
```

```cmd
# CMD
start-backend.bat
```

后端启动后，另开一个终端启动前端：

```bash
cd web
pnpm dev
```

### 方式二：手动启动

```bash
# 终端 1：启动 Docker 基础服务
docker-compose -f docker-compose.dev.yaml up -d

# 终端 2：启动后端 API（等 Docker 服务就绪后）
cd api
uv run flask db upgrade        # 数据库迁移（首次或有新迁移时）
uv run flask run --host 0.0.0.0 --port 5001 --debug

# 终端 3：启动前端
cd web
pnpm dev
```

### 方式三：桌面应用（Tauri）

后端启动后，直接运行 Tauri exe，前端会自动启动：

```
web\src-tauri\target\release\app.exe
```

或使用安装包：`web\src-tauri\target\release\bundle\nsis\CheersAI_1.12.0_x64-setup.exe`

---

## 访问地址

| 服务 | 地址 |
|------|------|
| 前端页面 | http://localhost:3000 |
| 后端 API | http://localhost:5001 |
| 数据脱敏 | http://localhost:3000/data-masking |

登录账号：`1@qq.com` / `password123`

---

## Docker 服务端口

| 服务 | 端口 | 说明 |
|------|------|------|
| PostgreSQL | 5432 | 主数据库（用户: postgres，密码: difyai123456） |
| Redis | 6700 | 缓存和消息队列（密码: difyai123456） |
| Weaviate | 8080 | 向量数据库 |
| Plugin Daemon | 5002 | 插件服务 |

---

## 停止服务

```bash
# 停止后端 API：在终端按 Ctrl+C
# 停止前端：在终端按 Ctrl+C

# 停止 Docker 服务
docker-compose -f docker-compose.dev.yaml down

# 停止并清除数据卷（慎用，会丢失数据库数据）
docker-compose -f docker-compose.dev.yaml down -v
```

---

## 常用开发命令

```bash
# 前端代码检查
cd web && pnpm lint:fix

# 前端类型检查
cd web && pnpm type-check:tsgo

# 运行数据脱敏相关测试
cd web && pnpm test data-masking

# 打包 Tauri 桌面应用
cd web && pnpm tauri build

# 后端测试
cd api && uv run pytest
```

---

## 端口占用排查

```powershell
# 查看端口占用
Get-NetTCPConnection -LocalPort 5432,6700,3000,5001 -ErrorAction SilentlyContinue |
  Select-Object LocalPort, OwningProcess, State

# 杀掉占用进程
Stop-Process -Id <PID> -Force

# 或使用清理脚本
.\scripts\cleanup-ports.ps1
```

---

## 不使用 uv 的替代方案

```bash
cd api
python -m venv .venv
.venv\Scripts\Activate.ps1    # Windows PowerShell
# 或 source .venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
flask db upgrade
flask run --host 0.0.0.0 --port 5001 --debug
```

---

## 项目结构

```
CheersAI/
├── start-backend.ps1/.bat      # 一键启动后端
├── docker-compose.dev.yaml     # Docker 服务配置
├── scripts/                    # 工具脚本
│   ├── cleanup-ports.ps1       #   端口清理
│   └── start-database.*        #   单独启动数据库
├── api/                        # 后端 (Python Flask)
│   ├── .env                    #   环境变量配置
│   └── app.py                  #   应用入口
├── web/                        # 前端 (Next.js + TypeScript)
│   ├── src-tauri/              #   Tauri 桌面应用
│   │   ├── src/main.rs         #     Rust 入口
│   │   └── target/release/     #     编译产物
│   └── app/                    #   Next.js 页面
│       └── components/
│           └── data-masking/   #   数据脱敏组件
├── QUICK_START.md              # 本文档
├── SETUP_GUIDE.md              # 详细环境搭建指南
└── PROJECT_STATUS.md           # 项目状态
```
