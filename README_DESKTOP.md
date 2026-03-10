# CheersAI 桌面应用

> 📚 **完整文档**：[docs/desktop/](docs/desktop/)

## 🚀 快速开始

### 开发模式
```bash
.\start-tauri-dev.ps1
```

### 生产打包
```bash
cd web
pnpm run build:tauri:full:debug  # Debug 版本
pnpm run build:tauri:full        # Release 版本
```

### Web 部署
```bash
.\start-database.ps1
.\start-backend.ps1
cd web && pnpm dev
```

## 📚 文档导航

| 文档 | 说明 |
|------|------|
| [快速开始](docs/desktop/快速开始.md) | 三种使用方式 |
| [打包完成状态](docs/desktop/打包完成状态.md) | 完成情况总结 |
| [生产打包指南](docs/desktop/TAURI_PRODUCTION_BUILD_GUIDE.md) | 完整打包流程 |
| [设置指南](docs/desktop/TAURI_SETUP.md) | 环境配置 |
| [完整索引](docs/desktop/README.md) | 所有文档 |

## ✅ 已完成功能

- ✅ Tauri 开发环境
- ✅ Rust 代码编译
- ✅ 嵌入式 Next.js 服务器
- ✅ 完整打包脚本
- ✅ 生产打包功能
- ✅ 完整文档

## 📦 打包产物

```
web/src-tauri/target/
├── debug/
│   └── app.exe          # Debug 可执行文件
└── release/
    ├── app.exe          # Release 可执行文件
    └── bundle/
        ├── msi/         # Windows 安装包
        └── nsis/        # Windows 安装程序
```

## ⚠️ 注意事项

- 用户需要安装 Node.js（或在安装包中包含）
- 首次启动需要 5-10 秒
- 打包时间约 5-10 分钟

## 🎯 推荐阅读

1. [快速开始](docs/desktop/快速开始.md) - 立即开始使用
2. [生产打包指南](docs/desktop/TAURI_PRODUCTION_BUILD_GUIDE.md) - 如何打包
3. [完整文档索引](docs/desktop/README.md) - 所有文档

---

**桌面应用打包已完成，可以立即使用！** 🎉
