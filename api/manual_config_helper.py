#!/usr/bin/env python3
"""
FileBay 手动配置助手

使用浏览器手动配置 FileBay 的交互式助手
"""
import sys


def print_header(text):
    """打印标题"""
    print()
    print("=" * 80)
    print(text)
    print("=" * 80)
    print()


def print_step(number, text):
    """打印步骤"""
    print(f"\n步骤 {number}: {text}")
    print("-" * 80)


def main():
    print_header("FileBay 手动配置助手")
    
    print("这个助手将指导你通过浏览器手动配置 FileBay。")
    print()
    print("需要配置的用户:")
    print("  1. 1@qq.com")
    print("  2. 103456686@qq.com")
    print()
    
    email = input("请输入要配置的用户邮箱 (或按 Enter 使用 1@qq.com): ").strip()
    if not email:
        email = "1@qq.com"
    
    print_header(f"为 {email} 配置 FileBay")
    
    # 步骤 1: 访问 Swagger
    print_step(1, "访问 FileBay Swagger API")
    print()
    print("  URL: https://uat-filebay.cheersai.cloud/api/swagger")
    print("  用户名: admin")
    print("  密码: 3DIS9cqlR8@E")
    print()
    input("按 Enter 继续...")
    
    # 步骤 2: 搜索用户
    print_step(2, "搜索用户")
    print()
    print("  1. 找到端点: GET /api/v1/admin/emails/search")
    print("  2. 点击 'Try it out'")
    print("  3. 输入参数:")
    print(f"     - q: {email}")
    print("     - limit: 10")
    print("  4. 点击 'Execute'")
    print("  5. 在返回结果中找到:")
    print("     - username (例如: user1)")
    print("     - id (例如: 123)")
    print()
    
    username = input("请输入找到的 username: ").strip()
    if not username:
        print("错误: username 不能为空")
        sys.exit(1)
    
    user_id = input("请输入找到的 id (可选): ").strip()
    
    # 步骤 3: 创建 Token
    print_step(3, "创建 Token")
    print()
    print("  1. 找到端点: POST /api/v1/users/{username}/tokens")
    print("  2. 点击 'Try it out'")
    print(f"  3. 输入 username: {username}")
    print("  4. 添加 Header:")
    print("     - 点击 'Add string item' in Headers")
    print("     - Name: Sudo")
    print(f"     - Value: {username}")
    print("  5. 输入 Request body:")
    print()
    print("     {")
    print('       "name": "desktop-token-1",')
    print('       "scopes": [')
    print('         "read:user",')
    print('         "read:repository",')
    print('         "write:repository"')
    print('       ]')
    print("     }")
    print()
    print("  6. 点击 'Execute'")
    print("  7. 复制返回的 Token (sha1 字段)")
    print()
    
    token = input("请粘贴复制的 Token: ").strip()
    if not token:
        print("错误: Token 不能为空")
        sys.exit(1)
    
    # 步骤 4: 保存到数据库
    print_step(4, "保存到数据库")
    print()
    print("  运行以下命令:")
    print()
    print(f'  python save_filebay_token.py "{email}" "{username}" "workspace" "{token}"')
    print()
    
    confirm = input("是否现在运行这个命令? (y/n): ").strip().lower()
    
    if confirm == 'y':
        import subprocess
        try:
            result = subprocess.run(
                ["python", "save_filebay_token.py", email, username, "workspace", token],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            print()
            print(result.stdout)
            if result.stderr:
                print(result.stderr)
            
            if result.returncode == 0:
                print()
                print("✓ 配置保存成功!")
                
                # 步骤 5: 验证
                print_step(5, "验证配置")
                print()
                print("  运行以下命令验证:")
                print()
                print(f'  python check_accounts_filebay.py check {email}')
                print()
                
                verify = input("是否现在验证? (y/n): ").strip().lower()
                if verify == 'y':
                    result = subprocess.run(
                        ["python", "check_accounts_filebay.py", "check", email],
                        capture_output=True,
                        text=True,
                        timeout=30
                    )
                    print()
                    print(result.stdout)
                    if result.stderr:
                        print(result.stderr)
            else:
                print()
                print("✗ 配置保存失败")
                print()
                print("请手动运行命令:")
                print(f'python save_filebay_token.py "{email}" "{username}" "workspace" "{token}"')
        
        except Exception as e:
            print()
            print(f"✗ 运行失败: {e}")
            print()
            print("请手动运行命令:")
            print(f'python save_filebay_token.py "{email}" "{username}" "workspace" "{token}"')
    else:
        print()
        print("请手动运行以下命令:")
        print()
        print(f'python save_filebay_token.py "{email}" "{username}" "workspace" "{token}"')
        print()
        print("然后验证:")
        print(f'python check_accounts_filebay.py check {email}')
    
    print_header("配置完成!")
    print()
    print("下一步:")
    print("  1. 如果还有其他用户需要配置，再次运行此脚本")
    print("  2. 测试前端文件选择器功能")
    print("  3. 验证可以浏览、上传、下载文件")
    print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print()
        print()
        print("已取消")
        sys.exit(0)
