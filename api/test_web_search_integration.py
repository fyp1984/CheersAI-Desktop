#!/usr/bin/env python3
"""
测试联网搜索功能集成

这个脚本直接测试 simple_chat.py 中的 _perform_web_search 方法
"""

import os
import sys

# 添加项目路径
sys.path.insert(0, os.path.dirname(__file__))

# 加载环境变量
from dotenv import load_dotenv
load_dotenv()

def test_web_search():
    """测试联网搜索功能"""
    print("=" * 60)
    print("测试联网搜索功能集成")
    print("=" * 60)
    print()
    
    # 导入 SimpleChatApi
    from controllers.console.chat.simple_chat import SimpleChatApi
    
    # 创建实例
    api = SimpleChatApi()
    
    # 测试搜索
    test_query = "今天娱乐圈有什么新闻"
    print(f"🔍 测试查询: {test_query}")
    print()
    
    try:
        results, success = api._perform_web_search(test_query)
        
        if success:
            print("✅ 搜索成功！")
            print()
            print("📊 搜索结果：")
            print("-" * 60)
            print(results)
            print("-" * 60)
        else:
            print("❌ 搜索失败")
            print(f"返回结果: {results}")
    
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print()
    print("=" * 60)
    print("✅ 测试完成")
    print("=" * 60)
    return True


if __name__ == "__main__":
    try:
        success = test_web_search()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n测试已取消")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
