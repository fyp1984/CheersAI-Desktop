# FileBay 文件选择器修复说明

## 问题诊断

### 原始错误
```
GET http://localhost:3000/console/api/filebay/list-files/?path= 500 (Internal Server Error)
```

### 根本原因
经过调试发现了两个问题：

1. **Next.js 代理配置错误**
   - Next.js 配置文件 `web/next.config.ts` 中的 API 代理指向了错误的端口
   - 配置：`http://localhost:5001` 
   - 实际后端运行在：`http://localhost:9000`
   - 导致前端请求无法到达后端 API

2. **缺少 CSRF Token**
   - FileBay 文件选择器组件使用原生 `fetch` 调用 API
   - 没有添加 CSRF token 到请求头
   - Dify 的认证系统要求所有 `/console/api/*` 请求必须包含 CSRF token

## 修复方案

### 1. 修复 Next.js 代理配置
**文件**: `web/next.config.ts`

```typescript
async rewrites() {
  return [
    {
      source: '/console/api/:path*',
      destination: 'http://localhost:9000/console/api/:path*',  // 从 5001 改为 9000
    },
  ]
},
```

### 2. 添加 CSRF Token 到 FileBay 文件选择器
**文件**: `web/app/components/base/file-uploader/filebay-file-picker/index.tsx`

**添加导入**:
```typescript
import Cookies from 'js-cookie'
import { CSRF_COOKIE_NAME, CSRF_HEADER_NAME } from '@/config'
```

**修改 loadFiles 函数**:
```typescript
const loadFiles = useCallback(async (path: string) => {
  setLoading(true)
  try {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    }
    
    // Add CSRF token for authentication
    const csrfToken = Cookies.get(CSRF_COOKIE_NAME())
    if (csrfToken)
      headers[CSRF_HEADER_NAME] = csrfToken
    
    const response = await fetch(`/console/api/filebay/list-files?path=${encodeURIComponent(path)}`, {
      method: 'GET',
      headers,
      credentials: 'include',
    })
    // ... rest of the code
  }
  // ...
}, [notify])
```

## 验证步骤

1. **重启前端服务**
   - Next.js 配置更改需要重启才能生效
   - 停止并重新启动 `pnpm dev`

2. **测试 API 端点**
   ```bash
   # 测试端点是否可访问（会返回 401 因为没有认证）
   curl -v http://localhost:9000/console/api/filebay/list-files?path=
   ```

3. **在浏览器中测试**
   - 打开聊天页面
   - 点击文件上传按钮
   - 选择 "从 FileBay 选择"
   - 应该能看到文件列表加载

## 技术细节

### Dify 认证机制
Dify 使用以下认证机制保护 Console API：

1. **Session Cookie**: 用户登录后设置
2. **CSRF Token**: 
   - Cookie 名称: `csrf_token` 或 `__Host-csrf_token` (HTTPS)
   - Header 名称: `X-CSRF-Token`
   - 每个请求都必须包含

### 参考实现
可以参考 Gitea 文件服务的实现：
- `web/service/gitea.ts` - 使用 `get()` 函数自动处理认证
- `web/service/base.ts` - 基础请求函数，自动添加 CSRF token
- `web/service/fetch.ts` - 底层 fetch 封装

### 为什么不使用 service 层？
FileBay 文件选择器直接使用 `fetch` 而不是 service 层的 `get()` 函数，因为：
1. 组件需要更细粒度的错误处理
2. 需要显示加载状态
3. 需要处理特定的响应格式

但是必须手动添加 CSRF token 来模拟 service 层的行为。

## 后续改进建议

1. **统一使用 service 层**
   - 创建 `web/service/filebay.ts`
   - 使用 `get()` 函数自动处理认证
   - 简化组件代码

2. **错误处理优化**
   - 区分不同类型的错误（网络错误、认证错误、权限错误）
   - 提供更友好的错误提示

3. **配置验证**
   - 在打开文件选择器前检查 FileBay 配置是否完整
   - 如果配置缺失，引导用户到设置页面

## 相关文件

- `web/next.config.ts` - Next.js 配置
- `web/app/components/base/file-uploader/filebay-file-picker/index.tsx` - FileBay 文件选择器
- `api/controllers/console/filebay_api/filebay_files.py` - 后端 API
- `web/service/base.ts` - 基础请求服务
- `web/service/fetch.ts` - Fetch 封装
- `web/config/index.ts` - 配置常量
