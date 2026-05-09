# 脱敏程序 Vault 集成实现指南

## 目标

在脱敏 Tauri 程序中读取 Vault 数据库（`~/.cheersai/vault.db`）中的 FileBay 配置。

## 完整实现步骤

### 步骤 1: 创建 Vault 命令模块

**文件位置**: `E:\CheersAI脱敏\cheersai-desktop\src-tauri\src\commands\vault.rs`

```rust
use serde::{Deserialize, Serialize};
use rusqlite::Connection;
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

/// 获取 Vault 数据库路径
fn get_vault_db_path() -> PathBuf {
    let home = dirs::home_dir().expect("Failed to get home directory");
    home.join(".cheersai").join("vault.db")
}

/// 列出所有可用的 FileBay 配置
#[tauri::command]
pub async fn list_vault_configs() -> Result<Vec<VaultFileBayConfig>, String> {
    let db_path = get_vault_db_path();
    
    if !db_path.exists() {
        return Err(format!(
            "Vault 数据库不存在: {:?}\n\n请先在 Vault 系统中登录:\nhttp://localhost:3000/signin",
            db_path
        ));
    }
    
    let conn = Connection::open(&db_path)
        .map_err(|e| format!("无法打开数据库: {}", e))?;
    
    let mut stmt = conn.prepare(
        "SELECT user_id, url, username, repo_name, email, token, updated_at 
         FROM filebay_configs 
         ORDER BY updated_at DESC"
    ).map_err(|e| format!("查询失败: {}", e))?;
    
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
    }).map_err(|e| format!("读取配置失败: {}", e))?;
    
    let mut result = Vec::new();
    for config in configs {
        if let Ok(c) = config {
            result.push(c);
        }
    }
    
    if result.is_empty() {
        return Err(
            "数据库中没有配置\n\n请先在 Vault 系统中登录并同步配置:\nhttp://localhost:3000/sync-config".to_string()
        );
    }
    
    Ok(result)
}

/// 通过用户 ID 获取配置
#[tauri::command]
pub async fn get_vault_config_by_user_id(user_id: String) -> Result<VaultFileBayConfig, String> {
    let db_path = get_vault_db_path();
    
    if !db_path.exists() {
        return Err("Vault 数据库不存在".to_string());
    }
    
    let conn = Connection::open(&db_path)
        .map_err(|e| format!("无法打开数据库: {}", e))?;
    
    let mut stmt = conn.prepare(
        "SELECT user_id, url, username, repo_name, email, token, updated_at 
         FROM filebay_configs 
         WHERE user_id = ?"
    ).map_err(|e| format!("查询失败: {}", e))?;
    
    let config = stmt.query_row([&user_id], |row| {
        Ok(VaultFileBayConfig {
            user_id: row.get(0)?,
            url: row.get(1)?,
            username: row.get(2)?,
            repo_name: row.get(3)?,
            email: row.get(4)?,
            token: row.get(5)?,
            updated_at: row.get(6)?,
        })
    }).map_err(|e| format!("未找到配置: {}", e))?;
    
    Ok(config)
}

/// 通过邮箱获取配置
#[tauri::command]
pub async fn get_vault_config_by_email(email: String) -> Result<VaultFileBayConfig, String> {
    let db_path = get_vault_db_path();
    
    if !db_path.exists() {
        return Err("Vault 数据库不存在".to_string());
    }
    
    let conn = Connection::open(&db_path)
        .map_err(|e| format!("无法打开数据库: {}", e))?;
    
    let mut stmt = conn.prepare(
        "SELECT user_id, url, username, repo_name, email, token, updated_at 
         FROM filebay_configs 
         WHERE email = ?"
    ).map_err(|e| format!("查询失败: {}", e))?;
    
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
    }).map_err(|e| format!("未找到配置: {}", e))?;
    
    Ok(config)
}

/// 检查 Vault 数据库是否存在
#[tauri::command]
pub async fn check_vault_db_exists() -> Result<bool, String> {
    let db_path = get_vault_db_path();
    Ok(db_path.exists())
}

/// 获取 Vault 数据库路径
#[tauri::command]
pub async fn get_vault_db_path_string() -> Result<String, String> {
    let db_path = get_vault_db_path();
    Ok(db_path.to_string_lossy().to_string())
}
```

### 步骤 2: 在 main.rs 中注册命令

**文件位置**: `E:\CheersAI脱敏\cheersai-desktop\src-tauri\src\main.rs`

在文件顶部添加模块声明：
```rust
mod commands;
```

