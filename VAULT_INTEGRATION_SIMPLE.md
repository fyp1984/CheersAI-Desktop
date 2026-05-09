# Vault 集成简化方案 - 无需 localStorage

## 核心思路

**不依赖 localStorage**，直接通过以下方式获取配置：

1. **方式 A**: 用户输入邮箱，从 Vault 数据库查询
2. **方式 B**: 扫描 Vault 数据库，列出所有可用配置
3. **方式 C**: 使用系统用户名作为标识

## 推荐实现：方式 B（最简单）

### 1. Rust 命令：列出所有配置

```rust
// src-tauri/src/commands/vault.rs
use serde::{Deserialize, Serialize};
use rusqlite::{Connection, Result};
use std::path::PathBuf;

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct VaultFileBayConfig {
    pub user_id: String,
    pub url: String,
    pub username: String,
    pub repo_name: String,
    pub email: String,
    pub token: String,
    pub updated_at: String,
}

fn get_vault_db_path() -> PathBuf {
    let home = dirs::home_dir().expect("Failed to get home directory");
    home.join(".cheersai").join("vault.db")
}

/// 列出所有可用的 FileBay 配置
#[tauri::command]
pub async fn list_vault_configs() -> Result<Vec<VaultFileBayConfig>, String> {
    let db_path = get_vault_db_path();
    
    if !db_path.exists() {
        return Err("Vault database not found. Please login to Vault system first.".to_string());
    }
    
    let conn = Connection::open(db_path)
        .map_err(|e| format!("Failed to open Vault database: {}", e))?;
    
    let mut stmt = conn.prepare(
        "SELECT user_id, url, username, repo_name, email, token, updated_at 
         FROM filebay_configs 
         ORDER BY updated_at DESC"
    ).map_err(|e| format!("Failed to prepare statement: {}", e))?;
    
    let configs = stmt.query_map([], |row| {
        Ok(VaultFileBayConfig {
            user_id: row.get(0)?,
            url: row.get(1)?,
            username: row.get(2)?,
            repo_name: row.get(3)?,
            email: row.get(4)?,
            token: row.get(5)?,
            updated_at: row.get(6)?,
        })
    }).map_err(|e| format!("Failed to query configs: {}", e))?;
    
    let mut result = Vec::new();
    for config in configs {
        if let Ok(c) = config {
            result.push(c);
        }
    }
    
    Ok(result)
}

/// 通过邮箱获取配置
#[tauri::command]
pub async fn get_vault_config_by_email(email: String) -> Result<VaultFileBayConfig, String> {
    let db_path = get_vault_db_path();
    
    if !db_path.exists() {
        return Err("Vault database not found".to_string());
    }
    
    let conn = Connection::open(db_path)
        .map_err(|e| format!("Failed to open Vault database: {}", e))?;
    
    let mut stmt = conn.prepare(
        "SELECT user_id, url, username, repo_name, email, token, updated_at 
         FROM filebay_configs 
         WHERE email = ?"
    ).map_err(|e| format!("Failed to prepare statement: {}", e))?;
    
    let config = stmt.query_row([&email], |row| {
        Ok(VaultFileBayConfig {
            user_id: row.get(0)?,
            url: row.get(1)?,
            username: row.get(2)?,
            repo_name: row.get(3)?,
            email: row.get(4)?,
            token: row.get(5)?,
            updated_at: row.get(6)?,
        })
    }).map_err(|e| format!("Config not found for email {}: {}", email, e))?;
    
    Ok(config)
}

/// 检查 Vault 数据库是否存在
#[tauri::command]
pub async fn check_vault_db_exists() -> Result<bool, String> {
    let db_path = get_vault_db_path();
    Ok(db_path.exists())
}
```

### 2. 前端：配置选择器

