/**
 * Script to optimize Next.js standalone output for production
 * Removes unnecessary files like jest-worker that are bundled with Next.js
 */

import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)

console.log('🔧 Optimizing standalone output...')

const nextDir = path.join(__dirname, '..', '.next')
const standaloneDir = path.join(__dirname, '..', '.next', 'standalone')
const standaloneWebDir = path.join(standaloneDir, 'web')
const runtimeRoot = fs.existsSync(path.join(standaloneDir, 'server.js'))
  ? standaloneDir
  : standaloneWebDir

// Check if standalone directory exists
if (!fs.existsSync(standaloneDir)) {
  console.error('❌ Standalone directory not found. Please run "next build" first.')
  process.exit(1)
}

// List of paths to remove (relative to standalone directory)
const pathsToRemove = [
  // Remove jest-worker from Next.js compiled dependencies
  'node_modules/.pnpm/next@*/node_modules/next/dist/compiled/jest-worker',
  // Remove jest-worker symlinks from terser-webpack-plugin
  'node_modules/.pnpm/terser-webpack-plugin@*/node_modules/jest-worker',
  // Remove actual jest-worker packages (directories only, not symlinks)
  'node_modules/.pnpm/jest-worker@*',
]

// Function to safely remove a path
function removePath(basePath, relativePath) {
  const fullPath = path.join(basePath, relativePath)

  // Handle wildcard patterns
  if (relativePath.includes('*')) {
    const parts = relativePath.split('/')
    let currentPath = basePath

    for (let i = 0; i < parts.length; i++) {
      const part = parts[i]
      if (part.includes('*')) {
        // Find matching directories
        if (fs.existsSync(currentPath)) {
          const entries = fs.readdirSync(currentPath)

          // replace '*' with '.*'
          const regexPattern = part.replace(/\*/g, '.*')

          const regex = new RegExp(`^${regexPattern}$`)

          for (const entry of entries) {
            if (regex.test(entry)) {
              const remainingPath = parts.slice(i + 1).join('/')
              const matchedPath = path.join(currentPath, entry, remainingPath)

              try {
                // Use lstatSync to check if path exists (works for both files and symlinks)
                const stats = fs.lstatSync(matchedPath)

                if (stats.isSymbolicLink()) {
                  // Remove symlink
                  fs.unlinkSync(matchedPath)
                  console.log(`✅ Removed symlink: ${path.relative(basePath, matchedPath)}`)
                }
                else {
                  // Remove directory/file
                  fs.rmSync(matchedPath, { recursive: true, force: true })
                  console.log(`✅ Removed: ${path.relative(basePath, matchedPath)}`)
                }
              }
              catch (error) {
                // Silently ignore ENOENT (path not found) errors
                if (error.code !== 'ENOENT') {
                  console.error(`❌ Failed to remove ${matchedPath}: ${error.message}`)
                }
              }
            }
          }
        }
        return
      }
      else {
        currentPath = path.join(currentPath, part)
      }
    }
  }
  else {
    // Direct path removal
    if (fs.existsSync(fullPath)) {
      try {
        fs.rmSync(fullPath, { recursive: true, force: true })
        console.log(`✅ Removed: ${relativePath}`)
      }
      catch (error) {
        console.error(`❌ Failed to remove ${fullPath}: ${error.message}`)
      }
    }
  }
}

// Remove unnecessary paths
console.log('🗑️  Removing unnecessary files...')
for (const pathToRemove of pathsToRemove) {
  removePath(standaloneDir, pathToRemove)
}

function syncPath(sourcePath, targetPath) {
  if (!fs.existsSync(sourcePath))
    return
  fs.rmSync(targetPath, { recursive: true, force: true })
  fs.mkdirSync(path.dirname(targetPath), { recursive: true })
  fs.cpSync(sourcePath, targetPath, { recursive: true })
  console.log(`✅ Synced: ${path.relative(path.join(__dirname, '..'), targetPath)}`)
}

console.log('📦 Syncing runtime assets...')
console.log(`📍 Runtime root: ${path.relative(path.join(__dirname, '..'), runtimeRoot)}`)
syncPath(path.join(nextDir, 'static'), path.join(runtimeRoot, '.next', 'static'))
syncPath(path.join(__dirname, '..', 'public'), path.join(runtimeRoot, 'public'))
// Server-side i18n uses dynamic JSON imports at runtime, so keep the locale files adjacent
// to the standalone server entry.
syncPath(path.join(__dirname, '..', 'i18n'), path.join(runtimeRoot, 'i18n'))

// Calculate size reduction
console.log('\n📊 Optimization complete!')

// Optional: Display the size of remaining jest-related files (if any)
const checkForJest = (dir) => {
  const jestFiles = []

  function walk(currentPath) {
    if (!fs.existsSync(currentPath))
      return

    try {
      const entries = fs.readdirSync(currentPath)
      for (const entry of entries) {
        const fullPath = path.join(currentPath, entry)

        try {
          const stat = fs.lstatSync(fullPath) // Use lstatSync to handle symlinks

          if (stat.isDirectory() && !stat.isSymbolicLink()) {
            // Skip node_modules subdirectories to avoid deep traversal
            if (entry === 'node_modules' && currentPath !== standaloneDir) {
              continue
            }
            walk(fullPath)
          }
          else if (stat.isFile() && entry.includes('jest')) {
            jestFiles.push(path.relative(standaloneDir, fullPath))
          }
        }
        catch (err) {
          // Skip files that can't be accessed
          continue
        }
      }
    }
    catch (err) {
      // Skip directories that can't be read

    }
  }

  walk(dir)
  return jestFiles
}

const remainingJestFiles = checkForJest(standaloneDir)
if (remainingJestFiles.length > 0) {
  console.log('\n⚠️  Warning: Some jest-related files still remain:')
  remainingJestFiles.forEach(file => console.log(`  - ${file}`))
}
else {
  console.log('\n✨ No jest-related files found in standalone output!')
}
