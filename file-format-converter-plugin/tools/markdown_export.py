"""
Markdown文档导出工具
"""
import os
import tempfile
from collections.abc import Generator
from datetime import datetime
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage


class MarkdownExportTool(Tool):
    """Markdown文档导出工具"""
    
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage]:
        """
        执行工具调用
        
        Args:
            tool_parameters: 工具参数
                - markdown_content: Markdown内容
                - document_name: 文档名称（可选）
                
        Yields:
            ToolInvokeMessage: 工具调用消息
        """
        # 获取参数
        markdown_content = tool_parameters.get('markdown_content', '')
        document_name = tool_parameters.get('document_name', 'document')
        
        if not markdown_content:
            yield self.create_text_message("错误：Markdown内容不能为空")
            return
        
        # 清理文件名
        document_name = self._sanitize_filename(document_name)
        
        # 生成临时文件路径
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{document_name}_{timestamp}.md"
        temp_dir = tempfile.gettempdir()
        output_path = os.path.join(temp_dir, filename)
        
        try:
            # 保存Markdown文件
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(markdown_content)
            
            # 读取文件内容
            with open(output_path, 'rb') as f:
                file_content = f.read()
            
            # 返回文件
            yield self.create_blob_message(
                blob=file_content,
                meta={
                    'mime_type': 'text/markdown',
                    'filename': filename
                }
            )
            yield self.create_text_message(f"✅ Markdown文档已生成：{filename}")
            
        except Exception as e:
            yield self.create_text_message(f"❌ 生成Markdown文档失败：{str(e)}")
        
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
        if filename.endswith('.md'):
            filename = filename[:-3]
        
        # 移除非法字符
        illegal_chars = '<>:"/\\|?*'
        for char in illegal_chars:
            filename = filename.replace(char, '_')
        
        # 限制长度
        if len(filename) > 100:
            filename = filename[:100]
        
        return filename or 'document'
