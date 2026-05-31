# 更新日志

所有重要的项目更改都将记录在此文件中。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，
并且本项目遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

## [未发布]

### 计划功能
- [ ] 支持更多格式（EPUB, RTF）
- [ ] 批量转换功能
- [ ] 自定义模板支持
- [ ] 图片处理和优化
- [ ] 目录自动生成

## [0.0.1] - 2026-05-24

### 新增
- Word 文档导出功能 (.docx)
- PDF 文档导出功能 (.pdf)
- HTML 文档导出功能 (.html)
- Markdown 文档导出功能 (.md)
- 完整的 Markdown 语法支持
- 自定义样式系统
- 文件名清理和验证
- 临时文件自动清理
- 中英文双语支持

### 技术特性
- 基于 python-docx 的 Word 生成
- 基于 WeasyPrint 的 PDF 生成
- 基于 markdown 库的 HTML 生成
- 支持代码高亮
- 支持表格格式化
- 支持引用块样式
- 内存优化（256MB）

### 文档
- 完整的 README 文档
- 使用示例
- 安装指南
- 故障排除指南
