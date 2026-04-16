"""
测试企业 API 获取用户 FileBay 配置
"""
import requests
from configs import dify_config

def test_get_user_gitea_config(email: str):
    """测试获取指定用户的 Gitea 配置"""
    
    # 获取 tunnel URL
    tunnel_url = dify_config.CLOUDFLARE_TUNNEL_URL or 'https://moisture-people-detail-possible.trycloudflare.com'
    enterprise_api_url = f'{tunnel_url}/inner/api/enterprise/gitea/config'
    
    print(f'\n{"="*60}')
    print(f'测试企业 API 获取用户 FileBay 配置')
    print(f'{"="*60}')
    print(f'用户邮箱: {email}')
    print(f'API 地址: {enterprise_api_url}')
    print(f'{"="*60}\n')
    
    try:
        # 调用企业 API
        print(f'正在调用: {enterprise_api_url}?email={email}')
        response = requests.get(
            enterprise_api_url,
            params={'email': email},
            timeout=10
        )
        
        print(f'\n响应状态码: {response.status_code}')
        print(f'响应头: {dict(response.headers)}')
        
        if response.status_code == 200:
            config_data = response.json()
            print(f'\n✅ 成功获取配置！')
            print(f'\n配置信息:')
            print(f'  - gitea_url: {config_data.get("gitea_url", "未设置")}')
            print(f'  - gitea_owner: {config_data.get("gitea_owner", "未设置")}')
            print(f'  - gitea_repo: {config_data.get("gitea_repo", "未设置")}')
            
            # 检查 token（不完整显示）
            token = config_data.get("gitea_token", "")
            if token:
                masked_token = token[:4] + '*' * (len(token) - 8) + token[-4:] if len(token) > 8 else '****'
                print(f'  - gitea_token: {masked_token} (长度: {len(token)})')
            else:
                print(f'  - gitea_token: 未设置')
            
            return config_data
        else:
            print(f'\n❌ 获取配置失败')
            print(f'响应内容: {response.text}')
            return None
            
    except requests.exceptions.Timeout:
        print(f'\n❌ 请求超时（10秒）')
        return None
    except requests.exceptions.ConnectionError as e:
        print(f'\n❌ 连接错误: {e}')
        return None
    except Exception as e:
        print(f'\n❌ 发生错误: {type(e).__name__}: {e}')
        return None

if __name__ == '__main__':
    # 测试指定用户
    test_email = '103456686@qq.com'
    config = test_get_user_gitea_config(test_email)
    
    if config:
        print(f'\n{"="*60}')
        print(f'测试结果: ✅ 成功')
        print(f'{"="*60}')
    else:
        print(f'\n{"="*60}')
        print(f'测试结果: ❌ 失败')
        print(f'{"="*60}')
