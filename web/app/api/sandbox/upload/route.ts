import { NextRequest, NextResponse } from 'next/server'
import { writeFile, mkdir } from 'fs/promises'
import { join } from 'path'
import { existsSync } from 'fs'

export async function POST(request: NextRequest) {
  try {
    const formData = await request.formData()
    const file = formData.get('file') as File
    
    if (!file) {
      return NextResponse.json({ error: '没有找到文件' }, { status: 400 })
    }

    // 创建脱敏沙箱目录
    const sandboxDir = join(process.cwd(), 'sandbox', 'uploads')
    if (!existsSync(sandboxDir)) {
      await mkdir(sandboxDir, { recursive: true })
    }

    // 生成安全的文件名
    const timestamp = Date.now()
    const sanitizedName = file.name.replace(/[^a-zA-Z0-9.-]/g, '_')
    const fileName = `${timestamp}_${sanitizedName}`
    const filePath = join(sandboxDir, fileName)

    // 保存文件
    const bytes = await file.arrayBuffer()
    const buffer = Buffer.from(bytes)
    await writeFile(filePath, buffer)

    console.log('📁 文件已保存到脱敏沙箱:', fileName)

    return NextResponse.json({
      success: true,
      fileName: fileName,
      sandboxPath: `/sandbox/uploads/${fileName}`,
      originalName: file.name,
      size: file.size,
      type: file.type,
    })

  } catch (error) {
    console.error('文件上传到沙箱失败:', error)
    return NextResponse.json(
      { error: '文件上传失败' }, 
      { status: 500 }
    )
  }
}