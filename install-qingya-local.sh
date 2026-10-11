#!/usr/bin/env bash
# 本地全量包安装脚本（放在仓库内避免 /tmp 被清理）
set -eu
PKG="/Users/chengjianfei/青崖输入法/target/pkg/qingjian-0.2.1-dev-4a3e963+-macos-arm64.pkg"
[[ -f "$PKG" ]] || { echo "找不到安装包: $PKG" >&2; exit 1; }
rm -rf "/Library/Input Methods/Qingjian.app"
installer -pkg "$PKG" -target /
pkill -x qingjian-macos 2>/dev/null || true
R="/Library/Input Methods/Qingjian.app/Contents/Resources"
echo "dict.qj: $(du -h "$R/dict.qj" | cut -f1)  lm.qj: $(du -h "$R/lm.qj" | cut -f1)"
echo "领域词库: $(ls "$R/dicts" | wc -l | tr -d ' ') 个"
echo "神经模型: $(ls "$R/models/hanzhang-zhiwei" "$R/models/hanzhang-tongbian" | wc -l | tr -d ' ') 个文件"
