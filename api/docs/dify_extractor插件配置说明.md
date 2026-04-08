# dify_extractor 插件配置说明

## 问题描述

文档处理失败，错误信息：
```
An error occurred in the langgenius/dify_extractor/dify_extractor
Error type: ConnectError
Error details: [Errno 111] Connection refused
```

## 根本原因

`dify_extractor` 插件无法连接到 Unstructured API 服务。虽然环境变量已经设置，但插件可能需要通过 Web 界面配置凭据。

## 解决方案

### 方案 1：在 Web 界面配置插件凭据（推荐）

1. 登录 Dify Web 界面
2. 进入"插件"页面
3. 找到 `dify_extractor` 插件
4. 点击"配置"或"设置"
5. 添加以下配置：
   - **Unstructured API URL**: `http://unstructured:8000/general/v0/general`
   - **API Key**: 留空（如果不需要）

### 方案 2：使用传统文档上传方式

如果插件配置困难，可以：

1. 创建新的知识库时，不要选择"RAG Pipeline"方式
2. 直接使用"上传文件"方式
3. 这样会使用 Dify 内置的文档处理器，不依赖 `dify_extractor` 插件

### 方案 3：检查并修复 Docker 网络配置

确保 Plugin Daemon 和 Unstructured 在同一个 Docker 网络中：

```bash
# 检查网络
docker network inspect dify_default

# 确保两个容器都在 dify_default 网络中
docker inspect docker-plugin_daemon-1 | grep NetworkMode
docker inspect docker-unstructured-1 | grep NetworkMode
```

## 验证

### 测试 Unstructured API

```bash
# 从宿主机测试
curl http://localhost:8000/healthcheck

# 从 Plugin Daemon 容器内测试
docker exec docker-plugin_daemon-1 curl http://unstructured:8000/healthcheck
```

### 检查环境变量

```bash
docker exec docker-plugin_daemon-1 sh -c "env | grep UNSTRUCTURED"
```

应该看到：
```
UNSTRUCTURED_API_URL=http://unstructured:8000/general/v0/general
UNSTRUCTURED_API_KEY=
```

## 当前状态

- ✅ Unstructured API 正在运行
- ✅ Plugin Daemon 可以访问 Unstructured
- ✅ 环境变量已正确设置
- ❌ `dify_extractor` 插件仍然无法连接

这说明插件可能需要通过 Web 界面配置，而不是仅依赖环境变量。

## 下一步

1. 尝试在 Web 界面配置插件凭据
2. 如果无法配置，考虑使用传统文档上传方式
3. 或者联系 Dify 社区获取 `dify_extractor` 插件的配置文档
