#!/usr/bin/env bash
# 獎補助資訊網：由 butzwang/deploy.sh 呼叫（同一份 data.json）。用法：deploy_gk.sh [--dry-run]
set -euo pipefail
H="$(cd "$(dirname "$0")" && pwd)"
if [ "${1:-}" = "--dry-run" ]; then python3 "$H/build_theme.py" --dry-run; exit 0; fi
timeout 1500 python3 "$H/rewrite.py" 60 || echo "摘要改寫未完成，沿用快取／原文"
python3 "$H/build_theme.py"
cd /workspace/grant-king
git add -A
if git diff --cached --quiet; then echo "獎補助資訊網：無變動"; exit 0; fi
git -c user.name=tommyliu2009 -c user.email=tommyliu2009@users.noreply.github.com commit -qm "資料更新 $(TZ=Asia/Taipei date '+%Y-%m-%d %H:%M')"
git push -q origin main
echo "獎補助資訊網已部署：$(git log -1 --format=%h)"
