# Vault 与 Desktop 脱敏系统集成方案

## 架构概述

### 系统组成
1. **CheersAI-Desktop (Vault系统)** - `E:\CheersAI-Desktop`
   - Web 端：Next.js + Tauri
   - API 端：Python Flask
   - 功能：用户认证、FileBay 配置管理、在线工作区

2. **cheersai-desktop (脱敏系统)** - `E:\CheersAI脱敏\cheersai-desktop`
   - Tauri Desktop App
   - 功能：文件脱敏、沙箱管理、FileBay 上传

## 集成目标

实现 Desktop 登录成功后，自动将 FileBay 配置信息写入本地 Vault 数据库，供脱敏系统使用。

## 当前实现状态

### ✅ 已实现功能

1. **Vault 系统 (CheersAI-Desktop)**
   - Desktop SSO 登录流程
   - FileBay 配置管理 API
   - FileBay 配置文件下载功能
   - 用户认证和权限管理
   - **Vault Bridge 服务** - 本地监听服务（localhost:8765）
   - **自动配置同步** - 登录成功后自动同步 FileBay 配置到 Vault 数据库

2. **脱敏系统 (cheersai-desktop)**
   - FileBay 配置读取/导入
   - 文件脱敏功能
   - 沙箱管理
   - FileBay 上传接口（待实现）

### 🔄 需要集成的部分

1. **脱敏系统读取 Vault 配置**
   - 创建 Rust 命令读取 Vault 数据库
   - 在 UI 中添加自动加载配置功能

## 集成方案

### 方案 A：HTTP 本地服务通信（推荐）

#### 架构
```
Desktop App (登录成功)
    ↓ HTTP POST
Vault Local Service (localhost:8765)
    ↓ 写入
Vault Database (SQLite/PostgreSQL)
    ↓ 读取
脱敏系统 (cheersai-desktop)
```

#### 优点
- 简单可靠
- 跨平台兼容
- 易于调试
- 支持远程调用

#### 实现步骤

1. **在 Vault 系统中创建本地监听服务**
   ```python
   # api/services/vault_bridge_service.py
   from flask import Flask, request, jsonify
   
   app = Flask(__name__)
   
   @app.route('/vault/config/filebay', methods=['POST'])
   def receive_filebay_config():
       data = request.json
       user_id = data.get('user_id')
       config = data.get('config')
       
       # 写入数据库
       save_filebay_config_to_vault(user_id, config)
       
       return jsonify({'success': True})
   ```

2. **在 Desktop 登录成功后调用**
   ```typescript
   // web/service/sso.ts
   export const notifyVaultBridge = async (userId: string, config: FileBayConfig) => {
     try {
       await fetch('http://localhost:8765/vault/config/filebay', {
         method: 'POST',
         headers: { 'Content-Type': 'application/json' },
         body: JSON.stringify({ user_id: userId, config })
       })
     } catch (error) {
       console.error('Failed to notify Vault bridge:', error)
     }
   }
   ```

3. **脱敏系统读取配置**
   ```rust
   // cheersai-desktop/src-tauri/src/commands/vault.rs
   #[tauri::command]
   pub async fn read_vault_filebay_config(user_id: String) -> Result<FileBayConfig, String> {
       // 从 Vault 数据库读取配置
       let config = query_vault_database(&user_id)?;
       Ok(config)
   }
   ```

### 方案 B：共享数据库文件

#### 架构
```
Desktop App (登录成功)
    ↓ 写入
Shared SQLite File (~/.cheersai/vault.db)
    ↓ 读取
脱敏系统 (cheersai-desktop)
```

#### 优点
- 无需额外服务
- 性能更好
- 离线可用

#### 缺点
- 需要处理文件锁
- 跨平台路径处理复杂

### 方案 C：Tauri IPC 通信

#### 架构
```
Desktop App (Tauri)
    ↓ Tauri IPC
Vault System (Tauri)
    ↓ 写入
Vault Database
```

#### 优点
- Tauri 原生支持
- 类型安全

#### 缺点
- 需要两个 Tauri 应用同时运行
- 复杂度较高

## 推荐实现：方案 A（HTTP 本地服务）

### 详细实现步骤

#### 1. 创建 Vault Bridge 服务

