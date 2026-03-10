# CheersAI Electron 打包指南

版本：v1.0  
更新日期：2026-02-04

## 📋 概述

本文档说明如何将 CheersAI 前端应用打包为 Electron 桌面应用。

---

## 🔧 环境要求

### 必需软件
- **Node.js**: >= 24.x
- **pnpm**: 10.27.0+
- **Python**: 2.7 或 3.x（用于 node-gyp）

### Windows 额外要求
- Visual Studio Build Tools 或 Visual Studio（包含 C++ 工作负载）
- Windows SDK

### macOS 额外要求
- Xcode Command Line Tools
- 代码签名证书（可选，用于发布）

### Linux 额外要求
- `libgtk-3-dev`
- `libnotify-dev`
- `libnss3-dev`
- `libxss1`
- `libxtst-dev`
- `libgconf-2-4`
- `libasound2-dev`

---

## 📦 项目结构

```
web/
├── electron/                    # Electron 相关文件
│   ├── main.js                 # 主进程入口
│   ├── preload.js              # 预加载脚本
│   ├── package.json            # Electron package.json
│   └── entitlements.mac.plist  # macOS 权限配置
├── electron-builder.json        # Electron Builder 配置
├── next.config.electron.ts      # Electron 专用 Next.js 配置
├── scripts/
│   └── build-electron.js       # 构建脚本
├── out/                        # Next.js 静态导出目录
└── dist-electron/              # Electron 打包输出目录
```

---

## 🚀 快速开始

### 1. 安装依赖

```bash
cd web
pnpm install
```

这会自动安装 Electron 和 electron-builder。

### 2. 开发模式

#### 方式 1：分别启动（推荐）

```bash
# 终端 1：启动 Next.js 开发服务器
pnpm dev

# 终端 2：启动 Electron
pnpm dev:electron
```

#### 方式 2：使用开发脚本

```bash
# 同时启动 Next.js 和 Electron
pnpm dev:electron
```

**注意**：确保 Next.js 开发服务器运行在 `http://localhost:3500`

### 3. 构建生产版本

#### 构建所有平台（需要在对应平台上运行）

```bash
pnpm build:electron
```

#### 仅构建 Windows

```bash
pnpm build:electron:win
```

输出文件：
- `dist-electron/CheersAI-1.12.0-x64.exe` - 安装程序
- `dist-electron/CheersAI-1.12.0-arm64.exe` - ARM64 安装程序
- `dist-electron/CheersAI-1.12.0-portable.exe` - 便携版

#### 仅构建 macOS

```bash
pnpm build:electron:mac
```

输出文件：
- `dist-electron/CheersAI-1.12.0-x64.dmg` - Intel Mac 安装包
- `dist-electron/CheersAI-1.12.0-arm64.dmg` - Apple Silicon 安装包
- `dist-electron/CheersAI-1.12.0-x64.zip` - Intel Mac 压缩包
- `dist-electron/CheersAI-1.12.0-arm64.zip` - Apple Silicon 压缩包

#### 仅构建 Linux

```bash
pnpm build:electron:linux
```

输出文件：
- `dist-electron/CheersAI-1.12.0-x64.AppImage` - AppImage 格式
- `dist-electron/CheersAI-1.12.0-arm64.AppImage` - ARM64 AppImage
- `dist-electron/CheersAI-1.12.0-x64.deb` - Debian 包
- `dist-electron/CheersAI-1.12.0-arm64.deb` - ARM64 Debian 包

---

## 📝 配置说明

### electron-builder.json

主要配置项：

```json
{
  "appId": "com.cheersai.desktop",        // 应用 ID
  "productName": "CheersAI",              // 产品名称
  "directories": {
    "output": "dist-electron",            // 输出目录
    "buildResources": "electron/resources" // 资源目录
  },
  "files": [
    "out/**/*",                           // Next.js 构建输出
    "electron/**/*",                      // Electron 文件
    "public/logo/**/*",                   // Logo 资源
    "package.json"
  ]
}
```

### next.config.electron.ts

Electron 专用配置：

```typescript
{
  output: 'export',           // 静态导出
  distDir: 'out',            // 输出目录
  images: {
    unoptimized: true,       // 禁用图片优化
  },
  trailingSlash: true,       // URL 尾部斜杠
}
```

### electron/main.js

主进程配置：

```javascript
{
  width: 1280,               // 窗口宽度
  height: 800,               // 窗口高度
  minWidth: 1024,            // 最小宽度
  minHeight: 768,            // 最小高度
  webPreferences: {
    nodeIntegration: false,  // 禁用 Node 集成（安全）
    contextIsolation: true,  // 启用上下文隔离（安全）
    preload: 'preload.js',   // 预加载脚本
  }
}
```

---

## 🔐 安全最佳实践

### 1. 禁用 Node 集成

