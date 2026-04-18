# SSO 到 FileBay 完整自动化流程

## 流程概述

```
用户 SSO 登录
    ↓
获取用户信息（email, name）
    ↓
调用企业 API 获取 FileBay 配置
    ↓
如果没有配置，触发自动配置流程：
    1. 在 FileBay 创建用户
    2. 创建私有仓库
    3. 生成访问 Token
    4. 初始化脱敏目录
    5. 保存配置到数据库
    ↓
Desktop 使用配置读取文件
```

## 现有实现

### 1. Beta Application Provisioning Service
**文件**: `api/services/beta_application_provisioning_service.py`

**功能**:
- 自动化配置流程的核心服务
- 包含以下步骤：
  1. `STEP_SSO_CREATE_USER` - SSO 创建用户
  2. `STEP_SSO_BIND_ROLE_PERMISSION` - SSO 绑定角色
  3. `STEP_FILEBAY_CREATE_USER` - FileBay 创建用户
  4. `STEP_FILEBAY_CREATE_REPO` - FileBay 创建仓库
  5. `STEP_FILEBAY_INIT_MASKED_DIR` - 初始化脱敏目录
  6. `STEP_NEXUS_RESOURCE_INIT` - Nexus 资源初始化

**FileBay 相关方法**:
- `_execute_filebay_create_user()` - 创建 FileBay 用户
- `_execute_filebay_create_repo()` - 创建私有仓库
- `_execute_filebay_init_masked_dir()` - 初始化目录

### 2. 企业 API
**文件**: `api/controllers/inner_api/gitea.py`

**端点**: `GET /inner/api/enterprise/gitea/config?email={email}`

**当前实现**:
- 从用户的 `custom_config_dict` 读取配置
- 如果没有配置，回退到环境变量

**需要改进**:
- 如果用户没有配置，应该触发自动配置流程
- 或者返回特殊状态码，让调用方知道需要配置

### 3. Console API
**文件**: `api/controllers/console/gitea_api/gitea_config.py`

**端点**: `GET /console/api/gitea/config`

**当前实现**:
- 调用本地企业 API 获取配置
- 如果失败，查询数据库
- 返回脱敏的配置

## 需要实现的功能

### 方案 A: 在企业 API 中触发自动配置

**优点**:
- 集中管理，逻辑清晰
- 前端无需改动

**实现步骤**:

1. **修改企业 API** (`api/controllers/inner_api/gitea.py`)

```python
@inner_api_ns.marshal_with(gitea_config_model)
def get(self):
    user_email = request.args.get('email')
    auto_provision = request.args.get('auto_provision', 'false').lower() == 'true'
    
    if user_email:
        # 查询用户配置
        account = db.session.query(Account).filter_by(email=user_email).first()
        
        if account and account.custom_config_dict and account.custom_config_dict.get('gitea_url'):
            # 已有配置，直接返回
            return {
                'gitea_url': account.custom_config_dict.get('gitea_url'),
                'gitea_owner': account.custom_config_dict.get('gitea_owner'),
                'gitea_repo': account.custom_config_dict.get('gitea_repo'),
                'gitea_token': account.custom_config_dict.get('gitea_token'),
            }
        
        # 没有配置
        if auto_provision:
            # 触发自动配置
            try:
                config = auto_provision_filebay_for_user(user_email)
                # 保存到数据库
                account.custom_config_dict = config
                db.session.commit()
                return config
            except Exception as e:
                logger.error(f'Auto provision failed: {e}')
                # 回退到环境变量
        
    # 回退到环境变量
    return {
        'gitea_url': os.getenv('GITEA_URL', ''),
        'gitea_owner': os.getenv('GITEA_OWNER', ''),
        'gitea_repo': os.getenv('GITEA_REPO', ''),
        'gitea_token': os.getenv('GITEA_TOKEN', ''),
    }
```

2. **创建自动配置函数**

```python
def auto_provision_filebay_for_user(email: str) -> dict:
    """为用户自动配置 FileBay"""
    from services.filebay_auto_provision_service import FileBayAutoProvisionService
    
    service = FileBayAutoProvisionService()
    
    # 1. 生成用户名（基于 email）
    username = service.generate_username_from_email(email)
    
    # 2. 在 FileBay 创建用户
    password = service.create_filebay_user(username, email)
    
    # 3. 创建私有仓库
    repo_name = service.create_filebay_repo(username)
    
    # 4. 生成访问 Token
    token = service.generate_filebay_token(username, password)
    
    # 5. 初始化脱敏目录
    service.init_masked_directory(username, repo_name, token)
    
    return {
        'gitea_url': service.filebay_base_url,
        'gitea_owner': username,
        'gitea_repo': repo_name,
        'gitea_token': token,
    }
```

3. **创建 FileBay 自动配置服务**

