"""
Vault 同步服务

负责在用户登录后自动同步 FileBay 配置到 Vault
"""

import logging
import requests
from typing import Optional, Dict, Any
import json
import os

logger = logging.getLogger(__name__)

VAULT_API_URL = "http://localhost:7788"
VAULT_API_TIMEOUT = 5  # 秒


class VaultSyncService:
    """Vault 同步服务"""

    @staticmethod
    def is_vault_available() -> bool:
        """
        检查 Vault API 是否可用
        
        Returns:
            bool: Vault API 是否可用
        """
        try:
            response = requests.get(
                f"{VAULT_API_URL}/api/v1/health",
                timeout=VAULT_API_TIMEOUT
            )
            return response.status_code == 200
        except Exception as e:
            logger.debug(f"Vault API not available: {e}")
            return False

    @staticmethod
    def sync_filebay_config_to_vault(config: Dict[str, Any]) -> bool:
        """
        同步 FileBay 配置到 Vault
        
        Args:
            config: FileBay 配置字典，包含:
                - url: FileBay URL
                - username: 用户名
                - repo_name: 仓库名
                - email: 邮箱
                - token: 访问令牌
                - downloaded_at: 下载时间 (可选)
                - version: 版本 (可选)
        
        Returns:
            bool: 是否同步成功
        """
        try:
            # 检查 Vault 是否可用
            if not VaultSyncService.is_vault_available():
                logger.warning("Vault API is not available, skipping FileBay config sync")
                return False

            # 发送配置到 Vault
            response = requests.post(
                f"{VAULT_API_URL}/api/v1/filebay/config",
                json=config,
                timeout=VAULT_API_TIMEOUT
            )

            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    logger.info(f"✅ FileBay config synced to Vault successfully for user: {config.get('username')}")
                    return True
                else:
                    logger.error(f"❌ Vault API returned error: {data.get('message')}")
                    return False
            else:
                logger.error(f"❌ Failed to sync FileBay config to Vault: HTTP {response.status_code}")
                return False

        except requests.exceptions.Timeout:
            logger.warning("⏱️ Vault API request timeout, skipping sync")
            return False
        except Exception as e:
            logger.error(f"❌ Error syncing FileBay config to Vault: {e}")
            return False

    @staticmethod
    def sync_filebay_config_from_file(file_path: str) -> bool:
        """
        从文件读取 FileBay 配置并同步到 Vault
        
        Args:
            file_path: FileBay 配置文件路径
        
        Returns:
            bool: 是否同步成功
        """
        try:
            if not os.path.exists(file_path):
                logger.debug(f"FileBay config file not found: {file_path}")
                return False

            with open(file_path, 'r', encoding='utf-8') as f:
                file_config = json.load(f)

            # 转换为 API 格式
            config = {
                "url": file_config.get('url'),
                "username": file_config.get('username'),
                "repo_name": file_config.get('repoName'),
                "email": file_config.get('email'),
                "token": file_config.get('token'),
                "downloaded_at": file_config.get('downloadedAt'),
                "version": file_config.get('version', '1.0.0')
            }

            return VaultSyncService.sync_filebay_config_to_vault(config)

        except json.JSONDecodeError as e:
            logger.error(f"❌ Invalid JSON in FileBay config file: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Error reading FileBay config file: {e}")
            return False

    @staticmethod
    def auto_sync_on_login(account_id: str) -> bool:
        """
        登录时自动同步 FileBay 配置
        
        这个方法会尝试从多个位置查找 FileBay 配置:
        1. 用户特定的配置文件
        2. 全局配置文件
        
        Args:
            account_id: 账户 ID
        
        Returns:
            bool: 是否同步成功
        """
        try:
            # 尝试从环境变量或配置中获取 Vault 路径
            vault_base_path = os.environ.get('VAULT_BASE_PATH', r'E:\CheersAI脱敏\cheersai-desktop')
            
            # 可能的配置文件位置
            config_paths = [
                os.path.join(vault_base_path, 'filebay-config.json'),
                # 可以添加更多路径
            ]

            for config_path in config_paths:
                if os.path.exists(config_path):
                    logger.info(f"📋 Found FileBay config at: {config_path}")
                    if VaultSyncService.sync_filebay_config_from_file(config_path):
                        logger.info(f"✅ Auto-sync completed for account: {account_id}")
                        return True
                    else:
                        logger.warning(f"⚠️ Failed to sync config from: {config_path}")

            logger.debug(f"No FileBay config found for account: {account_id}")
            return False

        except Exception as e:
            logger.error(f"❌ Error in auto-sync: {e}")
            return False
