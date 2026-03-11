# 对话应用沙箱文件上传功能

## 功能概述

对话应用现在使用与工作流相同的沙箱文件选择机制，确保安全性和一致性：

- **沙箱模式**：只能从预先脱敏的沙箱文件中选择
- **统一体验**：与工作流文件翻译功能使用相同的文件选择器
- **安全保障**：所有文件都经过脱敏处理，防止敏感信息泄露

## 主要特性

### 1. 沙箱文件选择器
- 使用 `SandboxFilePicker` 组件，与工作流保持一致
- 显示沙箱路径和文件列表
- 支持多文件选择
- 文件类型过滤

### 2. 智能文件内容处理
- **文本文件**：自动读取并包含完整内容到AI prompt中
- **二进制文件**：显示文件信息（名称、大小、类型）
- **支持格式**：`.txt, .json, .csv, .md` 等文本格式会被完整读取

### 3. 安全模式
- 移除了普通文件上传选项
- 强制使用沙箱文件，确保数据安全
- 所有文件都标记为"沙箱文件"

### 4. AI文件内容识别
- 文本文件内容会自动包含在发送给AI的prompt中
- AI可以直接分析、处理文件内容
- 支持多文件同时处理

## 技术实现

### 前端组件

#### 沙箱文件选择器集成
```typescript
import { SandboxFilePicker } from '@/app/components/base/sandbox-file-picker'

// 处理沙箱文件选择
const handleSandboxFilesSelected = async (selectedFiles: File[]) => {
  const newFiles: UploadedFile[] = []
  
  for (const file of selectedFiles) {
    let content = ''
    if (file.type.startsWith('text/') || file.type === 'application/json') {
      content = await file.text()
    }
    
    newFiles.push({
      id: Date.now().toString(),
      name: file.name,
      size: file.size,
      type: file.type,
      isDesensitized: true,
      content: content,
    })
  }
  
  setUploadedFiles(prev => [...prev, ...newFiles])
}
```

#### AI Prompt构建
```typescript
let fullPrompt = userMessage.content

if (uploadedFiles.length > 0) {
  const fileContents = await Promise.all(
    uploadedFiles.map(async (file) => {
      const content = await readFileContent(file)
      return `\n\n--- 文件: ${file.name} ---\n${content}\n--- 文件结束 ---`
    })
  )
  fullPrompt += '\n\n以下是用户上传的文件内容：' + fileContents.join('')
}
```

### 沙箱安全上下文

#### 上下文提供者
- 应用根布局已配置 `SandboxSecurityProvider`
- 自动管理沙箱路径和安全设置
- 支持localStorage持久化

#### 使用方式
```typescript
import { useSandboxSecurity } from '@/context/sandbox-security-context'

const { sandboxPath, isConfigured } = useSandboxSecurity()
```

## 使用方法

### 1. 沙箱文件选择
1. **点击附件按钮** → 打开沙箱文件选择器
2. **浏览文件列表** → 查看所有可用的脱敏文件
3. **选择文件** → 支持单选或多选
4. **确认选择** → 文件添加到对话中

### 2. 文件内容处理
- **文本文件**：内容会在选择时自动读取
- **AI分析**：文件内容包含在发送给AI的prompt中
- **多文件**：所有文件内容按顺序添加

### 3. 安全保障
- **沙箱隔离**：只能访问预先脱敏的文件
- **路径验证**：防止路径遍历攻击
- **内容过滤**：只有安全的文件类型会被处理

## 与工作流的一致性

### 1. 相同的组件
- 使用相同的 `SandboxFilePicker` 组件
- 相同的UI设计和交互逻辑
- 统一的文件选择体验

### 2. 相同的安全机制
- 相同的沙箱路径配置
- 相同的文件访问控制
- 相同的安全上下文管理

### 3. 相同的后端API
- 使用相同的沙箱文件列表API
- 使用相同的文件读取API
- 统一的错误处理机制

## 配置要求

### 1. 沙箱路径配置
- 需要在「脱敏沙箱 → 沙箱配置」中设置沙箱路径
- 路径会自动保存到localStorage
- 支持路径验证和测试

### 2. 后端服务
- 需要启动数据脱敏后端服务
- API端点：`http://localhost:5001/console/api/data-masking/sandbox/`
- 支持文件列表和文件读取功能

## 故障排查

### 1. 沙箱路径未配置
**错误**：显示"沙箱路径未配置"
**解决**：在脱敏沙箱模块中配置正确的沙箱路径

### 2. 无法加载文件列表
**错误**：显示"无法加载沙箱文件列表"
**解决**：确认后端服务已启动，检查API连接

### 3. 文件内容读取失败
**错误**：文件显示但AI看不到内容
**解决**：检查文件格式是否为支持的文本类型

### 4. 沙箱目录为空
**错误**：显示"沙箱目录中没有文件"
**解决**：先在数据脱敏模块中处理文件

## 测试验证

### 1. 基本文件选择测试
```
1. 点击附件按钮
2. 验证显示沙箱文件选择器
3. 选择一个文本文件
4. 确认文件显示在对话中
```

### 2. AI文件内容分析测试
```
1. 选择一个包含文本内容的文件
2. 发送消息："请分析这个文件的内容"
3. 验证AI回复中包含对文件内容的分析
```

### 3. 多文件处理测试
```
1. 选择多个文本文件
2. 发送消息："比较这些文件的内容"
3. 验证AI能够同时处理多个文件
```

## 已更新的文件

- ✅ `web/app/(commonLayout)/chat/page.tsx` - 集成SandboxFilePicker
- ✅ `FILE_UPLOAD_FEATURE.md` - 更新功能说明文档

## 功能状态

- ✅ 沙箱文件选择器集成
- ✅ 与工作流保持一致的用户体验
- ✅ AI文件内容识别和分析
- ✅ 安全模式强制执行
- ✅ 多文件处理支持

---

**功能状态**: ✅ 完全实现，与工作流文件翻译功能保持一致