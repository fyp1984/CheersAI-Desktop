"""
HTML文档导出工具
"""
import os
import tempfile
from collections.abc import Generator
from datetime import datetime
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage


class HtmlExportTool(Tool):
    """HTML文档导出工具"""
    
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage]:
        """
        执行工具调用
        
        Args:
            tool_parameters: 工具参数
                - markdown_content: Markdown内容
                - document_name: 文档名称（可选）
                - include_css: 是否包含CSS样式（可选）
                
        Yields:
            ToolInvokeMessage: 工具调用消息
        """
        # 获取参数
        markdown_content = tool_parameters.get('markdown_content', '')
        document_name = tool_parameters.get('document_name', 'document')
        include_css = tool_parameters.get('include_css', True)
        
        if not markdown_content:
            yield self.create_text_message("错误：Markdown内容不能为空")
            return
        
        # 清理文件名
        document_name = self._sanitize_filename(document_name)
        
        # 生成临时文件路径
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{document_name}_{timestamp}.html"
        temp_dir = tempfile.gettempdir()
        output_path = os.path.join(temp_dir, filename)
        
        try:
            # 转换为HTML文档
            import markdown
            
            html_content = markdown.markdown(markdown_content, extensions=['extra', 'codehilite'])
            
            # 构建完整HTML
            if include_css:
                full_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{document_name}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            line-height: 1.6;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            color: #333;
        }}
        h1, h2, h3, h4, h5, h6 {{
            margin-top: 24px;
            margin-bottom: 16px;
            font-weight: 600;
            line-height: 1.25;
        }}
        h1 {{ font-size: 2em; border-bottom: 2px solid #eee; padding-bottom: 10px; }}
        h2 {{ font-size: 1.5em; border-bottom: 1px solid #eee; padding-bottom: 8px; }}
        code {{
            background: #f6f8fa;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: 'Courier New', monospace;
            font-size: 0.9em;
        }}
        pre {{
            background: #f6f8fa;
            padding: 16px;
            border-radius: 6px;
            overflow-x: auto;
        }}
        pre code {{
            background: none;
            padding: 0;
        }}
        blockquote {{
            border-left: 4px solid #ddd;
            padding-left: 16px;
            color: #666;
            margin: 0;
        }}
        a {{ color: #0366d6; text-decoration: none; }}
        a:hover {{ text-decoration: underline; }}
        ul, ol {{ padding-left: 2em; }}
        table {{
            border-collapse: collapse;
            width: 100%;
            margin: 16px 0;
        }}
        th, td {{
            border: 1px solid #ddd;
            padding: 8px 12px;
            text-align: left;
        }}
        th {{ background: #f6f8fa; font-weight: 600; }}
    </style>
</head>
<body>
{html_content}
</body>
</html>"""
            else:
                full_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>{document_name}</title>
</head>
<body>
{html_content}
</body>
</html>"""
            
            # 保存文件
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(full_html)
            
            # 读取文件内容
            with open(output_path, 'rb') as f:
                file_content = f.read()
            
            # 返回文件
            yield self.create_blob_message(
                blob=file_content,
                meta={
                    'mime_type': 'text/html',
                    'filename': filename
                }
            )
            yield self.create_text_message(f"✅ HTML文档已生成：{filename}")
            
        except Exception as e:
            yield self.create_text_message(f"❌ 生成HTML文档失败：{str(e)}")
        
        finally:
            # 清理临时文件
            if os.path.exists(output_path):
                try:
                    os.remove(output_path)
                except:
                    pass
    
    def _sanitize_filename(self, filename: str) -> str:
        """清理文件名，移除非法字符"""
        # 移除文件扩展名
        if filename.endswith('.html'):
            filename = filename[:-5]
        
        # 移除非法字符
        illegal_chars = '<>:"/\\|?*'
        for char in illegal_chars:
            filename = filename.replace(char, '_')
        
        # 限制长度
        if len(filename) > 100:
            filename = filename[:100]
        
        return filename or 'document'
