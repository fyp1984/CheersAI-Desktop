#!/usr/bin/env node

/**
 * 打包 Next.js 服务器为独立可执行文件
 * 用于 Tauri 嵌入式服务器方案
 */

const { execSync } = require('node:child_process')
const fs = require('node:fs')
const path = require('node:path')

console.log('📦 开始打包 Next.js 服务器...\n')

const serverDir = path.join(__dirname, '../server')
const outputDir = path.join(__dirname, '../src-tauri/binaries')

// 1. 创建输出目录
if (!fs.existsSync(serverDir)) {
  fs.mkdirSync(serverDir, { recursive: true })
}
if (!fs.existsSync(outputDir)) {
  fs.mkdirSync(outputDir, { recursive: true })
}

// 2. 创建服务器入口文件
console.log('📝 创建服务器入口文件...')
const serverEntry = `
const { createServer } = require('http');
const { parse } = require('url');
const next = require('next');

const dev = false;
const hostname = 'localhost';
const port = process.env.PORT || 3000;

const app = next({ dev, hostname, port, dir: __dirname });
const handle = app.getRequestHandler();

app.prepare().then(() => {
  createServer(async (req, res) => {
    try {
      const parsedUrl = parse(req.url, true);
      await handle(req, res, parsedUrl);
    } catch (err) {
      console.error('Error occurred handling', req.url, err);
      res.statusCode = 500;
      res.end('internal server error');
    }
  })
    .once('error', (err) => {
      console.error(err);
      process.exit(1);
    })
    .listen(port, () => {
      console.log(\`> Ready on http://\${hostname}:\${port}\`);
    });
});
`

fs.writeFileSync(path.join(serverDir, 'server.js'), serverEntry)

// 3. 创建 package.json
console.log('📝 创建 package.json...')
const packageJson = {
  name: 'cheersai-server',
  version: '1.0.0',
  private: true,
  scripts: {
    start: 'node server.js',
  },
  dependencies: {
    'next': require('../package.json').dependencies.next,
    'react': require('../package.json').dependencies.react,
    'react-dom': require('../package.json').dependencies['react-dom'],
  },
}

fs.writeFileSync(
  path.join(serverDir, 'package.json'),
  JSON.stringify(packageJson, null, 2),
)

// 4. 构建 Next.js
console.log('🔨 构建 Next.js 应用...')
try {
  execSync('pnpm build:docker', {
    stdio: 'inherit',
    cwd: path.join(__dirname, '..'),
  })
}
catch {
  console.error('❌ Next.js 构建失败')
  process.exit(1)
}

// 5. 复制构建产物
console.log('📋 复制构建产物...')
const standaloneDir = path.join(__dirname, '../.next/standalone')
const staticDir = path.join(__dirname, '../.next/static')
const publicDir = path.join(__dirname, '../public')

// 复制 standalone
if (fs.existsSync(standaloneDir)) {
  execSync(`xcopy /E /I /Y "${standaloneDir}" "${serverDir}"`, { stdio: 'inherit' })
}

// 复制 static
const targetStaticDir = path.join(serverDir, '.next/static')
if (fs.existsSync(staticDir)) {
  if (!fs.existsSync(path.dirname(targetStaticDir))) {
    fs.mkdirSync(path.dirname(targetStaticDir), { recursive: true })
  }
  execSync(`xcopy /E /I /Y "${staticDir}" "${targetStaticDir}"`, { stdio: 'inherit' })
}

// 复制 public
const targetPublicDir = path.join(serverDir, 'public')
if (fs.existsSync(publicDir)) {
  execSync(`xcopy /E /I /Y "${publicDir}" "${targetPublicDir}"`, { stdio: 'inherit' })
}

console.log('✅ Next.js 服务器打包完成！')
console.log(`📁 输出目录: ${serverDir}`)
console.log('\n⚠️  注意：此服务器需要 Node.js 运行时')
console.log('💡 下一步：将 Node.js 运行时打包到 Tauri 应用中')
