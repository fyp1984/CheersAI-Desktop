# 多方法 FileBay 配置加载器

## 概述

提供 5 种方法读取 FileBay 配置，按优先级自动尝试，确保总能获取到配置。

## 方法列表

| 方法 | 优先级 | 说明 | 优点 | 缺点 |
|------|--------|------|------|------|
| 方法 1: Vault 数据库 | ⭐⭐⭐⭐⭐ | 读取 ~/.cheersai/vault.db | 最可靠、最快 | 需要先登录 Vault |
| 方法 2: Vault Bridge API | ⭐⭐⭐⭐ | HTTP 请求 localhost:8765 | 实时、跨应用 | 需要 Vault Bridge 运行 |
| 方法 3: Web API | ⭐⭐⭐ | HTTP 请求 localhost:3000 | 实时、最新 | 需要 Web 服务运行 |
| 方法 4: 浏览器 localStorage | ⭐⭐ | 读取浏览器文件 | 直接访问 | 复杂、浏览器相关 |
| 方法 5: 手动输入 | ⭐ | 用户手动输入 | 总是可用 | 用户体验差 |

## 完整实现

### Rust 后端 (src-tauri/src/commands/config_loader.rs)

```rust
use serde::{Deserialize, Serialize};
use rusqlite::Connection;
use std::path::PathBuf;
use std::fs;

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct FileBayConfig {
    pub url: String,
    pub username: String,
    pub repo_name: String,
    pub email: String,
    pub token: String,
    pub source: String, // 记录配置来源
}

#[derive(Debug, Serialize, Deserialize)]
pub struct ConfigLoadResult {
    pub success: bool,
    pub config: Option<FileBayConfig>,
    pub method: String,
    pub message: String,
}

// ============================================================================
// 方法 1: 从 Vault 数据库读取
// ============================================================================

#[tauri::command]
pub async fn load_config_from_vault_db() -> Result<ConfigLoadResult, String> {
    let db_path = dirs::home_dir()
        .ok_or("Failed to get home directory")?
        .join(".cheersai")
        .join("vault.db");
    
    if !db_path.exists() {
        return Ok(ConfigLoadResult {
            success: false,
            config: None,
            method: "vault_db".to_string(),
            message: format!("Vault database not found at {:?}", db_path),
        });
    }
    
    match Connection::open(&db_path) {
        Ok(conn) => {
            let mut stmt = conn.prepare(
                "SELECT url, username, repo_name, email, token 
                 FROM filebay_configs 
                 ORDER BY updated_at DESC 
                 LIMIT 1"
            ).map_err(|e| e.to_string())?;
            
            match stmt.query_row([], |row| {
                Ok(FileBayConfig {
                    url: row.get(0)?,
                    username: row.get(1)?,
                    repo_name: row.get(2)?,
                    email: row.get(3)?,
                    token: row.get(4)?,
                    source: "vault_db".to_string(),
                })
            }) {
                Ok(config) => Ok(ConfigLoadResult {
                    success: true,
                    config: Some(config),
                    method: "vault_db".to_string(),
                    message: "Successfully loaded from Vault database".to_string(),
                }),
                Err(e) => Ok(ConfigLoadResult {
                    success: false,
                    config: None,
                    method: "vault_db".to_string(),
                    message: format!("No config found in database: {}", e),
                }),
            }
        }
        Err(e) => Ok(ConfigLoadResult {
            success: false,
            config: None,
            method: "vault_db".to_string(),
            message: format!("Failed to open database: {}", e),
        }),
    }
}

// ============================================================================
// 方法 2: 从 Vault Bridge API 读取
// ============================================================================

#[tauri::command]
pub async fn load_config_from_vault_bridge() -> Result<ConfigLoadResult, String> {
    let client = reqwest::Client::new();
    
    // 先检查健康状态
    match client
        .get("http://localhost:8765/health")
        .timeout(std::time::Duration::from_secs(2))
        .send()
        .await
    {
        Ok(response) if response.status().is_success() => {
            // Vault Bridge 运行中，尝试获取配置列表
            match client
                .get("http://localhost:8765/vault/config/filebay/list")
                .timeout(std::time::Duration::from_secs(5))
                .send()
                .await
            {
                Ok(response) if response.status().is_success() => {
                    match response.json::<Vec<FileBayConfig>>().await {
                        Ok(configs) if !configs.is_empty() => {
                            let mut config = configs[0].clone();
                            config.source = "vault_bridge".to_string();
                            
                            Ok(ConfigLoadResult {
                                success: true,
                                config: Some(config),
                                method: "vault_bridge".to_string(),
                                message: "Successfully loaded from Vault Bridge API".to_string(),
                            })
                        }
                        Ok(_) => Ok(ConfigLoadResult {
                            success: false,
                            config: None,
                            method: "vault_bridge".to_string(),
                            message: "No configs found in Vault Bridge".to_string(),
                        }),
                        Err(e) => Ok(ConfigLoadResult {
                            success: false,
                            config: None,
                            method: "vault_bridge".to_string(),
                            message: format!("Failed to parse response: {}", e),
                        }),
                    }
                }
                Ok(response) => Ok(ConfigLoadResult {
                    success: false,
                    config: None,
                    method: "vault_bridge".to_string(),
                    message: format!("Vault Bridge returned error: {}", response.status()),
                }),
                Err(e) => Ok(ConfigLoadResult {
                    success: false,
                    config: None,
                    method: "vault_bridge".to_string(),
                    message: format!("Failed to connect to Vault Bridge: {}", e),
                }),
            }
        }
        _ => Ok(ConfigLoadResult {
            success: false,
            config: None,
            method: "vault_bridge".to_string(),
            message: "Vault Bridge is not running".to_string(),
        }),
    }
}

// ============================================================================
// 方法 3: 从 Web API 读取
// ============================================================================

#[tauri::command]
pub async fn load_config_from_web_api() -> Result<ConfigLoadResult, String> {
    let client = reqwest::Client::new();
    
    match client
        .get("http://localhost:3000/api/local-config")
        .timeout(std::time::Duration::from_secs(5))
        .send()
        .await
    {
        Ok(response) if response.status().is_success() => {
            match response.json::<FileBayConfig>().await {
                Ok(mut config) => {
                    config.source = "web_api".to_string();
                    
                    Ok(ConfigLoadResult {
                        success: true,
                        config: Some(config),
                        method: "web_api".to_string(),
                        message: "Successfully loaded from Web API".to_string(),
                    })
                }
                Err(e) => Ok(ConfigLoadResult {
                    success: false,
                    config: None,
                    method: "web_api".to_string(),
                    message: format!("Failed to parse response: {}", e),
                }),
            }
        }
        Ok(response) => Ok(ConfigLoadResult {
            success: false,
            config: None,
            method: "web_api".to_string(),
            message: format!("Web API returned error: {}", response.status()),
        }),
        Err(e) => Ok(ConfigLoadResult {
            success: false,
            config: None,
            method: "web_api".to_string(),
            message: format!("Failed to connect to Web API: {}", e),
        }),
    }
}

// ============================================================================
// 方法 4: 从浏览器 localStorage 读取
// ============================================================================

#[tauri::command]
pub async fn load_config_from_browser_storage() -> Result<ConfigLoadResult, String> {
    // Chrome localStorage 路径
    let chrome_path = dirs::home_dir()
        .ok_or("Failed to get home directory")?
        .join("AppData")
        .join("Local")
        .join("Google")
        .join("Chrome")
        .join("User Data")
        .join("Default")
        .join("Local Storage")
        .join("leveldb");
    
    if chrome_path.exists() {
        // 尝试读取 localStorage 文件
        // 注意：这需要解析 LevelDB 格式，比较复杂
        // 这里提供一个简化的实现
        
        match fs::read_dir(&chrome_path) {
            Ok(entries) => {
                for entry in entries.flatten() {
                    let path = entry.path();
                    if path.extension().and_then(|s| s.to_str()) == Some("log") {
                        if let Ok(content) = fs::read_to_string(&path) {
                            // 搜索 filebay 相关的配置
                            if content.contains("filebay") || content.contains("gitea") {
                                // 尝试提取配置
                                // 这里需要更复杂的解析逻辑
                                return Ok(ConfigLoadResult {
                                    success: false,
                                    config: None,
                                    method: "browser_storage".to_string(),
                                    message: "Found potential config in browser storage, but parsing not implemented".to_string(),
                                });
                            }
                        }
                    }
                }
                
                Ok(ConfigLoadResult {
                    success: false,
                    config: None,
                    method: "browser_storage".to_string(),
                    message: "No config found in browser storage".to_string(),
                })
            }
            Err(e) => Ok(ConfigLoadResult {
                success: false,
                config: None,
                method: "browser_storage".to_string(),
                message: format!("Failed to read browser storage: {}", e),
            }),
        }
    } else {
        Ok(ConfigLoadResult {
            success: false,
            config: None,
            method: "browser_storage".to_string(),
            message: format!("Chrome localStorage not found at {:?}", chrome_path),
        })
    }
}

// ============================================================================
// 智能加载器：按优先级尝试所有方法
// ============================================================================

#[tauri::command]
pub async fn load_config_smart() -> Result<ConfigLoadResult, String> {
    println!("[Config Loader] Starting smart config loading...");
    
    // 方法 1: Vault 数据库
    println!("[Config Loader] Trying method 1: Vault Database");
    match load_config_from_vault_db().await {
        Ok(result) if result.success => {
            println!("[Config Loader] ✓ Success with method 1");
            return Ok(result);
        }
        Ok(result) => println!("[Config Loader] ✗ Method 1 failed: {}", result.message),
        Err(e) => println!("[Config Loader] ✗ Method 1 error: {}", e),
    }
    
    // 方法 2: Vault Bridge API
    println!("[Config Loader] Trying method 2: Vault Bridge API");
    match load_config_from_vault_bridge().await {
        Ok(result) if result.success => {
            println!("[Config Loader] ✓ Success with method 2");
            return Ok(result);
        }
        Ok(result) => println!("[Config Loader] ✗ Method 2 failed: {}", result.message),
        Err(e) => println!("[Config Loader] ✗ Method 2 error: {}", e),
    }
    
    // 方法 3: Web API
    println!("[Config Loader] Trying method 3: Web API");
    match load_config_from_web_api().await {
        Ok(result) if result.success => {
            println!("[Config Loader] ✓ Success with method 3");
            return Ok(result);
        }
        Ok(result) => println!("[Config Loader] ✗ Method 3 failed: {}", result.message),
        Err(e) => println!("[Config Loader] ✗ Method 3 error: {}", e),
    }
    
    // 方法 4: 浏览器 localStorage
    println!("[Config Loader] Trying method 4: Browser Storage");
    match load_config_from_browser_storage().await {
        Ok(result) if result.success => {
            println!("[Config Loader] ✓ Success with method 4");
            return Ok(result);
        }
        Ok(result) => println!("[Config Loader] ✗ Method 4 failed: {}", result.message),
        Err(e) => println!("[Config Loader] ✗ Method 4 error: {}", e),
    }
    
    // 所有方法都失败
    println!("[Config Loader] ✗ All methods failed");
    Ok(ConfigLoadResult {
        success: false,
        config: None,
        method: "none".to_string(),
        message: "All config loading methods failed. Please login to Vault or enter config manually.".to_string(),
    })
}

// ============================================================================
// 测试所有方法
// ============================================================================

#[derive(Debug, Serialize, Deserialize)]
pub struct AllMethodsResult {
    pub vault_db: ConfigLoadResult,
    pub vault_bridge: ConfigLoadResult,
    pub web_api: ConfigLoadResult,
    pub browser_storage: ConfigLoadResult,
    pub summary: String,
}

#[tauri::command]
pub async fn test_all_config_methods() -> Result<AllMethodsResult, String> {
    println!("[Config Loader] Testing all methods...");
    
    let vault_db = load_config_from_vault_db().await.unwrap_or_else(|e| ConfigLoadResult {
        success: false,
        config: None,
        method: "vault_db".to_string(),
        message: e,
    });
    
    let vault_bridge = load_config_from_vault_bridge().await.unwrap_or_else(|e| ConfigLoadResult {
        success: false,
        config: None,
        method: "vault_bridge".to_string(),
        message: e,
    });
    
    let web_api = load_config_from_web_api().await.unwrap_or_else(|e| ConfigLoadResult {
        success: false,
        config: None,
        method: "web_api".to_string(),
        message: e,
    });
    
    let browser_storage = load_config_from_browser_storage().await.unwrap_or_else(|e| ConfigLoadResult {
        success: false,
        config: None,
        method: "browser_storage".to_string(),
        message: e,
    });
    
    let success_count = [&vault_db, &vault_bridge, &web_api, &browser_storage]
        .iter()
        .filter(|r| r.success)
        .count();
    
    let summary = format!(
        "Tested 4 methods: {} succeeded, {} failed",
        success_count,
        4 - success_count
    );
    
    Ok(AllMethodsResult {
        vault_db,
        vault_bridge,
        web_api,
        browser_storage,
        summary,
    })
}
```

