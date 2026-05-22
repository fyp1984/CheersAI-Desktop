# FileBay API 使用说明与 Python 示例

本文说明如何通过 FileBay/Gitea Contents API 写入文件，并给出 Python 示例。所有上传动作都应由用户主动触发，只上传用户确认过或已脱敏的内容。

## 基础配置

需要准备以下信息：

| 配置项 | 说明 |
| --- | --- |
| `FILEBAY_URL` | FileBay 服务地址，例如 `https://uat-filebay.cheersai.cloud` |
| `FILEBAY_TOKEN` | FileBay/Gitea API Token，需要仓库读写权限 |
| `FILEBAY_OWNER` | 仓库所有者或组织名 |
| `FILEBAY_REPO` | 仓库名 |
| `FILEBAY_BRANCH` | 分支名，默认 `main` |

认证头：

```http
Authorization: token <FILEBAY_TOKEN>
Accept: application/json
Content-Type: application/json
```

## 常用接口

FileBay 当前按 Gitea Contents API 方式读写文件：

| 操作 | 方法与路径 | 说明 |
| --- | --- | --- |
| 获取文件或目录 | `GET /api/v1/repos/{owner}/{repo}/contents/{path}?ref={branch}` | 读取目录列表、文件元信息和 `sha` |
| 新建文件 | `POST /api/v1/repos/{owner}/{repo}/contents/{path}` | `content` 字段传 Base64 |
| 更新文件 | `PUT /api/v1/repos/{owner}/{repo}/contents/{path}` | 需要带现有文件的 `sha` |
| 读取原始文件 | `GET /{owner}/{repo}/raw/branch/{branch}/{path}` | 下载原始内容 |

写入请求体示例：

```json
{
  "message": "Write file",
  "content": "IyBIZWxsbyBGaWxlQmF5Cg==",
  "branch": "main",
  "sha": "existing-file-sha-when-updating"
}
```

## Markdown 写入规则

Markdown 文件在业务侧按普通字符串处理：

1. 调用方传入 Python `str`。
2. 客户端用 UTF-8 编码成字节。
3. 发送 FileBay Contents API 前再转换成 Base64。

示例：

```python
from examples.filebay_api_examples import client_from_env

client = client_from_env()

markdown = """# 项目日报

- 今日完成 FileBay API 文档
- Markdown 以字符串方式写入
"""

client.write_markdown_string("reports/daily.md", markdown)
```

## 图片写入规则

图片按二进制流方式读取，适合 PNG、JPG、WebP 等文件：

1. 调用方打开 `rb` 二进制流。
2. 客户端按块读取，避免一次性把大图片读入业务逻辑。
3. 发送 FileBay Contents API 前按块转换并拼接 Base64。

示例：

```python
from examples.filebay_api_examples import client_from_env

client = client_from_env()

with open("chart.png", "rb") as image_stream:
    client.write_image_stream("images/chart.png", image_stream)
```

完整示例文件见：[docs/examples/filebay_api_examples.py](examples/filebay_api_examples.py)。

## Markdown 转换插件

sandbox 依赖文件已加入以下转换插件：

| 目标格式 | 依赖 | 说明 |
| --- | --- | --- |
| Markdown 解析 | `markdown` | Markdown 转 HTML 或中间结构 |
| DOCX | `python-docx` | 生成 Word 文档 |
| CSV | Python 标准库 `csv` | 生成表格文本文件 |
| XLSX | `openpyxl` | 生成 Excel 工作簿 |
| PDF | `reportlab`、`pypdfium2` | 生成 PDF、读取或渲染 PDF |
| PPTX | `python-pptx` | 生成 PowerPoint 文件 |
| 图片处理 | `Pillow` | 在 PDF/PPTX 中插入或处理图片 |
| HTML 清洗/转换 | `beautifulsoup4`、`lxml`、`markdownify` | HTML 与 Markdown 互转辅助 |

依赖位置：

```text
docker/volumes/sandbox/dependencies/python-requirements.txt
```

容器重新安装依赖后，插件即可在 sandbox Python 环境中使用。
