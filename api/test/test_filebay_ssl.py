#!/usr/bin/env python3
"""测试 FileBay SSL 连接"""
import sys
import ssl
import socket
import requests
import urllib3

# 禁用 SSL 警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

FILEBAY_URL = "uat-filebay.cheersai.cloud"
FILEBAY_PORT = 443


def test_socket_connection():
    """测试基本 socket 连接"""
    print("\n" + "=" * 80)
    print("测试 1: 基本 Socket 连接")
    print("=" * 80)
    
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        sock.connect((FILEBAY_URL, FILEBAY_PORT))
        print(f"✓ Socket 连接成功: {FILEBAY_URL}:{FILEBAY_PORT}")
        sock.close()
        return True
    except Exception as e:
        print(f"✗ Socket 连接失败: {e}")
        return False


def test_ssl_connection():
    """测试 SSL 连接"""
    print("\n" + "=" * 80)
    print("测试 2: SSL 连接")
    print("=" * 80)
    
    try:
        context = ssl.create_default_context()
        
        with socket.create_connection((FILEBAY_URL, FILEBAY_PORT), timeout=10) as sock:
            with context.wrap_socket(sock, server_hostname=FILEBAY_URL) as ssock:
                print(f"✓ SSL 连接成功")
                print(f"  SSL 版本: {ssock.version()}")
                print(f"  加密套件: {ssock.cipher()}")
                
                cert = ssock.getpeercert()
                print(f"  证书主题: {cert.get('subject')}")
                print(f"  证书颁发者: {cert.get('issuer')}")
                print(f"  证书有效期: {cert.get('notBefore')} - {cert.get('notAfter')}")
                return True
    except ssl.SSLError as e:
        print(f"✗ SSL 错误: {e}")
        return False
    except Exception as e:
        print(f"✗ 连接失败: {e}")
        return False


def test_ssl_no_verify():
    """测试不验证证书的 SSL 连接"""
    print("\n" + "=" * 80)
    print("测试 3: SSL 连接（不验证证书）")
    print("=" * 80)
    
    try:
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        
        with socket.create_connection((FILEBAY_URL, FILEBAY_PORT), timeout=10) as sock:
            with context.wrap_socket(sock, server_hostname=FILEBAY_URL) as ssock:
                print(f"✓ SSL 连接成功（未验证证书）")
                print(f"  SSL 版本: {ssock.version()}")
                return True
    except Exception as e:
        print(f"✗ 连接失败: {e}")
        return False


def test_requests_with_verify():
    """测试 requests 库（验证证书）"""
    print("\n" + "=" * 80)
    print("测试 4: Requests 库（验证证书）")
    print("=" * 80)
    
    try:
        response = requests.get(
            f"https://{FILEBAY_URL}/api/v1/version",
            timeout=10
        )
        print(f"✓ 请求成功")
        print(f"  状态码: {response.status_code}")
        print(f"  响应: {response.text[:200]}")
        return True
    except requests.exceptions.SSLError as e:
        print(f"✗ SSL 错误: {e}")
        return False
    except Exception as e:
        print(f"✗ 请求失败: {e}")
        return False


def test_requests_no_verify():
    """测试 requests 库（不验证证书）"""
    print("\n" + "=" * 80)
    print("测试 5: Requests 库（不验证证书）")
    print("=" * 80)
    
    try:
        response = requests.get(
            f"https://{FILEBAY_URL}/api/v1/version",
            verify=False,
            timeout=10
        )
        print(f"✓ 请求成功")
        print(f"  状态码: {response.status_code}")
        print(f"  响应: {response.text[:200]}")
        return True
    except Exception as e:
        print(f"✗ 请求失败: {e}")
        return False


def test_http_connection():
    """测试 HTTP 连接（非加密）"""
    print("\n" + "=" * 80)
    print("测试 6: HTTP 连接（非加密）")
    print("=" * 80)
    
    try:
        response = requests.get(
            f"http://{FILEBAY_URL}/api/v1/version",
            timeout=10
        )
        print(f"✓ HTTP 请求成功")
        print(f"  状态码: {response.status_code}")
        print(f"  响应: {response.text[:200]}")
        return True
    except Exception as e:
        print(f"✗ HTTP 请求失败: {e}")
        return False


def main():
    print("=" * 80)
    print(f"FileBay SSL 连接诊断")
    print(f"目标: {FILEBAY_URL}:{FILEBAY_PORT}")
    print("=" * 80)
    
    results = []
    
    # 测试 1: Socket 连接
    results.append(("Socket 连接", test_socket_connection()))
    
    # 测试 2: SSL 连接
    results.append(("SSL 连接（验证证书）", test_ssl_connection()))
    
    # 测试 3: SSL 不验证证书
    results.append(("SSL 连接（不验证）", test_ssl_no_verify()))
    
    # 测试 4: Requests 验证证书
    results.append(("Requests（验证证书）", test_requests_with_verify()))
    
    # 测试 5: Requests 不验证证书
    results.append(("Requests（不验证）", test_requests_no_verify()))
    
    # 测试 6: HTTP 连接
    results.append(("HTTP 连接", test_http_connection()))
    
    # 汇总结果
    print("\n" + "=" * 80)
    print("测试结果汇总")
    print("=" * 80)
    
    for name, success in results:
        status = "✓ 通过" if success else "✗ 失败"
        print(f"{status:10} {name}")
    
    success_count = sum(1 for _, success in results if success)
    print(f"\n通过: {success_count}/{len(results)}")
    
    # 诊断建议
    print("\n" + "=" * 80)
    print("诊断建议")
    print("=" * 80)
    
    if not results[0][1]:
        print("✗ 基本网络连接失败")
        print("  建议: 检查网络连接和防火墙设置")
    elif not results[1][1] and not results[2][1]:
        print("✗ SSL 握手失败")
        print("  建议: FileBay 服务器 SSL 配置有问题")
        print("  可能原因:")
        print("    - SSL 证书过期或无效")
        print("    - SSL 协议版本不匹配")
        print("    - 服务器配置错误")
    elif not results[1][1] and results[2][1]:
        print("⚠ SSL 证书验证失败，但连接正常")
        print("  建议: 证书可能是自签名或过期")
        print("  临时方案: 使用 verify=False（仅开发环境）")
    elif results[4][1]:
        print("✓ Requests 库可以连接（不验证证书）")
        print("  建议: 在代码中使用 verify=False")
    elif results[5][1]:
        print("✓ HTTP 连接正常")
        print("  建议: 临时使用 HTTP（仅开发环境）")
    else:
        print("✓ 所有测试通过")
        print("  FileBay SSL 连接正常")
    
    print("=" * 80)


if __name__ == "__main__":
    main()
