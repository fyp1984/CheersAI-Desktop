# 工作流文件上传添加 FileBay 按钮 - 完成

## ✅ 需求

在工作流的文件上传界面中，在 "从本地上传" 和 "粘贴文件链接" 两个按钮之间添加一个 "从 FileBay 选择" 按钮。

## 🎯 实现位置

**组件**: `web/app/components/base/file-uploader/file-uploader-in-attachment/index.tsx`

这个组件用于：
- 工作流节点的文件输入（如 Doc Extractor）
- 工作流运行时的文件上传
- 所有需要附件式文件上传的场景

## 🔧 修改内容

### 1. 添加图标导入

```typescript
import {
  RiLink,
  RiUploadCloud2Line,
  RiDatabase2Line,  // 新增：FileBay 图标
} from '@remixicon/react'
```

### 2. 在选项列表中添加 FileBay 选项

```typescript
const options = [
  {
    value: TransferMethod.local_file,
    label: t('fileUploader.uploadFromComputer', { ns: 'common' }),
    icon: <RiUploadCloud2Line className="h-4 w-4" />,
  },
  {
    value: 'filebay' as const,  // 新增
    label: '从 FileBay 选择',    // 新增
    icon: <RiDatabase2Line className="h-4 w-4" />,  // 新增
  },
  {
    value: TransferMethod.remote_url,
    label: t('fileUploader.pasteFileLink', { ns: 'common' }),
    icon: <RiLink className="h-4 w-4" />,
  },
]
```

### 3. 在渲染逻辑中处理 FileBay 选项

```typescript
const renderOption = useCallback((option: Option) => {
  if (option.value === TransferMethod.local_file && fileConfig?.allowed_file_upload_methods?.includes(TransferMethod.local_file))
    return renderButton(option)

  // 新增：FileBay 选项
  if (option.value === 'filebay') {
    return (
      <FileFromLinkOrLocal
        key={option.value}
        showFromLocal={false}
        showFromLink={false}
        showFromFileBay={true}  // 只显示 FileBay 选项
        trigger={renderTrigger(option)}
        fileConfig={fileConfig}
      />
    )
  }

  if (option.value === TransferMethod.remote_url && fileConfig?.allowed_file_upload_methods?.includes(TransferMethod.remote_url)) {
    return (
      <FileFromLinkOrLocal
        key={option.value}
        showFromLocal={false}
        trigger={renderTrigger(option)}
        fileConfig={fileConfig}
      />
    )
  }
}, [renderButton, renderTrigger, fileConfig])
```

## 📊 按钮顺序

修改后的按钮顺序（从左到右）：
1. **从本地上传** (RiUploadCloud2Line 图标)
2. **从 FileBay 选择** (RiDatabase2Line 图标) ← 新增
3. **粘贴文件链接** (RiLink 图标)

## 🎨 UI 效果

```
┌─────────────────────────────────────────────────────────────┐
│  Upload Document 上传文档                                    │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ 📤 从本地上传 │  │ 🗄️ 从FileBay │  │ 🔗 粘贴文件链接│     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## 🔄 工作流程

### 用户操作流程：
1. 用户在工作流中添加需要文件输入的节点（如 Doc Extractor）
2. 点击 "从 FileBay 选择" 按钮
3. 弹出 FileBay 文件选择器
4. 浏览目录，选择文件
5. 点击确认
6. 文件上传到 Dify 存储
7. 文件显示在附件列表中
8. 运行工作流时使用该文件

### 技术流程：
```
点击 "从 FileBay 选择"
  ↓
FileFromLinkOrLocal 组件
  ├─ showFromLocal={false}
  ├─ showFromLink={false}
  └─ showFromFileBay={true}
  ↓
FileBayFilePicker 组件
  ↓
选择文件 → 调用 /console/api/filebay/upload-file
  ↓
后端下载文件并上传到 Dify 存储
  ↓
返回文件信息
  ↓
添加到文件列表
  ↓
显示在附件区域
```

## 📁 相关组件

### 组件层级：
```
FileUploaderInAttachmentWrapper (容器)
  └─ FileUploaderInAttachment (主组件)
      ├─ FileFromLinkOrLocal (文件来源选择)
      │   └─ FileBayFilePicker (FileBay 文件选择器)
      └─ FileItem (文件项显示)
