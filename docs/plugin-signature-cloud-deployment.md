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

## 插件服务环境变量

在云端插件服务的进程管理配置中加入以下环境变量。若使用 systemd，可通过 `systemctl edit <plugin-daemon-service>` 配置：

```ini
[Service]
Environment="THIRD_PARTY_SIGNATURE_VERIFICATION_ENABLED=true"
Environment="THIRD_PARTY_SIGNATURE_VERIFICATION_PUBLIC_KEYS=/etc/dify/plugin-signatures/cheersai-plugin-signing.public.pem"
Environment="FORCE_VERIFYING_SIGNATURE=true"
```

如果云端不是 systemd 管理，把同样三个环境变量放到实际的启动脚本、Supervisor、PM2 或平台环境变量中。

配置完成后重启插件服务：

```bash
sudo systemctl daemon-reload
sudo systemctl restart <plugin-daemon-service>
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
- `THIRD_PARTY_SIGNATURE_VERIFICATION_PUBLIC_KEYS` 指向服务器实际存在的公钥文件。
- 插件服务重启后读取到了新的环境变量。
- 公钥内容与仓库 `deploy/plugin-signature-keys/cheersai-plugin-signing.public.pem` 一致。
