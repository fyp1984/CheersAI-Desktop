# 文件命名规则测试

## 修改说明

修改了 `getMaskedFileName` 函数，现在所有类型的文件（包括图片和需要OCR的文件）都会保持原始扩展名，只添加 `.masked` 后缀。

## 新的命名规则

### 修改前
```typescript
// 文本文件
"document.txt" → "document.masked.txt" ✅
"data.json" → "data.masked.json" ✅

// 二进制文件（PDF、Word等）
"report.pdf" → "report.masked.txt" ❌ (强制转换为txt)
"document.docx" → "document.masked.txt" ❌ (强制转换为txt)

// 图片文件
"image.jpg" → "image.masked.txt" ❌ (强制转换为txt)
"photo.png" → "photo.masked.txt" ❌ (强制转换为txt)
```

### 修改后
```typescript
// 文本文件
"document.txt" → "document.masked.txt" ✅
"data.json" → "data.masked.json" ✅

// 二进制文件（PDF、Word等）
"report.pdf" → "report.masked.pdf" ✅ (保持原扩展名)
"document.docx" → "document.masked.docx" ✅ (保持原扩展名)

// 图片文件
"image.jpg" → "image.masked.jpg" ✅ (保持原扩展名)
"photo.png" → "photo.masked.png" ✅ (保持原扩展名)

// 无扩展名文件
"README" → "README.masked.txt" ✅ (添加默认扩展名)
```

## 实际测试用例

### 支持的文件类型测试
| 原文件名 | 脱敏后文件名 | 文件类型 |
|----------|--------------|----------|
| `contract.pdf` | `contract.masked.pdf` | PDF文档 |
| `report.docx` | `report.masked.docx` | Word文档 |
| `data.xlsx` | `data.masked.xlsx` | Excel表格 |
| `presentation.pptx` | `presentation.masked.pptx` | PowerPoint |
| `photo.jpg` | `photo.masked.jpg` | JPEG图片 |
| `screenshot.png` | `screenshot.masked.png` | PNG图片 |
| `document.txt` | `document.masked.txt` | 文本文件 |
| `config.json` | `config.masked.json` | JSON文件 |
| `data.csv` | `data.masked.csv` | CSV文件 |
| `README` | `README.masked.txt` | 无扩展名 |

## 优势

### 1. 文件类型识别
- ✅ 保持原始文件扩展名，便于识别文件类型
- ✅ 系统和应用程序可以正确识别文件格式
- ✅ 用户可以直观了解文件的原始类型

### 2. 兼容性
- ✅ 与现有文件管理系统兼容
- ✅ 支持文件类型图标显示
- ✅ 便于文件分类和管理

### 3. 用户体验
- ✅ 文件名更直观，用户容易理解
- ✅ 保持文件的语义信息
- ✅ 便于批量处理和管理

## 技术实现

### 修改的函数
```typescript
function getMaskedFileName(originalName: string): string {
  const dotIdx = originalName.lastIndexOf('.')
  if (dotIdx === -1) return `${originalName}.masked.txt`
  const ext = originalName.substring(dotIdx)
  const base = originalName.substring(0, dotIdx)
  // 所有文件都保持原扩展名，只添加 .masked 后缀
  return `${base}.masked${ext}`
}
```

### 关键变化
1. **移除了文件类型判断**: 不再区分文本文件和二进制文件
2. **统一命名规则**: 所有文件都使用 `原名.masked.原扩展名` 格式
3. **保持向后兼容**: 无扩展名文件仍然添加 `.txt` 后缀

## 影响范围

### 受影响的功能
1. **文件脱敏处理** - 生成的脱敏文件名格式变化
2. **映射文件生成** - 映射关系中的文件名更新
3. **文件还原功能** - 需要适配新的文件名格式
4. **文件列表显示** - UI中显示的文件名格式变化

### 不受影响的功能
1. **文件内容处理** - 脱敏逻辑保持不变
2. **加密机制** - 加密算法和密钥管理不变
3. **文件上传** - 上传逻辑保持不变
4. **权限控制** - 安全机制保持不变

## 测试建议

### 功能测试
1. **单文件脱敏测试**
   - 测试各种文件类型的脱敏处理
   - 验证生成的文件名格式正确

2. **批量文件脱敏测试**
   - 测试混合文件类型的批量处理
   - 验证所有文件都使用正确的命名格式

3. **文件还原测试**
   - 验证新格式的脱敏文件可以正确还原
   - 测试映射文件的兼容性

### 边界测试
1. **特殊文件名测试**
   - 包含特殊字符的文件名
   - 超长文件名
   - 多个点号的文件名（如 `file.backup.txt`）

2. **无扩展名文件测试**
   - 验证默认添加 `.txt` 扩展名
   - 确保处理逻辑正确

---

**修改状态**: ✅ 已完成  
**测试状态**: 待验证  
**影响评估**: 低风险，向后兼容