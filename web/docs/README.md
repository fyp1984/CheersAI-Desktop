# CheersAI Desktop 文档索引

本目录只保留仍有持续维护价值的设计、配置和稳定说明文档。临时修复记录、测试通知和 PR 过程文档已从仓库清理。

## 推荐入口

### SSO 设计与实现
- [角色权限设计方案](./sso/角色权限设计方案.md)
- [SSO角色权限设计](./sso/SSO角色权限设计.md)
- [快速实现说明](./sso/快速实现说明.md)
- [仅SSO登录模式](./sso/仅SSO登录模式.md)
- [简洁登录界面设计](./sso/简洁登录界面设计.md)
- [sso.md](./sso.md)

### SSO 配置与接入
- [本地SSO配置和测试](./sso/本地SSO配置和测试.md)
- [Casdoor角色配置指南](./sso/Casdoor角色配置指南.md)
- [获取Client-Secret说明](./获取Client-Secret说明.md)
- [快速配置SSO角色](./sso/快速配置SSO角色.md)

### 产品需求
- [PRD 索引](./prd/README.md)
- [CheersAI-Desktop菜单优化与用户体验升级PRD_v1.2](./prd/CheersAI-Desktop菜单优化与用户体验升级PRD_v1.2.md)

### 其他
- [lint.md](./lint.md)

## 启动与开发

- Web 侧启动说明以 [web/README.md](../README.md) 为准
- 仓库级部署与环境说明以根目录 `docs/` 为准

## 维护规则

- 只保留设计、配置、接入和长期有效的实现说明
- 删除一次性修复记录、测试清单、进度汇报和 PR 操作文档
- 同主题文档优先收敛到 `sso/README.md` 或本文件，避免重复副本