### 前端 TypeScript (src/lib/config-loader.ts)

```typescript
import { invoke } from '@tauri-apps/api/core';

export interface FileBayConfig {
  url: string;
  username: string;
  repo_name: string;
  email: string;
  token: string;
  source: string;
}

export interface ConfigLoadResult {
  success: boolean;
  config: FileBayConfig | null;
  method: string;
  message: string;
}

export interface AllMethodsResult {
  vault_db: ConfigLoadResult;
  vault_bridge: ConfigLoadResult;
  web_api: ConfigLoadResult;
  browser_storage: ConfigLoadResult;
  summary: string;
}

/**
 * 智能加载配置：自动尝试所有方法
 */
export async function loadConfigSmart(): Promise<ConfigLoadResult> {
  return await invoke<ConfigLoadResult>('load_config_smart');
}

/**
 * 测试所有方法
 */
export async function testAllMethods(): Promise<AllMethodsResult> {
  return await invoke<AllMethodsResult>('test_all_config_methods');
}

/**
 * 单独测试每个方法
 */
export async function loadFromVaultDb(): Promise<ConfigLoadResult> {
  return await invoke<ConfigLoadResult>('load_config_from_vault_db');
}

export async function loadFromVaultBridge(): Promise<ConfigLoadResult> {
  return await invoke<ConfigLoadResult>('load_config_from_vault_bridge');
}

export async function loadFromWebApi(): Promise<ConfigLoadResult> {
  return await invoke<ConfigLoadResult>('load_config_from_web_api');
}

export async function loadFromBrowserStorage(): Promise<ConfigLoadResult> {
  return await invoke<ConfigLoadResult>('load_config_from_browser_storage');
}
```

