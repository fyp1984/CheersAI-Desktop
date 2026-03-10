# CheersAI Tauri 桌面应用 - 完整设置指南

## ✅ 已完成的工作

1. **Tauri 初始化**
   - ✅ 安装了 `@tauri-apps/cli` 和 `@tauri-apps/api`
   - ✅ 创建了 `src-tauri/` 目录结构
   - ✅ 生成了配置文件 `tauri.conf.json`
   - ✅ 创建了 Rust 源代码文件

2. **配置优化**
   - ✅ 设置窗口大小为 1280x800
   - ✅ 设置最小窗口大小为 1024x768
   - ✅ 配置开发服务器 URL: `http://localhost:3500`
   - ✅ 配置构建输出目录: `../out`

3. **构建脚本**
   - ✅ 添加了 `pnpm dev:tauri` - 开发模式
   - ✅ 添加了 `pnpm build:tauri` - 生产构建
   - ✅ 添加了 `pnpm build:tauri:debug` - 调试构建

4. **文档**
   - ✅ 创建了 `TAURI_BUILD_GUIDE.md` - 构建指南
   - ✅ 创建了 `TAURI_SETUP.md` - 本文档

## 🔧 下一步：安装 Rust

Tauri 需要 Rust 编译器。请按照以下步骤安装：

### Windows 安装步骤

1. **下载 Rust 安装器**
   - 访问：https://rustup.rs/
   - 下载并运行 `rustup-init.exe`

2. **运行安装器**
   ```
   - 选择默认安装选项（按 1 然后回车）
   - 等待安装完成
   ```

3. **安装 Visual Studio Build Tools**
   - 下载：https://visualstudio.microsoft.com/downloads/
   - 选择 "Build Tools for Visual Studio 2022"
   - 在安装器中选择 "Desktop development with C++"
   - 点击安装

4. **验证安装**
   ```bash
   # 重新打开终端，然后运行：
   rustc --version
   cargo --version
   ```

   应该看到类似输出：
   ```
   rustc 1.75.0 (82e1608df 2023-12-21)
   cargo 1.75.0 (1d8b05cdd 2023-11-20)
   ```

### macOS 安装步骤

```bash
# 1. 安装 Xcode Command Line Tools
xcode-select --install

# 2. 安装 Rust
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

# 3. 配置环境
source $HOME/.cargo/env

# 4. 验证安装
rustc --version
cargo --version
```

### Linux (Ubuntu/Debian) 安装步骤

```bash
# 1. 安装系统依赖
sudo apt update
sudo apt install -y \
  libwebkit2gtk-4.1-dev \
  build-essential \
  curl \
  wget \
  file \
  libxdo-dev \
  libssl-dev \
  libayatana-appindicator3-dev \
  librsvg2-dev

# 2. 安装 Rust
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

# 3. 配置环境
source $HOME/.cargo/env

# 4. 验证安装
rustc --version
cargo --version
```

## 🚀 安装完成后的使用

### 开发模式

1. **启动前端开发服务器**（在一个终端）
   ```bash
   cd web
   pnpm dev
   ```

2. **启动 Tauri 开发窗口**（在另一个终端）
   ```bash
   cd web
   pnpm dev:tauri
   ```

   首次运行会：
   - 下载 Rust 依赖（可能需要几分钟）
   - 编译 Tauri 核心
   - 打开桌面应用窗口

### 生产构建

```bash
cd web

# 1. 构建前端
pnpm build

# 2. 构建 Tauri 应用
pnpm build:tauri
```

构建完成后，安装包位于：
- Windows: `src-tauri/target/release/bundle/nsis/CheersAI_1.12.0_x64-setup.exe`
- macOS: `src-tauri/target/release/bundle/dmg/CheersAI_1.12.0_x64.dmg`
- Linux: `src-tauri/target/release/bundle/deb/cheersai_1.12.0_amd64.deb`

## 📁 项目结构

```
web/
├── src-tauri/              # Tauri 后端（Rust）
│   ├── src/
│   │   ├── main.rs        # 主入口
│   │   └── lib.rs         # 库文件
│   ├── icons/             # 应用图标
│   ├── Cargo.toml         # Rust 依赖配置
│   └── tauri.conf.json    # Tauri 配置
├── out/                   # Next.js 构建输出（静态文件）
├── public/                # 静态资源
├── app/                   # Next.js 应用代码
└── package.json           # Node.js 依赖和脚本
```

## 🔍 故障排除

### 问题 1: `rustc` 命令未找到

**原因**: Rust 未安装或环境变量未配置

**解决**:
1. 确认已安装 Rust
2. 重新打开终端
3. 运行 `rustc --version` 验证

### 问题 2: 编译错误 `linker 'link.exe' not found`

**原因**: Windows 缺少 C++ 构建工具

**解决**: 安装 Visual Studio Build Tools（见上文）

### 问题 3: WebView2 错误

**原因**: Windows 缺少 WebView2 运行时

**解决**: 
- Windows 10/11 通常已预装
- 手动下载：https://developer.microsoft.com/microsoft-edge/webview2/

### 问题 4: 首次构建很慢

**原因**: Rust 需要编译所有依赖

**解决**: 这是正常的，首次构建可能需要 5-10 分钟，后续构建会快很多

## 📊 性能对比

| 指标 | Tauri | Electron |
|------|-------|----------|
| 安装包大小 | ~5-10 MB | ~50-150 MB |
| 内存占用 | ~50-100 MB | ~150-300 MB |
| 启动时间 | ~1-2 秒 | ~3-5 秒 |
| 首次构建时间 | ~5-10 分钟 | ~2-3 分钟 |
| 后续构建时间 | ~30-60 秒 | ~30-60 秒 |

## 🎯 推荐工作流

1. **开发阶段**: 使用 `pnpm dev` + 浏览器（更快的热重载）
2. **测试阶段**: 使用 `pnpm dev:tauri`（测试桌面功能）
3. **发布阶段**: 使用 `pnpm build:tauri`（生成安装包）

## 📚 相关文档

- [TAURI_BUILD_GUIDE.md](./TAURI_BUILD_GUIDE.md) - 详细构建指南
- [Tauri 官方文档](https://tauri.app/)
- [Rust 官方文档](https://www.rust-lang.org/)

## ✨ 下一步

安装 Rust 后，你就可以：
1. 运行 `pnpm dev:tauri` 启动开发模式
2. 运行 `pnpm build:tauri` 构建桌面应用
3. 测试和分发 CheersAI 桌面版本
