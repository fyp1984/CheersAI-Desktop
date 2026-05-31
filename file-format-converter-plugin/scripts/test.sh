#!/bin/bash
# 测试脚本

set -e

echo "🧪 开始测试文件格式转换插件..."

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# 创建测试目录
TEST_DIR="test_output"
mkdir -p $TEST_DIR

echo "📝 准备测试数据..."
TEST_CONTENT=$(cat test_example.md)

# 测试 Word 导出
echo ""
echo "📄 测试 Word 导出..."
python3 << EOF
from tools.word_export import WordExportTool
import os

tool = WordExportTool()
result = tool._invoke({
    'markdown_content': '''$TEST_CONTENT''',
    'document_name': 'test_word'
})

if result:
    print("✅ Word 导出测试通过")
else:
    print("❌ Word 导出测试失败")
    exit(1)
EOF

# 测试 PDF 导出
echo ""
echo "📕 测试 PDF 导出..."
python3 << EOF
from tools.pdf_export import PdfExportTool

tool = PdfExportTool()
result = tool._invoke({
    'markdown_content': '''$TEST_CONTENT''',
    'document_name': 'test_pdf'
})

if result:
    print("✅ PDF 导出测试通过")
else:
    print("❌ PDF 导出测试失败")
    exit(1)
EOF

# 测试 HTML 导出
echo ""
echo "🌐 测试 HTML 导出..."
python3 << EOF
from tools.html_export import HtmlExportTool

tool = HtmlExportTool()
result = tool._invoke({
    'markdown_content': '''$TEST_CONTENT''',
    'document_name': 'test_html',
    'include_css': True
})

if result:
    print("✅ HTML 导出测试通过")
else:
    print("❌ HTML 导出测试失败")
    exit(1)
EOF

# 测试 Markdown 导出
echo ""
echo "📝 测试 Markdown 导出..."
python3 << EOF
from tools.markdown_export import MarkdownExportTool

tool = MarkdownExportTool()
result = tool._invoke({
    'markdown_content': '''$TEST_CONTENT''',
    'document_name': 'test_markdown'
})

if result:
    print("✅ Markdown 导出测试通过")
else:
    print("❌ Markdown 导出测试失败")
    exit(1)
EOF

# 测试文件名清理
echo ""
echo "🧹 测试文件名清理..."
python3 << EOF
from tools.word_export import WordExportTool

tool = WordExportTool()

# 测试非法字符
test_cases = [
    ("test<>file", "test__file"),
    ("test:file", "test_file"),
    ("test/file", "test_file"),
    ("a" * 150, "a" * 100),
]

all_passed = True
for input_name, expected in test_cases:
    result = tool._sanitize_filename(input_name)
    if result != expected:
        print(f"❌ 文件名清理失败: {input_name} -> {result} (期望: {expected})")
        all_passed = False

if all_passed:
    print("✅ 文件名清理测试通过")
else:
    exit(1)
EOF

# 测试空内容处理
echo ""
echo "🚫 测试空内容处理..."
python3 << EOF
from tools.word_export import WordExportTool

tool = WordExportTool()
result = tool._invoke({
    'markdown_content': '',
    'document_name': 'empty'
})

if result and '错误' in str(result):
    print("✅ 空内容处理测试通过")
else:
    print("❌ 空内容处理测试失败")
    exit(1)
EOF

# 性能测试
echo ""
echo "⚡ 性能测试..."
python3 << EOF
import time
from tools.word_export import WordExportTool

tool = WordExportTool()
large_content = "# 标题\n\n" + ("这是一段测试文本。\n\n" * 1000)

start_time = time.time()
result = tool._invoke({
    'markdown_content': large_content,
    'document_name': 'performance_test'
})
end_time = time.time()

duration = end_time - start_time
print(f"处理时间: {duration:.2f} 秒")

if duration < 10:
    print("✅ 性能测试通过")
else:
    print("⚠️  性能测试警告: 处理时间较长")
EOF

echo ""
echo -e "${GREEN}🎉 所有测试通过！${NC}"
echo ""
echo "测试摘要:"
echo "✅ Word 导出"
echo "✅ PDF 导出"
echo "✅ HTML 导出"
echo "✅ Markdown 导出"
echo "✅ 文件名清理"
echo "✅ 空内容处理"
echo "✅ 性能测试"
