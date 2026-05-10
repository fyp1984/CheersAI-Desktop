#!/usr/bin/env python3
"""
Tavily API 测试脚本

用于测试 Tavily API Key 是否配置正确并能正常工作。

使用方法：
    python test_tavily.py
"""

import os
import sys


def load_env_file():
    """加载 .env 文件中的环境变量"""
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    if os.path.exists(env_path):
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                # 跳过注释和空行
                if not line or line.startswith('#'):
                    continue
                # 解析 KEY=VALUE
                if '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    # 只设置 TAVILY_API_KEY
                    if key == 'TAVILY_API_KEY' and value:
                        os.environ[key] = value


def test_tavily_api():
    """测试 Tavily API 配置和功能"""
    
    print("=" * 60)
    print("Tavily API 测试脚本")
    print("=" * 60)
    print()
    
    # 1. 检查 tavily-python 是否已安装
    print("1️⃣  检查 tavily-python 包...")
    try:
        from tavily import TavilyClient
        print("   ✅ tavily-python 已安装")
    except ImportError:
        print("   ❌ tavily-python 未安装")
        print("   请运行: pip install tavily-python")
        return False
    print()
    
    # 2. 检查 API Key 是否配置
    print("2️⃣  检查 TAVILY_API_KEY 环境变量...")
    api_key = os.environ.get('TAVILY_API_KEY')
    if not api_key:
        print("   ❌ TAVILY_API_KEY 未配置")
        print()
        print("   请在 api/.env 文件中添加：")
        print("   TAVILY_API_KEY=tvly-your-api-key-here")
        print()
        print("   或在命令行中设置：")
        print("   export TAVILY_API_KEY=tvly-your-api-key-here  # Linux/Mac")
        print("   $env:TAVILY_API_KEY=\"tvly-your-api-key-here\"  # Windows PowerShell")
        return False
    
    # 检查 API Key 格式
    if not api_key.startswith('tvly-'):
        print(f"   ⚠️  API Key 格式可能不正确: {api_key[:10]}...")
        print("   Tavily API Key 应该以 'tvly-' 开头")
    else:
        print(f"   ✅ TAVILY_API_KEY 已配置: {api_key[:10]}...")
    print()
    
    # 3. 测试 API 连接
    print("3️⃣  测试 Tavily API 连接...")
    try:
        client = TavilyClient(api_key=api_key)
        print("   ✅ Tavily 客户端初始化成功")
    except Exception as e:
        print(f"   ❌ 客户端初始化失败: {e}")
        return False
    print()
    
    # 4. 执行测试搜索
    print("4️⃣  执行测试搜索...")
    test_query = "Python programming language"
    try:
        print(f"   搜索查询: {test_query}")
        response = client.search(
            query=test_query,
            search_depth="basic",
            max_results=3,
            include_answer=True,
        )
        
        print("   ✅ 搜索成功！")
        print()
        
        # 显示结果
        print("   📊 搜索结果：")
        print("   " + "-" * 56)
        
        if response.get('answer'):
            print(f"   📌 快速答案: {response['answer'][:100]}...")
            print()
        
        if response.get('results'):
            print(f"   找到 {len(response['results'])} 个结果：")
            for idx, result in enumerate(response['results'], 1):
                title = result.get('title', 'N/A')
                url = result.get('url', 'N/A')
                score = result.get('score', 0)
                print(f"   {idx}. {title}")
                print(f"      URL: {url}")
                print(f"      相关度: {score:.2f}")
                print()
        
        print("   " + "-" * 56)
        
    except Exception as e:
        print(f"   ❌ 搜索失败: {e}")
        print()
        
        # 提供错误诊断
        error_str = str(e).lower()
        if '401' in error_str or 'unauthorized' in error_str:
            print("   💡 诊断: API Key 无效或未授权")
            print("      - 检查 API Key 是否正确")
            print("      - 登录 https://app.tavily.com 验证 API Key")
        elif '429' in error_str or 'rate limit' in error_str:
            print("   💡 诊断: 超过配额限制")
            print("      - 登录 https://app.tavily.com 查看使用量")
            print("      - 等待下个月配额重置或升级计划")
        elif 'timeout' in error_str or 'connection' in error_str:
            print("   💡 诊断: 网络连接问题")
            print("      - 检查网络连接")
            print("      - 检查防火墙设置")
        else:
            print("   💡 请查看错误信息并访问 https://docs.tavily.com")
        
        return False
    print()
    
    # 5. 测试完成
    print("=" * 60)
    print("✅ 所有测试通过！Tavily API 配置正确且工作正常。")
    print("=" * 60)
    print()
    print("下一步：")
    print("1. 启动 Flask API: cd api && python app.py")
    print("2. 打开聊天页面: http://localhost:3000/chat")
    print("3. 勾选'联网搜索'复选框")
    print("4. 输入需要实时信息的问题进行测试")
    print()
    
    return True


if __name__ == "__main__":
    try:
        # 首先加载 .env 文件
        load_env_file()
        
        success = test_tavily_api()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n测试已取消")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
