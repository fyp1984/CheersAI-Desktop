# CheersAI 数据脱敏版本 - 完整启动指南

## 目录
1. [系统要求](#系统要求)
2. [快速启动](#快速启动)
3. [详细启动步骤](#详细启动步骤)
4. [对原版 Dify 的修改说明](#对原版-dify-的修改说明)
5. [功能验证](#功能验证)
6. [常见问题](#常见问题)
7. [开发指南](#开发指南)

---

## 系统要求

### 必需软件
- **Docker Desktop** (最新版本)
- **Node.js** 18+ 或 20+
- **pnpm** 8+
- **Python** 3.12
- **uv** (Python 包管理器)

### 可选软件（桌面应用开发）
- **Rust** 1.93.0+
- **Tauri CLI** 2.10.0+

### 系统配置
- **操作系统**: Windows 10/11
- **内存**: 至少 8GB RAM
- **磁盘空间**: 至少 20GB 可用空间

---

## 快速启动

### 方式一：一键启动脚本（推荐）

```powershell
# PowerShell - 一键启动后端（Docker 服务 + 数据库迁移 + Flask API）
.\start-backend.ps1

# 前端（新开终端）
cd web
pnpm dev
```

```cmd
# CMD
start-backend.bat
```

脚本会自动完成：启动 Docker 服务 → 等待数据库就绪 → 运行数据库迁移 → 启动 Flask API

### 方式二：手动命令

```bash
# 终端 1: 启动 Docker + 后端
docker-compose -f docker-compose.dev.yaml up -d
cd api
uv run flask run --host 0.0.0.0 --port 5001 --debug

# 终端 2: 启动前端
cd web
pnpm dev
```

### 方式三：桌面应用

后端启动后，双击 Tauri 桌面应用 exe，前端会自动启动。

访问: http://localhost:3000  
登录: `1@qq.com` / `password123`

---

## 详细启动步骤

### 步骤 1: 环境准备

#### 1.1 安装 Docker Desktop
```powershell
docker --version
docker ps
```

#### 1.2 安装 Node.js 和 pnpm
```powershell
node --version   # v18+ 或 v20+
npm install -g pnpm
pnpm --version
```

#### 1.3 安装 Python 和 uv
```powershell
python --version  # 3.12+
pip install uv
uv --version
```

#### 1.4 安装项目依赖
```powershell
# 前端
cd web && pnpm install

# 后端
cd api && uv sync
```

---

### 步骤 2: 配置环境变量

#### 后端 `api/.env`（已预配置）
```env
DB_USERNAME=postgres
DB_PASSWORD=difyai123456
DB_HOST=localhost
DB_PORT=5432
DB_DATABASE=dify
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=difyai123456
CELERY_BROKER_URL=redis://:difyai123456@localhost:6379/1
VECTOR_STORE=weaviate
WEAVIATE_ENDPOINT=http://localhost:8080
WEAVIATE_API_KEY=WVF5YThaHlkYwhGUSmCRgsX3tD5ngdN8pkih
PLUGIN_DAEMON_ENDPOINT=http://127.0.0.1:5002
```

---

## 对原版 Dify 的修改说明

### 1. Docker 服务配置
**文件**: `docker-compose.dev.yaml`

新增服务:
- Plugin Daemon (端口 5002) - 原版缺少此服务导致 500 错误
- Weaviate 向量数据库 (端口 8080)

### 2. 后端环境变量
**文件**: `api/.env`

新增:
```env
PLUGIN_DAEMON_ENDPOINT=http://127.0.0.1:5002
VECTOR_STORE=weaviate
WEAVIATE_ENDPOINT=http://localhost:8080
WEAVIATE_API_KEY=WVF5YThaHlkYwhGUSmCRgsX3tD5ngdN8pkih
```

### 3. 数据脱敏功能（全新）

```
web/lib/data-masking/           # 核心逻辑（25+ 文件）
├── masking-engine.ts           # 脱敏引擎
├── sandbox-manager.ts          # 沙箱管理
├── mapping-store.ts            # 映射存储
├── reverse-substitution.ts     # 反向替换
├── rules-manager.ts            # 规则管理
├── file-uploader.ts            # 文件上传
├── credential-manager.ts       # 凭证管理
├── crypto-utils.ts             # 加密工具
├── database.ts / indexeddb.ts  # 数据库层
├── transaction-manager.ts      # 事务管理
├── logger.ts                   # 日志系统
└── __tests__/                  # 131 个测试（100% 通过）

web/app/components/data-masking/ # UI 组件
├── sandbox-config.tsx
├── file-masking.tsx
├── file-list.tsx
└── list.tsx

web/app/(commonLayout)/data-masking/page.tsx  # 主页面
web/service/data-masking.ts                    # API 服务
web/i18n/zh-Hans/data-masking.json            # 中文翻译 (107 键)
web/i18n/en-US/data-masking.json              # 英文翻译 (107 键)
```

### 4. 国际化配置
**文件**: `web/i18n-config/resources.ts`
- 注册 `dataMasking` 命名空间

### 5. 前端布局修复
**文件**: `web/app/layout.tsx`
- 移除未使用的 Google Fonts 引用，修复 `instrumentSerif is not defined` 错误

### 6. Tauri 桌面应用（全新）

```
web/src-tauri/
├── src/main.rs          # Rust 后端（内嵌 Next.js 服务器）
├── Cargo.toml           # Rust 依赖
└── tauri.conf.json      # Tauri 配置

web/scripts/
├── build-tauri-with-server.cjs
├── build-tauri.cjs
└── package-nextjs-server.cjs
```

### 7. 启动脚本
```
start-backend.ps1/.bat    # 一键启动后端（Docker + 迁移 + Flask）
scripts/
├── cleanup-ports.ps1     # 端口清理工具
├── start-database.ps1    # 单独启动数据库
└── start-database.bat
```

### 修改统计

| 类别 | 新增文件 | 修改文件 | 代码行数 |
|------|---------|---------|---------|
| Docker 配置 | 0 | 1 | ~50 |
| 启动脚本 | 4 | 0 | ~200 |
| 数据脱敏功能 | 25+ | 0 | ~3000 |
| 国际化 | 2 | 1 | ~200 |
| Tauri 应用 | 10+ | 0 | ~500 |
| 文档 | 5 | 0 | ~500 |
| **总计** | **46+** | **2** | **~4450** |

---

## 功能验证

### 验证后端
```powershell
curl http://localhost:5001/health
```

### 验证数据脱敏
1. 访问 http://localhost:3000/data-masking
2. 测试沙箱配置、脱敏规则、文件脱敏功能

### 验证国际化
- 在设置中切换语言，验证数据脱敏页面中英文正确显示

---

## 常见问题

### 端口占用
```powershell
# 检查端口
Get-NetTCPConnection -LocalPort 5432,3000,5001 -ErrorAction SilentlyContinue

# 清理端口
.\scripts\cleanup-ports.ps1
```

### Docker 服务启动失败
```powershell
docker-compose -f docker-compose.dev.yaml down -v
docker-compose -f docker-compose.dev.yaml up -d
```

### uv 命令找不到
重启 PowerShell 7，或使用完整路径，或使用传统方式:
```powershell
cd api
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
flask run --host 0.0.0.0 --port 5001 --debug
```

---

## 开发指南

```powershell
# 测试
cd web && pnpm test data-masking

# 代码检查
cd web && pnpm lint:fix

# 构建桌面应用
cd web && pnpm tauri build
```

---

## 项目结构

```
├── start-backend.ps1/.bat      # 一键启动后端
├── docker-compose.dev.yaml     # Docker 服务配置
├── scripts/                    # 工具脚本
│   ├── cleanup-ports.ps1
│   └── start-database.*
├── api/                        # 后端 Flask API
├── web/                        # 前端 Next.js
│   ├── src-tauri/              # Tauri 桌面应用
│   ├── lib/data-masking/       # 数据脱敏核心
│   └── app/components/data-masking/  # 脱敏 UI
├── docs/                       # 项目文档
├── QUICK_START.md              # 快速启动
├── SETUP_GUIDE.md              # 本文档
└── PROJECT_STATUS.md           # 项目状态
```

---

## 核心端口

| 服务 | 端口 |
|------|------|
| 前端 | 3000 |
| 后端 API | 5001 |
| Plugin Daemon | 5002 |
| PostgreSQL | 5432 |
| Redis | 6700 |
| Weaviate | 8080 |

---

**最后更新**: 2026-02-22