```python
# api/services/filebay_auto_provision_service.py

import hashlib
import secrets
import requests
from configs import dify_config

class FileBayAutoProvisionService:
    def __init__(self):
        self.filebay_base_url = dify_config.FILEBAY_BASE_URL.rstrip('/')
        self.admin_username = dify_config.FILEBAY_ADMIN_USERNAME
        self.admin_password = dify_config.FILEBAY_ADMIN_PASSWORD
        self.default_repo = dify_config.FILEBAY_DEFAULT_REPO
        self.default_branch = dify_config.FILEBAY_DEFAULT_BRANCH
        self.masked_dir = dify_config.FILEBAY_DEFAULT_MASKED_DIR
    
    def generate_username_from_email(self, email: str) -> str:
        """从 email 生成用户名"""
        # 使用 email 的哈希值生成唯一用户名
        hash_suffix = hashlib.md5(email.encode()).hexdigest()[:6]
        username = f"user_{hash_suffix}"
        return username
    
    def create_filebay_user(self, username: str, email: str) -> str:
        """在 FileBay 创建用户，返回密码"""
        password = secrets.token_urlsafe(16)
        
        response = requests.post(
            f"{self.filebay_base_url}/api/v1/admin/users",
            auth=(self.admin_username, self.admin_password),
            json={
                "username": username,
                "email": email,
                "password": password,
                "must_change_password": False,
            },
            timeout=10
        )
        response.raise_for_status()
        return password
    
    def create_filebay_repo(self, username: str) -> str:
        """创建私有仓库"""
        repo_name = self.default_repo
        
        response = requests.post(
            f"{self.filebay_base_url}/api/v1/admin/users/{username}/repos",
            auth=(self.admin_username, self.admin_password),
            json={
                "name": repo_name,
                "private": True,
                "auto_init": True,
            },
            timeout=10
        )
        response.raise_for_status()
        return repo_name
    
    def generate_filebay_token(self, username: str, password: str) -> str:
        """生成访问 Token"""
        response = requests.post(
            f"{self.filebay_base_url}/api/v1/users/{username}/tokens",
            auth=(username, password),
            json={
                "name": f"desktop_token_{secrets.token_hex(4)}",
                "scopes": ["read:repository", "write:repository"],
            },
            timeout=10
        )
        response.raise_for_status()
        data = response.json()
        return data['sha1']
    
    def init_masked_directory(self, username: str, repo_name: str, token: str):
        """初始化脱敏目录"""
        import base64
        
        placeholder_content = "# Masked Directory\n\nThis directory is for masked files."
        content_base64 = base64.b64encode(placeholder_content.encode()).decode()
        
        response = requests.post(
            f"{self.filebay_base_url}/api/v1/repos/{username}/{repo_name}/contents/{self.masked_dir}/README.md",
            headers={"Authorization": f"token {token}"},
            json={
                "content": content_base64,
                "message": "Initialize masked directory",
            },
            timeout=10
        )
        response.raise_for_status()
```

### 方案 B: 在 SSO 登录时触发

**优点**:
- 用户登录时立即配置
- 用户体验更好

**实现步骤**:

1. **修改 SSO 登录回调** (`api/controllers/console/auth/desktop_sso.py`)

```python
# 在用户登录成功后
if account:
    # 检查是否有 FileBay 配置
    if not account.custom_config_dict or not account.custom_config_dict.get('gitea_url'):
        # 触发自动配置
        try:
            from services.filebay_auto_provision_service import FileBayAutoProvisionService
            service = FileBayAutoProvisionService()
            config = service.auto_provision(account.email)
            account.custom_config_dict = config
            db.session.commit()
            logger.info(f'Auto provisioned FileBay for {account.email}')
        except Exception as e:
            logger.error(f'Failed to auto provision FileBay: {e}')
```

## 测试方案

### 1. 单元测试

```python
# api/tests/test_filebay_auto_provision.py

def test_generate_username_from_email():
    service = FileBayAutoProvisionService()
    username = service.generate_username_from_email('test@example.com')
    assert username.startswith('user_')
    assert len(username) == 11  # user_ + 6 chars

def test_create_filebay_user():
    service = FileBayAutoProvisionService()
    password = service.create_filebay_user('test_user', 'test@example.com')
    assert len(password) > 0

# ... 更多测试
```

### 2. 集成测试

```bash
# 测试完整流程
python test_complete_sso_filebay_flow.py
```

### 3. 手动测试步骤

1. 使用 SSO 登录
2. 检查数据库中的 `custom_config`
3. 调用企业 API 验证配置
4. 使用文件选择器测试文件读取

## 环境变量配置

```env
# FileBay Admin 配置（用于自动创建用户和仓库）
FILEBAY_BASE_URL=https://uat-filebay.cheersai.cloud
FILEBAY_ADMIN_USERNAME=admin
FILEBAY_ADMIN_PASSWORD=3DIS9cqlR8@E

# FileBay 默认配置
FILEBAY_DEFAULT_REPO=workspace
FILEBAY_DEFAULT_BRANCH=main
FILEBAY_DEFAULT_MASKED_DIR=masked
```

## 下一步

1. 实现 `FileBayAutoProvisionService`
2. 修改企业 API 支持自动配置
3. 添加单元测试
4. 进行集成测试
5. 更新文档

## 注意事项

1. **安全性**: Admin 凭据需要妥善保管
2. **错误处理**: 自动配置失败时的回退机制
3. **幂等性**: 重复调用不应该创建重复资源
4. **日志记录**: 详细记录配置过程
5. **性能**: 自动配置可能需要几秒钟，考虑异步处理

---

**文档版本**: 1.0  
**更新时间**: 2026-04-17
