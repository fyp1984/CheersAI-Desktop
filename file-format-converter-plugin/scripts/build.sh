#!/bin/bash
# 构建和打包插件脚本

set -e

echo "🔨 开始构建文件格式转换插件..."

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 检查 Python 版本
echo "📋 检查 Python 版本..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
required_version="3.12"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then 
    echo -e "${RED}❌ 错误: 需要 Python $required_version 或更高版本${NC}"
    echo -e "${YELLOW}当前版本: $python_version${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Python 版本检查通过: $python_version${NC}"

# 检查依赖
echo "📦 检查依赖..."
if ! pip3 show dify-plugin > /dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  未找到 dify-plugin，正在安装...${NC}"
    pip3 install dify-plugin
fi

# 安装项目依赖
echo "📥 安装项目依赖..."
pip3 install -r requirements.txt

# 运行代码检查
echo "🔍 运行代码检查..."
if command -v flake8 &> /dev/null; then
    echo "运行 flake8..."
    flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics || true
else
    echo -e "${YELLOW}⚠️  flake8 未安装，跳过代码检查${NC}"
fi

# 运行格式化
echo "✨ 格式化代码..."
if command -v black &> /dev/null; then
    black . --check || true
else
    echo -e "${YELLOW}⚠️  black 未安装，跳过代码格式化${NC}"
fi

# 清理旧的构建文件
echo "🧹 清理旧的构建文件..."
rm -rf build/ dist/ *.egg-info
rm -f *.difypkg

# 创建打包目录
echo "📁 创建打包目录..."
mkdir -p dist

# 打包插件
echo "📦 打包插件..."
if command -v dify &> /dev/null; then
    dify plugin package . -o dist/
    echo -e "${GREEN}✅ 插件打包成功！${NC}"
    echo -e "${GREEN}📦 输出文件: dist/*.difypkg${NC}"
else
    echo -e "${YELLOW}⚠️  dify CLI 未安装${NC}"
    echo -e "${YELLOW}手动打包: 将所有文件压缩为 .difypkg 格式${NC}"
    
    # 手动创建打包文件
    zip -r dist/file-format-converter-0.0.1.difypkg \
        manifest.yaml \
        *.yaml \
        requirements.txt \
        main.py \
        tools/ \
        utils/ \
        icon.png \
        README.md \
        LICENSE \
        -x "*.pyc" -x "__pycache__/*" -x ".git/*" -x "*.egg-info/*"
    
    echo -e "${GREEN}✅ 手动打包完成！${NC}"
fi

# 显示文件信息
echo ""
echo "📊 构建信息:"
echo "----------------------------------------"
ls -lh dist/ 2>/dev/null || echo "dist/ 目录为空"
echo "----------------------------------------"

# 验证打包文件
echo ""
echo "🔍 验证打包文件..."
if [ -f dist/*.difypkg ]; then
    echo -e "${GREEN}✅ 找到打包文件${NC}"
    unzip -l dist/*.difypkg | head -20
else
    echo -e "${RED}❌ 未找到打包文件${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}🎉 构建完成！${NC}"
echo ""
echo "下一步:"
echo "1. 测试插件: python3 main.py"
echo "2. 安装插件: 在 Dify 中导入 dist/*.difypkg"
echo "3. 发布插件: 上传到 Dify 插件市场"
