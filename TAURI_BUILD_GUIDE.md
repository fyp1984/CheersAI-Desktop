# CheersAI Tauri 桌面应用构建指南

## 概述

CheersAI 现在支持使用 Tauri 打包为桌面应用。Tauri 是一个现代的桌面应用框架，相比 Electron 有以下优势：

- ✅ **更小的体积**：使用系统 WebView 而不是打包 Chromium
- ✅ **更好的性能**：使用 Rust 而不是 Node.js
- ✅ **更好的安全性**：默认的安全配置
- ✅ **跨平台支持**：Windows、macOS、Linux

## 前置要求

### Windows
1. **安装 Rust**
   ```bash
   # 下载并安装 rustup
   # https://rustup.rs/
   ```

2. **安装 WebView2**（Windows 10/11 通常已预装）
   - 如果没有，会在首次运行时自动安装

3. **安装 Visual Studio Build Tools**
   - 下载：https://visualstudio.microsoft.com/downloads/
   - 选择 "Desktop development with C++"

### macOS
```bash
# 安装 Xcode Command Line Tools
xcode-select --install

# 安装 Rust
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
```

### Linux (Ubuntu/Debian)
```bash
# 安装依赖
sudo apt update
sudo apt install libwebkit2gtk-4.1-dev \
  build-essential \
  curl \
  wget \
  file \
  libxdo-dev \
  libssl-dev \
  libayatana-appindicator3-dev \
  librsvg2-dev

# 安装 Rust
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
```

## 开发模式

### 1. 启动开发服务器
```bash
cd web
pnpm dev
```
在另一个终端窗口中启动 Tauri：

### 2. 启动 Tauri 开发模式
```bash
cd web
pnpm dev:tauri
```

这会：
- 打开一个桌面窗口
- 连接到 `http://localhost:3500`
- 支持热重载

## 生产构建

### 构建前准备

1. **确保前端已构建**
   ```bash
   cd web
   pnpm build
   ```

2. **生成图标**（可选，如果要使用自定义图标）
   ```bash
   node scripts/generate-tauri-icons.cjs
   ```

### 构建应用

```bash
cd web
pnpm build:tauri
```

这会：
- 构建 Next.js 应用（静态导出到 `out/` 目录）
- 编译 Rust 代码
- 打包为平台特定的安装包

### 构建输出

构建完成后，安装包位于：

**Windows:**
- `web/src-tauri/target/release/bundle/nsis/CheersAI_1.12.0_x64-setup.exe` (安装程序)
- `web/src-tauri/target/release/bundle/msi/CheersAI_1.12.0_x64_en-US.msi` (MSI 安装包)

**macOS:**
- `web/src-tauri/target/release/bundle/dmg/CheersAI_1.12.0_x64.dmg`
- `web/src-tauri/target/release/bundle/macos/CheersAI.app`

**Linux:**
- `web/src-tauri/target/release/bundle/deb/cheersai_1.12.0_amd64.deb`
- `web/src-tauri/target/release/bundle/appimage/cheersai_1.12.0_amd64.AppImage`

## 调试构建

如果需要调试版本（包含调试符号，构建更快）：

```bash
pnpm build:tauri:debug
```

## 配置

### Tauri 配置文件

主配置文件：`web/src-tauri/tauri.conf.json`

关键配置项：
```json
{
  "productName": "CheersAI",
  "version": "1.12.0",
  "identifier": "com.cheersai.desktop",
  "build": {
    "frontendDist": "../out",
    "devUrl": "http://localhost:3500"
  }
}
```

### 窗口配置

在 `tauri.conf.json` 中修改窗口设置：
```json
{
  "app": {
    "windows": [
      {
        "title": "CheersAI",
        "width": 1280,
        "height": 800,
        "minWidth": 1024,
        "minHeight": 768
      }
    ]
  }
}
```

## 常见问题

### 1. Rust 编译错误

**问题**: `error: linker 'link.exe' not found`

**解决**: 安装 Visual Studio Build Tools（Windows）

### 2. WebView2 缺失

**问题**: 应用启动失败，提示缺少 WebView2

**解决**: 
- Windows 10/11: 通常已预装
- 手动下载：https://developer.microsoft.com/microsoft-edge/webview2/

### 3. 构建体积大

**问题**: 构建的应用体积较大

**解决**: 
- 使用 `pnpm build:tauri` 而不是 debug 模式
- Tauri 会自动优化和压缩

### 4. 图标显示不正确

**问题**: 应用图标显示为默认图标

**解决**:
```bash
# 重新生成图标
node scripts/generate-tauri-icons.cjs

# 清理并重新构建
cd src-tauri
cargo clean
cd ..
pnpm build:tauri
```

## 与 Electron 的对比

| 特性 | Tauri | Electron |
|------|-------|----------|
| 运行时 | Rust + 系统 WebView | Node.js + Chromium |
| 安装包大小 | ~3-10 MB | ~50-150 MB |
| 内存占用 | 更低 | 更高 |
| 启动速度 | 更快 | 较慢 |
| 跨平台 | ✅ | ✅ |
| 生态系统 | 较新 | 成熟 |

## 下一步

1. **测试应用**: 在目标平台上测试构建的应用
2. **代码签名**: 为生产环境添加代码签名
3. **自动更新**: 配置 Tauri 的自动更新功能
4. **CI/CD**: 设置自动化构建流程

## 参考资源

- [Tauri 官方文档](https://tauri.app/)
- [Tauri API 文档](https://tauri.app/v1/api/js/)
- [Rust 安装指南](https://www.rust-lang.org/tools/install)
