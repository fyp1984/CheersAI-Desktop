#!/usr/bin/env python3
"""启动 Vault Bridge 服务的独立脚本

用法：
    python start_vault_bridge.py [--port PORT] [--debug]

示例：
    python start_vault_bridge.py
    python start_vault_bridge.py --port 8765
    python start_vault_bridge.py --port 8765 --debug
"""
import argparse
import logging
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from services.vault_bridge_service import start_vault_bridge


def main():
    parser = argparse.ArgumentParser(
        description='启动 Vault Bridge 服务，用于 Desktop 登录后同步 FileBay 配置到脱敏系统'
    )
    parser.add_argument(
        '--port',
        type=int,
        default=8765,
        help='监听端口（默认: 8765）'
    )
    parser.add_argument(
        '--host',
        type=str,
        default='127.0.0.1',
        help='监听地址（默认: 127.0.0.1，只允许本地访问）'
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        help='启用调试模式'
    )
    
    args = parser.parse_args()
    
    # 配置日志
    log_level = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('vault_bridge.log')
        ]
    )
    
    logger = logging.getLogger(__name__)
    logger.info('=' * 60)
    logger.info('Vault Bridge Service')
    logger.info('=' * 60)
    logger.info(f'Host: {args.host}')
    logger.info(f'Port: {args.port}')
    logger.info(f'Debug: {args.debug}')
    logger.info('=' * 60)
    
    try:
        start_vault_bridge(host=args.host, port=args.port, debug=args.debug)
    except KeyboardInterrupt:
        logger.info('Vault Bridge service stopped by user')
    except Exception as e:
        logger.error('Vault Bridge service failed: %s', e, exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
