#!/usr/bin/env python3
"""
生成插件图标
创建一个简单的文件转换图标
"""
from PIL import Image, ImageDraw, ImageFont
import os

def create_icon(size=256):
    """创建插件图标"""
    # 创建画布
    img = Image.new('RGB', (size, size), color='#3498db')
    draw = ImageDraw.Draw(img)
    
    # 绘制背景渐变效果（简化版）
    for i in range(size):
        color = int(52 + (100 - 52) * i / size)
        draw.line([(0, i), (size, i)], fill=(color, 152, 219))
    
    # 绘制文档图标
    margin = size // 8
    doc_width = size - 2 * margin
    doc_height = int(doc_width * 1.3)
    doc_x = margin
    doc_y = (size - doc_height) // 2
    
    # 文档主体（白色矩形）
    draw.rectangle(
        [doc_x, doc_y, doc_x + doc_width, doc_y + doc_height],
        fill='white',
        outline='#2c3e50',
        width=3
    )
    
    # 文档折角
    fold_size = size // 6
    fold_points = [
        (doc_x + doc_width - fold_size, doc_y),
        (doc_x + doc_width, doc_y + fold_size),
        (doc_x + doc_width, doc_y)
    ]
    draw.polygon(fold_points, fill='#ecf0f1', outline='#2c3e50')
    draw.line(
        [(doc_x + doc_width - fold_size, doc_y),
         (doc_x + doc_width - fold_size, doc_y + fold_size),
         (doc_x + doc_width, doc_y + fold_size)],
        fill='#2c3e50',
        width=2
    )
    
    # 绘制文档内容线条
    line_margin = margin + size // 12
    line_width = doc_width - 2 * (size // 12)
    line_y_start = doc_y + size // 8
    line_spacing = size // 16
    
    for i in range(5):
        y = line_y_start + i * line_spacing
        if y < doc_y + doc_height - size // 8:
            draw.line(
                [(doc_x + size // 12, y),
                 (doc_x + size // 12 + line_width, y)],
                fill='#95a5a6',
                width=2
            )
    
    # 绘制转换箭头
    arrow_y = doc_y + doc_height + size // 12
    arrow_size = size // 8
    
    # 向右的箭头
    arrow_points = [
        (size // 2 - arrow_size, arrow_y),
        (size // 2 + arrow_size, arrow_y),
        (size // 2 + arrow_size, arrow_y - arrow_size // 2),
        (size // 2 + arrow_size * 1.5, arrow_y + arrow_size // 2),
        (size // 2 + arrow_size, arrow_y + arrow_size * 1.5),
        (size // 2 + arrow_size, arrow_y + arrow_size),
        (size // 2 - arrow_size, arrow_y + arrow_size)
    ]
    draw.polygon(arrow_points, fill='#f39c12', outline='#e67e22')
    
    # 添加文字标识
    try:
        # 尝试使用系统字体
        font_size = size // 12
        try:
            font = ImageFont.truetype("arial.ttf", font_size)
        except:
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size)
            except:
                font = ImageFont.load_default()
        
        # 绘制格式标识
        formats = ["DOC", "PDF", "HTML", "MD"]
        format_y = size - margin - size // 16
        format_spacing = doc_width // len(formats)
        
        for i, fmt in enumerate(formats):
            x = doc_x + i * format_spacing + format_spacing // 2
            # 获取文本边界框
            bbox = draw.textbbox((x, format_y), fmt, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            draw.text(
                (x - text_width // 2, format_y - text_height // 2),
                fmt,
                fill='white',
                font=font
            )
    except Exception as e:
        print(f"警告: 无法添加文字 - {e}")
    
    return img


def main():
    """主函数"""
    print("生成插件图标...")
    
    # 生成不同尺寸的图标
    sizes = [256, 128, 64, 32]
    
    for size in sizes:
        img = create_icon(size)
        filename = f"icon_{size}.png" if size != 256 else "icon.png"
        img.save(filename)
        print(f"✅ 生成 {filename} ({size}x{size})")
    
    print("\n✅ 图标生成完成！")
    print("主图标: icon.png (256x256)")


if __name__ == "__main__":
    main()
