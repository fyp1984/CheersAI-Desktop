import type { NextRequest } from 'next/server'
import { existsSync } from 'node:fs'
import { mkdir, writeFile } from 'node:fs/promises'
import { join } from 'node:path'
import { NextResponse } from 'next/server'

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
    const sanitizedName = file.name.replace(/[^a-z0-9.-]/gi, '_')
    const fileName = `${timestamp}_${sanitizedName}`
    const filePath = join(sandboxDir, fileName)

    // 保存文件
    const bytes = await file.arrayBuffer()
    const fileBytes = new Uint8Array(bytes)
    await writeFile(filePath, fileBytes)

    return NextResponse.json({
      success: true,
      fileName,
      sandboxPath: `/sandbox/uploads/${fileName}`,
      originalName: file.name,
      size: file.size,
      type: file.type,
    })
  }
  catch (error) {
    console.error('文件上传到沙箱失败:', error)
    return NextResponse.json(
      { error: '文件上传失败' },
      { status: 500 },
    )
  }
}
