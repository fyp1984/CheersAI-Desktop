# 🚀 构建 CheersAI Electron 应用

## 📍 EXE 文件位置

构建完成后，exe 文件会在以下位置：

```
web/dist-electron/
├── CheersAI-1.12.0-x64.exe          # 64位安装程序
├── CheersAI-1.12.0-arm64.exe        # ARM64安装程序
└── CheersAI-1.12.0-portable.exe     # 便携版（无需安装）
```

---

## 🔨 构建步骤

### 方法 1：完整构建（推荐）

```bash
# 1. 进入 web 目录
cd web

# 2. 构建 Windows 版本
npx pnpm build:electron:win
```

**预计时间**：首次构建约 5-10 分钟

### 方法 2：分步构建

```bash
# 1. 进入 web 目录
cd web

# 2. 先构建 Next.js（使用 Electron 配置）
# 临时重命名配置
mv next.config.ts next.config.ts.backup
cp next.config.electron.ts next.config.ts

# 3. 构建 Next.js
npx pnpm next build

# 4. 恢复配置
mv next.config.ts.backup next.config.ts

# 5. 打包 Electron
npx electron-builder --win
```

---

## ⚡ 快速构建命令

```bash
cd web && npx pnpm build:electron:win
```

---

## 📦 构建输出

构建成功后，你会看到：

```
✔ Building...
✔ Packaging...
✔ Building NSIS installer...

Output:
  • web\dist-electron\CheersAI-1.12.0-x64.exe
  • web\dist-electron\CheersAI-1.12.0-arm64.exe
  • web\dist-electron\CheersAI-1.12.0-portable.exe
```

---

## 🎯 安装包说明

### CheersAI-1.12.0-x64.exe
- **类型**：NSIS 安装程序
- **架构**：64位 (x64)
- **大小**：约 150-200 MB
- **用途**：标准安装，会在开始菜单创建快捷方式

### CheersAI-1.12.0-arm64.exe
- **类型**：NSIS 安装程序
- **架构**：ARM64
- **用途**：用于 ARM64 Windows 设备（如 Surface Pro X）

### CheersAI-1.12.0-portable.exe
- **类型**：便携版
- **架构**：64位 (x64)
- **用途**：无需安装，直接运行
- **优点**：可放在 U 盘中随身携带

---

## ⚠️ 常见问题

### 1. 构建失败：找不到 Python

**错误信息**：
```
gyp ERR! find Python
```

**解决方案**：
```bash
# 安装 Python（推荐 Python 3.x）
# 或安装 Windows Build Tools
npm install --global windows-build-tools
```

### 2. 构建失败：缺少 Visual Studio

**错误信息**：
```
error MSB8036: The Windows SDK version was not found
```

**解决方案**：
安装 Visual Studio Build Tools：
```bash
npm install --global windows-build-tools
```

或下载安装：https://visualstudio.microsoft.com/downloads/

### 3. 构建很慢

**原因**：首次构建需要下载依赖

**解决方案**：
- 耐心等待（首次约 5-10 分钟）
- 后续构建会快很多（约 2-3 分钟）

### 4. 内存不足

**错误信息**：
```
FATAL ERROR: Ineffective mark-compacts near heap limit
```

**解决方案**：
```bash
# 增加 Node.js 内存限制
set NODE_OPTIONS=--max-old-space-size=4096
npx pnpm build:electron:win
```

---

## 🧪 测试安装包

### 测试安装程序
```bash
# 运行安装程序
.\web\dist-electron\CheersAI-1.12.0-x64.exe
```

### 测试便携版
```bash
# 直接运行
.\web\dist-electron\CheersAI-1.12.0-portable.exe
```

---

## 📊 构建进度说明

构建过程会显示以下阶段：

1. **Building Next.js** - 构建前端（约 2-3 分钟）
   ```
   ▲ Next.js 16.1.5
   - Creating an optimized production build...
   ```

2. **Packaging** - 打包应用（约 1-2 分钟）
   ```
   • electron-builder version=25.1.8
   • loaded configuration file=electron-builder.json
   ```

3. **Building NSIS installer** - 创建安装程序（约 1-2 分钟）
   ```
   • building target=nsis file=CheersAI-1.12.0-x64.exe
   ```

4. **Done** - 完成
   ```
   ✔ Building complete!
   ```

---

## 🎉 构建成功后

1. **找到 exe 文件**
   ```
   web\dist-electron\CheersAI-1.12.0-x64.exe
   ```

2. **测试运行**
   - 双击运行安装程序
   - 或运行便携版

3. **分发**
   - 可以直接分享 exe 文件
   - 用户双击即可安装/运行

---

## 💡 提示

### 加快后续构建
```bash
# 只重新打包（不重新构建 Next.js）
cd web
npx electron-builder --win --dir
```

### 清理构建缓存
```bash
cd web
rm -rf .next out dist-electron
npx pnpm build:electron:win
```

### 查看详细日志
```bash
cd web
set DEBUG=electron-builder
npx pnpm build:electron:win
```

---

## 📞 需要帮助？

如果构建遇到问题：

1. 查看本文档的"常见问题"部分
2. 查看 `ELECTRON_BUILD_GUIDE.md` 获取详细说明
3. 检查终端的错误信息
4. 确保已安装所有依赖：
   ```bash
   cd web
   npx pnpm install
   ```

---

**准备好了吗？运行这个命令开始构建：**

```bash
cd web && npx pnpm build:electron:win
```

构建完成后，exe 文件就在 `web\dist-electron\` 目录中！🎉