```typescript
// src/components/settings/VaultConfigSelector.tsx
import { useEffect, useState } from 'react';
import { invoke } from '@tauri-apps/api/core';

interface VaultConfig {
  user_id: string;
  url: string;
  username: string;
  repo_name: string;
  email: string;
  token: string;
  updated_at: string;
}

export function VaultConfigSelector({ onConfigSelected }: { 
  onConfigSelected: (config: VaultConfig) => void 
}) {
  const [configs, setConfigs] = useState<VaultConfig[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [vaultExists, setVaultExists] = useState(false);

  useEffect(() => {
    checkVaultAndLoadConfigs();
  }, []);

  const checkVaultAndLoadConfigs = async () => {
    setLoading(true);
    setError(null);
    
    try {
      // 检查 Vault 数据库是否存在
      const exists = await invoke<boolean>('check_vault_db_exists');
      setVaultExists(exists);
      
      if (!exists) {
        setError('未找到 Vault 数据库。请先在 Vault 系统中登录。');
        return;
      }
      
      // 加载所有配置
      const configList = await invoke<VaultConfig[]>('list_vault_configs');
      
      if (configList.length === 0) {
        setError('Vault 数据库中没有配置。请先在 Vault 系统中登录。');
      } else {
        setConfigs(configList);
        
        // 如果只有一个配置，自动选择
        if (configList.length === 1) {
          onConfigSelected(configList[0]);
        }
      }
    } catch (err) {
      console.error('Failed to load Vault configs:', err);
      setError(`加载配置失败: ${err}`);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="loading">正在加载 Vault 配置...</div>;
  }

  if (error) {
    return (
      <div className="error-container">
        <div className="error-message">{error}</div>
        <div className="help-text">
          <p>请按照以下步骤操作：</p>
          <ol>
            <li>打开 Vault 系统：<a href="http://localhost:3000/signin" target="_blank">http://localhost:3000/signin</a></li>
            <li>使用 Desktop SSO 登录</li>
            <li>登录成功后，配置会自动同步到本地</li>
            <li>返回此应用，点击"重新加载"按钮</li>
          </ol>
        </div>
        <button onClick={checkVaultAndLoadConfigs}>重新加载</button>
      </div>
    );
  }

  if (configs.length === 0) {
    return (
      <div className="empty-state">
        <p>没有找到配置</p>
        <button onClick={checkVaultAndLoadConfigs}>重新加载</button>
      </div>
    );
  }

  return (
    <div className="config-selector">
      <h3>选择 FileBay 配置</h3>
      <div className="config-list">
        {configs.map((config) => (
          <div 
            key={config.user_id} 
            className="config-item"
            onClick={() => onConfigSelected(config)}
          >
            <div className="config-header">
              <strong>{config.email}</strong>
              <span className="config-username">@{config.username}</span>
            </div>
            <div className="config-details">
              <div>URL: {config.url}</div>
              <div>仓库: {config.repo_name}</div>
              <div>更新时间: {new Date(config.updated_at).toLocaleString()}</div>
            </div>
          </div>
        ))}
      </div>
      <button onClick={checkVaultAndLoadConfigs} className="refresh-btn">
        刷新配置列表
      </button>
    </div>
  );
}
```

### 3. 在设置页面中使用

```typescript
// src/pages/Settings.tsx
import { useState } from 'react';
import { VaultConfigSelector } from '@/components/settings/VaultConfigSelector';

export function Settings() {
  const [config, setConfig] = useState({
    url: '',
    token: '',
    owner: '',
    repo: '',
  });
  const [configLoaded, setConfigLoaded] = useState(false);

  const handleConfigSelected = (vaultConfig: any) => {
    setConfig({
      url: vaultConfig.url,
      token: vaultConfig.token,
      owner: vaultConfig.username,
      repo: vaultConfig.repo_name,
    });
    setConfigLoaded(true);
    
    // 可选：保存到本地存储
    localStorage.setItem('selected_config_email', vaultConfig.email);
  };

  return (
    <div className="settings-page">
      <h1>设置</h1>
      
      {!configLoaded ? (
        <VaultConfigSelector onConfigSelected={handleConfigSelected} />
      ) : (
        <div className="config-loaded">
          <div className="success-message">
            ✓ 配置已加载
          </div>
          <div className="config-display">
            <div>URL: {config.url}</div>
            <div>用户: {config.owner}</div>
            <div>仓库: {config.repo}</div>
          </div>
          <button onClick={() => setConfigLoaded(false)}>
            切换配置
          </button>
        </div>
      )}
    </div>
  );
}
```

## 优势

1. **无需 localStorage**: 不依赖前端存储
2. **自动发现**: 自动列出所有可用配置
3. **多用户支持**: 支持多个用户配置切换
4. **简单直观**: 用户界面清晰，易于使用
5. **容错性好**: 提供详细的错误提示和帮助信息

## 用户体验流程

```
用户打开脱敏应用
    ↓
自动检查 Vault 数据库
    ↓
┌─────────────────────┬─────────────────────┐
│  数据库不存在        │  数据库存在          │
│  或没有配置          │  且有配置            │
└─────────┬───────────┴─────────┬───────────┘
          │                     │
          ▼                     ▼
    显示帮助信息          列出所有配置
    引导用户登录          用户选择配置
          │                     │
          │                     ▼
          │              配置自动加载
          │              开始使用
          │                     │
          └─────────────────────┘
```

## 实现步骤

1. ✅ 创建 Rust 命令（上面的代码）
2. ✅ 创建前端组件（上面的代码）
3. ⏳ 在 main.rs 中注册命令
4. ⏳ 在设置页面中集成
5. ⏳ 测试完整流程

## 下一步

这个方案**不需要 localStorage**，完全依赖 Vault 数据库。用户只需：

1. 在 Vault 系统中登录一次
2. 打开脱敏应用
3. 选择配置（如果有多个）
4. 开始使用

简单、直观、可靠！🎉
