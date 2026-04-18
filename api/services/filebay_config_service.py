"""FileBay configuration service - 使用 NoSNI 客户端解决 SSL 问题"""
from __future__ import annotations

import os
import ssl
import socket
import json
import base64
from dataclasses import dataclass
from uuid import uuid4
from urllib.parse import urlencode
from typing import Optional, Dict, Any

from configs import dify_config
from extensions.ext_database import db
from models.account import Account


class NoSNIHTTPSClient:
    """不使用 SNI 的 HTTPS 客户端
    
    根本原因: UAT FileBay 服务器的 SNI 配置有问题
    解决方案: 使用原始 socket + SSL，不传递 server_hostname
    """
    
    def __init__(self, base_url: str, username: str, password: str, timeout: int = 30):
        self.base_url = base_url.rstrip('/')
        self.username = username
        self.password = password
        self.timeout = timeout
        
        # 解析 URL
        from urllib.parse import urlparse
        parsed = urlparse(self.base_url)
        self.host = parsed.hostname
        self.port = parsed.port or 443
        
        # 创建认证头
        credentials = f"{username}:{password}"
        self.auth_header = base64.b64encode(credentials.encode()).decode()
    
    def _create_ssl_socket(self) -> ssl.SSLSocket:
        """创建 SSL socket，不使用 SNI"""
        # 创建 TCP socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(self.timeout)
        sock.connect((self.host, self.port))
        
        # 创建 SSL 上下文
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        
        try:
            context.set_ciphers('ALL:@SECLEVEL=0')
        except:
            context.set_ciphers('DEFAULT')
        
        # 包装 socket，关键: 不传递 server_hostname（禁用 SNI）
        ssl_sock = context.wrap_socket(sock)
        
        return ssl_sock
    
    def _send_request(
        self,
        method: str,
        path: str,
        headers: Optional[Dict[str, str]] = None,
        body: Optional[str] = None
    ) -> tuple[int, Dict[str, str], bytes]:
        """发送 HTTP 请求"""
        ssl_sock = self._create_ssl_socket()
        
        try:
            # 构建请求头
            request_headers = {
                "Host": self.host,
                "Authorization": f"Basic {self.auth_header}",
                "User-Agent": "FileBay-NoSNI-Client/1.0",
                "Accept": "application/json",
                "Connection": "close"
            }
            
            if headers:
                request_headers.update(headers)
            
            if body:
                request_headers["Content-Length"] = str(len(body.encode('utf-8')))
                if "Content-Type" not in request_headers:
                    request_headers["Content-Type"] = "application/json"
            
            # 构建 HTTP 请求
            request_line = f"{method} {path} HTTP/1.1\r\n"
            header_lines = "\r\n".join(f"{k}: {v}" for k, v in request_headers.items())
            request = f"{request_line}{header_lines}\r\n\r\n"
            
            if body:
                request += body
            
            # 发送请求
            ssl_sock.sendall(request.encode('utf-8'))
            
            # 接收响应
            response_data = b""
            while True:
                chunk = ssl_sock.recv(4096)
                if not chunk:
                    break
                response_data += chunk
            
            # 解析响应
            response_str = response_data.decode('utf-8', errors='ignore')
            
            # 分离头和体
            parts = response_str.split('\r\n\r\n', 1)
            if len(parts) != 2:
                raise ValueError("Invalid HTTP response")
            
            header_part, body_part = parts
            
            # 解析状态行
            lines = header_part.split('\r\n')
            status_line = lines[0]
            status_code = int(status_line.split()[1])
            
            # 解析响应头
            response_headers = {}
            for line in lines[1:]:
                if ':' in line:
                    key, value = line.split(':', 1)
                    response_headers[key.strip()] = value.strip()
            
            return status_code, response_headers, body_part.encode('utf-8')
            
        finally:
            ssl_sock.close()
    
    def get(self, path: str, params: Optional[Dict[str, Any]] = None) -> tuple[int, Any]:
        """发送 GET 请求"""
        if params:
            query_string = urlencode(params)
            path = f"{path}?{query_string}"
        
        status_code, headers, body = self._send_request("GET", path)
        
        # 解析 JSON 响应
        try:
            data = json.loads(body.decode('utf-8'))
        except:
            data = body.decode('utf-8')
        
        return status_code, data
    
    def post(
        self,
        path: str,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> tuple[int, Any]:
        """发送 POST 请求"""
        body = json.dumps(data) if data else None
        
        status_code, response_headers, response_body = self._send_request(
            "POST",
            path,
            headers=headers,
            body=body
        )
        
        # 解析 JSON 响应
        try:
            response_data = json.loads(response_body.decode('utf-8'))
        except:
            response_data = response_body.decode('utf-8')
        
        return status_code, response_data
    
    def patch(
        self,
        path: str,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> tuple[int, Any]:
        """发送 PATCH 请求"""
        body = json.dumps(data) if data else None
        
        status_code, response_headers, response_body = self._send_request(
            "PATCH",
            path,
            headers=headers,
            body=body
        )
        
        # 解析 JSON 响应
        try:
            response_data = json.loads(response_body.decode('utf-8'))
        except:
            response_data = response_body.decode('utf-8')
        
        return status_code, response_data


@dataclass(frozen=True)
class FileBayConfig:
    gitea_url: str
    gitea_owner: str
    gitea_repo: str
    gitea_token: str


def _mask_token(token: str) -> str:
    """脱敏 Token"""
    if not token:
        return ""
    if len(token) <= 8:
        return "****"
    return f"{token[:4]}{'*' * (len(token) - 8)}{token[-4:]}"


def _build_filebay_base_url() -> str:
    """构建 FileBay 基础 URL"""
    # 优先使用 dify_config，然后回退到环境变量
    return (
        dify_config.FILEBAY_BASE_URL or 
        dify_config.GITEA_URL or 
        os.getenv("FILEBAY_BASE_URL") or 
        os.getenv("GITEA_URL", "")
    ).rstrip("/")


def _normalize_identifier(identifier: str | int | None) -> str:
    """规范化标识符"""
    return str(identifier).strip() if identifier is not None else ""


def _extract_json_dict(status_code: int, data: Any) -> dict | None:
    """从响应中提取 JSON 字典"""
    if status_code != 200:
        return None
    return data if isinstance(data, dict) else None


def _extract_json_list(status_code: int, data: Any) -> list[dict]:
    """从响应中提取 JSON 列表"""
    if status_code != 200:
        return []
    
    if isinstance(data, list):
        return [item for item in data if isinstance(item, dict)]
    if isinstance(data, dict):
        for key in ("data", "items", "repos", "users"):
            items = data.get(key)
            if isinstance(items, list):
                return [item for item in items if isinstance(item, dict)]
    return []


def _filebay_admin_request(
    *,
    method: str,
    path: str,
    params: dict | None = None,
    json_payload: dict | None = None,
) -> tuple[int, Any]:
    """使用 Admin 权限请求 FileBay API（使用 NoSNI 客户端）"""
    base_url = _build_filebay_base_url()
    if not base_url:
        raise RuntimeError("Missing FileBay base URL.")
    if not dify_config.FILEBAY_ADMIN_USERNAME:
        raise RuntimeError("Missing FileBay admin username.")
    if not dify_config.FILEBAY_ADMIN_PASSWORD:
        raise RuntimeError("Missing FileBay admin password.")

    # 使用 NoSNI 客户端
    client = NoSNIHTTPSClient(
        base_url,
        dify_config.FILEBAY_ADMIN_USERNAME,
        dify_config.FILEBAY_ADMIN_PASSWORD,
        timeout=max(1, int(dify_config.BETA_PROVISION_HTTP_TIMEOUT))
    )
    
    try:
        if method.upper() == "GET":
            status_code, data = client.get(path, params=params)
        elif method.upper() == "POST":
            status_code, data = client.post(path, data=json_payload)
        elif method.upper() == "PATCH":
            status_code, data = client.patch(path, data=json_payload)
        else:
            raise ValueError(f"Unsupported method: {method}")
        
        return status_code, data
    except Exception as exc:
        raise RuntimeError(f"Request to FileBay failed: {exc}") from exc


def create_filebay_user_token(
    *,
    base_url: str,
    admin_username: str,
    admin_password: str,
    username: str,
    token_name: str,
    timeout: int,
    ssl_verify: bool,
) -> str:
    """为 FileBay 用户创建访问 Token（使用 NoSNI 客户端）"""
    request_payload = {
        "name": token_name,
        "scopes": ["read:user", "read:repository", "write:repository"],
    }

    # 使用 NoSNI 客户端
    client = NoSNIHTTPSClient(base_url, admin_username, admin_password, timeout=timeout)
    
    try:
        status_code, data = client.post(
            f"/api/v1/users/{username}/tokens",
            data=request_payload,
            headers={"Sudo": username}
        )
    except Exception as exc:
        raise RuntimeError(f"Request to create FileBay token failed: {exc}") from exc

    if status_code not in (200, 201):
        raise RuntimeError(
            f"FileBay create token failed: {status_code} {str(data)[:1000]}"
        )

    if not isinstance(data, dict):
        raise RuntimeError("FileBay create token succeeded, but response payload was not a JSON object.")

    token = data.get("sha1") or data.get("token") or data.get("access_token")
    if not token:
        raise RuntimeError("FileBay token creation succeeded, but response did not include a token value.")
    return str(token)


def _resolve_global_config(*, mask_token: bool = False) -> FileBayConfig:
    """解析全局配置（从环境变量）"""
    gitea_url = _build_filebay_base_url()
    gitea_token = os.getenv("GITEA_TOKEN", "")
    gitea_owner = os.getenv("GITEA_OWNER", "cheersai")
    gitea_repo = os.getenv("GITEA_REPO", "file-storage")
    return FileBayConfig(
        gitea_url=gitea_url,
        gitea_owner=gitea_owner,
        gitea_repo=gitea_repo,
        gitea_token=_mask_token(gitea_token) if mask_token else gitea_token,
    )


def _get_account_config(identifier: str) -> dict | None:
    """从 Account.custom_config_dict 获取配置"""
    normalized_email = _normalize_identifier(identifier).lower()
    if not normalized_email or "@" not in normalized_email:
        return None

    account = db.session.query(Account).filter_by(email=normalized_email).first()
    if not account:
        return None

    config = account.custom_config_dict
    if config and config.get('gitea_url'):
        return config
    return None


def _lookup_filebay_user_by_email(email: str) -> dict | None:
    """通过邮箱查找 FileBay 用户"""
    normalized_email = _normalize_identifier(email).lower()
    if not normalized_email:
        return None

    status_code, data = _filebay_admin_request(
        method="GET",
        path="/api/v1/admin/emails/search",
        params={"q": normalized_email, "limit": 50, "page": 1},
    )
    if status_code != 200:
        return None

    for item in _extract_json_list(status_code, data):
        item_email = _normalize_identifier(item.get("email")).lower()
        if item_email == normalized_email:
            return item
    return None


def _lookup_filebay_user_by_username(username: str) -> dict | None:
    """通过用户名查找 FileBay 用户"""
    normalized_username = _normalize_identifier(username)
    if not normalized_username:
        return None

    status_code, data = _filebay_admin_request(method="GET", path=f"/api/v1/users/{normalized_username}")
    if status_code != 200:
        return None

    payload = _extract_json_dict(status_code, data)
    if isinstance(payload, dict):
        return payload
    return None


def _lookup_filebay_user_by_id(user_id: int) -> dict | None:
    """通过 ID 查找 FileBay 用户"""
    page = 1
    while page <= 20:
        status_code, data = _filebay_admin_request(
            method="GET",
            path="/api/v1/admin/users",
            params={"page": page, "limit": 100},
        )
        if status_code != 200:
            return None

        items = _extract_json_list(status_code, data)
        if not items:
            return None

        for item in items:
            if item.get("id") == user_id:
                return item
        page += 1

    return None


def _lookup_filebay_user(identifier: str | int | None) -> dict | None:
    """查找 FileBay 用户（支持邮箱、用户名、ID）"""
    normalized = _normalize_identifier(identifier)
    if not normalized:
        return None

    if "@" in normalized:
        return _lookup_filebay_user_by_email(normalized)
    if normalized.isdigit():
        return _lookup_filebay_user_by_id(int(normalized))
    return _lookup_filebay_user_by_username(normalized)


def _lookup_filebay_repos(user_id: int) -> list[dict]:
    """查找用户的仓库列表"""
    status_code, data = _filebay_admin_request(
        method="GET",
        path="/api/v1/repos/search",
        params={"uid": user_id, "private": True, "limit": 100, "page": 1},
    )
    if status_code != 200:
        return []
    return _extract_json_list(status_code, data)


def _pick_repo_name(repos: list[dict]) -> str:
    """选择合适的仓库名"""
    preferred_names = [
        _normalize_identifier(dify_config.FILEBAY_DEFAULT_REPO),
        _normalize_identifier(os.getenv("GITEA_REPO", "")),
    ]
    for preferred_name in preferred_names:
        if not preferred_name:
            continue
        for repo in repos:
            repo_name = _normalize_identifier(repo.get("name"))
            if repo_name == preferred_name:
                return repo_name

    if repos:
        return _normalize_identifier(repos[0].get("name"))
    return ""


def _build_config_for_filebay_user(
    *,
    username: str,
    repo_name: str,
    token: str,
    mask_token: bool,
) -> FileBayConfig:
    """构建 FileBay 配置"""
    return FileBayConfig(
        gitea_url=_build_filebay_base_url(),
        gitea_owner=username,
        gitea_repo=repo_name,
        gitea_token=_mask_token(token) if mask_token else token,
    )


def _auto_provision_filebay_user(email: str) -> dict:
    """
    自动为用户创建 FileBay 账号、仓库和 Token
    
    Args:
        email: 用户邮箱
        
    Returns:
        配置字典 {gitea_url, gitea_owner, gitea_repo, gitea_token}
    """
    import hashlib
    import secrets
    import string
    import base64
    
    # 1. 生成用户名
    username = _generate_username_from_email(email)
    
    # 2. 检查用户是否已存在
    existing_user = _get_filebay_user_by_username(username)
    if not existing_user:
        # 创建用户
        password = _generate_password()
        _create_filebay_user(username, email, password)
    
    # 3. 检查仓库是否已存在
    repo_name = dify_config.FILEBAY_DEFAULT_REPO or "workspace"
    existing_repo = _get_filebay_repo(username, repo_name)
    if not existing_repo:
        # 创建仓库
        _create_filebay_repo(username, repo_name)
    
    # 4. 生成 Token
    token = create_filebay_user_token(
        base_url=_build_filebay_base_url(),
        admin_username=dify_config.FILEBAY_ADMIN_USERNAME,
        admin_password=dify_config.FILEBAY_ADMIN_PASSWORD,
        username=username,
        token_name=f"desktop-auto-{secrets.token_hex(4)}",
        timeout=max(1, int(dify_config.BETA_PROVISION_HTTP_TIMEOUT)),
        ssl_verify=False,  # 使用 SSL workaround
    )
    
    # 5. 初始化 masked 目录
    _init_masked_directory(username, repo_name, token)
    
    return {
        'gitea_url': _build_filebay_base_url(),
        'gitea_owner': username,
        'gitea_repo': repo_name,
        'gitea_token': token,
    }


def _generate_username_from_email(email: str) -> str:
    """从邮箱生成唯一用户名"""
    import re
    import hashlib
    
    email = (email or "").strip().lower()
    # 移除特殊字符，只保留字母数字和下划线
    base = re.sub(r"[^a-z0-9]+", "_", email).strip("_") or "user"
    # 生成哈希后缀确保唯一性
    suffix = hashlib.sha1(email.encode("utf-8")).hexdigest()[:6]
    # 限制在 39 字符以内
    trimmed_base = base[:32].rstrip("_") or "user"
    return f"{trimmed_base}_{suffix}"[:39]


def _generate_password(length: int = 16) -> str:
    """生成安全的随机密码"""
    import secrets
    import string
    
    alphabet = string.ascii_letters + string.digits
    random_part = "".join(secrets.choice(alphabet) for _ in range(max(8, length - 4)))
    return f"Aa1!{random_part}"[:length]


def _get_filebay_user_by_username(username: str) -> dict | None:
    """通过用户名获取 FileBay 用户"""
    try:
        status_code, data = _filebay_admin_request(
            method="GET",
            path=f"/api/v1/users/{username}"
        )
        if status_code == 200:
            return data
    except:
        pass
    return None


def _get_filebay_repo(owner: str, repo_name: str) -> dict | None:
    """获取 FileBay 仓库信息"""
    try:
        status_code, data = _filebay_admin_request(
            method="GET",
            path=f"/api/v1/repos/{owner}/{repo_name}"
        )
        if status_code == 200:
            return data
    except:
        pass
    return None


def _create_filebay_user(username: str, email: str, password: str):
    """创建 FileBay 用户"""
    payload = {
        "username": username,
        "email": email,
        "password": password,
        "must_change_password": False,
        "visibility": "private",
        "send_notify": False,
    }
    
    status_code, data = _filebay_admin_request(
        method="POST",
        path="/api/v1/admin/users",
        json_payload=payload
    )
    
    if status_code not in (200, 201):
        # 检查是否已存在
        if status_code in (409, 422):
            return  # 用户已存在，继续
        raise RuntimeError(f"Failed to create FileBay user: {status_code} {str(data)[:200]}")
    
    # 创建成功后，再次确认 must_change_password 设置为 False
    try:
        update_payload = {
            "login_name": username,
            "email": email,
            "must_change_password": False,
        }
        status_code, data = _filebay_admin_request(
            method="PATCH",
            path=f"/api/v1/admin/users/{username}",
            json_payload=update_payload
        )
        if status_code not in (200, 201):
            import logging
            logging.warning(f"Failed to update must_change_password for {username}: {status_code}")
    except Exception as e:
        import logging
        logging.warning(f"Failed to update must_change_password for {username}: {e}")


def _create_filebay_repo(username: str, repo_name: str):
    """创建 FileBay 仓库"""
    payload = {
        "name": repo_name,
        "private": True,
        "auto_init": True,
        "default_branch": dify_config.FILEBAY_DEFAULT_BRANCH or "main",
    }
    
    status_code, data = _filebay_admin_request(
        method="POST",
        path=f"/api/v1/admin/users/{username}/repos",
        json_payload=payload
    )
    
    if status_code not in (200, 201):
        # 检查是否已存在
        if status_code in (409, 422):
            return  # 仓库已存在，继续
        raise RuntimeError(f"Failed to create FileBay repo: {status_code} {str(data)[:200]}")


def _init_masked_directory(username: str, repo_name: str, token: str):
    """初始化 masked 目录"""
    import base64
    
    masked_dir = (dify_config.FILEBAY_DEFAULT_MASKED_DIR or "masked").strip("/")
    placeholder_path = f"{masked_dir}/.keep"
    
    # 检查是否已存在
    try:
        status_code, data = _filebay_admin_request(
            method="GET",
            path=f"/api/v1/repos/{username}/{repo_name}/contents/{placeholder_path}"
        )
        if status_code == 200:
            return  # 已存在
    except:
        pass
    
    # 创建占位文件
    content = "# Masked Directory\n\nThis directory is for masked/sensitive files.\n"
    content_base64 = base64.b64encode(content.encode()).decode()
    
    payload = {
        "message": f"Initialize {masked_dir} directory",
        "content": content_base64,
        "branch": dify_config.FILEBAY_DEFAULT_BRANCH or "main",
    }
    
    try:
        status_code, data = _filebay_admin_request(
            method="POST",
            path=f"/api/v1/repos/{username}/{repo_name}/contents/{placeholder_path}",
            json_payload=payload
        )
    except:
        pass  # 忽略初始化失败


def _save_config_to_account(email: str, config: dict):
    """保存配置到账号"""
    account = db.session.query(Account).filter_by(email=email).first()
    if account:
        account.custom_config_dict = config
        db.session.commit()


def resolve_filebay_config(
    identifier: str | int | None = None,
    *,
    allow_global_fallback: bool = True,
    auto_provision: bool = True,
    mask_token: bool = False,
) -> FileBayConfig:
    """
    解析 FileBay 配置
    
    优先级：
    1. Account.custom_config_dict（如果有）
    2. 查找 FileBay 已有用户并生成 Token
    3. 自动创建新用户、仓库和 Token（如果 auto_provision=True）
    4. 全局配置（环境变量）
    """
    normalized_identifier = _normalize_identifier(identifier)
    
    # 1. 尝试从 Account.custom_config_dict 获取
    if normalized_identifier and "@" in normalized_identifier:
        account_config = _get_account_config(normalized_identifier)
        if account_config:
            return FileBayConfig(
                gitea_url=account_config.get('gitea_url', ''),
                gitea_owner=account_config.get('gitea_owner', ''),
                gitea_repo=account_config.get('gitea_repo', ''),
                gitea_token=_mask_token(account_config.get('gitea_token', '')) if mask_token else account_config.get('gitea_token', ''),
            )
    
    # 2. 查找 FileBay 已有用户
    if normalized_identifier:
        try:
            filebay_user = _lookup_filebay_user(normalized_identifier)
            if filebay_user:
                username = _normalize_identifier(filebay_user.get("login") or filebay_user.get("username"))
                user_id = filebay_user.get("id")
                repo_name = ""
                if isinstance(user_id, int):
                    repo_name = _pick_repo_name(_lookup_filebay_repos(user_id))
                if not repo_name:
                    repo_name = _normalize_identifier(dify_config.FILEBAY_DEFAULT_REPO or os.getenv("GITEA_REPO", ""))
                if not username:
                    raise LookupError("FileBay user lookup succeeded, but username was empty.")

                # 动态生成 Token
                token = create_filebay_user_token(
                    base_url=_build_filebay_base_url(),
                    admin_username=dify_config.FILEBAY_ADMIN_USERNAME,
                    admin_password=dify_config.FILEBAY_ADMIN_PASSWORD,
                    username=username,
                    token_name=f"desktop-{username}-{uuid4().hex[:8]}",
                    timeout=max(1, int(dify_config.BETA_PROVISION_HTTP_TIMEOUT)),
                    ssl_verify=False,
                )
                return _build_config_for_filebay_user(
                    username=username,
                    repo_name=repo_name,
                    token=token,
                    mask_token=mask_token,
                )
        except Exception as e:
            # 查找失败（可能是 SSL 问题），继续尝试自动配置
            import logging
            logging.warning(f"User lookup failed for {normalized_identifier}: {e}")
        
        # 3. 自动创建新用户（如果启用）
        if auto_provision and "@" in normalized_identifier:
            try:
                config = _auto_provision_filebay_user(normalized_identifier)
                # 保存到数据库
                _save_config_to_account(normalized_identifier, config)
                return FileBayConfig(
                    gitea_url=config['gitea_url'],
                    gitea_owner=config['gitea_owner'],
                    gitea_repo=config['gitea_repo'],
                    gitea_token=_mask_token(config['gitea_token']) if mask_token else config['gitea_token'],
                )
            except Exception as e:
                # 自动配置失败，继续尝试 fallback
                import logging
                logging.warning(f"Auto provision failed for {normalized_identifier}: {e}")

        if not allow_global_fallback:
            raise LookupError(f"No FileBay user found for {normalized_identifier}.")

    # 4. 回退到全局配置
    return _resolve_global_config(mask_token=mask_token)
