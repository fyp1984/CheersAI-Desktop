"""FileBay Auto Provision Service for SSO users."""
import base64
import hashlib
import logging
import secrets
import string
from typing import Any

import requests
import urllib3

from configs import dify_config

logger = logging.getLogger(__name__)


class FileBayAutoProvisionService:
    """Automatically provision FileBay resources for SSO users."""

    def __init__(self):
        self.filebay_base_url = (dify_config.FILEBAY_BASE_URL or dify_config.GITEA_URL or "").rstrip("/")
        self.admin_username = dify_config.FILEBAY_ADMIN_USERNAME
        self.admin_password = dify_config.FILEBAY_ADMIN_PASSWORD
        self.default_repo = dify_config.FILEBAY_DEFAULT_REPO or "workspace"
        self.default_branch = dify_config.FILEBAY_DEFAULT_BRANCH or "main"
        self.masked_dir = (dify_config.FILEBAY_DEFAULT_MASKED_DIR or "masked").strip("/")
        self.http_timeout = 30
        self.ssl_verify = dify_config.BETA_PROVISION_SSL_VERIFY
        
        if not self.ssl_verify:
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    def auto_provision(self, email: str) -> dict[str, str]:
        """
        Complete auto-provision flow for a user.
        
        Args:
            email: User email address
            
        Returns:
            Dictionary with gitea_url, gitea_owner, gitea_repo, gitea_token
            
        Raises:
            Exception: If any step fails
        """
        logger.info("[FileBay Auto Provision] Starting for %s", email)
        
        # 1. Generate username from email
        username = self.generate_username_from_email(email)
        logger.info("[FileBay Auto Provision] Generated username: %s", username)
        
        # 2. Check if user already exists
        existing_user = self._get_user(username)
        if existing_user:
            logger.info("[FileBay Auto Provision] User %s already exists", username)
        else:
            # Create user
            password = self.create_filebay_user(username, email)
            logger.info("[FileBay Auto Provision] Created user %s", username)
        
        # 3. Check if repo already exists
        repo_name = self.default_repo
        existing_repo = self._get_repo(username, repo_name)
        if existing_repo:
            logger.info("[FileBay Auto Provision] Repo %s/%s already exists", username, repo_name)
        else:
            # Create repo
            self.create_filebay_repo(username, repo_name)
            logger.info("[FileBay Auto Provision] Created repo %s/%s", username, repo_name)
        
        # 4. Generate access token (use admin to create token for user)
        token = self.generate_filebay_token(username)
        logger.info("[FileBay Auto Provision] Generated token for %s", username)
        
        # 5. Initialize masked directory
        self.init_masked_directory(username, repo_name, token)
        logger.info("[FileBay Auto Provision] Initialized masked directory")
        
        config = {
            "gitea_url": self.filebay_base_url,
            "gitea_owner": username,
            "gitea_repo": repo_name,
            "gitea_token": token,
        }
        
        logger.info("[FileBay Auto Provision] Completed for %s", email)
        return config

    def generate_username_from_email(self, email: str) -> str:
        """
        Generate a unique username from email address.
        
        Args:
            email: User email address
            
        Returns:
            Generated username (max 39 chars)
        """
        import re
        
        email = (email or "").strip().lower()
        # Remove special characters, keep only alphanumeric and underscore
        base = re.sub(r"[^a-z0-9]+", "_", email).strip("_") or "user"
        # Generate hash suffix for uniqueness
        suffix = hashlib.sha1(email.encode("utf-8")).hexdigest()[:6]
        # Trim base to fit within 39 char limit (username_suffix format)
        trimmed_base = base[:32].rstrip("_") or "user"
        return f"{trimmed_base}_{suffix}"[:39]

    def create_filebay_user(self, username: str, email: str) -> str:
        """
        Create a FileBay user account.
        
        Args:
            username: Username to create
            email: User email address
            
        Returns:
            Generated password
            
        Raises:
            Exception: If user creation fails
        """
        password = self._generate_password()
        
        payload = {
            "username": username,
            "email": email,
            "password": password,
            "must_change_password": False,  # Don't force password change for auto-provisioned users
            "visibility": "private",
            "send_notify": False,
        }
        
        response = self._request(
            method="POST",
            path="/api/v1/admin/users",
            json_payload=payload,
        )
        
        if response.status_code not in (200, 201):
            # Check if user already exists
            if self._looks_like_already_exists(response):
                logger.warning("[FileBay Auto Provision] User %s already exists", username)
                return password
            
            error_msg = self._extract_error_message(response)
            raise Exception(f"Failed to create FileBay user: {error_msg}")
        
        return password

    def create_filebay_repo(self, username: str, repo_name: str) -> dict[str, Any]:
        """
        Create a private repository for the user.
        
        Args:
            username: Repository owner username
            repo_name: Repository name
            
        Returns:
            Repository information
            
        Raises:
            Exception: If repository creation fails
        """
        payload = {
            "name": repo_name,
            "private": True,
            "auto_init": True,
            "default_branch": self.default_branch,
        }
        
        response = self._request(
            method="POST",
            path=f"/api/v1/admin/users/{username}/repos",
            json_payload=payload,
        )
        
        if response.status_code not in (200, 201):
            # Check if repo already exists
            if self._looks_like_already_exists(response):
                logger.warning("[FileBay Auto Provision] Repo %s/%s already exists", username, repo_name)
                return {}
            
            error_msg = self._extract_error_message(response)
            raise Exception(f"Failed to create FileBay repository: {error_msg}")
        
        return response.json()

    def generate_filebay_token(self, username: str) -> str:
        """
        Generate an access token for the user using admin privileges.
        
        Args:
            username: Username to generate token for
            
        Returns:
            Access token (sha1)
            
        Raises:
            Exception: If token generation fails
        """
        token_name = f"desktop_auto_{secrets.token_hex(4)}"
        
        payload = {
            "name": token_name,
            "scopes": ["read:repository", "write:repository", "read:user"],
        }
        
        # Use admin to create token for user
        response = self._request(
            method="POST",
            path=f"/api/v1/admin/users/{username}/tokens",
            json_payload=payload,
        )
        
        if response.status_code not in (200, 201):
            error_msg = self._extract_error_message(response)
            raise Exception(f"Failed to generate FileBay token: {error_msg}")
        
        data = response.json()
        token = data.get("sha1")
        
        if not token:
            raise Exception("Token generation succeeded but no token returned")
        
        return token

    def init_masked_directory(self, username: str, repo_name: str, token: str):
        """
        Initialize the masked directory in the repository.
        
        Args:
            username: Repository owner
            repo_name: Repository name
            token: Access token
            
        Raises:
            Exception: If directory initialization fails
        """
        placeholder_path = f"{self.masked_dir}/.keep"
        
        # Check if already exists
        existing = self._get_content(username, repo_name, placeholder_path)
        if existing:
            logger.info("[FileBay Auto Provision] Masked directory already initialized")
            return
        
        # Create placeholder file
        content = "# Masked Directory\n\nThis directory is for masked/sensitive files.\n"
        content_base64 = base64.b64encode(content.encode()).decode()
        
        payload = {
            "message": f"Initialize {self.masked_dir} directory",
            "content": content_base64,
            "branch": self.default_branch,
        }
        
        # Use admin auth for initialization
        response = self._request(
            method="POST",
            path=f"/api/v1/repos/{username}/{repo_name}/contents/{placeholder_path}",
            json_payload=payload,
        )
        
        if response.status_code not in (200, 201):
            # Check if already exists
            if self._looks_like_already_exists(response):
                logger.warning("[FileBay Auto Provision] Masked directory already exists")
                return
            
            error_msg = self._extract_error_message(response)
            raise Exception(f"Failed to initialize masked directory: {error_msg}")

    def _get_user(self, username: str) -> dict[str, Any] | None:
        """Get user information."""
        response = self._request(
            method="GET",
            path=f"/api/v1/users/{username}",
        )
        
        if response.status_code == 404:
            return None
        if response.status_code != 200:
            return None
        
        return response.json()

    def _get_repo(self, owner: str, repo_name: str) -> dict[str, Any] | None:
        """Get repository information."""
        response = self._request(
            method="GET",
            path=f"/api/v1/repos/{owner}/{repo_name}",
        )
        
        if response.status_code == 404:
            return None
        if response.status_code != 200:
            return None
        
        return response.json()

    def _get_content(self, owner: str, repo_name: str, path: str) -> dict[str, Any] | None:
        """Get file content information."""
        response = self._request(
            method="GET",
            path=f"/api/v1/repos/{owner}/{repo_name}/contents/{path}",
        )
        
        if response.status_code == 404:
            return None
        if response.status_code != 200:
            return None
        
        return response.json()

    def _request(
        self,
        *,
        method: str,
        path: str,
        json_payload: dict[str, Any] | None = None,
    ) -> requests.Response:
        """Make HTTP request to FileBay API."""
        url = f"{self.filebay_base_url}{path}"
        
        try:
            response = requests.request(
                method=method,
                url=url,
                auth=(self.admin_username, self.admin_password),
                json=json_payload,
                timeout=self.http_timeout,
                verify=self.ssl_verify,
            )
            return response
        except requests.RequestException as exc:
            raise Exception(f"Request to {url} failed: {exc}") from exc

    def _generate_password(self, length: int = 16) -> str:
        """Generate a secure random password."""
        alphabet = string.ascii_letters + string.digits
        random_part = "".join(secrets.choice(alphabet) for _ in range(max(8, length - 4)))
        return f"Aa1!{random_part}"[:length]

    def _extract_error_message(self, response: requests.Response) -> str:
        """Extract error message from response."""
        try:
            data = response.json()
            message = data.get("message") or data.get("msg") or data.get("error")
            if message:
                return f"HTTP {response.status_code}: {message}"
        except Exception:
            pass
        
        return f"HTTP {response.status_code}: {response.text[:200]}"

    def _looks_like_already_exists(self, response: requests.Response) -> bool:
        """Check if error indicates resource already exists."""
        if response.status_code in (409, 422):
            return True
        
        try:
            data = response.json()
            message = str(data.get("message", "")).lower()
            if any(keyword in message for keyword in ["already exists", "has been taken", "duplicate"]):
                return True
        except Exception:
            pass
        
        return False
