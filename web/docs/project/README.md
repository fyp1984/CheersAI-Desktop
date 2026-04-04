# 项目文档

项目启动、配置和开发环境相关文档。

## 📋 文档列表

- **项目启动完成-V1.2.md** - V1.2 版本项目启动指南
- **项目启动完成.md** - 基础项目启动指南

## 🚀 快速开始

### 1. 环境要求
- Node.js 16+
- Python 3.10+
- Docker
- pnpm

### 2. 启动步骤

#### 启动 Docker 服务
```bash
docker-compose -f docker-compose.dev.yaml up -d
```

#### 启动后端
```bash
cd api
.venv/Scripts/python.exe -m flask run --host 0.0.0.0 --port=5001 --debug
```

#### 启动前端
```bash
cd web
pnpm dev
```

### 3. 访问应用
- 前端: http://localhost:3000
- 后端 API: http://localhost:5001

## 🔧 服务端口

| 服务 | 端口 | 说明 |
|------|------|------|
| 前端 | 3000 | Next.js 开发服务器 |
| 后端 API | 5001 | Flask API 服务器 |
| PostgreSQL | 5432 | 数据库 |
| Redis | 6700 | 缓存服务 |
| Weaviate | 8081 | 向量数据库 |
| Gitea | 8080 | Git 服务 |

## 📖 详细文档

查看 `项目启动完成-V1.2.md` 了解完整的启动步骤和配置说明。
