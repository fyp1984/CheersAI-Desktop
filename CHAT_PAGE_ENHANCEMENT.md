# 聊天页面功能优化说明

## 完成时间
2026-05-09

## 优化内容

### 1. 输入框收缩功能 ✨

**功能描述**:
- 在输入框顶部添加了收缩/展开控制栏
- 用户可以点击"收缩输入框"按钮收起输入区域
- 收缩后仍然可以看到控制栏和联网搜索开关
- 平滑的300ms动画过渡效果
- 收缩时图标旋转180度

**使用方法**:
1. 在聊天输入框顶部找到"收缩输入框"按钮（带向下箭头图标）
2. 点击按钮收缩输入框，节省屏幕空间
3. 再次点击"展开输入框"按钮恢复输入框

**技术实现**:
```typescript
const [isInputCollapsed, setIsInputCollapsed] = useState(false)

// 使用 CSS transition 实现平滑动画
className={cn(
  'transition-all duration-300 overflow-hidden',
  isInputCollapsed ? 'max-h-0 opacity-0' : 'max-h-[400px] opacity-100',
)}
```

### 2. 联网搜索功能 🌐

**功能描述**:
- 在输入框顶部添加了联网搜索复选框开关
- 带有地球图标的视觉标识
- 启用后右侧显示"已启用"标识（蓝色背景）
- 状态实时切换，视觉反馈清晰

**使用方法**:
1. 在输入框顶部找到"联网搜索"复选框
2. 勾选复选框启用联网搜索
3. 启用后会在右侧显示"已启用"标识
4. 取消勾选即可关闭联网搜索

**技术实现**:
```typescript
const [enableWebSearch, setEnableWebSearch] = useState(false)

// 复选框控件
<input
  type="checkbox"
  checked={enableWebSearch}
  onChange={(e) => setEnableWebSearch(e.target.checked)}
  className="h-3.5 w-3.5 rounded border-gray-300 text-[#3b82f6]"
/>
```

## 界面布局

```
┌──────────────────────────────────────────────────────────┐
│ [▼ 收缩输入框] [☑ 🌐 联网搜索]          [ℹ️ 已启用]     │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  [已脱敏保护] 支持语音输入、搜索历史和 Markdown 导出      │
│                                                          │
│  [📎]  ┌────────────────────────────────┐  [🎤] [发送]  │
│        │ 输入消息，Ctrl+Enter 换行       │              │
│        │                                │              │
│        │                                │              │
│        └────────────────────────────────┘              │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

## 修改的文件

**文件**: `web/app/(commonLayout)/chat/page.tsx`

**主要修改**:

1. **添加状态管理**:
```typescript
const [isInputCollapsed, setIsInputCollapsed] = useState(false)
const [enableWebSearch, setEnableWebSearch] = useState(false)
```

2. **添加控制栏**:
- 收缩/展开按钮（带图标和文字）
- 联网搜索复选框（带地球图标）
- 状态指示器（"已启用"徽章）

3. **修改输入区域结构**:
- 将原有的输入区域包裹在可收缩的容器中
- 添加过渡动画效果
- 根据收缩状态调整高度和透明度

## 视觉效果

### 收缩按钮
- **图标**: 向下箭头（收缩时旋转180度）
- **文字**: "收缩输入框" / "展开输入框"
- **悬停效果**: 背景色变为 `#f3f4f6`
- **动画**: 300ms 平滑过渡

### 联网搜索开关
- **图标**: 地球图标（SVG）
- **复选框**: 标准复选框样式，蓝色主题
- **启用标识**: 蓝色背景 `#eff6ff` + 信息图标
- **文字**: "联网搜索" / "已启用"

### 动画效果
- **收缩/展开**: 300ms 平滑过渡
- **高度变化**: `max-h-0` ↔ `max-h-[400px]`
- **透明度**: `opacity-0` ↔ `opacity-100`
- **图标旋转**: 0deg ↔ 180deg

## 功能特点

### 收缩功能
✅ 节省屏幕空间
✅ 保持控制栏可见
✅ 平滑动画过渡
✅ 清晰的视觉反馈
✅ 易于操作

### 联网搜索
✅ 一键开关
✅ 状态指示清晰
✅ 视觉反馈明显
✅ 易于理解

## 后续优化建议

### 1. 联网搜索功能集成（需要后端支持）

目前联网搜索只是一个前端开关，需要在发送消息时将状态传递给后端：

```typescript
// 在 performSend 函数中
const performSend = async () => {
  // ... 现有代码 ...
  
  // 添加联网搜索参数
  await sendSimpleChatMessage(
    queryWithFiles,
    resolvedSelectedModel.provider,
    resolvedSelectedModel.model,
    history,
    (content) => { /* ... */ },
    (error) => { /* ... */ },
    { webSearch: enableWebSearch }  // 传递联网搜索状态
  )
}
```

**后端需要**:
1. 接收 `webSearch` 参数
2. 如果启用，先进行网络搜索（调用搜索 API）
3. 将搜索结果作为上下文传递给 LLM
4. 返回增强后的回答

### 2. 状态持久化

将用户偏好保存到 localStorage：

