#!/usr/bin/env python3
"""
插件打包脚本
用于将插件打包成 .difypkg 格式
"""
import os
import sys
import yaml
import zipfile
import shutil
from pathlib import Path


def check_required_files():
    """检查必需文件"""
    print("\n[1/5] 检查必需文件...")
    
    required_files = [
        "manifest.yaml",
        "main.py",
        "requirements.txt",
        "_assets/icon.svg",
        "provider/doc_exporter.yaml",
        "provider/doc_exporter.py",
        "provider/tools/word_export.yaml",
        "provider/tools/pdf_export.yaml",
        "provider/tools/html_export.yaml",
        "provider/tools/markdown_export.yaml",
        "tools/word_export.py",
        "tools/pdf_export.py",
        "tools/html_export.py",
        "tools/markdown_export.py",
        "utils/docx_utils.py",
        "utils/pdf_utils.py",
        "utils/html_utils.py",
    ]
    
    missing = []
    for file in required_files:
        if not os.path.exists(file):
            missing.append(file)
    
    if missing:
        print(f"❌ 缺少必需文件:")
        for file in missing:
            print(f"   - {file}")
        return False
    
    print("✅ 所有必需文件存在")
    return True


def validate_manifest():
    """验证 manifest.yaml"""
    print("\n[2/5] 验证 manifest.yaml...")
    
    try:
        with open('manifest.yaml', 'r', encoding='utf-8') as f:
            manifest = yaml.safe_load(f)
        
        # 检查必需字段
        required_fields = ['version', 'type', 'author', 'label']
        for field in required_fields:
            if field not in manifest:
                print(f"❌ manifest.yaml 缺少字段: {field}")
                return False, None
        
        print("✅ manifest.yaml 格式正确")
        return True, manifest
        
    except Exception as e:
        print(f"❌ manifest.yaml 格式错误: {e}")
        return False, None


def check_dependencies():
    """检查依赖"""
    print("\n[3/5] 检查 Python 依赖...")
    
    try:
        import docx
        print("✅ python-docx 已安装")
    except ImportError:
        print("⚠️  python-docx 未安装")
    
    try:
        import markdown
        print("✅ markdown 已安装")
    except ImportError:
        print("⚠️  markdown 未安装")
    
    try:
        from bs4 import BeautifulSoup
        print("✅ beautifulsoup4 已安装")
    except ImportError:
        print("⚠️  beautifulsoup4 未安装")
    
    return True


def create_package(manifest):
    """创建插件包"""
    print("\n[4/5] 打包插件...")
    
    version = manifest.get('version', '0.0.1')
    package_name = f"file-format-converter-plugin-{version}.difypkg"
    
    # 删除旧包
    if os.path.exists(package_name):
        os.remove(package_name)
        print(f"   删除旧包: {package_name}")
    
    # 创建 ZIP 包
    with zipfile.ZipFile(package_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # 添加 manifest.yaml
        zipf.write('manifest.yaml', 'manifest.yaml')
        print(f"   添加: manifest.yaml")
        
        # 添加 _assets 目录（包含图标）
        if os.path.isdir('_assets'):
            for root, dirs, files in os.walk('_assets'):
                for file in files:
                    file_path = os.path.join(root, file)
                    arc_path = file_path.replace('\\', '/')
                    zipf.write(file_path, arc_path)
                    print(f"   添加: {arc_path}")
        
        # 添加其他必需文件
        for file in ['main.py', 'requirements.txt', 'LICENSE']:
            if os.path.exists(file):
                zipf.write(file, file)
                print(f"   添加: {file}")
        
        # 添加工具定义文件
        if os.path.isdir('provider'):
            for root, dirs, files in os.walk('provider'):
                dirs[:] = [d for d in dirs if d != '__pycache__']
                for file in files:
                    if file.endswith(('.yaml', '.py')):
                        file_path = os.path.join(root, file)
                        arc_path = file_path.replace('\\', '/')
                        zipf.write(file_path, arc_path)
                        print(f"   添加: {arc_path}")
        
        # 添加 tools 目录
        if os.path.isdir('tools'):
            for root, dirs, files in os.walk('tools'):
                dirs[:] = [d for d in dirs if d != '__pycache__']
                for file in files:
                    if file.endswith('.py'):
                        file_path = os.path.join(root, file)
                        arc_path = file_path.replace('\\', '/')
                        zipf.write(file_path, arc_path)
                        print(f"   添加: {arc_path}")
        
        # 添加 utils 目录
        if os.path.isdir('utils'):
            for root, dirs, files in os.walk('utils'):
                dirs[:] = [d for d in dirs if d != '__pycache__']
                for file in files:
                    if file.endswith('.py'):
                        file_path = os.path.join(root, file)
                        arc_path = file_path.replace('\\', '/')
                        zipf.write(file_path, arc_path)
                        print(f"   添加: {arc_path}")
    
    print(f"✅ 打包完成: {package_name}")
    return package_name


def show_package_info(package_name):
    """显示包信息"""
    print("\n[5/5] 包信息")
    
    file_size = os.path.getsize(package_name)
    file_size_mb = file_size / (1024 * 1024)
    
    abs_path = os.path.abspath(package_name)
    
    print(f"   名称: {package_name}")
    print(f"   大小: {file_size_mb:.2f} MB ({file_size} bytes)")
    print(f"   路径: {abs_path}")


def main():
    """主函数"""
    print("=" * 60)
    print("文件格式转换插件 - 打包脚本")
    print("=" * 60)
    
    # 检查必需文件
    if not check_required_files():
        return 1
    
    # 验证 manifest
    valid, manifest = validate_manifest()
    if not valid:
        return 1
    
    # 检查依赖
    check_dependencies()
    
    # 创建包
    try:
        package_name = create_package(manifest)
    except Exception as e:
        print(f"\n❌ 打包失败: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    # 显示包信息
    show_package_info(package_name)
    
    # 完成
    print("\n" + "=" * 60)
    print("✅ 打包完成！")
    print("=" * 60)
    print("\n下一步:")
    print("  1. 上传到 Dify: 登录管理后台 → 插件管理 → 上传插件")
    print(f"  2. 选择文件: {package_name}")
    print("  3. 启用插件并开始使用")
    print()
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
