# Tauri 中使用 localStorage 和 Vault 集成指南

## 概述

在 Tauri 应用中，有多种方式存储和读取用户数据，包括 localStorage、Tauri Store、以及直接访问 Vault 数据库。

## 方案对比

| 方案 | 优点 | 缺点 | 适用场景 |
|------|------|------|----------|
| 前端 localStorage | 简单、标准 API | 只能前端访问 | 临时数据、UI 状态 |
| Tauri Store | Rust 可访问、类型安全 | 需要额外依赖 | 应用配置、用户偏好 |
| Vault 数据库 | 跨应用共享、持久化 | 需要 Vault Bridge | FileBay 配置、敏感数据 |

## 推荐方案：组合使用

### 1. 前端 localStorage 存储用户 ID

```typescript
// src/lib/auth.ts
export const saveUserId = (userId: string) => {
  localStorage.setItem('user_id', userId);
  localStorage.setItem('user_id_timestamp', Date.now().toString());
};

export const getUserId = (): string | null => {
  return localStorage.getItem('user_id');
};

export const clearUserId = () => {
  localStorage.removeItem('user_id');
  localStorage.removeItem('user_id_timestamp');
};
```

### 2. Rust 命令读取 Vault 配置

```rust
// src-tauri/src/commands/vault.rs
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
        return Err("Vault database not found. Please login to Vault system first.".to_string());
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
    }).map_err(|e| format!("Config not found for user {}: {}", user_id, e))?;
    
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

#[tauri::command]
pub async fn get_vault_config_by_email(email: String) -> Result<VaultFileBayConfig, String> {
    let db_path = get_vault_db_path();
    
    if !db_path.exists() {
        return Err("Vault database not found".to_string());
    }
    
    let conn = Connection::open(db_path)
        .map_err(|e| format!("Failed to open Vault database: {}", e))?;
    
    let mut stmt = conn.prepare(
        "SELECT url, username, repo_name, email, token, updated_at 
         FROM filebay_configs 
         WHERE email = ?"
    ).map_err(|e| format!("Failed to prepare statement: {}", e))?;
    
    let config = stmt.query_row([&email], |row| {
        Ok(VaultFileBayConfig {
            url: row.get(0)?,
            username: row.get(1)?,
            repo_name: row.get(2)?,
            email: row.get(3)?,
            token: row.get(4)?,
            updated_at: row.get(5)?,
        })
    }).map_err(|e| format!("Config not found for email {}: {}", email, e))?;
    
    Ok(config)
}
```

### 3. 前端集成

```typescript
// src/lib/vault.ts
import { invoke } from '@tauri-apps/api/core';

export interface VaultFileBayConfig {
  url: string;
  username: string;
  repo_name: string;
  email: string | null;
  token: string;
  updated_at: string;
}

/**
 * 从 Vault 数据库读取 FileBay 配置
 * 优先使用 localStorage 中的 user_id
 */
export async function loadVaultConfig(): Promise<VaultFileBayConfig | null> {
  try {
    // 1. 尝试从 localStorage 获取 user_id
    const userId = localStorage.getItem('user_id');
    
    if (userId) {
      console.log('[Vault] Loading config for user:', userId);
      
      // 2. 检查配置是否存在
      const exists = await invoke<boolean>('check_vault_config_exists', { userId });
      
      if (exists) {
        // 3. 读取配置
        const config = await invoke<VaultFileBayConfig>('read_vault_filebay_config', { userId });
        console.log('[Vault] Config loaded successfully');
        return config;
      } else {
        console.warn('[Vault] No config found for user:', userId);
        return null;
      }
    } else {
      console.warn('[Vault] No user_id in localStorage');
      return null;
    }
  } catch (error) {
    console.error('[Vault] Failed to load config:', error);
    return null;
  }
}

/**
 * 通过邮箱从 Vault 数据库读取配置
 */
export async function loadVaultConfigByEmail(email: string): Promise<VaultFileBayConfig | null> {
  try {
    const config = await invoke<VaultFileBayConfig>('get_vault_config_by_email', { email });
    console.log('[Vault] Config loaded by email successfully');
    return config;
  } catch (error) {
    console.error('[Vault] Failed to load config by email:', error);
    return null;
  }
}
```

### 4. 在组件中使用