在 `tauri::Builder` 中注册命令：
```rust
fn main() {
    tauri::Builder::default()
        .invoke_handler(tauri::generate_handler![
            // ... 现有命令 ...
            
            // Vault 集成命令
            commands::vault::list_vault_configs,
            commands::vault::get_vault_config_by_user_id,
            commands::vault::get_vault_config_by_email,
            commands::vault::check_vault_db_exists,
            commands::vault::get_vault_db_path_string,
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
```

### 步骤 3: 在 commands/mod.rs 中声明模块

**文件位置**: `E:\CheersAI脱敏\cheersai-desktop\src-tauri\src\commands\mod.rs`

添加：
```rust
pub mod vault;
```

### 步骤 4: 添加依赖

**文件位置**: `E:\CheersAI脱敏\cheersai-desktop\src-tauri\Cargo.toml`

在 `[dependencies]` 部分添加：
```toml
rusqlite = { version = "0.32", features = ["bundled"] }
dirs = "5.0"
```

### 步骤 5: 创建 TypeScript 类型和工具函数

**文件位置**: `E:\CheersAI脱敏\cheersai-desktop\src\lib\vault.ts`

```typescript
import { invoke } from '@tauri-apps/api/core';

export interface VaultFileBayConfig {
  user_id: string;
  url: string;
  username: string;
  repo_name: string;
  email: string;
  token: string;
  updated_at: string;
}

/**
 * 列出所有可用的 Vault 配置
 */
export async function listVaultConfigs(): Promise<VaultFileBayConfig[]> {
  return await invoke<VaultFileBayConfig[]>('list_vault_configs');
}

/**
 * 通过用户 ID 获取配置
 */
export async function getVaultConfigByUserId(userId: string): Promise<VaultFileBayConfig> {
  return await invoke<VaultFileBayConfig>('get_vault_config_by_user_id', { userId });
}

/**
 * 通过邮箱获取配置
 */
export async function getVaultConfigByEmail(email: string): Promise<VaultFileBayConfig> {
  return await invoke<VaultFileBayConfig>('get_vault_config_by_email', { email });
}

/**
 * 检查 Vault 数据库是否存在
 */
export async function checkVaultDbExists(): Promise<boolean> {
  return await invoke<boolean>('check_vault_db_exists');
}

/**
 * 获取 Vault 数据库路径
 */
export async function getVaultDbPath(): Promise<string> {
  return await invoke<string>('get_vault_db_path_string');
}
```

### 步骤 6: 创建配置选择器组件

**文件位置**: `E:\CheersAI脱敏\cheersai-desktop\src\components\VaultConfigSelector.tsx`

