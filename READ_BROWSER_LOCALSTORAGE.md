# 从浏览器 localStorage 读取 FileBay 配置

## 问题场景

- **Vault Web 系统** (http://localhost:3000) 在浏览器 localStorage 中存储了 FileBay 配置
- **Tauri 脱敏应用** (本地应用) 需要读取这个配置

## 浏览器 localStorage 存储位置

### Chrome/Edge (Chromium)

```
Windows:
C:\Users\<用户名>\AppData\Local\Google\Chrome\User Data\Default\Local Storage\leveldb\
C:\Users\<用户名>\AppData\Local\Microsoft\Edge\User Data\Default\Local Storage\leveldb\

Mac:
~/Library/Application Support/Google/Chrome/Default/Local Storage/leveldb/
~/Library/Application Support/Microsoft Edge/Default/Local Storage/leveldb/

Linux:
~/.config/google-chrome/Default/Local Storage/leveldb/
~/.config/microsoft-edge/Default/Local Storage/leveldb/
```

### Firefox

```
Windows:
C:\Users\<用户名>\AppData\Roaming\Mozilla\Firefox\Profiles\<profile>\storage\default\http+++localhost+3000\ls\

Mac:
~/Library/Application Support/Firefox/Profiles/<profile>/storage/default/http+++localhost+3000/ls/

Linux:
~/.mozilla/firefox/<profile>/storage/default/http+++localhost+3000/ls/
```

## 解决方案 1: 使用 Vault Bridge（推荐）✅

**这是最简单、最可靠的方案！**

Web 端登录后，通过 Vault Bridge 将配置同步到共享数据库，Tauri 应用直接读取数据库。

### 优势
- ✅ 不需要解析浏览器文件
- ✅ 跨浏览器兼容
- ✅ 数据格式统一
- ✅ 已经实现（前面的工作）

### 实现
```rust
// 直接读取 Vault 数据库
#[tauri::command]
pub async fn list_vault_configs() -> Result<Vec<VaultFileBayConfig>, String> {
    let db_path = dirs::home_dir()
        .expect("Failed to get home directory")
        .join(".cheersai")
        .join("vault.db");
    
    // 读取配置...
}
```

## 解决方案 2: 通过 Web API 获取

让 Web 端提供一个 API，Tauri 应用通过 HTTP 请求获取配置。

### Web 端实现

```typescript
// web/app/api/local-config/route.ts
import { NextRequest, NextResponse } from 'next/server';

export async function GET(request: NextRequest) {
  // 从 session 或 cookie 获取用户信息
  const userId = request.cookies.get('user_id')?.value;
  
  if (!userId) {
    return NextResponse.json({ error: 'Not authenticated' }, { status: 401 });
  }
  
  // 获取 FileBay 配置
  const config = await getFileBayConfig(userId);
  
  return NextResponse.json(config);
}
```

### Tauri 端实现

```rust
#[tauri::command]
pub async fn fetch_config_from_web() -> Result<FileBayConfig, String> {
    let client = reqwest::Client::new();
    
    let response = client
        .get("http://localhost:3000/api/local-config")
        .send()
        .await
        .map_err(|e| format!("Request failed: {}", e))?;
    
    if !response.status().is_success() {
        return Err("Failed to fetch config from web".to_string());
    }
    
    let config: FileBayConfig = response
        .json()
        .await
        .map_err(|e| format!("Failed to parse config: {}", e))?;
    
    Ok(config)
}
```

## 解决方案 3: 内嵌 WebView 读取

在 Tauri 应用中内嵌一个隐藏的 WebView，访问 Web 端并读取 localStorage。

### 实现

```rust
use tauri::Manager;

#[tauri::command]
pub async fn read_web_localstorage(app: tauri::AppHandle) -> Result<String, String> {
    let window = app.get_window("main").unwrap();
    
    // 执行 JavaScript 读取 localStorage
    let result = window
        .eval(&format!(
            r#"
            (async () => {{
                const iframe = document.createElement('iframe');
                iframe.src = 'http://localhost:3000';
                iframe.style.display = 'none';
                document.body.appendChild(iframe);
                
                await new Promise(resolve => setTimeout(resolve, 1000));
                
                const config = iframe.contentWindow.localStorage.getItem('filebay_config');
                document.body.removeChild(iframe);
                
                return config;
            }})()
            "#
        ))
        .await
        .map_err(|e| format!("Failed to read localStorage: {}", e))?;
    
    Ok(result.to_string())
}
```

## 推荐实现：组合方案

结合 Vault Bridge 和 Web API，提供最佳用户体验。

### 完整流程

```
┌─────────────────────────────────────────────────────────────┐
│  1. 用户在 Web 端登录                                         │
│     - Desktop SSO 认证                                       │
│     - 获取 FileBay 配置                                      │
│     - 配置存储到 localStorage                                │
│     - 同时同步到 Vault Bridge                                │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│  2. Vault Bridge 保存到数据库                                 │
│     - POST http://localhost:8765/vault/config/filebay        │
│     - 保存到 ~/.cheersai/vault.db                            │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│  3. Tauri 应用读取配置                                        │
│     方式 A: 直接读取 Vault 数据库 ✅ (推荐)                   │
│     方式 B: 调用 Web API                                     │
│     方式 C: 读取浏览器 localStorage 文件                      │
└─────────────────────────────────────────────────────────────┘
```

### Tauri 端完整实现

```rust
// src-tauri/src/commands/config.rs
use serde::{Deserialize, Serialize};
use rusqlite::Connection;
use std::path::PathBuf;

#[derive(Debug, Serialize, Deserialize)]
pub struct FileBayConfig {
    pub url: String,
    pub username: String,
    pub repo_name: String,
    pub token: String,
    pub email: String,
}

/// 优先级：Vault DB > Web API > 手动输入
#[tauri::command]
pub async fn get_filebay_config() -> Result<FileBayConfig, String> {
    // 1. 尝试从 Vault 数据库读取
    if let Ok(config) = read_from_vault_db().await {
        println!("[Config] Loaded from Vault database");
        return Ok(config);
    }
    
    // 2. 尝试从 Web API 获取
    if let Ok(config) = fetch_from_web_api().await {
        println!("[Config] Fetched from Web API");
        // 保存到 Vault 数据库以便下次使用
        let _ = save_to_vault_db(&config).await;
        return Ok(config);
    }
    
    // 3. 返回错误，提示用户手动输入或登录
    Err("No config found. Please login to Vault system first.".to_string())
}

async fn read_from_vault_db() -> Result<FileBayConfig, String> {
    let db_path = dirs::home_dir()
        .ok_or("Failed to get home directory")?
        .join(".cheersai")
        .join("vault.db");
    
    if !db_path.exists() {
        return Err("Vault database not found".to_string());
    }
    
    let conn = Connection::open(db_path)
        .map_err(|e| format!("Failed to open database: {}", e))?;
    
    // 获取最新的配置
    let mut stmt = conn.prepare(
        "SELECT url, username, repo_name, token, email 
         FROM filebay_configs 
         ORDER BY updated_at DESC 
         LIMIT 1"
    ).map_err(|e| format!("Failed to prepare statement: {}", e))?;
    
    let config = stmt.query_row([], |row| {
        Ok(FileBayConfig {
            url: row.get(0)?,
            username: row.get(1)?,
            repo_name: row.get(2)?,
            token: row.get(3)?,
            email: row.get(4)?,
        })
    }).map_err(|e| format!("No config found: {}", e))?;
    
    Ok(config)
}

async fn fetch_from_web_api() -> Result<FileBayConfig, String> {
    let client = reqwest::Client::new();
    
    let response = client
        .get("http://localhost:3000/api/local-config")
        .timeout(std::time::Duration::from_secs(5))
        .send()
        .await
        .map_err(|e| format!("Web API request failed: {}", e))?;
    
    if !response.status().is_success() {
        return Err("Web API returned error".to_string());
    }
    
    let config: FileBayConfig = response
        .json()
        .await
        .map_err(|e| format!("Failed to parse response: {}", e))?;
    
    Ok(config)
}

async fn save_to_vault_db(config: &FileBayConfig) -> Result<(), String> {
    // 保存到 Vault 数据库的实现
    // ...
    Ok(())
}
```

### 前端使用

```typescript
// src/lib/config.ts
import { invoke } from '@tauri-apps/api/core';

export async function loadFileBayConfig() {
  try {
    const config = await invoke('get_filebay_config');
    console.log('[Config] Loaded successfully:', config);
    return config;
  } catch (error) {
    console.error('[Config] Failed to load:', error);
    throw error;
  }
}
```

## 最佳实践

1. **优先使用 Vault Bridge** ✅
   - 最可靠
   - 最简单
   - 已经实现

2. **Web API 作为备选**
   - 当 Vault 数据库不存在时
   - 实时获取最新配置

3. **提供手动输入**
   - 作为最后的备选方案
   - 用户体验最差，但总能工作

## 依赖

```toml
[dependencies]
reqwest = { version = "0.11", features = ["json"] }
rusqlite = { version = "0.32", features = ["bundled"] }
dirs = "5.0"
serde = { version = "1.0", features = ["derive"] }
serde_json = "1.0"
```

## 总结

**推荐方案**: 使用已经实现的 Vault Bridge！

- ✅ 不需要解析浏览器文件
- ✅ 不需要额外的 Web API
- ✅ 简单、可靠、已验证
- ✅ 只需要实现 Rust 读取数据库的代码

你只需要在脱敏应用中添加读取 `~/.cheersai/vault.db` 的代码即可！
