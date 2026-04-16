# API 认证错误修复 - 完整版

## 问题描述

前端在未登录状态下不断发送 API 请求，导致后端返回 401 Unauthorized 错误：
- `GET /console/api/workspaces/current/model-providers`
- `GET /console/api/workspaces/current/models/model-types/llm`

错误日志显示每 5 秒重复一次，说明有定时轮询机制在未认证时仍在运行。

## 根本原因

React Query hooks 在用户未登录时仍然执行 API 调用，原因是：

1. **`use-common.ts` 中的 hooks 配置不当**：
   - `useModelProviders` 和 `useModelListByType` 有激进的 refetch 设置
   - `refetchOnWindowFocus: true` - 窗口获得焦点时重新获取
   - `refetchOnMount: 'always'` - 每次挂载时都获取
   - `refetchInterval: 5000` - 每 5 秒自动刷新

2. **`provider-context.tsx` 调用 hooks 时缺少认证检查**：
   - `useModelListByType(ModelTypeEnum.textGeneration)` 没有传递 `enabled` 参数
   - 即使用户未登录，hook 仍会执行

## 修复方案

### 修复 1: `use-common.ts` - 添加认证检查

```typescript
export const useModelProviders = (enabled = true) => {
  const { data: workspace } = useCurrentWorkspace()
  const { data: userProfile } = useUserProfile()
  return useQuery<{ data: ModelProvider[] }>({
    queryKey: commonQueryKeys.modelProviders(workspace?.id, userProfile?.profile?.id),
    queryFn: () => get<{ data: ModelProvider[] }>('/workspaces/current/model-providers'),
    refetchOnWindowFocus: true,
    refetchOnMount: 'always',
    refetchInterval: 5000,
    enabled: enabled && !!workspace?.id && !!userProfile?.profile?.id, // ✅ 添加认证检查
  })
}

export const useModelListByType = (type: ModelTypeEnum, enabled = true) => {
  const { data: workspace } = useCurrentWorkspace()
  const { data: userProfile } = useUserProfile()
  return useQuery<{ data: Model[] }>({
    queryKey: commonQueryKeys.modelList(type, workspace?.id, userProfile?.profile?.id),
    queryFn: () => get<{ data: Model[] }>(`/workspaces/current/models/model-types/${type}`),
    enabled: enabled && !!workspace?.id && !!userProfile?.profile?.id, // ✅ 添加认证检查
    refetchOnWindowFocus: true,
    refetchOnMount: 'always',
    refetchInterval: 5000,
  })
}
```

### 修复 2: `provider-context.tsx` - 传递 enabled 参数

```typescript
export const ProviderContextProvider = ({
  children,
}: ProviderContextProviderProps) => {
  const queryClient = useQueryClient()
  const canManageModelProviders = useAppContextSelector((state) => {
    const capabilities = state.currentWorkspace.capabilities || []
    return capabilities.includes('desktop_model_provider_manage') || capabilities.includes('desktop_model_manage')
  })
  const { data: providersData } = useModelProviders(canManageModelProviders)
  const { data: textGenerationModelList } = useModelListByType(
    ModelTypeEnum.textGeneration, 
    canManageModelProviders // ✅ 传递 enabled 参数
  )
  // ...
}
```

## 修复逻辑

1. **双重检查机制**：
   - Hook 内部检查：`!!workspace?.id && !!userProfile?.profile?.id`
   - 调用方检查：`canManageModelProviders`（基于用户权限）

2. **只有同时满足以下条件时才执行 API 调用**：
   - 用户已登录（有 userProfile）
   - 工作空间已加载（有 workspace）
   - 用户有管理模型的权限（canManageModelProviders）

3. **React Query 的 `enabled` 参数**：
   - 当 `enabled: false` 时，query 不会执行
   - 当依赖数据变为可用时，query 会自动执行

## 验证步骤

### 1. 重启前端开发服务器

虽然 Turbopack 支持热重载，但对于 hooks 的修改，建议重启：

```bash
# 在 web 目录下
# 停止当前服务器 (Ctrl+C)
npm run dev
# 或
yarn dev
```

### 2. 清除浏览器缓存

- 打开开发者工具 (F12)
- 右键点击刷新按钮
- 选择"清空缓存并硬性重新加载"

### 3. 检查网络请求

在未登录状态下：
- 打开开发者工具 -> Network 标签
- 过滤 `/console/api/workspaces/current/`
- 应该看不到任何请求

在登录后：
- 应该能看到正常的 API 请求
- 返回 200 状态码

### 4. 检查控制台错误

- 不应该再看到 401 错误
- 不应该看到 "Failed to fetch" 错误

## 其他需要注意的地方

### `moderation-setting-modal.tsx`

这个文件也调用了 `useModelProviders()`，但因为它在 Modal 组件内部，只有在打开模态框时才会执行，所以优先级较低。如果需要，可以添加类似的检查：

```typescript
const { data: workspace } = useCurrentWorkspace()
const { data: userProfile } = useUserProfile()
const { data: modelProviders, isPending: isLoading, refetch: refetchModelProviders } = useModelProviders(
  !!workspace?.id && !!userProfile?.profile?.id
)
```

## 技术细节

### React Query 的 enabled 参数工作原理

```typescript
useQuery({
  queryKey: ['data'],
  queryFn: fetchData,
  enabled: false, // query 不会执行
})
```

- `enabled: false` 时，query 处于"暂停"状态
- 不会发送网络请求
- 不会触发 refetch
- 当 `enabled` 变为 `true` 时，query 会自动执行

### 为什么需要检查 workspace?.id 和 userProfile?.profile?.id

1. **workspace?.id**：
   - 后端 API 需要当前工作空间 ID
   - 未登录时，`useCurrentWorkspace()` 返回 undefined
   - 检查 `workspace?.id` 确保工作空间已加载

2. **userProfile?.profile?.id**：
   - 确保用户已认证
   - 未登录时，`useUserProfile()` 返回 undefined
   - 检查 `userProfile?.profile?.id` 确保用户信息已加载

3. **canManageModelProviders**：
   - 基于用户权限的额外检查
   - 即使用户已登录，也可能没有管理模型的权限
   - 避免无权限用户发送无用请求

## 预期效果

修复后：
- ✅ 未登录用户不会触发模型相关 API 请求
- ✅ 不会看到 401 错误日志
- ✅ 登录后，API 请求正常工作
- ✅ 减少不必要的网络请求，提升性能
- ✅ 减少后端日志噪音

## 相关文件

- `CheersAI-Desktop/web/service/use-common.ts` - Hook 定义
- `CheersAI-Desktop/web/context/provider-context.tsx` - Hook 调用
- `CheersAI-Desktop/web/context/app-context.tsx` - 认证状态管理
- `CheersAI-Desktop/api/controllers/console/workspace/model_providers.py` - 后端端点
- `CheersAI-Desktop/api/controllers/console/workspace/models.py` - 后端端点

## 修复时间

2026-04-16 15:45
