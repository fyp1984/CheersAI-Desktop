# 修复文件预览 URL 端口错误

## 🐛 错误信息

```
Error downloading file: Reached maximum retries (3) for URL 
http://localhost:5001/files/9db3172d-265f-403d-80ee-080bfe63fa7a/file-preview?timestamp=1778525527&nonce=b104e18daf3146344f0c593b0765edbe&sign=W8yIGJvIzkKPudZHCfdgKVA0etluyjrHqH3TxuasbE8%3D
```

## 🔍 问题分析

### 错误原因
后端生成的文件预览 URL 指向了 `http://localhost:5001`，但实际的后端 API 运行在 `9000` 端口。

### 为什么会这样？
1. 后端使用 `FILES_URL` 环境变量来生成文件访问 URL
2. `.env` 文件中 `FILES_URL` 配置为 `http://localhost:5001`
3. 但我们的后端实际运行在 `9000` 端口
4. 导致生成的文件 URL 无法访问

### 影响范围
所有需要访问文件的功能都会受影响：
- 文件预览
- 文件下载
- 图片显示
- 文档处理
- 工作流中的文件节点

## ✅ 解决方案

### 修改 .env 文件

**文件**: `api/.env`

**修改内容**:
```env
# 修改前
CONSOLE_API_URL=http://localhost:5001
SERVICE_API_URL=http://localhost:5001
FILES_URL=http://localhost:5001

# 修改后
CONSOLE_API_URL=http://localhost:9000
SERVICE_API_URL=http://localhost:9000
FILES_URL=http://localhost:9000
```

### 完整的服务 URL 配置

```env
# === 服务 URL 配置 (本地开发) ===
CONSOLE_API_URL=http://localhost:9000
CONSOLE_WEB_URL=http://localhost:3000
SERVICE_API_URL=http://localhost:9000
APP_WEB_URL=http://localhost:3000
FILES_URL=http://localhost:9000
INTERNAL_FILES_URL=http://127.0.0.1:8080
```

### 重启后端服务

修改 `.env` 文件后，必须重启后端服务才能使配置生效：

```bash
# 停止当前的后端进程
# 然后重新启动
cd api
uv run waitress-serve --host=127.0.0.1 --port=9000 --threads=4 app:app
```

## 📊 相关配置说明

### FILES_URL
- **作用**: 生成文件访问 URL 的基础地址
- **使用场景**: 
  - 文件预览 URL
  - 文件下载 URL
  - 图片 URL
  - 签名 URL 生成

### CONSOLE_API_URL
- **作用**: Console API 的基础地址
- **使用场景**: 
  - 前端调用后端 API
  - API 文档生成
  - 内部服务调用

### SERVICE_API_URL
- **作用**: Service API 的基础地址
- **使用场景**: 
  - 应用 API 调用
  - Webhook 回调
  - 外部服务集成

### INTERNAL_FILES_URL
- **作用**: 内部文件访问地址（用于 Docker 容器间通信）
- **使用场景**: 
  - Plugin Daemon 访问文件
  - 容器间文件传输
  - 内部服务文件访问

## 🔄 文件 URL 生成流程

```
文件上传
  ↓
保存到存储（本地/S3/等）
  ↓
生成文件记录（upload_file_id）
  ↓
生成签名 URL
  ├─ 使用 FILES_URL 作为基础地址
  ├─ 添加文件 ID
  ├─ 添加时间戳、nonce、签名
  └─ 生成完整 URL
  ↓
返回给前端
  ↓
前端使用 URL 访问文件
  ↓
后端验证签名并返回文件
```

### 示例 URL 结构

```
http://localhost:9000/files/{upload_file_id}/file-preview?timestamp={ts}&nonce={nonce}&sign={signature}
```

- `http://localhost:9000` - 来自 FILES_URL
- `/files/{upload_file_id}/file-preview` - 文件预览路径
- `timestamp` - 时间戳（防止重放攻击）
- `nonce` - 随机数（增加安全性）
- `sign` - 签名（验证请求合法性）

## 🧪 验证修复

### 1. 检查配置
```bash
# 查看 .env 文件
cat api/.env | grep FILES_URL
# 应该显示: FILES_URL=http://localhost:9000
```

### 2. 测试文件上传
1. 上传一个文件（从 FileBay 或本地）
2. 检查返回的 URL
3. 确认 URL 包含 `http://localhost:9000`

### 3. 测试文件预览
1. 点击已上传的文件
2. 应该能正常预览
3. 不应该有 "Reached maximum retries" 错误

### 4. 检查网络请求
打开浏览器开发者工具 → Network：
- 文件请求应该指向 `http://localhost:9000`
- 状态码应该是 200
- 应该能正常下载文件内容

## 🎯 其他需要注意的端口配置

### Next.js 代理配置
**文件**: `web/next.config.ts`

```typescript
async rewrites() {
  return [
    {
      source: '/console/api/:path*',
      destination: 'http://localhost:9000/console/api/:path*',  // 确保是 9000
    },
  ]
}
```

### 前端环境变量
**文件**: `web/.env`

检查是否有相关的 API URL 配置，确保指向正确的端口。

## 📝 端口使用总结

| 服务 | 端口 | 说明 |
|------|------|------|
| 前端 (Next.js) | 3000 | Web 界面 |
| 后端 API | 9000 | Flask API（之前是 5001） |
| PostgreSQL | 5432 | 数据库 |
| Redis | 6700 | 缓存和消息队列 |
| Weaviate | 8081 | 向量数据库 |
| Plugin Daemon | 5012 | 插件服务 |
| Unstructured | 8000 | 文档解析服务 |

## ⚠️ 重要提示

### 1. 环境一致性
确保所有配置文件中的端口都一致：
- `api/.env` - 后端配置
- `web/next.config.ts` - 前端代理配置
- `docker-compose.dev.yaml` - Docker 配置（如果使用）

### 2. 重启服务
修改 `.env` 文件后，必须重启相关服务：
- 后端 API 服务
- 前端开发服务（如果修改了 next.config.ts）

### 3. 清除缓存
如果问题仍然存在，尝试：
- 清除浏览器缓存
- 重启浏览器
- 清除 Redis 缓存

## ✅ 完成状态

- ✅ 修改 `api/.env` 中的 `FILES_URL` 为 `http://localhost:9000`
- ✅ 修改 `CONSOLE_API_URL` 为 `http://localhost:9000`
- ✅ 修改 `SERVICE_API_URL` 为 `http://localhost:9000`
- ✅ 重启后端 API 服务
- ✅ 后端成功启动在 9000 端口

现在文件预览 URL 应该指向正确的端口，文件访问功能应该正常工作了！

## 🚀 测试建议

1. **上传文件测试**
   - 从 FileBay 上传文件
   - 从本地上传文件
   - 粘贴文件链接

2. **文件预览测试**
   - 预览图片文件
   - 预览文档文件
   - 预览 PDF 文件

3. **工作流测试**
   - 在工作流中使用文件
   - Doc Extractor 节点
   - 文件处理节点

4. **聊天测试**
   - 在聊天中发送文件
   - 查看历史消息中的文件
   - 下载聊天中的文件

所有功能应该都能正常工作！🎉
