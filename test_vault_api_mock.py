#!/usr/bin/env python3
"""
Vault API Mock Server - 用于测试 Desktop 集成
模拟 Vault API 服务器，无需编译 Rust 代码
"""

from flask import Flask, request, jsonify
from datetime import datetime

app = Flask(__name__)

# 模拟存储
config_storage = {}

@app.route('/api/v1/health', methods=['GET'])
def health():
    """健康检查"""
    return jsonify({
        'success': True,
        'message': 'Vault API Mock Server is running',
        'data': None
    })

@app.route('/api/v1/filebay/config', methods=['POST'])
def save_config():
    """保存配置"""
    try:
        data = request.get_json()
        
        # 验证必需字段
        required_fields = ['url', 'username', 'repo_name', 'email', 'token']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'message': f'Missing required field: {field}',
                    'data': None
                }), 400
        
        # 保存配置
        config_storage['filebay_config'] = {
            **data,
            'saved_at': datetime.now().isoformat()
        }
        
        print(f"\n✅ Config saved:")
        print(f"   URL: {data['url']}")
        print(f"   Username: {data['username']}")
        print(f"   Repo: {data['repo_name']}")
        print(f"   Email: {data['email']}")
        print(f"   Token: {data['token'][:10]}..." if len(data['token']) > 10 else data['token'])
        
        return jsonify({
            'success': True,
            'message': 'FileBay configuration saved successfully',
            'data': data
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}',
            'data': None
        }), 500

@app.route('/api/v1/filebay/config', methods=['GET'])
def get_config():
    """获取配置"""
    if 'filebay_config' in config_storage:
        return jsonify({
            'success': True,
            'message': 'Configuration retrieved successfully',
            'data': config_storage['filebay_config']
        })
    else:
        return jsonify({
            'success': False,
            'message': 'No configuration found',
            'data': None
        }), 404

@app.route('/api/v1/filebay/config', methods=['DELETE'])
def delete_config():
    """删除配置"""
    if 'filebay_config' in config_storage:
        del config_storage['filebay_config']
        print("\n🗑️  Config deleted")
        return jsonify({
            'success': True,
            'message': 'Configuration deleted successfully',
            'data': None
        })
    else:
        return jsonify({
            'success': False,
            'message': 'No configuration found',
            'data': None
        }), 404

if __name__ == '__main__':
    print("\n" + "="*60)
    print("  🚀 Vault API Mock Server")
    print("="*60)
    print("\n  监听地址: http://localhost:7788")
    print("  健康检查: http://localhost:7788/api/v1/health")
    print("\n  按 Ctrl+C 停止服务器\n")
    print("="*60 + "\n")
    
    app.run(host='127.0.0.1', port=7788, debug=True)