```typescript
// src/components/settings/GiteaSettings.tsx
import { useEffect, useState } from 'react';
import { loadVaultConfig } from '@/lib/vault';

export function GiteaSettings() {
  const [config, setConfig] = useState({
    url: '',
    token: '',
    owner: '',
    repo: '',
  });
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<{type: 'success' | 'error', text: string} | null>(null);

  // 组件加载时自动从 Vault 加载配置
  useEffect(() => {
    loadConfigFromVault();
  }, []);

  const loadConfigFromVault = async () => {
    setLoading(true);
    setMessage(null);
    
    try {
      const vaultConfig = await loadVaultConfig();
      
      if (vaultConfig) {
        setConfig({
          url: vaultConfig.url,
          token: vaultConfig.token,
          owner: vaultConfig.username,
          repo: vaultConfig.repo_name,
        });
        
        setMessage({
          type: 'success',
          text: `已从 Vault 自动加载配置（更新时间: ${new Date(vaultConfig.updated_at).toLocaleString()}）`
        });
      } else {
        setMessage({
          type: 'error',
          text: '未找到 Vault 配置，请先在 Vault 系统中登录'
        });
      }
    } catch (error) {
      console.error('Failed to load config from Vault:', error);
      setMessage({
        type: 'error',
        text: `加载配置失败: ${error}`
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <h2>FileBay 配置</h2>
      
      {message && (
        <div className={`message ${message.type}`}>
          {message.text}
        </div>
      )}
      
      <button onClick={loadConfigFromVault} disabled={loading}>
        {loading ? '加载中...' : '从 Vault 重新加载配置'}
      </button>
      
      {/* 配置表单 */}
      <form>
        <input 
          type="text" 
          value={config.url} 
          onChange={(e) => setConfig({...config, url: e.target.value})}
          placeholder="FileBay URL"
        />
        {/* 其他字段... */}
      </form>
    </div>
  );
}
```

## 完整工作流程

```
┌─────────────────────────────────────────────────────────────┐
│  1. 用户在 Vault Web 中登录                                   │
│     - Desktop SSO 认证                                       │
│     - 获取 user_id 和 FileBay 配置                           │
│     - 配置同步到 Vault 数据库                                 │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│  2. 用户打开 Tauri 脱敏应用                                   │
│     - 前端从 localStorage 读取 user_id                       │
│     - 如果没有，提示用户输入或登录                            │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│  3. 自动加载 Vault 配置                                       │
│     - 调用 Rust 命令 read_vault_filebay_config()            │
│     - 从 ~/.cheersai/vault.db 读取配置                       │
│     - 自动填充到表单                                          │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│  4. 用户使用配置进行文件脱敏和上传                             │
│     - 配置已自动加载，无需手动输入                            │
│     - 开始文件处理流程                                        │
└─────────────────────────────────────────────────────────────┘
```

## 依赖配置

### Cargo.toml

```toml
[dependencies]
tauri = { version = "2.0", features = [] }
serde = { version = "1.0", features = ["derive"] }
serde_json = "1.0"
rusqlite = { version = "0.32", features = ["bundled"] }
dirs = "5.0"
```

### main.rs

```rust
mod commands;

fn main() {
    tauri::Builder::default()
        .invoke_handler(tauri::generate_handler![
            // ... 现有命令
            commands::vault::read_vault_filebay_config,
            commands::vault::check_vault_config_exists,
            commands::vault::get_vault_config_by_email,
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
```

## 优势

1. **无需手动输入**: 用户只需在 Vault 登录一次，配置自动同步
2. **跨应用共享**: Vault 和脱敏系统共享同一个配置数据库
3. **安全性**: 配置存储在本地，不通过网络传输
4. **灵活性**: 支持多种查询方式（user_id、email）
5. **用户体验**: 自动加载，无感知配置同步

## 注意事项

1. **user_id 存储**: 建议在用户首次使用时保存到 localStorage
2. **配置更新**: Vault 登录时会自动更新配置
3. **错误处理**: 如果 Vault 数据库不存在，提示用户先登录 Vault
4. **Token 安全**: Token 存储在本地数据库，确保文件权限正确

## 测试步骤

1. 在 Vault Web 中登录，配置会自动同步到 `~/.cheersai/vault.db`
2. 打开 Tauri 脱敏应用
3. 应用自动从 Vault 数据库读取配置
4. 配置自动填充到表单
5. 开始使用文件脱敏功能