```typescript
import { useEffect, useState } from 'react';
import { listVaultConfigs, checkVaultDbExists, getVaultDbPath, VaultFileBayConfig } from '@/lib/vault';

interface VaultConfigSelectorProps {
  onConfigSelected: (config: VaultFileBayConfig) => void;
}

export function VaultConfigSelector({ onConfigSelected }: VaultConfigSelectorProps) {
  const [configs, setConfigs] = useState<VaultFileBayConfig[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [dbPath, setDbPath] = useState<string>('');
  const [dbExists, setDbExists] = useState(false);

  useEffect(() => {
    loadConfigs();
  }, []);

  const loadConfigs = async () => {
    setLoading(true);
    setError(null);
    
    try {
      // 获取数据库路径
      const path = await getVaultDbPath();
      setDbPath(path);
      
      // 检查数据库是否存在
      const exists = await checkVaultDbExists();
      setDbExists(exists);
      
      if (!exists) {
        setError('Vault 数据库不存在');
        return;
      }
      
      // 加载配置列表
      const configList = await listVaultConfigs();
      setConfigs(configList);
      
      // 如果只有一个配置，自动选择
      if (configList.length === 1) {
        onConfigSelected(configList[0]);
      }
    } catch (err: any) {
      console.error('Failed to load Vault configs:', err);
      setError(err.toString());
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        <span className="ml-3 text-gray-600">正在加载 Vault 配置...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6 bg-red-50 border border-red-200 rounded-lg">
        <h3 className="text-lg font-semibold text-red-900 mb-2">无法加载配置</h3>
        <p className="text-red-700 mb-4">{error}</p>
        
        <div className="bg-white p-4 rounded border border-red-200 mb-4">
          <p className="text-sm text-gray-600 mb-2">
            <strong>数据库路径:</strong> {dbPath}
          </p>
          <p className="text-sm text-gray-600">
            <strong>数据库存在:</strong> {dbExists ? '是' : '否'}
          </p>
        </div>
        
        <div className="bg-yellow-50 border-l-4 border-yellow-400 p-4 mb-4">
          <h4 className="font-semibold text-yellow-900 mb-2">解决步骤：</h4>
          <ol className="list-decimal list-inside space-y-1 text-yellow-800 text-sm">
            <li>打开浏览器访问: <code className="bg-yellow-100 px-1 rounded">http://localhost:3000/signin</code></li>
            <li>使用 Desktop SSO 登录</li>
            <li>访问: <code className="bg-yellow-100 px-1 rounded">http://localhost:3000/sync-config</code></li>
            <li>点击"开始同步"按钮</li>
            <li>返回此应用，点击下面的"重新加载"按钮</li>
          </ol>
        </div>
        
        <button
          onClick={loadConfigs}
          className="w-full bg-blue-600 text-white py-2 px-4 rounded hover:bg-blue-700 transition"
        >
          重新加载
        </button>
      </div>
    );
  }

  if (configs.length === 0) {
    return (
      <div className="p-6 bg-gray-50 border border-gray-200 rounded-lg">
        <p className="text-gray-600 mb-4">没有找到配置</p>
        <button
          onClick={loadConfigs}
          className="w-full bg-blue-600 text-white py-2 px-4 rounded hover:bg-blue-700 transition"
        >
          重新加载
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900">选择 FileBay 配置</h3>
        <button
          onClick={loadConfigs}
          className="text-sm text-blue-600 hover:text-blue-700"
        >
          刷新
        </button>
      </div>
      
      <div className="space-y-3">
        {configs.map((config) => (
          <div
            key={config.user_id}
            onClick={() => onConfigSelected(config)}
            className="p-4 border-2 border-gray-200 rounded-lg hover:border-blue-500 cursor-pointer transition bg-white"
          >
            <div className="flex items-center justify-between mb-2">
              <span className="font-semibold text-gray-900">{config.email}</span>
              <span className="text-sm text-gray-500">@{config.username}</span>
            </div>
            <div className="space-y-1 text-sm text-gray-600">
              <div><strong>URL:</strong> {config.url}</div>
              <div><strong>仓库:</strong> {config.repo_name}</div>
              <div><strong>更新:</strong> {new Date(config.updated_at).toLocaleString()}</div>
            </div>
          </div>
        ))}
      </div>
      
      <div className="text-xs text-gray-500 mt-4">
        数据库位置: {dbPath}
      </div>
    </div>
  );
}
```

### 步骤 7: 在设置页面中使用

**文件位置**: `E:\CheersAI脱敏\cheersai-desktop\src\pages\Settings.tsx` (或相应的设置页面)

```typescript
import { useState } from 'react';
import { VaultConfigSelector } from '@/components/VaultConfigSelector';
import { VaultFileBayConfig } from '@/lib/vault';

export function Settings() {
  const [config, setConfig] = useState<{
    url: string;
    token: string;
    owner: string;
    repo: string;
  } | null>(null);
  
  const [showSelector, setShowSelector] = useState(true);

  const handleConfigSelected = (vaultConfig: VaultFileBayConfig) => {
    setConfig({
      url: vaultConfig.url,
      token: vaultConfig.token,
      owner: vaultConfig.username,
      repo: vaultConfig.repo_name,
    });
    setShowSelector(false);
    
    // 可选：保存到本地存储
    localStorage.setItem('selected_config_email', vaultConfig.email);
  };

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-6">设置</h1>
      
      {showSelector ? (
        <VaultConfigSelector onConfigSelected={handleConfigSelected} />
      ) : (
        <div className="space-y-4">
          <div className="bg-green-50 border border-green-200 rounded-lg p-4">
            <h3 className="font-semibold text-green-900 mb-2">✓ 配置已加载</h3>
            <div className="space-y-2 text-sm text-green-800">
              <div><strong>URL:</strong> {config?.url}</div>
              <div><strong>用户:</strong> {config?.owner}</div>
              <div><strong>仓库:</strong> {config?.repo}</div>
            </div>
          </div>
          
          <button
            onClick={() => setShowSelector(true)}
            className="text-blue-600 hover:text-blue-700"
          >
            切换配置
          </button>
        </div>
      )}
    </div>
  );
}
```

## 使用流程

1. **在 Vault 系统中同步配置**:
   - 访问 `http://localhost:3000/sync-config`
   - 点击"开始同步"

2. **在脱敏程序中使用**:
   - 打开脱敏应用
   - 自动显示可用配置列表
   - 选择配置
   - 开始使用

## 测试

```bash
# 在脱敏程序目录
cd E:\CheersAI脱敏\cheersai-desktop

# 安装依赖
cargo build

# 运行
pnpm tauri dev
```

## 完成！

现在脱敏程序可以直接从 Vault 数据库读取配置，无需手动输入！🎉
