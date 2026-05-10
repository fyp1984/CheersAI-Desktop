#!/usr/bin/env python3
"""
测试联网搜索功能
"""
import requests
from urllib.parse import quote

def test_duckduckgo_search(query: str):
    """测试 DuckDuckGo 搜索"""
    print(f"\n测试搜索: {query}")
    print("=" * 60)
    
    try:
        encoded_query = quote(query)
        url = f"https://api.duckduckgo.com/?q={encoded_query}&format=json&no_html=1&skip_disambig=1"
        
        print(f"请求 URL: {url}")
        
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
        
        print(f"\n响应状态: {response.status_code}")
        print(f"响应数据键: {list(data.keys())}")
        
        results = []
        
        # Abstract (main answer)
        if data.get("Abstract"):
            print(f"\n摘要: {data['Abstract']}")
            results.append(f"摘要：{data['Abstract']}")
            if data.get("AbstractURL"):
                print(f"来源: {data['AbstractURL']}")
                results.append(f"来源：{data['AbstractURL']}")
        else:
            print("\n没有找到摘要")
        
        # Related topics
        if data.get("RelatedTopics"):
            print(f"\n相关主题数量: {len(data['RelatedTopics'])}")
            results.append("\n相关信息：")
            for i, topic in enumerate(data["RelatedTopics"][:3], 1):
                if isinstance(topic, dict) and topic.get("Text"):
                    print(f"{i}. {topic['Text'][:100]}...")
                    results.append(f"{i}. {topic['Text']}")
                    if topic.get("FirstURL"):
                        results.append(f"   链接：{topic['FirstURL']}")
        else:
            print("\n没有找到相关主题")
        
        if results:
            formatted_results = "\n".join(results)
            print(f"\n格式化结果:\n{formatted_results}")
            return formatted_results
        else:
            print(f"\n未找到关于 '{query}' 的相关信息。")
            return f"未找到关于 '{query}' 的相关信息。"
            
    except Exception as e:
        print(f"\n错误: {e}")
        return f"网络搜索暂时不可用: {e}"

if __name__ == "__main__":
    # 测试几个查询
    queries = [
        "今天什么日期",
        "Python programming",
        "weather today",
        "北京天气",
    ]
    
    for query in queries:
        result = test_duckduckgo_search(query)
        print("\n" + "=" * 60 + "\n")