```javascript
webPreferences: {
  nodeIntegration: false,
  contextIsolation: true,
}
```

### 2. 使用预加载脚本

通过 `contextBridge` 暴露安全的 API：

```javascript
// electron/preload.js
contextBridge.exposeInMainWorld('electron', {
  platform: process.platform,
  // 只暴露必要的 API
})
```

### 3. 内容安全策略（CSP）

在 Next.js 中配置 CSP 头部。

---

## 🎨 自定义配置

### 修改应用图标

1. 准备图标文件：
   - Windows: `.ico` 格式，256x256 或更大
   - macOS: `.icns` 格式，512x512 或更大
   - Linux: `.png` 格式，512x512 或更大

2. 放置图标：
   ```
   web/public/logo/icon.ico   # Windows
   web/public/logo/icon.icns  # macOS
   web/public/logo/icon.png   # Linux
   ```

3. 更新 `electron-builder.json`：
   ```json
   {
     "win": {
       "icon": "public/logo/icon.ico"
     },
     "mac": {
       "icon": "public/logo/icon.icns"
     },
     "linux": {
       "icon": "public/logo/icon.png"
     }
   }
   ```

### 修改窗口大小

编辑 `electron/main.js`：

```javascript
mainWindow = new BrowserWindow({
  width: 1600,      // 修改宽度
  height: 900,      // 修改高度
  minWidth: 1280,   // 修改最小宽度
  minHeight: 720,   // 修改最小高度
})
```

### 添加自定义菜单

在 `electron/main.js` 的 `createMenu()` 函数中添加菜单项。

---

## 🐛 常见问题

### 1. 构建失败：找不到 Python

**解决方案**：
```bash
# Windows
npm install --global windows-build-tools

# macOS/Linux
# 安装 Python 2.7 或 3.x
```

### 2. Windows 构建失败：缺少 Visual Studio

**解决方案**：
安装 Visual Studio Build Tools：
```bash
npm install --global windows-build-tools
```

### 3. macOS 代码签名失败

**解决方案**：
- 开发环境可以跳过签名：
  ```bash
  export CSC_IDENTITY_AUTO_DISCOVERY=false
  pnpm build:electron:mac
  ```

### 4. 应用启动后白屏

**原因**：Next.js 路由问题

**解决方案**：
1. 确保使用 `output: 'export'` 配置
2. 检查 `electron/main.js` 中的加载路径
3. 开发模式确保 Next.js 服务器运行在正确端口

### 5. 图片无法加载

**原因**：Next.js 图片优化不支持静态导出

**解决方案**：
在 `next.config.electron.ts` 中设置：
```typescript
images: {
  unoptimized: true,
}
```

### 6. API 请求失败

**原因**：Electron 中需要配置后端 API 地址

**解决方案**：
在环境变量中设置：
```bash
NEXT_PUBLIC_API_URL=http://localhost:5001
```

---

## 📊 构建优化

### 减小包体积

1. **启用 asar 打包**（默认已启用）
   ```json
   {
     "asar": true
   }
   ```

2. **排除不必要的文件**
   ```json
   {
     "files": [
       "!**/*.map",
       "!**/*.md",
       "!**/test/**"
     ]
   }
   ```

3. **压缩代码**
   Next.js 生产构建会自动压缩。

### 加快构建速度

1. **使用缓存**
   ```bash
   # electron-builder 会自动缓存
   ```

2. **并行构建**
   ```bash
   # 同时构建多个架构
   electron-builder --win --x64 --arm64
   ```

---

## 🚢 发布流程

### 1. 更新版本号

编辑 `web/package.json`：
```json
{
  "version": "1.13.0"
}
```

### 2. 构建所有平台

```bash
# Windows
pnpm build:electron:win

# macOS（需要在 Mac 上运行）
pnpm build:electron:mac

# Linux（需要在 Linux 上运行）
pnpm build:electron:linux
```

### 3. 测试安装包

在目标平台上测试安装和运行。

### 4. 发布

将 `dist-electron/` 目录中的文件上传到发布平台。

---

## 📚 相关资源

- [Electron 官方文档](https://www.electronjs.org/docs)
- [electron-builder 文档](https://www.electron.build/)
- [Next.js 静态导出](https://nextjs.org/docs/app/building-your-application/deploying/static-exports)
- [Electron 安全指南](https://www.electronjs.org/docs/latest/tutorial/security)

---

## 🔄 更新日志

### v1.0 (2026-02-04)
- ✅ 初始 Electron 配置
- ✅ 支持 Windows/macOS/Linux 打包
- ✅ 配置开发和生产环境
- ✅ 添加安全最佳实践
- ✅ 创建构建脚本

---

## 📞 支持

如有问题，请查看：
1. 本文档的"常见问题"部分
2. Electron 官方文档
3. 项目 Issues

---

**文档维护者**：开发团队  
**最后更新**：2026-02-04
