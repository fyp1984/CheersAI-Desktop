"""Gitea storage service for file retrieval."""
import os
import ssl
import warnings

import requests
from requests.adapters import HTTPAdapter
from urllib3.poolmanager import PoolManager

# Suppress SSL warnings when verification is disabled
warnings.filterwarnings('ignore', message='Unverified HTTPS request')


class SSLAdapter(HTTPAdapter):
    """Custom HTTPAdapter that uses legacy SSL settings for compatibility."""
    
    def init_poolmanager(self, *args, **kwargs):
        """Initialize pool manager with custom SSL context."""
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        # Allow legacy SSL/TLS versions and weak ciphers for compatibility
        try:
            context.minimum_version = ssl.TLSVersion.TLSv1
        except AttributeError:
            # Python < 3.7
            pass
        try:
            context.set_ciphers('DEFAULT@SECLEVEL=0')
        except ssl.SSLError:
            context.set_ciphers('DEFAULT')
        # Disable certificate validation completely
        context.options |= ssl.OP_NO_SSLv2 | ssl.OP_NO_SSLv3
        kwargs['ssl_context'] = context
        return super().init_poolmanager(*args, **kwargs)


class GiteaStorageService:
    """Service for retrieving files from Gitea."""

    def __init__(self):
        """Initialize Gitea storage service."""
        self.gitea_url = os.getenv("GITEA_URL", "http://localhost:3000").rstrip("/")
        self.gitea_proxy_url = os.getenv("GITEA_PROXY_URL", "").rstrip("/")
        self.gitea_token = os.getenv("GITEA_TOKEN", "")
        self.gitea_owner = os.getenv("GITEA_OWNER", "cheersai")
        self.gitea_repo = os.getenv("GITEA_REPO", "file-storage")
        self.request_base_url = self.gitea_proxy_url or self.gitea_url

        # Token is optional for public repositories
        self.use_auth = bool(self.gitea_token)
        
        # SSL verification setting (set to False for self-signed certificates)
        self.verify_ssl = os.getenv("GITEA_VERIFY_SSL", "true").lower() == "true"
        
        # Create session - pyOpenSSL should already be injected by core.ssl_config
        # No need for custom SSLAdapter when using pyOpenSSL
        self.session = requests.Session()

    def get_file(self, file_path: str) -> bytes:
        """
        Get file content from Gitea repository.
        
        Args:
            file_path: Path to the file in the repository
            
        Returns:
            bytes: File content
        """
        # Use raw file URL for direct download
        raw_url = f"{self.request_base_url}/{self.gitea_owner}/{self.gitea_repo}/raw/branch/main/{file_path}"
        
        headers = {}
        if self.use_auth:
            headers["Authorization"] = f"token {self.gitea_token}"
        
        response = self.session.get(raw_url, headers=headers, timeout=30, verify=self.verify_ssl)
        
        if response.status_code == 200:
            return response.content
        elif response.status_code == 404:
            raise FileNotFoundError(f"File not found in Gitea: {file_path}")
        else:
            raise Exception(f"Failed to get file from Gitea: {response.status_code} - {response.text}")

    def get_file_metadata(self, file_path: str) -> dict:
        """
        Get file metadata from Gitea repository.
        
        Args:
            file_path: Path to the file in the repository
            
        Returns:
            dict: File metadata including name, size, sha, etc.
        """
        api_url = f"{self.request_base_url}/api/v1/repos/{self.gitea_owner}/{self.gitea_repo}/contents/{file_path}"
        
        headers = {}
        if self.use_auth:
            headers["Authorization"] = f"token {self.gitea_token}"
        
        response = self.session.get(api_url, headers=headers, timeout=10, verify=self.verify_ssl)
        
        if response.status_code == 200:
            data = response.json()
            return {
                "name": data.get("name"),
                "path": data.get("path"),
                "sha": data.get("sha"),
                "size": data.get("size"),
                "url": data.get("download_url"),
                "type": data.get("type"),
            }
        elif response.status_code == 404:
            raise FileNotFoundError(f"File not found in Gitea: {file_path}")
        else:
            raise Exception(f"Failed to get file metadata: {response.status_code}")

    def list_files(self, directory_path: str = "") -> list:
        """
        List files in a directory in Gitea repository.
        
        Args:
            directory_path: Path to the directory in the repository
            
        Returns:
            list: List of file metadata dictionaries
        """
        api_url = f"{self.request_base_url}/api/v1/repos/{self.gitea_owner}/{self.gitea_repo}/contents/{directory_path}"
        
        headers = {}
        if self.use_auth:
            headers["Authorization"] = f"token {self.gitea_token}"
        
        response = self.session.get(api_url, headers=headers, timeout=10, verify=self.verify_ssl)
        
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list):
                return [
                    {
                        "name": item.get("name"),
                        "path": item.get("path"),
                        "type": item.get("type"),
                        "size": item.get("size"),
                        "sha": item.get("sha"),
                        "url": item.get("download_url"),
                    }
                    for item in data
                ]
            return []
        elif response.status_code == 404:
            raise FileNotFoundError(f"Directory not found in Gitea: {directory_path}")
        else:
            raise Exception(f"Failed to list files: {response.status_code}")

    def get_file_url(self, file_path: str) -> str:
        """
        Get the download URL for a file.
        
        Args:
            file_path: Path to the file in the repository
            
        Returns:
            str: Download URL
        """
        return f"{self.gitea_url}/{self.gitea_owner}/{self.gitea_repo}/raw/branch/main/{file_path}"

    def file_exists(self, file_path: str) -> bool:
        """
        Check if a file exists in Gitea repository.
        
        Args:
            file_path: Path to the file in the repository
            
        Returns:
            bool: True if file exists, False otherwise
        """
        try:
            self.get_file_metadata(file_path)
            return True
        except FileNotFoundError:
            return False
        except Exception:
            return False
