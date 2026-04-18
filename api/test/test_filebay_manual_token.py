#!/usr/bin/env python3
"""手动获取 FileBay Token 的方法"""

print("=" * 80)
print("FileBay Token 手动获取指南")
print("=" * 80)

print("""
由于 Python SSL 连接失败，我们需要手动获取 Token。以下是几种方法：

方法 1: 通过浏览器访问 FileBay Swagger API
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. 在浏览器中打开:
   https://uat-filebay.cheersai.cloud/api/swagger

2. 使用管理员账号登录:
   用户名: admin
   密码: 3DIS9cqlR8@E

3. 找到 "user" 相关的 API 端点

4. 查看现有用户列表或搜索用户


方法 2: 通过浏览器直接创建 Token
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. 在浏览器中登录 FileBay:
   https://uat-filebay.cheersai.cloud

2. 使用管理员账号:
   用户名: admin
   密码: 3DIS9cqlR8@E

3. 进入 Settings > Applications > Generate New Token

4. 创建 Token 并复制


方法 3: 使用 curl 命令（如果你的系统 curl 可以连接）
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# 1. 搜索用户 (1@qq.com)
curl -k -u "admin:3DIS9cqlR8@E" \\
  "https://uat-filebay.cheersai.cloud/api/v1/admin/emails/search?q=1@qq.com"

# 2. 为用户创建 Token (假设用户名是 user1)
curl -k -X POST -u "admin:3DIS9cqlR8@E" \\
  -H "Content-Type: application/json" \\
  -H "Sudo: user1" \\
  -d '{"name":"desktop-token","scopes":["read:user","read:repository","write:repository"]}' \\
  "https://uat-filebay.cheersai.cloud/api/v1/users/user1/tokens"


方法 4: 使用 Postman 或其他 API 工具
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. 打开 Postman

2. 禁用 SSL 验证:
   Settings > General > SSL certificate verification: OFF

3. 创建请求:
   Method: GET
   URL: https://uat-filebay.cheersai.cloud/api/v1/admin/emails/search?q=1@qq.com
   Auth: Basic Auth
     Username: admin
     Password: 3DIS9cqlR8@E

4. 发送请求查看用户信息

5. 创建 Token:
   Method: POST
   URL: https://uat-filebay.cheersai.cloud/api/v1/users/{username}/tokens
   Headers:
     Content-Type: application/json
     Sudo: {username}
   Auth: Basic Auth
     Username: admin
     Password: 3DIS9cqlR8@E
   Body (JSON):
     {
       "name": "desktop-token",
       "scopes": ["read:user", "read:repository", "write:repository"]
     }


方法 5: 使用 Rust 测试程序
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

如果你有 Rust 环境，可以使用已有的测试程序:

cd E:\\CheersAI脱敏\\cheersai-desktop
cargo run --bin test_filebay_connection


需要查找的用户信息
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

真实用户:
1. 1@qq.com
2. 103456686@qq.com

需要获取的信息:
- FileBay 用户名 (login/username)
- FileBay 用户 ID
- 用户的仓库列表
- 为用户创建的 Token


获取 Token 后的操作
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. 将 Token 保存到数据库:

   python -c "
   from flask import Flask
   from extensions.ext_database import db
   from models.account import Account
   from configs import dify_config
   
   app = Flask(__name__)
   app.config['SQLALCHEMY_DATABASE_URI'] = dify_config.SQLALCHEMY_DATABASE_URI
   app.config['SQLALCHEMY_ENGINE_OPTIONS'] = dify_config.SQLALCHEMY_ENGINE_OPTIONS
   db.init_app(app)
   
   with app.app_context():
       account = db.session.query(Account).filter_by(email='1@qq.com').first()
       if account:
           account.custom_config = {
               'gitea_url': 'https://uat-filebay.cheersai.cloud',
               'gitea_owner': 'user_login_name',  # 替换为实际用户名
               'gitea_repo': 'workspace',
               'gitea_token': 'actual_token_here'  # 替换为实际 Token
           }
           db.session.commit()
           print('✓ Token 已保存')
   "

2. 验证配置:

   python check_accounts_filebay.py check 1@qq.com


注意事项
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. Token 是敏感信息，请妥善保管
2. 不要将 Token 提交到 Git 仓库
3. Token 可能有过期时间，需要定期更新
4. 使用 Sudo 头可以以其他用户身份创建 Token

""")

print("=" * 80)
print("请选择一种方法手动获取 Token")
print("=" * 80)
