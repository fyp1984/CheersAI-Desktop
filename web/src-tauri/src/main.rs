// Prevents additional console window on Windows in release, DO NOT REMOVE!!
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

// ===== 文件系统 Commands =====

#[derive(serde::Serialize)]
struct SandboxFileInfo {
    name: String,
    size: u64,
    created_at: String,
}

#[tauri::command]
fn sandbox_write_file(dir: String, file_name: String, content: String) -> Result<String, String> {
    let dir_path = std::path::Path::new(&dir);
    if !dir_path.exists() {
        std::fs::create_dir_all(dir_path).map_err(|e| format!("创建目录失败: {}", e))?;
    }
    let file_path = dir_path.join(&file_name);
    std::fs::write(&file_path, &content).map_err(|e| format!("写入文件失败: {}", e))?;
    Ok(file_path.to_string_lossy().to_string())
}

#[tauri::command]
fn sandbox_read_file(path: String) -> Result<String, String> {
    std::fs::read_to_string(&path).map_err(|e| format!("读取文件失败: {}", e))
}

#[tauri::command]
fn sandbox_list_files(dir: String) -> Result<Vec<SandboxFileInfo>, String> {
    let dir_path = std::path::Path::new(&dir);
    if !dir_path.exists() {
        return Ok(vec![]);
    }
    let mut files = Vec::new();
    let entries = std::fs::read_dir(dir_path).map_err(|e| format!("读取目录失败: {}", e))?;
    for entry in entries {
        if let Ok(entry) = entry {
            if let Ok(meta) = entry.metadata() {
                if meta.is_file() {
                    let created = meta.created()
                        .map(|t| {
                            let dt: chrono::DateTime<chrono::Local> = t.into();
                            dt.format("%Y-%m-%dT%H:%M:%S").to_string()
                        })
                        .unwrap_or_default();
                    files.push(SandboxFileInfo {
                        name: entry.file_name().to_string_lossy().to_string(),
                        size: meta.len(),
                        created_at: created,
                    });
                }
            }
        }
    }
    files.sort_by(|a, b| b.created_at.cmp(&a.created_at));
    Ok(files)
}

#[tauri::command]
fn sandbox_delete_file(path: String) -> Result<(), String> {
    std::fs::remove_file(&path).map_err(|e| format!("删除文件失败: {}", e))
}

#[tauri::command]
fn sandbox_ensure_dir(dir: String) -> Result<bool, String> {
    let dir_path = std::path::Path::new(&dir);
    if !dir_path.exists() {
        std::fs::create_dir_all(dir_path).map_err(|e| format!("创建目录失败: {}", e))?;
    }
    Ok(dir_path.exists() && dir_path.is_dir())
}

fn main() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .invoke_handler(tauri::generate_handler![
            sandbox_write_file,
            sandbox_read_file,
            sandbox_list_files,
            sandbox_delete_file,
            sandbox_ensure_dir,
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
