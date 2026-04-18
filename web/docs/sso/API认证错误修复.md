# API 认证错误修复说明

## 问题描述

前端在未登录状态下不断请求需要认证的 API 端点,导致大量 400/401 错误:
- `GET /console/api/workspaces/current/model-providers` 
- `GET /console/api/workspaces/current/models/model-types/llm`

## 根本原因

`web/service/use-common.ts` 中的 React Query hooks 在用户未登录时也会自动执行:

```typescript
// 问题代码
export const useModelProviders = (enabled = true) => {
  return useQuery({
    queryFn: () => get('/workspaces/current/model-providers'),
    enabled,  // ❌ 没有检查用户是否已登录
  })
}
```

这些 hooks 配置了:
- `refetchOnWindowFocus: true` - 窗口获得焦点时重新请求
- `refetchOnMount: 'always'` - 每次挂载时都请求
- `refetchInterval: 5000` - 每 5 秒自动请求

导致即使在安装页面或未登录状态下,也会不断发送请求。

## 解决方案

添加认证状态检查,只有在用户已登录且有工作空间时才执行查询:

```typescript
// 修复后的代码
export const useModelProviders = (enabled = true) => {
  const { data: workspace } = useCurrentWorkspace()
  const { data: userProfile } = useUserProfile()
  return useQuery({
    queryFn: () => get('/workspaces/current/model-providers'),
    enabled: enabled && !!workspace?.id && !!userProfile?.profile?.id,  // ✅ 检查认证状态
  })
}
```

## 修改的文件

- `web/service/use-common.ts`
  - `useModelProviders` - 添加 workspace 和 userProfile 检查
  - `useModelListByType` - 添加 workspace 和 userProfile 检查

## 效果

修复后:
- ✅ 未登录用户不会触发认证 API 请求
- ✅ 安装页面不会出现 401 错误
- ✅ 只有在用户登录且有工作空间后才会请求数据
- ✅ 减少不必要的网络请求和错误日志

## 测试建议

1. 清除浏览器缓存和 cookies
2. 访问安装页面 - 应该没有 401 错误
3. 完成登录 - API 请求应该正常工作
4. 检查浏览器控制台 - 不应该有重复的 401 错误

## 相关文件

- 后端 API: `api/controllers/console/workspace/model_providers.py`
- 后端 API: `api/controllers/console/workspace/models.py`
- 认证装饰器: `api/libs/login.py`
- 诊断脚本: `api/check_auth_status.py`