```

### 文件列表：
- `web/app/components/base/file-uploader/file-uploader-in-attachment/index.tsx` - 主组件（已修改）
- `web/app/components/base/file-uploader/file-from-link-or-local/index.tsx` - 文件来源选择
- `web/app/components/base/file-uploader/filebay-file-picker/index.tsx` - FileBay 文件选择器
- `api/controllers/console/filebay_api/filebay_files.py` - 后端 API

## 🧪 测试场景

### 1. Doc Extractor 节点
1. 创建工作流
2. 添加 Doc Extractor 节点
3. 点击 "运行一次"
4. 在文件输入区域应该看到三个按钮
5. 点击 "从 FileBay 选择"
6. 选择文件并上传
7. 运行工作流

### 2. 其他文件输入节点
测试所有支持文件输入的节点：
- Start 节点（文件输入）
- Parameter Extractor
- 任何自定义的文件输入节点

### 3. 多文件上传
1. 选择支持多文件的节点
2. 从 FileBay 上传第一个文件
3. 再次从 FileBay 上传第二个文件
4. 验证两个文件都显示在列表中

### 4. 文件类型限制
1. 配置节点只接受特定文件类型（如只接受 PDF）
2. 尝试从 FileBay 上传不支持的文件类型
3. 验证错误提示

## ✨ 特性

### 1. 无条件显示
- FileBay 按钮始终显示，不受 `allowed_file_upload_methods` 限制
- 这是因为 FileBay 是内部文件系统，不同于外部 URL

### 2. 独立配置
- FileBay 选项独立于 `local_file` 和 `remote_url`
- 可以与其他上传方式共存

### 3. 统一体验
- 使用相同的文件选择器组件
- 使用相同的上传流程
- 使用相同的文件显示方式

## 🎯 与聊天输入的区别

| 特性 | 聊天输入 | 工作流附件 |
|------|---------|-----------|
| 组件 | `FileUploaderInChatInput` | `FileUploaderInAttachment` |
| 按钮样式 | 单个图标按钮 | 三个并排按钮 |
| FileBay 显示 | 始终显示 | 始终显示 |
| 本地上传 | 根据配置 | 根据配置 |
| 粘贴链接 | 根据配置 | 根据配置 |

## 🔍 调试信息

### 检查按钮是否显示
1. 打开浏览器开发者工具
2. 检查元素，查找包含 "从 FileBay 选择" 的按钮
3. 确认按钮有正确的图标和样式

### 检查点击事件
1. 点击 "从 FileBay 选择" 按钮
2. 应该弹出 FileBay 文件选择器
3. 如果没有弹出，检查控制台错误

### 检查文件上传
1. 选择文件后点击确认
2. 查看网络请求：`POST /console/api/filebay/upload-file`
3. 检查响应是否包含文件信息
4. 确认文件显示在附件列表中

## 📝 注意事项

### 1. 配置要求
- 用户必须先配置 FileBay 设置
- 如果未配置，上传时会显示错误提示

### 2. 文件类型
- FileBay 按钮支持所有文件类型
- 但上传后仍会检查节点的文件类型限制

### 3. 文件大小
- 遵循系统的文件大小限制
- 超过限制会显示错误提示

### 4. 权限
- 需要用户登录
- 需要有效的 FileBay 访问权限

## 🚀 后续优化

### 1. 条件显示
可以根据用户是否配置 FileBay 来决定是否显示按钮：
```typescript
const hasFileBayConfig = useFileBayConfig() // 需要实现

if (hasFileBayConfig) {
  // 显示 FileBay 按钮
}
```

### 2. 图标优化
可以使用更合适的图标来表示 FileBay：
- 当前使用：`RiDatabase2Line`
- 可选：自定义 SVG 图标

### 3. 翻译支持
添加多语言支持：
```typescript
{
  value: 'filebay' as const,
  label: t('fileUploader.uploadFromFileBay', { ns: 'common' }),
  icon: <RiDatabase2Line className="h-4 w-4" />,
}
```

需要在翻译文件中添加：
```json
// web/i18n/zh-Hans/common.json
"fileUploader.uploadFromFileBay": "从 FileBay 选择"

// web/i18n/en-US/common.json
"fileUploader.uploadFromFileBay": "Select from FileBay"
```

## ✅ 完成状态

- ✅ 添加 FileBay 按钮到工作流文件上传界面
- ✅ 按钮显示在正确的位置（中间）
- ✅ 点击按钮打开 FileBay 文件选择器
- ✅ 文件上传功能正常工作
- ✅ 文件显示在附件列表中
- ✅ 工作流可以使用上传的文件
- ✅ 前端编译成功，无错误

**所有功能已完成！** 🎉

## 📸 效果预览

用户现在可以在工作流的文件上传界面看到三个按钮：
1. 从本地上传（左）
2. **从 FileBay 选择（中）** ← 新增
3. 粘贴文件链接（右）

点击 "从 FileBay 选择" 后，会弹出 FileBay 文件选择器，用户可以浏览和选择文件，选择后文件会自动上传到 Dify 存储并显示在附件列表中。
