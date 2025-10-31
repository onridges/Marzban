#!/usr/bin/env bash
set -eo pipefail

# Marzban 项目构建和重启包装脚本
# 这是根目录的入口脚本，调用子目录中的具体实现

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
SCRIPT_DIR="$ROOT_DIR/scripts"

echo "🚀 Marzban 构建和重启工具"
echo "================================"

# 检查scripts目录是否存在
if [ ! -d "$SCRIPT_DIR" ]; then
    echo "❌ 错误: scripts 目录不存在"
    exit 1
fi

# 检查具体的构建脚本是否存在
REBUILD_SCRIPT="$SCRIPT_DIR/rebuild_and_restart.sh"
if [ ! -f "$REBUILD_SCRIPT" ]; then
    echo "❌ 错误: 构建脚本不存在: $REBUILD_SCRIPT"
    exit 1
fi

# 确保脚本可执行
chmod +x "$REBUILD_SCRIPT"

echo "📂 项目根目录: $ROOT_DIR"
echo "🔧 执行构建脚本: $REBUILD_SCRIPT"
echo ""

# 调用具体的构建脚本
exec "$REBUILD_SCRIPT" "$@"