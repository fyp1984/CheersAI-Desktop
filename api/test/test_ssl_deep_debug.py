#!/usr/bin/env python3
"""深度 SSL 调试 - 尝试不同的 TLS 版本和加密套件"""
import ssl
import socket
import sys

FILEBAY_URL = "uat-filebay.cheersai.cloud"
FILEBAY_PORT = 443


def test_tls_version(protocol, protocol_name):
    """测试特定的 TLS 版本"""
    print(f"\n测试 {protocol_name}...")
    print("-" * 60)
    
    try:
        context = ssl.SSLContext(protocol)
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        
        # 尝试设置最宽松的加密套件
        try:
            context.set_ciphers('ALL:@SECLEVEL=0')
            print(f"  使用加密套件: ALL:@SECLEVEL=0")
        except:
            try:
                context.set_ciphers('DEFAULT:@SECLEVEL=0')
                print(f"  使用加密套件: DEFAULT:@SECLEVEL=0")
            except:
                context.set_ciphers('DEFAULT')
                print(f"  使用加密套件: DEFAULT")
        
        with socket.create_connection((FILEBAY_URL, FILEBAY_PORT), timeout=10) as sock:
            with context.wrap_socket(sock, server_hostname=FILEBAY_URL) as ssock:
                print(f"  ✓ 连接成功!")
                print(f"  SSL 版本: {ssock.version()}")
                print(f"  加密套件: {ssock.cipher()}")
                return True
    except ssl.SSLError as e:
        print(f"  ✗ SSL 错误: {e}")
        return False
    except Exception as e:
        print(f"  ✗ 连接失败: {e}")
        return False


def test_with_legacy_options():
    """测试使用传统选项"""
    print(f"\n测试使用传统 SSL 选项...")
    print("-" * 60)
    
    try:
        # 使用 PROTOCOL_TLS 并允许所有版本
        context = ssl.SSLContext(ssl.PROTOCOL_TLS)
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        
        # 设置选项以允许传统协议
        context.options &= ~ssl.OP_NO_SSLv2
        context.options &= ~ssl.OP_NO_SSLv3
        context.options &= ~ssl.OP_NO_TLSv1
        context.options &= ~ssl.OP_NO_TLSv1_1
        
        # 设置最宽松的加密套件
        try:
            context.set_ciphers('ALL:COMPLEMENTOFALL:@SECLEVEL=0')
            print(f"  使用加密套件: ALL:COMPLEMENTOFALL:@SECLEVEL=0")
        except:
            context.set_ciphers('ALL:@SECLEVEL=0')
            print(f"  使用加密套件: ALL:@SECLEVEL=0")
        
        with socket.create_connection((FILEBAY_URL, FILEBAY_PORT), timeout=10) as sock:
            with context.wrap_socket(sock, server_hostname=FILEBAY_URL) as ssock:
                print(f"  ✓ 连接成功!")
                print(f"  SSL 版本: {ssock.version()}")
                print(f"  加密套件: {ssock.cipher()}")
                return True
    except Exception as e:
        print(f"  ✗ 连接失败: {e}")
        return False


def test_without_sni():
    """测试不使用 SNI (Server Name Indication)"""
    print(f"\n测试不使用 SNI...")
    print("-" * 60)
    
    try:
        context = ssl.SSLContext(ssl.PROTOCOL_TLS)
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        
        try:
            context.set_ciphers('ALL:@SECLEVEL=0')
        except:
            context.set_ciphers('DEFAULT')
        
        with socket.create_connection((FILEBAY_URL, FILEBAY_PORT), timeout=10) as sock:
            # 不传递 server_hostname，即不使用 SNI
            with context.wrap_socket(sock) as ssock:
                print(f"  ✓ 连接成功!")
                print(f"  SSL 版本: {ssock.version()}")
                print(f"  加密套件: {ssock.cipher()}")
                return True
    except Exception as e:
        print(f"  ✗ 连接失败: {e}")
        return False


def test_raw_socket_ssl():
    """测试原始 socket SSL 包装"""
    print(f"\n测试原始 socket SSL 包装...")
    print("-" * 60)
    
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        sock.connect((FILEBAY_URL, FILEBAY_PORT))
        
        # 使用最简单的 SSL 包装
        ssl_sock = ssl.wrap_socket(
            sock,
            cert_reqs=ssl.CERT_NONE,
            ssl_version=ssl.PROTOCOL_TLS
        )
        
        print(f"  ✓ 连接成功!")
        print(f"  SSL 版本: {ssl_sock.version()}")
        print(f"  加密套件: {ssl_sock.cipher()}")
        
        ssl_sock.close()
        return True
    except Exception as e:
        print(f"  ✗ 连接失败: {e}")
        try:
            sock.close()
        except:
            pass
        return False


