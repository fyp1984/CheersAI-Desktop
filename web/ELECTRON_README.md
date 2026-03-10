# CheersAI Electron 桌面应用

## 🚀 快速开始

### 开发模式

1. **启动后端服务**（在项目根目录）：
```bash
cd api
python -m uv run python app.py
```

2. **启动前端开发服务器**（在 web 目录）：
```bash
cd web
npx pnpm dev
```

3. **启动 Electron**（新终端，在 web 目录）：
```bash
npx pnpm dev:electron
```

### 构建生产版本

#### Windows
```bash
cd web
npx pnpm build:electron:win
```

输出：`web/dist-electron/CheersAI-1.12.0-x64.exe`

#### macOS
```bash
cd web
npx pnpm build:electron:mac
```

输出：`web/dist-electron/CheersAI-1.12.0-x64.dmg`

#### Linux
```bash
cd web
npx pnpm build:electron:linux
```

输出：`web/dist-electron/CheersAI-1.12.0-x64.AppImage`

## 📁 项目结构

```
web/
├── electron/                    # Electron 主进程文件
│   ├── main.js                 # 主进程入口
│   ├── preload.js              # 预加载脚本
│   ├── package.json            # Electron package.json
│   └── entitlements.mac.plist  # macOS 权限
├── electron-builder.json        # 打包配置
├── next.config.electron.ts      # Electron 专用配置
└── dist-electron/              # 打包输出目录
```

## 🔧 配置

### 修改窗口大小

编辑 `electron/main.js`：

```javascript
mainWindow = new BrowserWindow({
  width: 1280,      // 窗口宽度
  height: 800,      // 窗口高度
  minWidth: 1024,   // 最小宽度
  minHeight: 768,   // 最小高度
})
```

### 修改应用信息

编辑 `electron-builder.json`：

```json
{
  "appId": "com.cheersai.desktop",
  "productName": "CheersAI",
  "copyright": "Copyright © 2026 CheersAI"
}
```

## 📝 可用脚本

| 命令 | 说明 |
|------|------|
| `npx pnpm dev:electron` | 开发模式启动 Electron |
| `npx pnpm build:electron` | 构建当前平台 |
| `npx pnpm build:electron:win` | 构建 Windows 版本 |
| `npx pnpm build:electron:mac` | 构建 macOS 版本 |
| `npx pnpm build:electron:linux` | 构建 Linux 版本 |
| `npx pnpm start:electron` | 运行已构建的应用 |

## 🐛 常见问题

### 1. Electron 启动后白屏

**解决方案**：确保 Next.js 开发服务器运行在 `http://localhost:3500`

### 2. 构建失败

**解决方案**：
```bash
# 清理缓存
rm -rf node_modules .next out dist-electron
npx pnpm install
```

### 3. 图片无法显示

**原因**：Next.js 图片优化不支持静态导出

**已解决**：`next.config.electron.ts` 中已配置 `images.unoptimized: true`

## 📚 详细文档

查看完整文档：[ELECTRON_BUILD_GUIDE.md](../ELECTRON_BUILD_GUIDE.md)

## 🔐 安全说明

- ✅ 已禁用 `nodeIntegration`
- ✅ 已启用 `contextIsolation`
- ✅ 使用 `preload.js` 安全暴露 API

## 📦 打包输出

构建完成后，安装包位于 `dist-electron/` 目录：

- **Windows**: `.exe` 安装程序和便携版
- **macOS**: `.dmg` 磁盘映像和 `.zip` 压缩包
- **Linux**: `.AppImage` 和 `.deb` 包

## 🎯 下一步

1. 测试开发模式
2. 构建生产版本
3. 在目标平台测试安装包
4. 根据需要自定义配置

---

**需要帮助？** 查看 [ELECTRON_BUILD_GUIDE.md](../ELECTRON_BUILD_GUIDE.md)
