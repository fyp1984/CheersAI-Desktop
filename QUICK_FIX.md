# 快速修复：Gitea 文件选择器问题

## 问题
文件选择器显示"无法从 Gitea 加载文件列表"

## 根本原因
前端代码已更新，但浏览器可能缓存了旧版本

## 立即解决方案

### 方法 1: 硬刷新浏览器（最简单）

1. 在浏览器中按 **Ctrl + Shift + R**（Windows）
2. 或按 **Ctrl + F5**
3. 这会清除缓存并重新加载页面

### 方法 2: 清除浏览器缓存

1. 按 **F12** 打开开发者工具
2. 右键点击刷新按钮
3. 选择"清空缓存并硬性重新加载"

### 方法 3: 手动测试 API（验证后端工作正常）

在浏览器控制台（F12 → Console）中运行：

```javascript
// 测试 Gitea API
async function testGiteaAPI() {
  const csrfToken = document.cookie.match(/csrf_token=([^;]+)/)?.[1] || '';
  console.log('CSRF Token:', csrfToken ? '✓ Found' : '✗ Not found');
  
  const url = 'http://localhost:5001/console/api/gitea/files?path=';
  console.log('Testing:', url);
  
  try {
    const res = await fetch(url, {
      credentials: 'include',
      headers: { 'X-CSRF-Token': csrfToken }
    });
    
    console.log('Status:', res.status);
    
    if (res.ok) {
      const data = await res.json();
      console.log('✓ Success! Files:', data);
      return data;
    } else {
      const error = await res.text();
      console.error('✗ Error:', error);
      return null;
    }
  } catch (err) {
    console.error('✗ Exception:', err);
    return null;
  }
}

// 运行测试
testGiteaAPI();
```

## 预期结果

### 成功的情况
```
CSRF Token: ✓ Found
Testing: http://localhost:5001/console/api/gitea/files?path=
Status: 200
✓ Success! Files: {files: [...]}
```

### 失败的情况

**401 错误**：
```
Status: 401
✗ Error: {"code":"unauthorized",...}
```
→ 解决：重新登录

**500 错误**：
```
Status: 500
✗ Error: Failed to list files...
```
→ 解决：检查 Gitea 配置

**CSRF Token 缺失**：
```
CSRF Token: ✗ Not found
```
→ 解决：重新登录

## 如果还是不行

告诉我以下信息：

1. **浏览器控制台的错误信息**（F12 → Console 标签）
2. **Network 标签中的请求详情**（F12 → Network → 找到 gitea/files 请求）
3. **测试脚本的输出结果**

## 验证 Gitea 配置

确认后端配置正确：

```bash
cd e:\CheersAI-Desktop
python test_gitea_direct.py
```

应该显示：
```
✓ Successfully connected!
Found X items in repository
```

## 最后的检查清单

- [ ] 后端服务正在运行（http://localhost:5001）
- [ ] 前端服务正在运行（http://localhost:3000）
- [ ] Gitea 服务正在运行（http://localhost:8080）
- [ ] 已在 Gitea 中创建 `root/cheersAI` 仓库
- [ ] `.env` 文件包含正确的 Gitea 配置
- [ ] 已硬刷新浏览器（Ctrl+Shift+R）
- [ ] 已重新登录 CheersAI

完成这些步骤后，文件选择器应该能正常工作！