```python
# api/services/vault_bridge_service.py
import json
import sqlite3
from pathlib import Path
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # 允许跨域

# Vault 数据库路径
VAULT_DB_PATH = Path.home() / '.cheersai' / 'vault.db'

def init_vault_db():
    """初始化 Vault 数据库"""
    VAULT_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    conn = sqlite3.connect(VAULT_DB_PATH)
    cursor = conn.cursor()
    
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
    
    conn.commit()
    conn.close()

@app.route('/health', methods=['GET'])
def health_check():
    """健康检查"""
    return jsonify({'status': 'ok', 'service': 'vault-bridge'})

@app.route('/vault/config/filebay', methods=['POST'])
def receive_filebay_config():
    """接收并保存 FileBay 配置"""
    try:
        data = request.json
        user_id = data.get('user_id')
        config = data.get('config')
        
        if not user_id or not config:
            return jsonify({'error': 'Missing user_id or config'}), 400
        
        # 保存到数据库
        conn = sqlite3.connect(VAULT_DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO filebay_configs 
            (user_id, url, username, repo_name, email, token, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ''', (
            user_id,
            config.get('url'),
            config.get('username'),
            config.get('repoName'),
            config.get('email'),
            config.get('token')
        ))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Config saved to Vault'})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/vault/config/filebay/<user_id>', methods=['GET'])
def get_filebay_config(user_id):
    """获取 FileBay 配置"""
    try:
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
            return jsonify({'error': 'Config not found'}), 404
        
        return jsonify({
            'url': row[0],
            'username': row[1],
            'repoName': row[2],
            'email': row[3],
            'token': row[4],
            'updatedAt': row[5]
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def start_vault_bridge(port=8765):
    """启动 Vault Bridge 服务"""
    init_vault_db()
    app.run(host='127.0.0.1', port=port, debug=False)

if __name__ == '__main__':
    start_vault_bridge()
```

#### 2. 在 Desktop 登录成功后通知 Vault

```typescript
// web/service/vault-bridge.ts
export interface VaultFileBayConfig {
  url: string
  username: string
  repoName: string
  email: string
  token: string
}

export const notifyVaultBridge = async (
  userId: string, 
  config: VaultFileBayConfig
): Promise<boolean> => {
  try {
    const response = await fetch('http://localhost:8765/vault/config/filebay', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        user_id: userId,
        config: config
      })
    })
    
    if (!response.ok) {
      console.error('Vault bridge notification failed:', await response.text())
      return false
    }
    
    console.log('FileBay config saved to Vault successfully')
    return true
  } catch (error) {
    console.error('Failed to notify Vault bridge:', error)
    return false
  }
}

export const checkVaultBridgeHealth = async (): Promise<boolean> => {
  try {
    const response = await fetch('http://localhost:8765/health', {
      method: 'GET',
      signal: AbortSignal.timeout(2000) // 2秒超时
    })
    return response.ok
  } catch {
    return false
  }
}
```

#### 3. 集成到登录流程

```typescript
// web/app/(commonLayout)/signin/page.tsx 或相关登录组件
import { notifyVaultBridge, checkVaultBridgeHealth } from '@/service/vault-bridge'

// 在登录成功后
const handleLoginSuccess = async (userInfo: any) => {
  // 获取 FileBay 配置
  const configResponse = await fetch('/console/api/gitea/config/download')
  if (configResponse.ok) {
    const config = await configResponse.json()
    
    // 检查 Vault Bridge 是否运行
    const isVaultBridgeRunning = await checkVaultBridgeHealth()
    
    if (isVaultBridgeRunning) {
      // 通知 Vault Bridge
      await notifyVaultBridge(userInfo.id, {
        url: config.gitea_url,
        username: config.gitea_owner,
        repoName: config.gitea_repo,
        email: userInfo.email,
        token: config.gitea_token
      })
    } else {
      console.warn('Vault Bridge is not running, config will not be synced')
    }
  }
}
```

#### 4. 脱敏系统读取 Vault 配置

```rust
// cheersai-desktop/src-tauri/src/commands/vault.rs
use serde::{Deserialize, Serialize};
use rusqlite::{Connection, Result};
use std::path::PathBuf;

#[derive(Debug, Serialize, Deserialize)]
pub struct VaultFileBayConfig {
    pub url: String,
    pub username: String,
    pub repo_name: String,
    pub email: Option<String>,
    pub token: String,
    pub updated_at: String,
}

fn get_vault_db_path() -> PathBuf {
    let home = dirs::home_dir().expect("Failed to get home directory");
    home.join(".cheersai").join("vault.db")
}

#[tauri::command]
pub async fn read_vault_filebay_config(user_id: String) -> Result<VaultFileBayConfig, String> {
    let db_path = get_vault_db_path();
    
    if !db_path.exists() {
        return Err("Vault database not found".to_string());
    }
    
    let conn = Connection::open(db_path)
        .map_err(|e| format!("Failed to open Vault database: {}", e))?;
    
    let mut stmt = conn.prepare(
        "SELECT url, username, repo_name, email, token, updated_at 
         FROM filebay_configs 
         WHERE user_id = ?"
    ).map_err(|e| format!("Failed to prepare statement: {}", e))?;
    
    let config = stmt.query_row([&user_id], |row| {
        Ok(VaultFileBayConfig {
            url: row.get(0)?,
            username: row.get(1)?,
            repo_name: row.get(2)?,
            email: row.get(3)?,
            token: row.get(4)?,
            updated_at: row.get(5)?,
        })
    }).map_err(|e| format!("Config not found: {}", e))?;
    
    Ok(config)
}

#[tauri::command]
pub async fn check_vault_config_exists(user_id: String) -> Result<bool, String> {
    let db_path = get_vault_db_path();
    
    if !db_path.exists() {
        return Ok(false);
    }
    
    let conn = Connection::open(db_path)
        .map_err(|e| format!("Failed to open Vault database: {}", e))?;
    
    let count: i64 = conn.query_row(
        "SELECT COUNT(*) FROM filebay_configs WHERE user_id = ?",
        [&user_id],
        |row| row.get(0)
    ).unwrap_or(0);
    
    Ok(count > 0)
}
```

