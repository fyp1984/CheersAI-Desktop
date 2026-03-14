#!/bin/bash
set -e

# 1. 检查环境
if ! command -v rustc &> /dev/null; then
    echo "❌ Rust 未安装。请运行以下命令安装："
    echo "curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh"
    echo "安装完成后，请重启终端或运行 'source \$HOME/.cargo/env'"
    exit 1
fi

echo "✅ Rust 环境已就绪 ($(rustc --version))"

# 2. 准备重定向页面
mkdir -p web/dist-redirect
cat <<EOF > web/dist-redirect/index.html
<!DOCTYPE html>
<html>
<head>
  <meta http-equiv="refresh" content="0; url=https://7smile.dlithink.com/cheersai_desktop" />
  <script>
    window.location.href = "https://7smile.dlithink.com/cheersai_desktop";
  </script>
  <style>
    body { font-family: system-ui, sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; background: #f9fafb; color: #374151; }
    .loader { border: 4px solid #f3f3f3; border-top: 4px solid #3b82f6; border-radius: 50%; width: 40px; height: 40px; animation: spin 1s linear infinite; margin-bottom: 1rem; }
    @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
    .container { text-align: center; }
  </style>
</head>
<body>
  <div class="container">
    <div class="loader" style="margin: 0 auto 1rem auto;"></div>
    <p>正在连接到 CheersAI Desktop...</p>
    <p style="font-size: 0.875rem; color: #6b7280;">https://7smile.dlithink.com/cheersai_desktop</p>
  </div>
</body>
</html>
EOF

echo "✅ 重定向页面已生成"

# 3. 确保 tauri.conf.json 指向 dist-redirect
# 兼容 macOS 和 Linux 的 sed
if [[ "$OSTYPE" == "darwin"* ]]; then
  sed -i '' 's|"frontendDist": "../dist-server"|"frontendDist": "../dist-redirect"|g' web/src-tauri/tauri.conf.json
else
  sed -i 's|"frontendDist": "../dist-server"|"frontendDist": "../dist-redirect"|g' web/src-tauri/tauri.conf.json
fi

echo "✅ Tauri 配置已更新"

# 4. 执行构建
echo "🚀 开始构建 Tauri 应用..."
cd web

# 检查 pnpm
if ! command -v pnpm &> /dev/null; then
    echo "⚠️ 未找到 pnpm，尝试使用 npm..."
    npm install
    npm run tauri build
else
    pnpm install
    pnpm tauri build
fi

echo "✅ 构建完成！安装包位于 web/src-tauri/target/release/bundle/"