def test_openssl_command():
    """测试使用 openssl 命令行工具"""
    print(f"\n测试使用 openssl 命令行...")
    print("-" * 60)
    
    import subprocess
    
    commands = [
        # 标准连接
        ["openssl", "s_client", "-connect", f"{FILEBAY_URL}:{FILEBAY_PORT}", "-showcerts"],
        # TLS 1.2
        ["openssl", "s_client", "-connect", f"{FILEBAY_URL}:{FILEBAY_PORT}", "-tls1_2"],
        # TLS 1.1
        ["openssl", "s_client", "-connect", f"{FILEBAY_URL}:{FILEBAY_PORT}", "-tls1_1"],
        # TLS 1.0
        ["openssl", "s_client", "-connect", f"{FILEBAY_URL}:{FILEBAY_PORT}", "-tls1"],
    ]
    
    for cmd in commands:
        try:
            print(f"  尝试: {' '.join(cmd[2:])}")
            result = subprocess.run(
                cmd,
                input=b"",
                capture_output=True,
                timeout=10
            )
            
            output = result.stdout.decode('utf-8', errors='ignore')
            
            if "Verify return code: 0" in output or "SSL handshake has read" in output:
                print(f"    ✓ 成功!")
                # 提取协议版本
                for line in output.split('\n'):
                    if 'Protocol' in line or 'Cipher' in line:
                        print(f"    {line.strip()}")
                return True
            else:
                print(f"    ✗ 失败")
        except subprocess.TimeoutExpired:
            print(f"    ✗ 超时")
        except FileNotFoundError:
            print(f"    ✗ openssl 命令未找到")
            return False
        except Exception as e:
            print(f"    ✗ 错误: {e}")
    
    return False


def main():
    print("=" * 80)
    print("FileBay SSL 深度调试")
    print(f"目标: {FILEBAY_URL}:{FILEBAY_PORT}")
    print("=" * 80)
    
    results = []
    
    # 测试不同的 TLS 版本
    print("\n" + "=" * 80)
    print("第一部分: 测试不同的 TLS 协议版本")
    print("=" * 80)
    
    tls_versions = [
        (ssl.PROTOCOL_TLS, "PROTOCOL_TLS (自动协商)"),
        (ssl.PROTOCOL_TLS_CLIENT, "PROTOCOL_TLS_CLIENT"),
    ]
    
    # 尝试添加特定版本（如果可用）
    if hasattr(ssl, 'PROTOCOL_TLSv1_2'):
        tls_versions.append((ssl.PROTOCOL_TLSv1_2, "TLSv1.2"))
    if hasattr(ssl, 'PROTOCOL_TLSv1_1'):
        tls_versions.append((ssl.PROTOCOL_TLSv1_1, "TLSv1.1"))
    if hasattr(ssl, 'PROTOCOL_TLSv1'):
        tls_versions.append((ssl.PROTOCOL_TLSv1, "TLSv1.0"))
    
    for protocol, name in tls_versions:
        results.append((name, test_tls_version(protocol, name)))
    
    # 测试其他选项
    print("\n" + "=" * 80)
    print("第二部分: 测试其他 SSL 选项")
    print("=" * 80)
    
    results.append(("传统选项", test_with_legacy_options()))
    results.append(("不使用 SNI", test_without_sni()))
    results.append(("原始 socket", test_raw_socket_ssl()))
    
    # 测试 openssl 命令行
    print("\n" + "=" * 80)
    print("第三部分: 测试 openssl 命令行工具")
    print("=" * 80)
    
    results.append(("openssl 命令", test_openssl_command()))
    
    # 汇总结果
    print("\n" + "=" * 80)
    print("测试结果汇总")
    print("=" * 80)
    
    for name, success in results:
        status = "✓ 成功" if success else "✗ 失败"
        print(f"{status:10} {name}")
    
    success_count = sum(1 for _, success in results if success)
    print(f"\n成功: {success_count}/{len(results)}")
    
    # 诊断建议
    print("\n" + "=" * 80)
    print("诊断结论")
    print("=" * 80)
    
    if success_count == 0:
        print("✗ 所有 SSL 连接尝试都失败了")
        print()
        print("可能的原因:")
        print("  1. 服务器 TLS 配置严重不兼容")
        print("  2. 服务器在握手过程中主动关闭连接")
        print("  3. 中间网络设备干扰 SSL 握手")
        print()
        print("建议:")
        print("  1. 联系 FileBay 团队检查服务器 TLS 配置")
        print("  2. 检查服务器日志查看握手失败原因")
        print("  3. 尝试从不同网络环境连接")
        print("  4. 考虑使用代理或 Rust 工具绕过")
    elif success_count < len(results):
        print("⚠ 部分 SSL 连接成功")
        print()
        print("成功的方法:")
        for name, success in results:
            if success:
                print(f"  ✓ {name}")
        print()
        print("建议: 在代码中使用成功的 SSL 配置方法")
    else:
        print("✓ 所有 SSL 连接测试都成功")
        print()
        print("建议: SSL 配置正常，检查应用层代码")
    
    print("=" * 80)


if __name__ == "__main__":
    main()
