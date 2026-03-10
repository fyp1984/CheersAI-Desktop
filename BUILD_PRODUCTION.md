# 生成 CheersAI 生产安装包

## 当前状态

- **开发版 exe**: `web\src-tauri\target\debug\app.exe` ✅ 已存在
- **生产安装包**: 尚未生成

## 生成生产安装包步骤

### 1. 确保前端已构建
```powershell
cd web
npx pnpm build
```

### 2. 构建 Tauri 生产版本
```powershell
# 添加 Rust 到 PATH
$env:Path += ";$env:USERPROFILE\.cargo\bin"

# 构建生产版本
npx pnpm build:tauri
```

### 3. 安装包位置

构建完成后，安装包将位于：

- **NSIS 安装程序**: `web\src-tauri\target\release\bundle\nsis\CheersAI_1.12.0_x64-setup.exe`
- **MSI 安装程序**: `web\src-tauri\target\release\bundle\msi\CheersAI_1.12.0_x64_en-US.msi`
- **便携版 exe**: `web\src-tauri\target\release\app.exe`

## 构建时间预估

- 首次构建：约 5-10 分钟（需要编译优化版本）
- 后续构建：约 2-5 分钟

## 注意事项

1. 生产构建会进行完整优化，文件体积更小，性能更好
2. 确保后端服务（API）正在运行，因为桌面应用需要连接后端
3. 安装包大小约 10-20 MB（比开发版小很多）

## 快速命令

```powershell
# 一键构建（从项目根目录）
cd web
$env:Path += ";$env:USERPROFILE\.cargo\bin"
npx pnpm build
npx pnpm build:tauri
```

构建完成后，安装包在：`web\src-tauri\target\release\bundle\nsis\CheersAI_1.12.0_x64-setup.exe`
