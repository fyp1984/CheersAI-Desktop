---
name: dev-standards
description: CheersAI Desktop 提交与发布规范。处理 Git 提交、PR、发布、SSO 登录链路、临时文件、日志文件、测试文件变更时必须遵守。
---

# CheersAI Desktop 开发规范

## 提交前硬规则

- 禁止使用 `git add .`、`git add -A` 做无差别提交；必须按文件白名单逐个 `git add <path>`。
- 不提交运行日志、审计日志、缓存、临时下载、签名私钥、本地工具二进制、构建产物。
- 不提交与当前修复无关的测试文件改动。尤其是 `api/tests/**`、`web/**/__tests__/**`、`*.spec.*`、`*.test.*`，除非用户明确要求补测试。
- 不提交 `logs/**` 的运行时变更，例如 `logs/*-audit.json`。
- 不提交 `plugin-signatures/**`、`.tools/**`、`docker/volumes/**`、本地下载目录、私钥或 token。
- 提交前必须运行 `git status --short` 和 `git diff --stat`，确认只包含本次任务相关文件。

## SSO 登录链路规则

- 修改登录、SSO、proxy、cookie、session、workspace bootstrap 时，必须重点检查：
  - `web/proxy.ts`
  - `web/app/oauth-callback/page.tsx`
  - `web/app/internal/auth-status/route.ts`
  - `web/service/sso-desktop-auth.ts`
- 浏览器登录态判断以 `/console/api/account/profile` 成功为主。不要把 `/workspaces/current` 的瞬时失败当成未登录，否则 UAT 会出现登录成功后又跳回 `/signin`。
- `/workspaces/current` 可作为元数据或延迟探测，不能作为 proxy 放行主界面的硬条件。
- 浏览器访问时不要探测本地桌面服务或 Vault Bridge；这类逻辑必须先判断桌面运行态。
- OAuth callback 里跳转 `/apps` 前要等待 session cookie 可被 `/internal/auth-status/` 读到，避免 cookie 写入时序导致回跳登录页。

## UAT 发布核对

- 发布分支必须包含最新 SSO 修复提交，特别是 `fix(sso): stabilize browser desktop login session`。
- 如果 UAT 登录后回到登录页，先对比当前发布分支与 `origin/master` 的这三个文件：
  - `web/proxy.ts`
  - `web/app/oauth-callback/page.tsx`
  - `web/app/internal/auth-status/route.ts`
- 不要把“模型调用失败”优先当作登录问题根因；登录回跳通常是 cookie/session/proxy/workspace 探测问题，和模型 provider 只会间接影响主界面加载。

## 插件签名发布规则

- 按 Dify 第三方签名校验流程处理插件包，参考 `docs/plugin-signature-cloud-deployment.md`。
- 私钥只能放在本机忽略目录 `plugin-signatures/`，禁止提交 Git，禁止上传云端。
- 可提交的公钥固定放在 `deploy/plugin-signature-keys/cheersai-plugin-signing.public.pem`。
- 云端非 Docker 部署时，插件服务读取服务器实际路径，例如 `/etc/dify/plugin-signatures/cheersai-plugin-signing.public.pem`。
- 发布安装必须使用 `.signed.difypkg`，不要把未签名原包上传到开启校验的云端。

## 推荐提交流程

```powershell
git status --short
git diff --stat
git diff -- web/proxy.ts web/app/oauth-callback/page.tsx web/app/internal/auth-status/route.ts
git add web/proxy.ts web/app/oauth-callback/page.tsx web/app/internal/auth-status/route.ts
git status --short
git commit -m "fix(sso): stabilize browser desktop login session"
```

## 禁止提交清单

```text
logs/**
plugin-signatures/**
.tools/**
docker/volumes/**
api/tests/**              # 除非用户明确要求测试变更
web/**/__tests__/**       # 除非用户明确要求测试变更
*.spec.ts
*.spec.tsx
*.test.ts
*.test.tsx
```
