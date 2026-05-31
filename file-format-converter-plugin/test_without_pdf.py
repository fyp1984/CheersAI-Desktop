#!/usr/bin/env python3
"""
简化的插件功能测试脚本（跳过 PDF）
测试 Word, HTML, Markdown 转换功能
"""
import os
import sys

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(__file__))

from utils.docx_utils import markdown_to_docx
from utils.html_utils import markdown_to_html


def test_markdown_content():
    """测试用的 Markdown 内容"""
    return """# 文件格式转换插件测试

## 简介

这是一个测试文档，用于验证文件格式转换插件的功能。

## 功能特性

### 支持的格式

1. **Word 文档** (.docx)
2. **PDF 文档** (.pdf)
3. **HTML 文档** (.html)
4. **Markdown 文档** (.md)

### 代码示例

```python
def hello_world():
    print("Hello, World!")
    return True
```

### 表格示例

| 格式 | 扩展名 | 状态 |
|------|--------|------|
| Word | .docx | ✅ |
| PDF | .pdf | ✅ |
| HTML | .html | ✅ |
| Markdown | .md | ✅ |

### 列表示例

- 项目 1
- 项目 2
  - 子项目 2.1
  - 子项目 2.2
- 项目 3

### 引用

> 这是一个引用块。
> 可以包含多行内容。

### 文本格式

这是 **粗体** 文本，这是 *斜体* 文本，这是 `代码` 文本。

---

## 结论

所有格式转换功能正常工作！
"""


def test_word_export():
    """测试 Word 导出"""
    print("\n" + "="*60)
    print("测试 Word 导出...")
    print("="*60)
    
    try:
        output_path = "测试文档.docx"
        result = markdown_to_docx(test_markdown_content(), output_path)
        
        if os.path.exists(output_path):
            file_size = os.path.getsize(output_path)
            print(f"✅ Word 导出成功: {output_path} ({file_size} bytes)")
            return True
        else:
            print(f"❌ Word 导出失败: 文件未生成")
            return False
            
    except Exception as e:
        print(f"❌ Word 导出失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_html_export():
    """测试 HTML 导出"""
    print("\n" + "="*60)
    print("测试 HTML 导出...")
    print("="*60)
    
    try:
        output_path = "测试文档.html"
        result = markdown_to_html(test_markdown_content(), output_path, include_css=True)
        
        if os.path.exists(output_path):
            file_size = os.path.getsize(output_path)
            print(f"✅ HTML 导出成功: {output_path} ({file_size} bytes)")
            return True
        else:
            print(f"❌ HTML 导出失败: 文件未生成")
            return False
            
    except Exception as e:
        print(f"❌ HTML 导出失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_markdown_export():
    """测试 Markdown 导出"""
    print("\n" + "="*60)
    print("测试 Markdown 导出...")
    print("="*60)
    
    try:
        output_path = "测试文档.md"
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(test_markdown_content())
        
        if os.path.exists(output_path):
            file_size = os.path.getsize(output_path)
            print(f"✅ Markdown 导出成功: {output_path} ({file_size} bytes)")
            return True
        else:
            print(f"❌ Markdown 导出失败: 文件未生成")
            return False
            
    except Exception as e:
        print(f"❌ Markdown 导出失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主测试函数"""
    print("\n" + "="*60)
    print("文件格式转换插件 - 功能测试")
    print("="*60)
    
    # 检查依赖
    print("\n检查依赖...")
    try:
        import docx
        print("✅ python-docx 已安装")
    except ImportError:
        print("❌ python-docx 未安装")
        
    try:
        import markdown
        print("✅ markdown 已安装")
    except ImportError:
        print("❌ markdown 未安装")
        
    try:
        from bs4 import BeautifulSoup
        print("✅ beautifulsoup4 已安装")
    except ImportError:
        print("❌ beautifulsoup4 未安装")
    
    print("⚠️  PDF 导出跳过（需要 GTK 系统依赖）")
    
    # 运行测试
    results = {
        "Word 导出": test_word_export(),
        "HTML 导出": test_html_export(),
        "Markdown 导出": test_markdown_export()
    }
    
    # 汇总结果
    print("\n" + "="*60)
    print("测试结果汇总")
    print("="*60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name}: {status}")
    
    print(f"\n总计: {passed}/{total} 测试通过")
    print("注意: PDF 导出需要安装 GTK 系统依赖，参考 INSTALLATION.md")
    
    if passed == total:
        print("\n🎉 所有测试通过！插件功能正常。")
        print("\n生成的文件:")
        for filename in ["测试文档.docx", "测试文档.html", "测试文档.md"]:
            if os.path.exists(filename):
                abs_path = os.path.abspath(filename)
                print(f"  - {abs_path}")
        return 0
    else:
        print(f"\n⚠️  {total - passed} 个测试失败，请检查错误信息。")
        return 1


if __name__ == "__main__":
    sys.exit(main())