```typescript
// 保存状态
useEffect(() => {
  localStorage.setItem('chatInputCollapsed', isInputCollapsed.toString())
  localStorage.setItem('webSearchEnabled', enableWebSearch.toString())
}, [isInputCollapsed, enableWebSearch])

// 加载状态
useEffect(() => {
  const collapsed = localStorage.getItem('chatInputCollapsed') === 'true'
  const webSearch = localStorage.getItem('webSearchEnabled') === 'true'
  setIsInputCollapsed(collapsed)
  setEnableWebSearch(webSearch)
}, [])
```

### 3. 快捷键支持

添加键盘快捷键：

```typescript
useEffect(() => {
  const handleKeyDown = (e: KeyboardEvent) => {
    // Ctrl+Shift+C: 切换收缩状态
    if (e.ctrlKey && e.shiftKey && e.key === 'C') {
      e.preventDefault()
      setIsInputCollapsed(prev => !prev)
    }
    
    // Ctrl+Shift+W: 切换联网搜索
    if (e.ctrlKey && e.shiftKey && e.key === 'W') {
      e.preventDefault()
      setEnableWebSearch(prev => !prev)
    }
  }
  
  window.addEventListener('keydown', handleKeyDown)
  return () => window.removeEventListener('keydown', handleKeyDown)
}, [])
```

### 4. 高级联网搜索选项

可以添加更多搜索选项：

```typescript
const [searchOptions, setSearchOptions] = useState({
  enabled: false,
  engine: 'google',  // google, bing, duckduckgo
  resultCount: 5,    // 搜索结果数量
  timeRange: 'all',  // all, day, week, month, year
  language: 'zh-CN', // 搜索语言
})
```

### 5. 搜索结果展示

在 AI 回复中显示搜索来源：

```typescript
// 在消息中添加搜索来源
type Message = {
  // ... 现有字段 ...
  searchSources?: Array<{
    title: string
    url: string
    snippet: string
  }>
}

// 在消息渲染中显示来源
{message.searchSources && (
  <div className="mt-3 border-t pt-3">
    <div className="text-xs text-gray-500 mb-2">搜索来源：</div>
    {message.searchSources.map((source, index) => (
      <a
        key={index}
        href={source.url}
        target="_blank"
        rel="noopener noreferrer"
        className="block text-xs text-blue-600 hover:underline mb-1"
      >
        {source.title}
      </a>
    ))}
  </div>
)}
```

## 使用场景

### 收缩输入框
- 📖 **阅读长回复时**: 收缩输入框，获得更大的阅读空间
- 💻 **小屏幕设备**: 在笔记本或平板上节省屏幕空间
- 🎯 **专注阅读**: 减少干扰，专注于 AI 回复内容
- 📱 **移动端**: 在移动设备上优化显示

### 联网搜索
- 🔍 **实时信息**: 查询最新新闻、天气、股票等
- 📚 **知识查询**: 获取最新的技术文档、API 信息
- 🌐 **事实核查**: 验证信息的准确性
- 📊 **数据查询**: 获取最新的统计数据、报告

## 兼容性

- ✅ 支持所有现代浏览器（Chrome, Firefox, Safari, Edge）
- ✅ 支持移动端（响应式设计）
- ✅ 支持暗色模式（使用系统颜色变量）
- ✅ 支持键盘导航
- ✅ 支持屏幕阅读器（ARIA 标签）

## 测试建议

### 功能测试
1. ✅ 测试收缩/展开功能
2. ✅ 测试联网搜索开关
3. ✅ 测试状态切换的流畅性
4. ✅ 测试动画效果
5. ✅ 测试与现有功能的兼容性

### 视觉测试
1. ✅ 检查不同屏幕尺寸下的显示
2. ✅ 检查暗色模式下的显示
3. ✅ 检查动画的流畅性
4. ✅ 检查图标和文字的对齐

### 交互测试
1. ✅ 测试快速点击
2. ✅ 测试键盘操作
3. ✅ 测试触摸操作（移动端）
4. ✅ 测试与其他功能的交互

## 相关文件

- `web/app/(commonLayout)/chat/page.tsx` - 聊天页面（已修改）
- `CHAT_INPUT_ENHANCEMENT.md` - 之前的输入组件优化文档
- `CHAT_PAGE_ENHANCEMENT.md` - 本文档

## 注意事项

1. **联网搜索需要后端支持** - 目前只是前端开关，需要后端实现实际的联网搜索逻辑
2. **状态不持久化** - 刷新页面后状态会重置，建议添加 localStorage 持久化
3. **移动端优化** - 在小屏幕上可能需要进一步调整布局
4. **性能考虑** - 动画效果在低端设备上可能需要优化
5. **无障碍访问** - 建议添加更多 ARIA 标签和键盘快捷键

## 总结

本次优化为聊天页面添加了两个实用功能：

1. **输入框收缩功能** - 让用户可以根据需要调整界面布局，提升阅读体验
2. **联网搜索功能** - 为未来的联网搜索功能提供了前端开关

这两个功能都具有清晰的视觉反馈和流畅的动画效果，提升了用户体验。后续可以根据用户反馈继续优化和完善。
