const { execSync } = require('child_process')
const fs = require('fs')
const path = require('path')

console.log('🚀 开始构建 CheersAI Electron 应用...\n')

const shareLayoutPath = path.join(__dirname, '../app/(shareLayout)')
const shareLayoutBackupPath = path.join(__dirname, '../.shareLayout.backup')

// 0. 生成图标文件
console.log('🎨 步骤 0/5: 生成应用图标...')
try {
  execSync('node scripts/create-icon.cjs', { stdio: 'inherit', cwd: path.join(__dirname, '..') })
  console.log('✅ 图标生成完成\n')
} catch (error) {
  console.error('❌ 图标生成失败:', error.message)
  process.exit(1)
}

// 1. 临时禁用不需要的动态路由（Web 分享页面）
console.log('📦 步骤 1/5: 准备构建环境...')
try {
  if (fs.existsSync(shareLayoutPath)) {
    fs.cpSync(shareLayoutPath, shareLayoutBackupPath, { recursive: true })
    fs.rmSync(shareLayoutPath, { recursive: true, force: true })
    console.log('✅ 已临时禁用 Web 分享页面\n')
  }
} catch (error) {
  console.error('❌ 准备构建环境失败:', error.message)
  process.exit(1)
}

// 2. 使用 Electron 配置构建 Next.js
console.log('📦 步骤 2/5: 构建 Next.js 应用（静态导出）...')
try {
  const originalConfig = path.join(__dirname, '../next.config.ts')
  const electronConfig = path.join(__dirname, '../next.config.electron.ts')
  const backupConfig = path.join(__dirname, '../next.config.ts.backup')

  if (fs.existsSync(originalConfig)) {
    fs.renameSync(originalConfig, backupConfig)
  }

  fs.copyFileSync(electronConfig, originalConfig)

  execSync('npx pnpm next build', { stdio: 'inherit', cwd: path.join(__dirname, '..') })

  fs.unlinkSync(originalConfig)
  if (fs.existsSync(backupConfig)) {
    fs.renameSync(backupConfig, originalConfig)
  }

  console.log('✅ Next.js 构建完成\n')
} catch (error) {
  console.error('❌ Next.js 构建失败:', error.message)
  
  // 恢复配置
  const originalConfig = path.join(__dirname, '../next.config.ts')
  const backupConfig = path.join(__dirname, '../next.config.ts.backup')
  if (fs.existsSync(backupConfig)) {
    if (fs.existsSync(originalConfig)) {
      fs.unlinkSync(originalConfig)
    }
    fs.renameSync(backupConfig, originalConfig)
  }
  
  // 恢复分享页面
  if (fs.existsSync(shareLayoutBackupPath)) {
    if (fs.existsSync(shareLayoutPath)) {
      fs.rmSync(shareLayoutPath, { recursive: true, force: true })
    }
    fs.cpSync(shareLayoutBackupPath, shareLayoutPath, { recursive: true })
    fs.rmSync(shareLayoutBackupPath, { recursive: true, force: true })
  }
  
  process.exit(1)
}

// 3. 恢复分享页面
console.log('📦 步骤 3/5: 恢复构建环境...')
try {
  if (fs.existsSync(shareLayoutBackupPath)) {
    if (fs.existsSync(shareLayoutPath)) {
      fs.rmSync(shareLayoutPath, { recursive: true, force: true })
    }
    fs.cpSync(shareLayoutBackupPath, shareLayoutPath, { recursive: true })
    fs.rmSync(shareLayoutBackupPath, { recursive: true, force: true })
    console.log('✅ 已恢复 Web 分享页面\n')
  }
} catch (error) {
  console.error('⚠️  恢复分享页面失败:', error.message)
}

// 4. 检查 out 目录
console.log('📦 步骤 4/5: 检查构建输出...')
const outDir = path.join(__dirname, '../out')
if (!fs.existsSync(outDir)) {
  console.error('❌ 错误: out 目录不存在')
  console.error('   Next.js 可能没有正确导出静态文件')
  process.exit(1)
}
console.log('✅ 构建输出检查通过\n')

// 5. 使用 electron-builder 打包
console.log('📦 步骤 5/5: 使用 Electron Builder 打包...')
try {
  const platform = process.argv[2] || 'win'
  let buildCommand
  
  switch (platform) {
    case 'win':
      buildCommand = 'npx electron-builder --win'
      break
    case 'mac':
      buildCommand = 'npx electron-builder --mac'
      break
    case 'linux':
      buildCommand = 'npx electron-builder --linux'
      break
    case 'all':
      buildCommand = 'npx electron-builder -mwl'
      break
    default:
      buildCommand = `npx electron-builder --${platform}`
  }

  execSync(buildCommand, { stdio: 'inherit', cwd: path.join(__dirname, '..') })
  console.log('✅ Electron 打包完成\n')
} catch (error) {
  console.error('❌ Electron 打包失败:', error.message)
  process.exit(1)
}

console.log('🎉 构建完成！')
console.log('📁 输出目录: web/dist-electron')
console.log('\n可用的安装包：')
const distDir = path.join(__dirname, '../dist-electron')
if (fs.existsSync(distDir)) {
  const files = fs.readdirSync(distDir)
  files.forEach(file => {
    if (file.endsWith('.exe') || file.endsWith('.dmg') || file.endsWith('.AppImage') || file.endsWith('.deb')) {
      console.log(`  ✓ ${file}`)
    }
  })
}
