# 账号和 Gitea 配置清单

## 系统账号总览

**统计信息：**
- 总账号数：3
- 已设置密码：1
- 已配置 Gitea：1
- 活跃账号：3

---

## 账号详情

### 账号 1: 测试账号（已配置 Gitea）✅

**基本信息：**
- 邮箱：`test_eacm9wzq@test.com`
- 用户名：`Test User test_eacm9wzq`
- 账号 ID：`8275ea19-7f66-4c8a-aa86-2cec458dc46b`
- 状态：`active`
- 密码：未设置
- 创建时间：2026-04-17 09:05:00
- 最后登录：从未登录

**Gitea 配置：**✅
```json
{
  "gitea_url": "https://test-filebay.example.com",
  "gitea_owner": "testuser",
  "gitea_repo": "test-repo",
  "gitea_token": "test_token_abc123xyz"
}
```

**用途：**
- 自动化测试账号
- 用于验证 Gitea 配置功能

---

### 账号 2: QQ 邮箱账号（未配置 Gitea）❌

**基本信息：**
- 邮箱：`103456686@qq.com`
- 用户名：`103456686_qq_com_nzvhyt`
- 账号 ID：`f3056f10-d994-4c2b-8acd-c02c49c4e5d7`
- 状态：`active`
- 密码：未设置
- 创建时间：2026-04-16 09:06:04
- 最后登录：2026-04-16 09:06:07

**Gitea 配置：**❌
- 未配置

**建议配置：**
```json
{
  "gitea_url": "https://uat-filebay.cheersai.cloud",
  "gitea_owner": "junqianxi",
  "gitea_repo": "CheersAI-Desktop",
  "gitea_token": "你的_gitea_token"
}
```

---

### 账号 3: 管理员账号（未配置 Gitea）❌

**基本信息：**
- 邮箱：`1@qq.com`
- 用户名：`admin`
- 账号 ID：`68393244-8477-4691-9f70-8a7dec8090dc`
- 状态：`active`
- 密码：✅ 已设置
- 密码哈希：`Y2Q1ZDI5ZTg4MmMyMTlk...`
- 创建时间：2026-04-16 07:52:29
- 最后登录：2026-04-16 07:52:30

**Gitea 配置：**❌
- 未配置

**建议配置：**
```json
{
  "gitea_url": "https://uat-filebay.cheersai.cloud",
  "gitea_owner": "admin",
  "gitea_repo": "admin-files",
  "gitea_token": "管理员的_gitea_token"
}
```

---

## 如何为账号配置 Gitea

### 方法 1：使用 Python 脚本（推荐）

```python
from extensions.ext_database import db
from models.account import Account
from app import create_app

app = create_app()

with app.app_context():
    # 为 103456686@qq.com 配置 Gitea
    account = db.session.query(Account).filter_by(email='103456686@qq.com').first()
    
    if account:
        account.custom_config_dict = {
            'gitea_url': 'https://uat-filebay.cheersai.cloud',
            'gitea_owner': 'junqianxi',
            'gitea_repo': 'CheersAI-Desktop',
            'gitea_token': '你的真实token'
        }
        db.session.commit()
        print('配置已保存')
```

### 方法 2：使用 SQL

```sql
-- 为 103456686@qq.com 配置 Gitea
UPDATE accounts 
SET custom_config = '{"gitea_url":"https://uat-filebay.cheersai.cloud","gitea_owner":"junqianxi","gitea_repo":"CheersAI-Desktop","gitea_token":"你的真实token"}'
WHERE email = '103456686@qq.com';

-- 为 admin 配置 Gitea
UPDATE accounts 
SET custom_config = '{"gitea_url":"https://uat-filebay.cheersai.cloud","gitea_owner":"admin","gitea_repo":"admin-files","gitea_token":"管理员的真实token"}'
WHERE email = '1@qq.com';
```

### 方法 3：使用快捷脚本

创建文件 `set_gitea_config.py`：

```python
"""为指定账号设置 Gitea 配置"""
import sys
from extensions.ext_database import db
from models.account import Account
from app import create_app

def set_gitea_config(email, gitea_url, gitea_owner, gitea_repo, gitea_token):
    app = create_app()
    with app.app_context():
        account = db.session.query(Account).filter_by(email=email).first()
        if not account:
            print(f'错误：未找到账号 {email}')
            return False
        
        account.custom_config_dict = {
            'gitea_url': gitea_url,
            'gitea_owner': gitea_owner,
            'gitea_repo': gitea_repo,
            'gitea_token': gitea_token
        }
        db.session.commit()
        print(f'✅ 已为 {email} 配置 Gitea')
        return True

if __name__ == '__main__':
    if len(sys.argv) != 6:
        print('用法: python set_gitea_config.py <email> <url> <owner> <repo> <token>')
        sys.exit(1)
    
    set_gitea_config(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5])
```

使用方法：
```bash
python set_gitea_config.py "103456686@qq.com" "https://uat-filebay.cheersai.cloud" "junqianxi" "CheersAI-Desktop" "你的token"
```

---

## 验证配置

### 1. 通过企业 API 验证

```bash
# 验证 103456686@qq.com 的配置
curl "http://localhost:5001/inner/api/enterprise/gitea/config?email=103456686@qq.com"

# 验证 admin 的配置
curl "http://localhost:5001/inner/api/enterprise/gitea/config?email=1@qq.com"
```

### 2. 通过数据库验证

```sql
SELECT email, name, custom_config 
FROM accounts 
WHERE email IN ('103456686@qq.com', '1@qq.com');
```

### 3. 通过 Python 脚本验证

```bash
python list_accounts_with_gitea.py
```

---

## 登录信息

### 可以登录的账号

**账号：** `1@qq.com` (admin)
- ✅ 已设置密码
- 可以直接登录前端
- 需要配置 Gitea 才能使用文件选择器

### 需要设置密码的账号

**账号 1：** `103456686@qq.com`
- ❌ 未设置密码
- 需要通过 SSO 登录或设置密码

**账号 2：** `test_eacm9wzq@test.com`
- ❌ 未设置密码
- 测试账号，建议通过 API 测试

---

## 为账号设置密码

```python
from werkzeug.security import generate_password_hash
from extensions.ext_database import db
from models.account import Account
from app import create_app

app = create_app()

with app.app_context():
    account = db.session.query(Account).filter_by(email='103456686@qq.com').first()
    if account:
        # 设置密码为 "password123"
        account.password = generate_password_hash('password123')
        account.password_salt = 'salt123'
        db.session.commit()
        print('密码已设置')
```

---

## 下一步操作建议

### 1. 为 103456686@qq.com 配置 Gitea
这个账号已经有登录记录，应该是实际使用的账号。

### 2. 为 admin 账号配置 Gitea
管理员账号已设置密码，可以直接登录测试。

### 3. 测试完整流程
1. 使用 admin 账号登录前端
2. 打开对话页面
3. 点击文件上传按钮
4. 选择"从 FileBay 选择"
5. 验证文件选择器是否显示正确的仓库

---

**更新时间：** 2026-04-17 09:38  
**文档版本：** 1.0