#### 5. 在脱敏系统中使用

```typescript
// cheersai-desktop/src/lib/tauri.ts
export const tauriCommands = {
  // ... 现有命令
  
  // Vault 集成
  readVaultFilebayConfig: (userId: string) =>
    invoke<FileBayConfig>("read_vault_filebay_config", { userId }),
  
  checkVaultConfigExists: (userId: string) =>
    invoke<boolean>("check_vault_config_exists", { userId }),
}
```

```typescript
// cheersai-desktop/src/components/settings/GiteaSettings.tsx
// 添加自动从 Vault 读取配置的功能

const loadConfigFromVault = async () => {
  try {
    // 假设用户 ID 存储在本地
    const userId = localStorage.getItem('user_id')
    if (!userId) return
    
    const hasConfig = await tauriCommands.checkVaultConfigExists(userId)
    if (hasConfig) {
      const vaultConfig = await tauriCommands.readVaultFilebayConfig(userId)
      
      // 自动填充配置
      setConfig({
        url: vaultConfig.url,
        token: vaultConfig.token,
        owner: vaultConfig.username,
        repo: vaultConfig.repo_name,
      })
      
      setMessage({
        type: 'success',
        text: '已从 Vault 自动加载配置'
      })
    }
  } catch (error) {
    console.error('Failed to load config from Vault:', error)
  }
}
```

## 部署和启动

### 1. 启动 Vault Bridge 服务

**方式 A: 使用 PowerShell 脚本（推荐）**

```powershell
# 在项目根目录
.\start_vault_bridge.ps1
```

**方式 B: 直接使用 Python**

```bash
# 在 api 目录
cd api
python start_vault_bridge.py

# 自定义端口
python start_vault_bridge.py --port 8765

# 启用调试模式
python start_vault_bridge.py --debug
```

**验证服务运行**

```bash
# 健康检查
curl http://localhost:8765/health
```

预期响应：
```json
{
  "status": "ok",
  "service": "vault-bridge",
  "version": "1.0.0",
  "database": "C:\\Users\\YourName\\.cheersai\\vault.db",
  "database_exists": true
}
```

### 2. 启动 Vault Web 服务

```bash
cd web
pnpm dev
```

### 3. 启动脱敏系统

```bash
cd E:\CheersAI脱敏\cheersai-desktop
pnpm tauri dev
```

## 已实现的文件

### Vault 系统 (CheersAI-Desktop)

1. **`api/services/vault_bridge_service.py`** ✅
   - Vault Bridge Flask 应用
   - SQLite 数据库初始化
   - FileBay 配置 CRUD API

2. **`web/service/vault-bridge.ts`** ✅
   - Vault Bridge 客户端工具函数
   - 健康检查、配置同步、配置查询

3. **`web/app/oauth-callback/page.tsx`** ✅
   - 集成 Vault Bridge 通知
   - 登录成功后自动同步配置

4. **`api/start_vault_bridge.py`** ✅
   - Vault Bridge 启动脚本

5. **`start_vault_bridge.ps1`** ✅
   - Windows PowerShell 启动脚本

### 脱敏系统 (cheersai-desktop) - 待实现

1. **`src-tauri/src/commands/vault.rs`** ⏳
   - Rust 命令：读取 Vault 配置
   - Rust 命令：检查配置是否存在

2. **`src/lib/tauri.ts`** ⏳
   - TypeScript 命令绑定

3. **`src/components/settings/GiteaSettings.tsx`** ⏳
   - 自动从 Vault 加载配置
   - "从 Vault 加载配置"按钮

## 测试流程

1. 启动 Vault Bridge 服务
2. 在 Vault Web 端登录
3. 登录成功后，检查 `~/.cheersai/vault.db` 是否创建并包含配置
4. 打开脱敏系统，验证是否能自动读取配置
5. 测试文件脱敏和上传功能

## 安全考虑

1. **Token 加密存储**
   - 在 Vault 数据库中加密存储 Token
   - 使用用户密钥派生加密密钥

2. **本地服务认证**
   - Vault Bridge 只监听 localhost
   - 可选：添加简单的 API Key 认证

3. **数据库权限**
   - 设置适当的文件权限（600）
   - 只允许当前用户访问

## 后续优化

1. **自动启动 Vault Bridge**
   - 作为系统服务自动启动
   - 或集成到主 API 服务中

2. **配置同步**
   - 支持配置更新通知
   - 实时同步配置变更

3. **多用户支持**
   - 支持多个用户配置
   - 用户切换时自动加载对应配置

4. **错误处理和重试**
   - 网络失败时自动重试
   - 提供用户友好的错误提示
