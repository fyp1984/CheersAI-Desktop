# CheersAI Desktop 云端插件签名部署

本文档对应 Dify 第三方插件签名校验流程：
https://docs.dify.ai/zh/develop-plugin/publishing/standards/third-party-signature-verification

## 当前签名资产

已生成并校验通过的本地资产：

```text
E:\CheersAI-Desktop\plugin-signatures\cheersai-plugin-signing.private.pem
E:\CheersAI-Desktop\plugin-signatures\cheersai-plugin-signing.public.pem
E:\CheersAI-Desktop\plugin-signatures\packages\file-format-converter-plugin-0.0.17.signed.difypkg
E:\CheersAI-Desktop\plugin-signatures\packages\zhipuai_web_search.signed.difypkg
```

安全规则：

- 私钥只保存在本机 `plugin-signatures/`，不得提交 Git，不得上传服务器。
- 已签名的 `.difypkg` 包作为发布产物上传，不提交 Git。
- 公钥可以提交，仓库内固定路径为：

```text
deploy/plugin-signature-keys/cheersai-plugin-signing.public.pem
```

## 云端非 Docker 部署路径

云端不是 Docker 运行时，建议把公钥放到系统级配置目录：

```text
/etc/dify/plugin-signatures/cheersai-plugin-signing.public.pem
```

部署时从仓库复制公钥：

```bash
sudo mkdir -p /etc/dify/plugin-signatures
sudo install -m 0644 deploy/plugin-signature-keys/cheersai-plugin-signing.public.pem /etc/dify/plugin-signatures/cheersai-plugin-signing.public.pem
```

也可以直接使用仓库脚本完成公钥安装和 env 文件生成：

```bash
sudo sh deploy/install-plugin-signature-key.sh
```

该脚本会生成：

```text
/etc/dify/plugin-signatures/cheersai-plugin-signing.public.pem
/etc/dify/plugin-signature.env
```

## 插件服务环境变量

签名校验发生在 **plugin-daemon** 进程中，不在 API/Web 进程中。非 Docker 部署时，必须把下面变量配置到实际启动 plugin-daemon 的 systemd、Supervisor、PM2 或启动脚本里。

在云端插件服务的进程管理配置中加入以下环境变量。若使用 systemd，可通过 `systemctl edit <plugin-daemon-service>` 配置：

```ini
[Service]
EnvironmentFile=/etc/dify/plugin-signature.env
```

如果不使用 `EnvironmentFile`，也可以显式写三行：

```ini
[Service]
Environment="THIRD_PARTY_SIGNATURE_VERIFICATION_ENABLED=true"
Environment="THIRD_PARTY_SIGNATURE_VERIFICATION_PUBLIC_KEYS=/etc/dify/plugin-signatures/cheersai-plugin-signing.public.pem"
Environment="FORCE_VERIFYING_SIGNATURE=true"
Environment="ENFORCE_LANGGENIUS_PLUGIN_SIGNATURES=false"
```

如果云端不是 systemd 管理，把同样变量放到实际的启动脚本、Supervisor、PM2 或平台环境变量中。

配置完成后重启插件服务：

```bash
sudo systemctl daemon-reload
sudo systemctl restart <plugin-daemon-service>
```

重启后检查运行中的 plugin-daemon 是否真的读到了环境变量：

```bash
sudo sh deploy/check-plugin-signature-env.sh <plugin-daemon-service>
```

如果不是 systemd 管理，传入 PID：

```bash
sudo sh deploy/check-plugin-signature-env.sh "" <plugin-daemon-pid>
```

## 发布安装流程

1. 在本机使用私钥签名插件包：

```powershell
.\.tools\dify-plugin.exe signature sign "E:\CheersAI-Desktop\file-format-converter-plugin\file-format-converter-plugin-0.0.17.difypkg" -p "E:\CheersAI-Desktop\plugin-signatures\cheersai-plugin-signing.private.pem"
.\.tools\dify-plugin.exe signature sign "E:\Edge Download\zhipuai_web_search.difypkg" -p "E:\CheersAI-Desktop\plugin-signatures\cheersai-plugin-signing.private.pem"
```

2. 上传并安装签名后的包：

```text
E:\CheersAI-Desktop\plugin-signatures\packages\file-format-converter-plugin-0.0.17.signed.difypkg
E:\CheersAI-Desktop\plugin-signatures\packages\zhipuai_web_search.signed.difypkg
```

3. 安装前可用公钥验证：

```powershell
.\.tools\dify-plugin.exe signature verify "E:\CheersAI-Desktop\plugin-signatures\packages\file-format-converter-plugin-0.0.17.signed.difypkg" -p "E:\CheersAI-Desktop\plugin-signatures\cheersai-plugin-signing.public.pem"
.\.tools\dify-plugin.exe signature verify "E:\CheersAI-Desktop\plugin-signatures\packages\zhipuai_web_search.signed.difypkg" -p "E:\CheersAI-Desktop\plugin-signatures\cheersai-plugin-signing.public.pem"
```

当前两包均已验证通过。

## 故障判断

出现以下错误时：

```text
PluginDaemonBadRequestError: plugin verification has been enabled, and the plugin you want to install has a bad signature
```

优先检查：

- 云端安装的是 `.signed.difypkg`，不是原始 `.difypkg`。
- 变量配置在 plugin-daemon 进程上，而不是只配置在 API/Web 进程上。
- `THIRD_PARTY_SIGNATURE_VERIFICATION_PUBLIC_KEYS` 指向服务器实际存在的公钥文件。
- 插件服务重启后读取到了新的环境变量，可用 `deploy/check-plugin-signature-env.sh` 验证。
- 公钥内容与仓库 `deploy/plugin-signature-keys/cheersai-plugin-signing.public.pem` 一致。
- 如果使用 Supervisor/PM2，确认它没有覆盖或清空环境变量。
- 如果通过反向代理上传包，确认没有把 `.signed.difypkg` 解压、重打包或改写字节内容。
- 如果同时存在多个 plugin-daemon 实例，确认所有实例都加载了同一公钥。

## 临时绕过方案

不建议在生产关闭签名校验。如果必须先恢复安装能力，可仅在内网临时把 plugin-daemon 的：

```text
FORCE_VERIFYING_SIGNATURE=false
THIRD_PARTY_SIGNATURE_VERIFICATION_ENABLED=false
```

改完后重启 plugin-daemon。安装完成后应恢复校验，否则任意未签名第三方插件都可能被安装。
