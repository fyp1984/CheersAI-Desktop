# 前端 Token 配额显示 - 实施说明

## 📋 概述

已在前端的 **Token 计费页面** 中添加了 **配额管理** 标签页，用户可以在设置中查看和管理 Token 配额。

## 🎯 功能位置

**路径**: 设置 → Token 计费 → 配额管理

```
设置页面
  └─ Token 计费
      ├─ Token 计费（原有）
      └─ 配额管理（新增）✨
```

## ✨ 新增功能

### 1. 配额管理标签页

在 Token 计费页面添加了两个标签页：
- **Token 计费** - 原有的计费统计功能
- **配额管理** - 新增的配额管理功能

### 2. 配额状态卡片

显示当前配额的实时状态：
- ✅ **配额充足** - 绿色徽章，显示"使用云端模型"
- ⚠️ **配额已用完** - 黄色徽章，显示"已切换到本地模型"
- 🔄 **刷新按钮** - 手动刷新配额信息
- 📊 **进度条** - 可视化显示配额使用情况
  - 绿色：使用率 < 70%
  - 黄色：使用率 70-90%
  - 红色：使用率 > 90%

### 3. 配额详情卡片

显示 4 个关键指标：
- **总使用量** - 本周期已使用的 Token 数
- **请求次数** - 本周期的 API 调用次数
- **输入 Token** - Prompt 使用的 Token 数
- **输出 Token** - 生成内容使用的 Token 数

### 4. 模型使用详情表格

显示各模型的使用情况：
- 模型名称（provider/model）
- Token 使用量
- 请求次数
- 使用占比（带进度条）

### 5. 配额配置信息

显示当前生效的配额规则：
- 配额名称
- 时间间隔（每小时/每天/每周/每月）
- 配额上限
- 状态（激活/暂停/已超额）
- 描述
- 云端模型列表
- 本地模型列表（超额后使用）

### 6. 周期信息

显示当前配额周期：
- 开始时间
- 结束时间
- 超额时间（如果已超额）

## 📁 文件结构

```
web/app/components/header/account-setting/token-billing-page/
├── index.tsx                    # 主页面（已更新）
└── quota-management.tsx         # 配额管理组件（新增）
```

## 🔧 技术实现

### 1. API 调用

```typescript
// 检查配额
fetch('/console/api/token-quota/check', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ tokens_to_use: 0 })
})
```

### 2. 自动刷新

- 每 60 秒自动刷新一次配额信息
- 用户可以手动点击刷新按钮

### 3. 响应式设计

- 移动端：单列布局
- 平板：2 列布局
- 桌面：4 列布局

## 🎨 UI 设计

### 颜色方案

- **主色**: #3b82f6 (品牌蓝)
- **成功**: 绿色徽章和进度条
- **警告**: 黄色徽章和进度条
- **错误**: 红色徽章和进度条

### 组件样式

- 使用 CheersAI UI 规范
- 圆角卡片设计
- 阴影效果
- 渐变背景

## 📊 数据展示

### 配额状态

```typescript
interface QuotaCheckResult {
  within_quota: boolean           // 是否在配额内
  remaining_tokens: number        // 剩余 Token 数
  should_use_local: boolean       // 是否应该使用本地模型
  quota_config: QuotaConfig       // 配额配置
  current_usage: QuotaUsage       // 当前使用情况
}
```

### 配额配置

```typescript
interface QuotaConfig {
  id: string
  name: string                    // 配额名称
  interval_type: string           // 时间间隔类型
  token_limit: number             // Token 配额上限
  cloud_models: Array<Model>      // 云端模型列表
  local_models: Array<Model>      // 本地模型列表
  status: string                  // 状态
}
```

### 使用记录

```typescript
interface QuotaUsage {
  total_tokens: number            // 总 Token 数
  input_tokens: number            // 输入 Token 数
  output_tokens: number           // 输出 Token 数
  request_count: number           // 请求次数
  is_exceeded: boolean            // 是否已超额
  model_usage_details: Record     // 模型使用详情
}
```

## 🚀 使用方式

### 1. 访问页面

1. 登录系统
2. 点击右上角头像
3. 选择"设置"
4. 点击"Token 计费"
5. 切换到"配额管理"标签页

### 2. 查看配额状态

- 页面顶部显示配额状态卡片
- 绿色徽章表示配额充足
- 黄色徽章表示配额已用完

### 3. 查看使用详情

- 向下滚动查看 4 个关键指标卡片
- 查看模型使用详情表格
- 查看配额配置信息

### 4. 刷新数据

- 点击右上角的刷新按钮
- 或等待自动刷新（每 60 秒）

## 📱 响应式布局

### 移动端（< 768px）
- 单列布局
- 卡片堆叠显示
- 表格横向滚动

### 平板（768px - 1280px）
- 2 列布局
- 卡片并排显示

### 桌面（> 1280px）
- 4 列布局
- 最佳视觉效果

## 🎯 用户体验

### 1. 实时反馈
- 配额状态实时更新
- 进度条动画效果
- 加载状态提示

### 2. 清晰的视觉层次
- 重要信息突出显示
- 使用颜色区分状态
- 合理的间距和布局

### 3. 易于理解
- 中文界面
- 清晰的标签和说明
- 直观的图表和进度条

## 🔍 状态说明

### 配额充足
```
✅ 配额充足
使用云端模型
剩余: 95,000 tokens
```

### 配额不足
```
⚠️ 配额已用完
已切换到本地模型
剩余: 0 tokens
```

## 📈 进度条颜色

- **绿色** (0-70%): 配额充足
- **黄色** (70-90%): 配额紧张
- **红色** (90-100%): 配额即将用完

## 🎨 徽章颜色

- **绿色徽章**: 激活状态、配额充足
- **黄色徽章**: 警告状态、配额紧张
- **红色徽章**: 错误状态、配额已超额
- **灰色徽章**: 暂停状态

## 🔄 自动刷新机制

```typescript
useEffect(() => {
  fetchQuotaInfo()
  // 每 60 秒刷新一次
  const interval = setInterval(fetchQuotaInfo, 60000)
  return () => clearInterval(interval)
}, [])
```

## 🎯 下一步优化（可选）

### 短期
- [ ] 添加配额编辑功能
- [ ] 添加配额历史趋势图
- [ ] 添加配额告警设置

### 中期
- [ ] 添加配额购买功能
- [ ] 添加配额转移功能
- [ ] 添加多租户配额管理

### 长期
- [ ] AI 驱动的配额优化建议
- [ ] 配额使用预测
- [ ] 成本优化建议

## 📝 注意事项

1. **API 权限**: 确保用户有权限访问配额 API
2. **错误处理**: 网络错误时显示友好提示
3. **性能优化**: 避免频繁刷新，使用合理的刷新间隔
4. **数据安全**: 不在前端存储敏感配额信息

## 🎉 完成状态

- ✅ 配额管理组件创建完成
- ✅ 集成到 Token 计费页面
- ✅ 标签页切换功能
- ✅ 配额状态显示
- ✅ 使用详情展示
- ✅ 模型使用统计
- ✅ 配额配置信息
- ✅ 自动刷新机制
- ✅ 响应式布局

## 📞 技术支持

如有问题，请参考：
- 后端 API 文档: `TOKEN_QUOTA_SYSTEM.md`
- 集成指南: `TOKEN_QUOTA_INTEGRATION_GUIDE.md`
- 流程图: `TOKEN_QUOTA_FLOW_DIAGRAM.md`

---

**前端配额显示功能已完成！** 🎉

用户现在可以在设置的 Token 计费页面中查看和管理 Token 配额了！
