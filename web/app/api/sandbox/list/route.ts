import { NextResponse } from 'next/server'
import { readdir, stat } from 'fs/promises'
import { join } from 'path'
import { existsSync } from 'fs'

export async function GET() {
  try {
    const sandboxDir = join(process.cwd(), 'sandbox', 'uploads')
    
    if (!existsSync(sandboxDir)) {
      return NextResponse.json([])
    }

    const files = await readdir(sandboxDir)
    const fileList = []

    for (const fileName of files) {
      try {
        const filePath = join(sandboxDir, fileName)
        const stats = await stat(filePath)
        
        if (stats.isFile()) {
          // 从文件名中提取原始名称（移除时间戳前缀）
          const originalName = fileName.replace(/^\d+_/, '')
          
          fileList.push({
            name: fileName,
            originalName: originalName,
            size: stats.size,
            type: getFileType(originalName),
            createdAt: stats.birthtime,
            modifiedAt: stats.mtime,
          })
        }
      } catch (error) {
        console.warn(`无法读取文件信息: ${fileName}`, error)
      }
    }

    // 按修改时间倒序排列
    fileList.sort((a, b) => b.modifiedAt.getTime() - a.modifiedAt.getTime())

    console.log('📁 获取沙箱文件列表:', fileList.length, '个文件')
    return NextResponse.json(fileList)

  } catch (error) {
    console.error('获取沙箱文件列表失败:', error)
    return NextResponse.json(
      { error: '获取文件列表失败' }, 
      { status: 500 }
    )
  }
}

function getFileType(fileName: string): string {
  const ext = fileName.split('.').pop()?.toLowerCase()
  
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
  
  return mimeTypes[ext || ''] || 'application/octet-stream'
}