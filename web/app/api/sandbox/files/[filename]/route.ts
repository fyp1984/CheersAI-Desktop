import { NextRequest, NextResponse } from 'next/server'
import { readFile } from 'fs/promises'
import { join } from 'path'
import { existsSync } from 'fs'

export async function GET(
  request: NextRequest,
  { params }: { params: { filename: string } }
) {
  try {
    const filename = params.filename
    
    // 安全检查：防止路径遍历攻击
    if (filename.includes('..') || filename.includes('/') || filename.includes('\\')) {
      return NextResponse.json({ error: '非法文件名' }, { status: 400 })
    }

    const filePath = join(process.cwd(), 'sandbox', 'uploads', filename)
    
    if (!existsSync(filePath)) {
      return NextResponse.json({ error: '文件不存在' }, { status: 404 })
    }

    const fileBuffer = await readFile(filePath)
    
    // 根据文件扩展名设置 Content-Type
    const ext = filename.split('.').pop()?.toLowerCase()
    let contentType = 'application/octet-stream'
    
    const mimeTypes: Record<string, string> = {
      'txt': 'text/plain',
      'pdf': 'application/pdf',
      'doc': 'application/msword',
      'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
      'xls': 'application/vnd.ms-excel',
      'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      'ppt': 'application/vnd.ms-powerpoint',
      'pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
      'jpg': 'image/jpeg',
      'jpeg': 'image/jpeg',
      'png': 'image/png',
      'gif': 'image/gif',
      'csv': 'text/csv',
      'json': 'application/json',
    }
    
    if (ext && mimeTypes[ext]) {
      contentType = mimeTypes[ext]
    }

    return new NextResponse(fileBuffer, {
      headers: {
        'Content-Type': contentType,
        'Content-Disposition': `inline; filename="${filename}"`,
      },
    })

  } catch (error) {
    console.error('读取沙箱文件失败:', error)
    return NextResponse.json(
      { error: '读取文件失败' }, 
      { status: 500 }
    )
  }
}