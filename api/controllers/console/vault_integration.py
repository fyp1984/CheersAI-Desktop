"""
Vault Integration Controller - Desktop 与 Vault 的集成接口

功能:
1. 登录后自动推送 FileBay 配置到 Vault
2. 提供手动同步接口
"""

from flask import request
from flask_login import current_user, login_required
from flask_restful import Resource, marshal_with, reqparse

from controllers.console import api
from controllers.console.wraps import account_initialization_required
from libs.filebay_user_config import resolve_user_filebay_config
from services.filebay_config_service import resolve_filebay_config

import requests
import logging

logger = logging.getLogger(__name__)


class VaultConfigSyncApi(Resource):
    """同步 FileBay 配置到 Vault"""

    @login_required
    @account_initialization_required
    def post(self):
        """
        推送 FileBay 配置到 Vault
        
        请求参数:
        - vault_api_url: Vault API 地址 (可选, 默认 http://localhost:7788)
        
        返回:
        - success: 是否成功
        - message: 消息
        """
        parser = reqparse.RequestParser()
        parser.add_argument('vault_api_url', type=str, required=False, location='json')
        args = parser.parse_args()

        vault_api_url = args.get('vault_api_url') or 'http://localhost:7788'
        
        try:
            # 1. 获取当前用户的 FileBay 配置
            user_email = current_user.email
            logger.info(f"[Vault Sync] Resolving FileBay config for user: {user_email}")
            
            # 使用 resolve_user_filebay_config 获取用户配置
            config_dict = resolve_user_filebay_config(
                identifier=user_email,
                account=current_user,
                mask_token=False,
                allow_global_fallback=False,
                log_prefix="[Vault Sync]"
            )
            
            if not config_dict:
                logger.warning(f"[Vault Sync] No FileBay config found for {user_email}")
                return {
                    'success': False,
                    'message': '未找到 FileBay 配置，请先在设置中配置 FileBay'
                }, 404
            
            # 2. 构建 Vault API 请求
            vault_payload = {
                'url': config_dict.get('gitea_url', ''),
                'username': config_dict.get('gitea_owner', ''),
                'repo_name': config_dict.get('gitea_repo', ''),
                'email': user_email,
                'token': config_dict.get('gitea_token', ''),
                'downloaded_at': '',  # 可以添加时间戳
                'version': '1.0'
            }
            
            logger.info(f"[Vault Sync] Sending config to Vault API: {vault_api_url}")
            logger.info(f"[Vault Sync] Config: url={vault_payload['url']}, username={vault_payload['username']}, repo={vault_payload['repo_name']}")
            
            # 3. 调用 Vault API
            response = requests.post(
                f"{vault_api_url}/api/v1/filebay/config",
                json=vault_payload,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    logger.info(f"[Vault Sync] Successfully synced config to Vault for {user_email}")
                    return {
                        'success': True,
                        'message': 'FileBay 配置已成功同步到 Vault'
                    }, 200
                else:
                    logger.error(f"[Vault Sync] Vault API returned error: {result.get('message')}")
                    return {
                        'success': False,
                        'message': f"Vault API 返回错误: {result.get('message')}"
                    }, 500
            else:
                logger.error(f"[Vault Sync] Vault API request failed: {response.status_code}")
                return {
                    'success': False,
                    'message': f'Vault API 请求失败: HTTP {response.status_code}'
                }, 500
                
        except requests.exceptions.ConnectionError:
            logger.error("[Vault Sync] Cannot connect to Vault API - is Vault running?")
            return {
                'success': False,
                'message': '无法连接到 Vault，请确保 Vault 应用正在运行'
            }, 503
        except requests.exceptions.Timeout:
            logger.error("[Vault Sync] Vault API request timeout")
            return {
                'success': False,
                'message': 'Vault API 请求超时'
            }, 504
        except Exception as e:
            logger.exception(f"[Vault Sync] Unexpected error: {e}")
            return {
                'success': False,
                'message': f'同步失败: {str(e)}'
            }, 500


class VaultHealthCheckApi(Resource):
    """检查 Vault API 健康状态"""

    def get(self):
        """
        检查 Vault API 是否可用
        
        请求参数:
        - vault_api_url: Vault API 地址 (可选, 默认 http://localhost:7788)
        
        返回:
        - available: Vault 是否可用
        - message: 消息
        """
        parser = reqparse.RequestParser()
        parser.add_argument('vault_api_url', type=str, required=False, location='args')
        args = parser.parse_args()

        vault_api_url = args.get('vault_api_url') or 'http://localhost:7788'
        
        try:
            response = requests.get(
                f"{vault_api_url}/api/v1/health",
                timeout=3
            )
            
            if response.status_code == 200:
                return {
                    'available': True,
                    'message': 'Vault API 可用'
                }, 200
            else:
                return {
                    'available': False,
                    'message': f'Vault API 返回错误: HTTP {response.status_code}'
                }, 200
                
        except requests.exceptions.ConnectionError:
            return {
                'available': False,
                'message': 'Vault 未运行或无法连接'
            }, 200
        except requests.exceptions.Timeout:
            return {
                'available': False,
                'message': 'Vault API 请求超时'
            }, 200
        except Exception as e:
            return {
                'available': False,
                'message': f'检查失败: {str(e)}'
            }, 200


# 注册路由
api.add_resource(VaultConfigSyncApi, '/vault/sync-config')
api.add_resource(VaultHealthCheckApi, '/vault/health')
