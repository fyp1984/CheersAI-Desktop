"""
智能体示例 - 文档助手

这个示例展示如何创建一个智能体，自动将对话内容导出为文档。
"""

# 智能体配置
AGENT_CONFIG = {
    "name": "文档助手",
    "description": "帮助用户整理和导出对话内容为各种文档格式",
    "model": "gpt-4",
    "tools": [
        "word_export",
        "pdf_export",
        "html_export",
        "markdown_export"
    ],
    "prompt": """
你是一个专业的文档助手。你的任务是：

1. 理解用户的需求
2. 整理和格式化内容
3. 选择合适的导出格式
4. 生成高质量的文档

## 能力

- 将对话内容导出为 Word 文档
- 生成 PDF 格式的报告
- 创建 HTML 网页
- 保存 Markdown 文件

## 工作流程

1. 询问用户需要导出什么内容
2. 确认导出格式（Word/PDF/HTML/Markdown）
3. 整理内容为结构化的 Markdown
4. 使用相应的工具导出文档
5. 确认导出成功

## 示例对话

用户: "帮我把今天的会议记录导出为 Word 文档"
助手: "好的，我来帮您整理会议记录并导出为 Word 文档。请提供会议的主要内容。"

用户: [提供会议内容]
助手: "我已经整理好了会议记录，现在为您导出为 Word 文档..."
[调用 word_export 工具]
助手: "✅ Word 文档已生成：会议记录_20260524_143022.docx"

## 注意事项

- 始终使用 Markdown 格式整理内容
- 为文档选择有意义的名称
- 确保内容结构清晰
- 根据内容类型选择合适的格式
    """,
    "opening_statement": "你好！我是文档助手，可以帮你将对话内容导出为 Word、PDF、HTML 或 Markdown 格式。需要什么帮助？",
    "suggested_questions": [
        "帮我导出今天的对话记录",
        "生成一份 PDF 格式的报告",
        "将这段内容保存为 Markdown 文件",
        "创建一个 HTML 网页"
    ]
}


# 使用示例
def example_usage():
    """示例：如何在代码中使用智能体"""
    
    # 1. 基本对话
    conversation = [
        {"role": "user", "content": "帮我把这段内容导出为 Word 文档：\n\n# 项目计划\n\n## 目标\n完成产品开发"},
        {"role": "assistant", "content": "好的，我来帮您导出为 Word 文档..."},
        # 智能体会自动调用 word_export 工具
    ]
    
    # 2. 批量导出
    documents = [
        {"title": "会议记录", "content": "# 会议记录\n\n..."},
        {"title": "项目报告", "content": "# 项目报告\n\n..."},
        {"title": "技术文档", "content": "# 技术文档\n\n..."},
    ]
    
    for doc in documents:
        # 智能体会为每个文档选择合适的格式
        pass
    
    # 3. 条件导出
    content_length = len(content)
    if content_length > 10000:
        # 长文档使用 PDF
        format_hint = "这是一份长文档，建议导出为 PDF 格式"
    else:
        # 短文档使用 Word
        format_hint = "这是一份短文档，建议导出为 Word 格式"


# 智能体提示词模板
PROMPT_TEMPLATES = {
    "meeting_notes": """
请将以下会议内容整理为标准的会议记录格式：

# {meeting_title}

## 会议信息
- 时间：{date}
- 地点：{location}
- 参与人员：{participants}

## 会议议题
{topics}

## 讨论内容
{discussion}

## 决议事项
{decisions}

## 待办事项
{action_items}

## 下次会议
{next_meeting}
    """,
    
    "technical_doc": """
请将以下技术内容整理为技术文档：

# {title}

## 概述
{overview}

## 技术架构
{architecture}

## 实现细节
{implementation}

## API 参考
{api_reference}

## 示例代码
{code_examples}

## 注意事项
{notes}
    """,
    
    "report": """
请将以下内容整理为报告格式：

# {report_title}

## 执行摘要
{executive_summary}

## 背景
{background}

## 数据分析
{data_analysis}

## 结论
{conclusion}

## 建议
{recommendations}

## 附录
{appendix}
    """
}


# 工具调用示例
def tool_call_examples():
    """工具调用示例"""
    
    # 示例 1: 导出会议记录为 Word
    word_export_call = {
        "tool": "word_export",
        "parameters": {
            "markdown_content": """
# 产品规划会议

## 会议信息
- 时间：2026-05-24 14:00
- 参与人员：张三、李四、王五

## 讨论内容
1. 产品功能优先级
2. 开发时间表
3. 资源分配

## 决议事项
- 优先开发核心功能
- 预计 6 月底完成
            """,
            "document_name": "产品规划会议_20260524"
        }
    }
    
    # 示例 2: 生成 PDF 报告
    pdf_export_call = {
        "tool": "pdf_export",
        "parameters": {
            "markdown_content": """
# 月度运营报告

## 数据概览
- 用户增长：+15%
- 活跃度：85%
- 收入：+20%

## 详细分析
[详细内容...]
            """,
            "document_name": "月度运营报告_2026年5月"
        }
    }
    
    # 示例 3: 创建 HTML 文档
    html_export_call = {
        "tool": "html_export",
        "parameters": {
            "markdown_content": """
# 产品介绍

## 功能特性
- 功能 1
- 功能 2
- 功能 3

## 使用指南
[使用说明...]
            """,
            "document_name": "产品介绍",
            "include_css": True
        }
    }
    
    return [word_export_call, pdf_export_call, html_export_call]


if __name__ == "__main__":
    print("智能体配置示例")
    print("=" * 50)
    print(f"名称: {AGENT_CONFIG['name']}")
    print(f"描述: {AGENT_CONFIG['description']}")
    print(f"工具: {', '.join(AGENT_CONFIG['tools'])}")
    print("\n提示词模板:")
    for name, template in PROMPT_TEMPLATES.items():
        print(f"\n{name}:")
        print(template[:200] + "...")