### 测试页面 (src/pages/ConfigLoaderTest.tsx)

```typescript
import { useState } from 'react';
import { testAllMethods, loadConfigSmart, AllMethodsResult, ConfigLoadResult } from '@/lib/config-loader';

export function ConfigLoaderTest() {
  const [testing, setTesting] = useState(false);
  const [result, setResult] = useState<AllMethodsResult | null>(null);
  const [smartResult, setSmartResult] = useState<ConfigLoadResult | null>(null);

  const handleTestAll = async () => {
    setTesting(true);
    try {
      const res = await testAllMethods();
      setResult(res);
    } catch (error) {
      console.error('Test failed:', error);
    } finally {
      setTesting(false);
    }
  };

  const handleSmartLoad = async () => {
    setTesting(true);
    try {
      const res = await loadConfigSmart();
      setSmartResult(res);
    } catch (error) {
      console.error('Smart load failed:', error);
    } finally {
      setTesting(false);
    }
  };

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-6">配置加载器测试</h1>
      
      <div className="space-y-4">
        <button
          onClick={handleSmartLoad}
          disabled={testing}
          className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
        >
          {testing ? '加载中...' : '智能加载配置'}
        </button>
        
        <button
          onClick={handleTestAll}
          disabled={testing}
          className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 ml-4"
        >
          {testing ? '测试中...' : '测试所有方法'}
        </button>
      </div>

      {smartResult && (
        <div className="mt-6 p-4 border rounded">
          <h2 className="text-xl font-semibold mb-2">智能加载结果</h2>
          <div className={`p-3 rounded ${smartResult.success ? 'bg-green-100' : 'bg-red-100'}`}>
            <p><strong>状态:</strong> {smartResult.success ? '✓ 成功' : '✗ 失败'}</p>
            <p><strong>方法:</strong> {smartResult.method}</p>
            <p><strong>消息:</strong> {smartResult.message}</p>
            {smartResult.config && (
              <div className="mt-2">
                <p><strong>URL:</strong> {smartResult.config.url}</p>
                <p><strong>用户名:</strong> {smartResult.config.username}</p>
                <p><strong>仓库:</strong> {smartResult.config.repo_name}</p>
                <p><strong>来源:</strong> {smartResult.config.source}</p>
              </div>
            )}
          </div>
        </div>
      )}

      {result && (
        <div className="mt-6 space-y-4">
          <h2 className="text-xl font-semibold">测试结果: {result.summary}</h2>
          
          {[
            { title: '方法 1: Vault 数据库', data: result.vault_db },
            { title: '方法 2: Vault Bridge API', data: result.vault_bridge },
            { title: '方法 3: Web API', data: result.web_api },
            { title: '方法 4: 浏览器 localStorage', data: result.browser_storage },
          ].map(({ title, data }) => (
            <div key={data.method} className="p-4 border rounded">
              <h3 className="font-semibold mb-2">{title}</h3>
              <div className={`p-3 rounded ${data.success ? 'bg-green-100' : 'bg-yellow-100'}`}>
                <p><strong>状态:</strong> {data.success ? '✓ 成功' : '✗ 失败'}</p>
                <p><strong>消息:</strong> {data.message}</p>
                {data.config && (
                  <div className="mt-2 text-sm">
                    <p>URL: {data.config.url}</p>
                    <p>用户: {data.config.username}</p>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
```

