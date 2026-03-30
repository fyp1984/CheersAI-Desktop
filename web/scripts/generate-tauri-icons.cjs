const fs = require('node:fs')
const path = require('node:path')
const sharp = require('sharp')

async function generateIcons() {
  const inputFile = path.join(__dirname, '../public/logo/CheersAI.png')
  const outputDir = path.join(__dirname, '../src-tauri/icons')

  if (!fs.existsSync(outputDir)) {
    fs.mkdirSync(outputDir, { recursive: true })
  }

  console.log('🎨 正在生成 Tauri 图标文件...\n')

  const sizes = [
    { name: '32x32.png', size: 32 },
    { name: '128x128.png', size: 128 },
    { name: '128x128@2x.png', size: 256 },
    { name: 'icon.png', size: 512 },
    { name: 'Square30x30Logo.png', size: 30 },
    { name: 'Square44x44Logo.png', size: 44 },
    { name: 'Square71x71Logo.png', size: 71 },
    { name: 'Square89x89Logo.png', size: 89 },
    { name: 'Square107x107Logo.png', size: 107 },
    { name: 'Square142x142Logo.png', size: 142 },
    { name: 'Square150x150Logo.png', size: 150 },
    { name: 'Square284x284Logo.png', size: 284 },
    { name: 'Square310x310Logo.png', size: 310 },
    { name: 'StoreLogo.png', size: 50 },
  ]

  try {
    for (const { name, size } of sizes) {
      await sharp(inputFile)
        .resize(size, size, {
          fit: 'contain',
          background: { r: 0, g: 0, b: 0, alpha: 0 },
        })
        .png()
        .toFile(path.join(outputDir, name))
      console.log(`✅ ${name}`)
    }

    console.log('\n✅ 所有图标生成完成！')
    console.log('⚠️  注意: icon.ico 和 icon.icns 需要专门工具生成')
    console.log('   Windows: 使用在线工具或 ImageMagick')
    console.log('   macOS: 使用 iconutil 或在线工具')
  }
  catch (error) {
    console.error('❌ 生成图标失败:', error.message)
    process.exit(1)
  }
}

generateIcons()
