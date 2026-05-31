"""
PDF转换工具
"""
import markdown
from weasyprint import HTML, CSS
from weasyprint.text.fonts import FontConfiguration


def markdown_to_pdf(markdown_content: str, output_path: str) -> str:
    """
    将Markdown内容转换为PDF文档
    
    Args:
        markdown_content: Markdown格式的文本内容
        output_path: 输出文件路径
        
    Returns:
        输出文件的路径
    """
    # 将Markdown转换为HTML
    html_content = markdown.markdown(
        markdown_content,
        extensions=['extra', 'codehilite', 'tables', 'fenced_code', 'toc']
    )
    
    # 添加CSS样式
    styled_html = _wrap_html_with_style(html_content)
    
    # 配置字体
    font_config = FontConfiguration()
    
    # 生成PDF
    HTML(string=styled_html).write_pdf(
        output_path,
        font_config=font_config
    )
    
    return output_path


def _wrap_html_with_style(html_content: str) -> str:
    """为HTML内容添加样式"""
    css_style = """
    <style>
        @page {
            size: A4;
            margin: 2cm;
        }
        
        body {
            font-family: 'Arial', 'Helvetica', sans-serif;
            font-size: 11pt;
            line-height: 1.6;
            color: #333;
            max-width: 800px;
            margin: 0 auto;
        }
        
        h1, h2, h3, h4, h5, h6 {
            color: #2c3e50;
            margin-top: 1.5em;
            margin-bottom: 0.5em;
            font-weight: bold;
        }
        
        h1 {
            font-size: 24pt;
            border-bottom: 2px solid #3498db;
            padding-bottom: 0.3em;
        }
        
        h2 {
            font-size: 20pt;
            border-bottom: 1px solid #bdc3c7;
            padding-bottom: 0.3em;
        }
        
        h3 {
            font-size: 16pt;
        }
        
        h4 {
            font-size: 14pt;
        }
        
        p {
            margin: 0.8em 0;
            text-align: justify;
        }
        
        code {
            background-color: #f4f4f4;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: 'Courier New', monospace;
            font-size: 9pt;
            color: #c7254e;
        }
        
        pre {
            background-color: #f8f8f8;
            border: 1px solid #ddd;
            border-radius: 4px;
            padding: 12px;
            overflow-x: auto;
            margin: 1em 0;
        }
        
        pre code {
            background-color: transparent;
            padding: 0;
            color: #333;
        }
        
        blockquote {
            border-left: 4px solid #3498db;
            padding-left: 1em;
            margin: 1em 0;
            color: #666;
            font-style: italic;
            background-color: #f9f9f9;
            padding: 0.5em 1em;
        }
        
        ul, ol {
            margin: 0.8em 0;
            padding-left: 2em;
        }
        
        li {
            margin: 0.3em 0;
        }
        
        table {
            border-collapse: collapse;
            width: 100%;
            margin: 1em 0;
        }
        
        th, td {
            border: 1px solid #ddd;
            padding: 8px 12px;
            text-align: left;
        }
        
        th {
            background-color: #3498db;
            color: white;
            font-weight: bold;
        }
        
        tr:nth-child(even) {
            background-color: #f9f9f9;
        }
        
        a {
            color: #3498db;
            text-decoration: none;
        }
        
        a:hover {
            text-decoration: underline;
        }
        
        hr {
            border: none;
            border-top: 1px solid #ddd;
            margin: 2em 0;
        }
        
        img {
            max-width: 100%;
            height: auto;
            display: block;
            margin: 1em auto;
        }
    </style>
    """
    
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        {css_style}
    </head>
    <body>
        {html_content}
    </body>
    </html>
    """