## 依赖配置

### Cargo.toml

```toml
[dependencies]
tauri = { version = "2.0", features = [] }
serde = { version = "1.0", features = ["derive"] }
serde_json = "1.0"
rusqlite = { version = "0.32", features = ["bundled"] }
reqwest = { version = "0.11", features = ["json"] }
dirs = "5.0"
```

### main.rs

```rust
mod commands;

fn main() {
    tauri::Builder::default()
        .invoke_handler(tauri::generate_handler![
            commands::config_loader::load_config_smart,
            commands::config_loader::test_all_config_methods,
            commands::config_loader::load_config_from_vault_db,
            commands::config_loader::load_config_from_vault_bridge,
            commands::config_loader::load_config_from_web_api,
            commands::config_loader::load_config_from_browser_storage,
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
```

## 使用方法

1. **智能加载**（推荐）:
   ```typescript
   const result = await loadConfigSmart();
   if (result.success) {
     console.log('Config loaded from:', result.method);
     console.log('Config:', result.config);
   }
   ```

2. **测试所有方法**:
   ```typescript
   const results = await testAllMethods();
   console.log(results.summary);
   ```

3. **单独测试某个方法**:
   ```typescript
   const result = await loadFromVaultDb();
   ```

这样你就可以测试所有方法，看哪个最适合你的场景！🎉
