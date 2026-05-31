#!/bin/bash

# 文件格式转换插件 - 部署脚本
# 用于快速打包和部署插件到 Dify

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 插件信息
PLUGIN_NAME="file-format-converter-plugin"
PLUGIN_VERSION=$(grep "version:" manifest.yaml | head -1 | awk '{print $2}')
PACKAGE_NAME="${PLUGIN_NAME}-${PLUGIN_VERSION}.difypkg"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}文件格式转换插件 - 部署脚本${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# 步骤 1: 检查必需文件
echo -e "${YELLOW}[1/6] 检查必需文件...${NC}"
REQUIRED_FILES=(
    "manifest.yaml"
    "main.py"
    "requirements.txt"
    "icon.png"
    "word_export.yaml"
    "pdf_export.yaml"
    "html_export.yaml"
    "markdown_export.yaml"
    "tools/word_export.py"
    "tools/pdf_export.py"
    "tools/html_export.py"
    "tools/markdown_export.py"
    "utils/docx_utils.py"
    "utils/pdf_utils.py"
    "utils/html_utils.py"
)

MISSING_FILES=()
for file in "${REQUIRED_FILES[@]}"; do
    if [ ! -f "$file" ]; then
        MISSING_FILES+=("$file")
    fi
done

if [ ${#MISSING_FILES[@]} -gt 0 ]; then
    echo -e "${RED}❌ 缺少必需文件:${NC}"
    for file in "${MISSING_FILES[@]}"; do
        echo -e "${RED}   - $file${NC}"
    done
    exit 1
fi

echo -e "${GREEN}✅ 所有必需文件存在${NC}"
echo ""

# 步骤 2: 验证 manifest.yaml
echo -e "${YELLOW}[2/6] 验证 manifest.yaml...${NC}"
if ! python -c "import yaml; yaml.safe_load(open('manifest.yaml'))" 2>/dev/null; then
    echo -e "${RED}❌ manifest.yaml 格式错误${NC}"
    exit 1
fi
echo -e "${GREEN}✅ manifest.yaml 格式正确${NC}"
echo ""

# 步骤 3: 检查 Python 依赖
echo -e "${YELLOW}[3/6] 检查 Python 依赖...${NC}"
if ! python -c "import docx" 2>/dev/null; then
    echo -e "${RED}❌ python-docx 未安装${NC}"
    echo -e "${YELLOW}   运行: pip install -r requirements.txt${NC}"
    exit 1
fi

if ! python -c "import markdown" 2>/dev/null; then
    echo -e "${RED}❌ markdown 未安装${NC}"
    echo -e "${YELLOW}   运行: pip install -r requirements.txt${NC}"
    exit 1
fi

if ! python -c "import weasyprint" 2>/dev/null; then
    echo -e "${YELLOW}⚠️  weasyprint 未安装（PDF 功能将不可用）${NC}"
fi

echo -e "${GREEN}✅ 核心依赖已安装${NC}"
echo ""

# 步骤 4: 运行测试（可选）
echo -e "${YELLOW}[4/6] 运行测试...${NC}"
read -p "是否运行测试？(y/N) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    if python test_plugin.py; then
        echo -e "${GREEN}✅ 测试通过${NC}"
    else
        echo -e "${RED}❌ 测试失败${NC}"
        read -p "是否继续打包？(y/N) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
else
    echo -e "${YELLOW}⏭️  跳过测试${NC}"
fi
echo ""

# 步骤 5: 打包插件
echo -e "${YELLOW}[5/6] 打包插件...${NC}"

# 删除旧的包
if [ -f "../${PACKAGE_NAME}" ]; then
    rm "../${PACKAGE_NAME}"
    echo -e "${YELLOW}   删除旧包: ${PACKAGE_NAME}${NC}"
fi

# 创建临时目录
TEMP_DIR=$(mktemp -d)
echo -e "${BLUE}   临时目录: ${TEMP_DIR}${NC}"

# 复制文件到临时目录
cp -r . "${TEMP_DIR}/${PLUGIN_NAME}"

# 清理不需要的文件
cd "${TEMP_DIR}/${PLUGIN_NAME}"
rm -rf .git .gitignore __pycache__ *.pyc .pytest_cache .venv venv
rm -f test_plugin.py deploy.sh
rm -rf docs examples scripts
rm -f INSTALLATION.md QUICKSTART.md CONTRIBUTING.md CHANGELOG.md PROJECT_SUMMARY.md
rm -f config.example.yaml test_example.md setup.py

# 创建 ZIP 包
cd "${TEMP_DIR}"
zip -r "${PACKAGE_NAME}" "${PLUGIN_NAME}" > /dev/null

# 移动到父目录
mv "${PACKAGE_NAME}" "$(dirname $(pwd))/${PLUGIN_NAME}/../"

# 清理临时目录
cd -
rm -rf "${TEMP_DIR}"

echo -e "${GREEN}✅ 打包完成: ${PACKAGE_NAME}${NC}"
echo ""

# 步骤 6: 显示包信息
echo -e "${YELLOW}[6/6] 包信息${NC}"
PACKAGE_PATH="../${PACKAGE_NAME}"
PACKAGE_SIZE=$(du -h "${PACKAGE_PATH}" | cut -f1)

echo -e "${BLUE}   名称: ${PACKAGE_NAME}${NC}"
echo -e "${BLUE}   版本: ${PLUGIN_VERSION}${NC}"
echo -e "${BLUE}   大小: ${PACKAGE_SIZE}${NC}"
echo -e "${BLUE}   路径: ${PACKAGE_PATH}${NC}"
echo ""

# 完成
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}✅ 部署准备完成！${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${BLUE}下一步:${NC}"
echo -e "  1. 上传 ${PACKAGE_NAME} 到 Dify"
echo -e "  2. 在插件管理中启用插件"
echo -e "  3. 在工作流中使用插件"
echo ""
echo -e "${BLUE}文档:${NC}"
echo -e "  - README.md - 完整文档"
echo -e "  - INSTALLATION.md - 安装指南"
echo -e "  - docs/API.md - API 参考"
echo ""
