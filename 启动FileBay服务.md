# FileBay 服务启动说明

## 前提条件
```bash
pip install pyopenssl
```

## 启动步骤

### 1. 启动 FileBay 代理（必须）
```bash
cd docker
python filebay_proxy.py
```
保持此终端运行

### 2. 启动 API 服务器
```bash
cd api
flask run --host=0.0.0.0 --port=5001 --debug
```
或
```bash
python app.py
```

### 3. 启动前端（如需要）
```bash
cd web
npm run dev
```

## 验证

### 测试代理
```bash
curl http://localhost:39091/api/v1/repos/beta_20260415162204_example_com_9838ca/workspace/contents/ -H "Authorization: token YOUR_TOKEN"
```

### 测试 API
```bash
curl http://localhost:5001/console/api/gitea/config
```

## 注意事项

1. FileBay 代理必须先启动
2. API 服务器会自动使用 OpenSSL 后端
3. 如果遇到 SSL 错误，检查 pyOpenSSL 是否已安装
4. 代理日志会显示所有请求
