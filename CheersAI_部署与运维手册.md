# cheersaidesktop 云端生产环境部署概要设计与配置规范

本文档仅用于生产环境部署的概要设计与配置规范要求，不包含具体操作步骤、流程、命令、脚本与完整配置文件。实际部署实施与验收完成后，应另行产出详细《配置手册》与《运维手册（Runbook）》。

---

## 1. 基本信息（列点）

- 域名：desktop.cheersai.cloud
- 公网 IP：62.234.210.100
- 部署形态：单机（非 Docker）
- 进程托管：systemd（服务级启停、开机自启、故障自动拉起）
- 对外入口：复用当前服务器现有 Nginx 网关体系与目录规范

---

## 2. 主机与 OS（列点）

- 主机规格建议：8 vCPU / 16 GB RAM（生产按容量评估与压测结果调整）
- 可用区：按云厂商资源与就近原则选取（本阶段不强制跨 AZ 高可用）
- 操作系统：Ubuntu 22.04 LTS 或 Debian 12
- 内核版本：≥ 5.15
- 时区：Asia/Shanghai
- 安全基线要求：
  - SSH 仅白名单访问
  - 禁止 root 直接登录（原则要求）
  - 最小化开放端口与最小权限
  - 关键配置与密钥必须可审计、可追溯

---

## 3. 目录与路径规范（列点，优先使用用户 home）

- 应用用户：cheersai
- 用户 home：/home/cheersai
- 应用根目录：/home/cheersai/cheersaidesktop
- 配置目录：/home/cheersai/cheersaidesktop/config（敏感配置需最小权限）
- 运行目录：/home/cheersai/cheersaidesktop/run（pid/socket/tmp 等，按需）
- 数据根目录：/home/cheersai/data
  - PostgreSQL：/home/cheersai/data/postgres
  - Redis（如启用持久化）：/home/cheersai/data/redis
  - Weaviate：/home/cheersai/data/weaviate
  - 应用文件存储：/home/cheersai/data/storage
- 日志根目录：/home/cheersai/logs
- 证书目录：/home/cheersai/certs（建议由 root 管控，Nginx 仅最小读权限）
- 权限原则：
  - 应用/数据/日志目录归属 cheersai:cheersai
  - 敏感文件（如 env、密钥）必须限制为仅 owner 可读写

---

## 4. 权限策略（列点，仅保留 cheersai）

- 唯一应用运行用户：cheersai
- 权限边界：
  - cheersai 仅管理应用运行所需目录与进程
  - cheersai 默认不授予全局 sudo（如必须授予，需命令级最小化并开启审计）
- Nginx 运行用户：沿用服务器现状（如 www-data），仅需要：
  - 读取证书文件（最小读权限）
  - 反代访问本机 127.0.0.1 端口

---

## 5. 端口规划（列点）

- 对外开放（安全组 + Nginx 入口）：
  - 22/TCP：SSH（仅管理员来源白名单）
  - 80/TCP：HTTP（跳转到 HTTPS + ACME）
  - 443/TCP：HTTPS（业务入口）
- 建议不对公网暴露（仅 127.0.0.1 或内网）：
  - 8080/TCP：API（本机监听端口，用作 Nginx upstream）
  - 3000/TCP：Web（本机监听端口，用作 Nginx upstream）
  - 9090/TCP：监控（Prometheus 等，仅内网/回环）

---

## 6. 防火墙策略（列点）

- 云安全组为主，主机防火墙为补充
- 放行：
  - 80/443：全网
  - 22：仅管理员 IP 白名单（办公网段/堡垒机）
- 禁止对公网访问：
  - 8080/3000/9090
- 允许：
  - 本机回环（lo）
  - 已建立连接（ESTABLISHED/RELATED）

---

## 7. 应用前后端技术架构（列点）

- 前端 Web：
  - 技术：Next.js + TypeScript + React + Tailwind CSS
  - 访问：仅通过 https://desktop.cheersai.cloud
  - 约束：前端必须通过同域路径访问 API（避免浏览器跨源）
  - 进程形态：Node.js 服务（systemd 托管）
- 后端 API：
  - 技术：Python 3.12 + Flask
  - 对外路径：/console/api/（由 Nginx 反代）
  - 进程形态：WSGI/HTTP 服务（systemd 托管），仅监听 127.0.0.1:8080
- 异步任务：
  - 技术：Celery（worker/beat）
  - 约束：不对外暴露端口
  - 进程形态：systemd 托管（worker 与 beat 分离）
- 数据与依赖：
  - PostgreSQL、Redis、Weaviate
  - 约束：不对公网暴露；数据必须落盘到 /home/cheersai/data
- 运行方式：
  - 非 Docker：systemd + 本机服务
  - Nginx 统一入口（80/443），上游为本机回环端口（3000/8080）

---

## 8. Nginx 配置规范（必须复用现有服务器规范）

### 8.1 现有 Nginx 目录与 include 规范（沿用）

- /etc/nginx/nginx.conf（全局）
- /etc/nginx/sites-available/00-gateway.conf（网关）
- /etc/nginx/sites-enabled/entry.conf（启用入口）
- /etc/nginx/locations/*.conf（业务路由片段）
- /etc/nginx/snippets/ssl-params.conf（SSL 统一参数）

### 8.2 CheersAI Desktop

- 业务接入文件：/etc/nginx/locations/cheersaidesktop.conf
- 规范要求：
  - 仅新增最小范围的 location/upstream 片段，不改动网关主流程
  - upstream 仅指向本机回环：127.0.0.1:3000（Web）、127.0.0.1:8080（API）
  - 必须支持 WebSocket（Upgrade/Connection 透传）
  - SSL 必须复用 snippets/ssl-params.conf 的统一参数（禁止业务私自发散）
  - 限流/连接数/缓存策略由现网网关统一策略决定，业务仅按要求挂载/引用

### 8.3 域名与路由（规范要求）

- server_name：desktop.cheersai.cloud
- 路由：
  - /console/api/ → 127.0.0.1:8080
  - / → 127.0.0.1:3000

---

## 9. 配置项要求（列点）

- 配置与密钥管理：
  - 环境变量文件与密钥不进入代码仓库
  - 生产密钥必须通过受控方式分发并留痕审计
  - 建议将运行期配置收敛为单一 EnvironmentFile（例如 /home/cheersai/cheersaidesktop/config/production.env）并设置最小权限
- 关键配置项（名称以工程实际为准）：
  - 数据库：DB_TYPE、DB_HOST、DB_PORT、DB_USERNAME、DB_PASSWORD、DB_DATABASE
  - Redis：REDIS_HOST、REDIS_PORT、REDIS_PASSWORD
  - Weaviate：WEAVIATE_ENDPOINT
  - 站点与 CORS：CONSOLE_WEB_URL、CONSOLE_CORS_ALLOW_ORIGINS
- 健康检查端点（验收要求）：
  - API：/console/api/ping
  - Web：/apps（或等价的前端可用性路径）

---

## 10. 变更记录

| 版本 | 日期 | 作者 | 变更原因 |
|---|---|---|---|
| v2.1 | 2026-03-03 | CheersAI Ops | 进一步简化为列点式概要规范，固化域名与公网 IP，并调整 Nginx 接入章节标题为 CheersAI Desktop |
| v2.2 | 2026-03-03 | CheersAI Ops | 将部署形态由 Docker 调整为非 Docker，按 systemd 进程托管重新梳理部署策略 |
