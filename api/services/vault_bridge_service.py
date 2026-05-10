"""Vault Bridge Service - 本地监听服务，用于 Desktop 登录后同步 FileBay 配置到脱敏系统

架构：
Desktop 登录成功 → HTTP POST → Vault Bridge (localhost:8765) → SQLite DB → 脱敏系统读取

数据库位置：~/.cheersai/vault.db
"""
import json
import sqlite3
import logging
from pathlib import Path
from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime

logger = logging.getLogger(__name__)

# Vault 数据库路径
VAULT_DB_PATH = Path.home() / '.cheersai' / 'vault.db'


def init_vault_db():
    """初始化 Vault 数据库"""
    try:
        VAULT_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        
        conn = sqlite3.connect(VAULT_DB_PATH)
        cursor = conn.cursor()
        
        # 创建 filebay_configs 表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS filebay_configs (
                user_id TEXT PRIMARY KEY,
                url TEXT NOT NULL,
                username TEXT NOT NULL,
                repo_name TEXT NOT NULL,
                email TEXT,
                token TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 创建索引
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_filebay_configs_email 
            ON filebay_configs(email)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_filebay_configs_username 
            ON filebay_configs(username)
        ''')
        
        conn.commit()
        conn.close()
        
        logger.info(f"Vault database initialized at {VAULT_DB_PATH}")
    except Exception as e:
        logger.error(f"Failed to initialize Vault database: {e}")
        raise


def create_vault_bridge_app():
    """创建 Vault Bridge Flask 应用"""
    app = Flask(__name__)
    CORS(app)  # 允许跨域请求
    
    @app.route('/health', methods=['GET'])
    def health_check():
        """健康检查端点"""
        return jsonify({
            'status': 'ok',
            'service': 'vault-bridge',
            'version': '1.0.0',
            'database': str(VAULT_DB_PATH),
            'database_exists': VAULT_DB_PATH.exists()
        })
    
    @app.route('/vault/config/filebay', methods=['POST'])
    def receive_filebay_config():
        """接收并保存 FileBay 配置
        
        请求体：
        {
            "user_id": "用户ID",
            "config": {
                "url": "FileBay URL",
                "username": "FileBay 用户名",
                "repoName": "仓库名",
                "email": "用户邮箱",
                "token": "访问 Token"
            }
        }
        """
        try:
            data = request.json
            if not data:
                return jsonify({'error': 'Request body is required'}), 400
            
            user_id = data.get('user_id')
            config = data.get('config')
            
            if not user_id:
                return jsonify({'error': 'Missing user_id'}), 400
            
            if not config or not isinstance(config, dict):
                return jsonify({'error': 'Missing or invalid config'}), 400
            
            # 验证必需字段
            required_fields = ['url', 'username', 'repoName', 'token']
            missing_fields = [f for f in required_fields if not config.get(f)]
            if missing_fields:
                return jsonify({
                    'error': f'Missing required config fields: {", ".join(missing_fields)}'
                }), 400
            
            # 保存到数据库
            conn = sqlite3.connect(VAULT_DB_PATH)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO filebay_configs 
                (user_id, url, username, repo_name, email, token, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                user_id,
                config.get('url'),
                config.get('username'),
                config.get('repoName'),
                config.get('email', ''),
                config.get('token'),
                datetime.now().isoformat()
            ))
            
            conn.commit()
            conn.close()
            
            logger.info(f"FileBay config saved for user {user_id} (username: {config.get('username')})")
            
            return jsonify({
                'success': True,
                'message': 'FileBay config saved to Vault',
                'user_id': user_id,
                'username': config.get('username'),
                'repo_name': config.get('repoName')
            })
        
        except Exception as e:
            logger.error(f"Failed to save FileBay config: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/vault/config/filebay/<user_id>', methods=['GET'])
    def get_filebay_config(user_id):
        """获取 FileBay 配置
        
        路径参数：
            user_id: 用户ID
        
        返回：
        {
            "url": "FileBay URL",
            "username": "FileBay 用户名",
            "repoName": "仓库名",
            "email": "用户邮箱",
            "token": "访问 Token",
            "updatedAt": "更新时间"
        }
        """
        try:
            if not VAULT_DB_PATH.exists():
                return jsonify({'error': 'Vault database not found'}), 404
            
            conn = sqlite3.connect(VAULT_DB_PATH)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT url, username, repo_name, email, token, updated_at
                FROM filebay_configs
                WHERE user_id = ?
            ''', (user_id,))
            
            row = cursor.fetchone()
            conn.close()
            
            if not row:
                return jsonify({'error': 'Config not found for this user'}), 404
            
            return jsonify({
                'url': row[0],
                'username': row[1],
                'repoName': row[2],
                'email': row[3],
                'token': row[4],
                'updatedAt': row[5]
            })
        
        except Exception as e:
            logger.error(f"Failed to get FileBay config: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/vault/config/filebay/by-email/<email>', methods=['GET'])
    def get_filebay_config_by_email(email):
        """通过邮箱获取 FileBay 配置"""
        try:
            if not VAULT_DB_PATH.exists():
                return jsonify({'error': 'Vault database not found'}), 404
            
            conn = sqlite3.connect(VAULT_DB_PATH)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT user_id, url, username, repo_name, email, token, updated_at
                FROM filebay_configs
                WHERE email = ?
            ''', (email,))
            
            row = cursor.fetchone()
            conn.close()
            
            if not row:
                return jsonify({'error': 'Config not found for this email'}), 404
            
            return jsonify({
                'userId': row[0],
                'url': row[1],
                'username': row[2],
                'repoName': row[3],
                'email': row[4],
                'token': row[5],
                'updatedAt': row[6]
            })
        
        except Exception as e:
            logger.error(f"Failed to get FileBay config by email: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/vault/config/filebay/<user_id>', methods=['DELETE'])
    def delete_filebay_config(user_id):
        """删除 FileBay 配置"""
        try:
            if not VAULT_DB_PATH.exists():
                return jsonify({'error': 'Vault database not found'}), 404
            
            conn = sqlite3.connect(VAULT_DB_PATH)
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM filebay_configs WHERE user_id = ?', (user_id,))
            deleted_count = cursor.rowcount
            
            conn.commit()
            conn.close()
            
            if deleted_count == 0:
                return jsonify({'error': 'Config not found'}), 404
            
            logger.info(f"FileBay config deleted for user {user_id}")
            
            return jsonify({
                'success': True,
                'message': 'FileBay config deleted from Vault'
            })
        
        except Exception as e:
            logger.error(f"Failed to delete FileBay config: {e}")
            return jsonify({'error': str(e)}), 500
    
    return app


def start_vault_bridge(host='127.0.0.1', port=8765, debug=False):
    """启动 Vault Bridge 服务
    
    Args:
        host: 监听地址（默认 127.0.0.1，只允许本地访问）
        port: 监听端口（默认 8765）
        debug: 是否启用调试模式
    """
    # 初始化数据库
    init_vault_db()
    
    # 创建应用
    app = create_vault_bridge_app()
    
    logger.info(f"Starting Vault Bridge service on {host}:{port}")
    logger.info(f"Database location: {VAULT_DB_PATH}")
    
    # 启动服务
    app.run(host=host, port=port, debug=debug, threaded=True)


if __name__ == '__main__':
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 启动服务
    start_vault_bridge()
