# 🚀 CheersAI Tauri 快速启动

## ✅ 你已完成
- ✅ 安装了 Rust
- ✅ 所有配置就绪

## 🔄 重要：重新打开终端

**关闭当前终端，打开新的 PowerShell**

验证 Rust：
```powershell
rustc --version
cargo --version
```

## 🎯 启动开发模式

**终端 1**：
```powershell
cd E:\dify-main\dify-main\web
npx pnpm dev
```

**终端 2**：
```powershell
cd E:\dify-main\dify-main\web
npx pnpm dev:tauri
```

## ⏱️ 首次运行

首次运行需要 **5-10 分钟**（下载和编译 Rust 依赖）

后续运行只需 **10-30 秒**

## 📦 构建安装包

```powershell
cd E:\dify-main\dify-main\web
npx pnpm build
npx pnpm build:tauri
```

安装包位置：
```
web\src-tauri\target\release\bundle\nsis\CheersAI_1.12.0_x64-setup.exe
```

## 🐛 常见问题

**cargo 未找到**: 重新打开终端

**link.exe 未找到**: 安装 Visual Studio Build Tools
- https://visualstudio.microsoft.com/downloads/
- 选择 "Desktop development with C++"

**无法连接**: 确保前端服务器在运行 (`npx pnpm dev`)

## 📚 详细文档

- [TAURI_SETUP.md](./TAURI_SETUP.md) - 完整设置
- [TAURI_BUILD_GUIDE.md](./TAURI_BUILD_GUIDE.md) - 构建指南
- [CHEERSAI_DESKTOP_README.md](./CHEERSAI_DESKTOP_README.md) - 总览

---

**准备好了？重新打开终端，然后运行 `npx pnpm dev:tauri`！** 🚀
