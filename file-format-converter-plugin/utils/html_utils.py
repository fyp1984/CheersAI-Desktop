"""
HTML转换工具
"""
import markdown


def markdown_to_html(markdown_content: str, output_path: str, include_css: bool = True) -> str:
    """
    将Markdown内容转换为HTML文档
    
    Args:
        markdown_content: Markdown格式的文本内容
        output_path: 输出文件路径
        include_css: 是否包含CSS样式
        
    Returns:
        输出文件的路径
    """
    # 将Markdown转换为HTML
    html_body = markdown.markdown(
        markdown_content,
        extensions=['extra', 'codehilite', 'tables', 'fenced_code', 'toc']
    )
    
    # 构建完整的HTML文档
    if include_css:
        html_content = _wrap_html_with_style(html_body)
    else:
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Document</title>
</head>
<body>
    {html_body}
</body>
</html>
"""
    
    # 保存文件
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    return output_path


def _wrap_html_with_style(html_body: str) -> str:
    """为HTML内容添加样式"""
    return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Document</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Helvetica', 'Arial', sans-serif;
            font-size: 16px;
            line-height: 1.6;
            color: #333;
            max-width: 900px;
            margin: 0 auto;
            padding: 20px;
            background-color: #fff;
        }}
        
        h1, h2, h3, h4, h5, h6 {{
            color: #2c3e50;
            margin-top: 24px;
            margin-bottom: 16px;
            font-weight: 600;
            line-height: 1.25;
        }}
        
        h1 {{
            font-size: 2em;
            border-bottom: 2px solid #3498db;
            padding-bottom: 0.3em;
        }}
        
        h2 {{
            font-size: 1.5em;
            border-bottom: 1px solid #eaecef;
            padding-bottom: 0.3em;
        }}
        
        h3 {{
            font-size: 1.25em;
        }}
        
        h4 {{
            font-size: 1em;
        }}
        
        p {{
            margin-top: 0;
            margin-bottom: 16px;
        }}
        
        code {{
            background-color: #f6f8fa;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: 'SFMono-Regular', 'Consolas', 'Liberation Mono', 'Menlo', monospace;
            font-size: 85%;
            color: #e83e8c;
        }}
        
        pre {{
            background-color: #f6f8fa;
            border-radius: 6px;
            padding: 16px;
            overflow: auto;
            line-height: 1.45;
            margin-bottom: 16px;
        }}
        
        pre code {{
            background-color: transparent;
            padding: 0;
            color: #24292e;
            font-size: 100%;
        }}
        
        blockquote {{
            border-left: 4px solid #3498db;
            padding: 0 15px;
            margin: 0 0 16px 0;
            color: #6a737d;
        }}
        
        ul, ol {{
            padding-left: 2em;
            margin-top: 0;
            margin-bottom: 16px;
        }}
        
        li {{
            margin-bottom: 0.25em;
        }}
        
        table {{
            border-collapse: collapse;
            width: 100%;
            margin-bottom: 16px;
            display: block;
            overflow: auto;
        }}
        
        th, td {{
            border: 1px solid #dfe2e5;
            padding: 6px 13px;
        }}
        
        th {{
            background-color: #f6f8fa;
            font-weight: 600;
        }}
        
        tr:nth-child(2n) {{
            background-color: #f6f8fa;
        }}
        
        a {{
            color: #0366d6;
            text-decoration: none;
        }}
        
        a:hover {{
            text-decoration: underline;
        }}
        
        hr {{
            border: 0;
            border-top: 1px solid #eaecef;
            margin: 24px 0;
        }}
        
        img {{
            max-width: 100%;
            height: auto;
            display: block;
            margin: 16px auto;
        }}
        
        .codehilite {{
            background-color: #f6f8fa;
            border-radius: 6px;
            padding: 16px;
            overflow: auto;
            margin-bottom: 16px;
        }}
    </style>
</head>
<body>
    {html_body}
</body>
</html>
"""
