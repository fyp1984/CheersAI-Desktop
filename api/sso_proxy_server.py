#!/usr/bin/env python3
"""
SSO Proxy Server - Forwards SSO requests from Docker containers to SSO server via host
This solves the SSL/network connectivity issue between Docker and SSO server
"""
import logging
import sys
from flask import Flask, request, jsonify
import requests
import urllib3

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

SSO_BASE_URL = "https://uat-sso.cheersai.cloud"

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({"status": "ok"}), 200

@app.route('/api/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH'])
def proxy_api(path):
    """Proxy all /api/* requests to SSO server"""
    try:
        target_url = f"{SSO_BASE_URL}/api/{path}"
        logger.info(f"Proxying {request.method} request to: {target_url}")
        
        # Forward headers (exclude host)
        headers = {k: v for k, v in request.headers if k.lower() != 'host'}
        
        # Make request to SSO server with SSL verification disabled
        response = requests.request(
            method=request.method,
            url=target_url,
            headers=headers,
            params=request.args,
            data=request.get_data(),
            verify=False,  # Disable SSL verification
            timeout=30,
            allow_redirects=False
        )
        
        logger.info(f"SSO response: {response.status_code}")
        
        # Return response
        return response.content, response.status_code, dict(response.headers)
        
    except requests.RequestException as e:
        logger.error(f"Proxy request failed: {str(e)}", exc_info=True)
        return jsonify({"error": "Failed to connect to SSO server", "details": str(e)}), 502
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        return jsonify({"error": "Internal proxy error", "details": str(e)}), 500

@app.route('/login/<path:path>', methods=['GET'])
def proxy_login(path):
    """Proxy login page requests"""
    try:
        target_url = f"{SSO_BASE_URL}/login/{path}"
        logger.info(f"Proxying login request to: {target_url}")
        
        headers = {k: v for k, v in request.headers if k.lower() != 'host'}
        
        response = requests.get(
            target_url,
            headers=headers,
            params=request.args,
            verify=False,
            timeout=30,
            allow_redirects=False
        )
        
        return response.content, response.status_code, dict(response.headers)
        
    except Exception as e:
        logger.error(f"Login proxy failed: {str(e)}", exc_info=True)
        return jsonify({"error": "Failed to proxy login", "details": str(e)}), 502

if __name__ == '__main__':
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 5555
    logger.info(f"Starting SSO Proxy Server on port {port}")
    logger.info(f"Proxying requests to: {SSO_BASE_URL}")
    app.run(host='0.0.0.0', port=port, debug=False)
