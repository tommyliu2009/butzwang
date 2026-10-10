#!/usr/bin/env bash
# 補助王：從最新 CSV 重建資料並推送到 GitHub Pages
# 用法：./deploy.sh [CSV路徑]   (預設 /workspace/subsidy/補助資料庫.csv)
set -euo pipefail
cd "$(dirname "$0")"
CSV="${1:-/workspace/subsidy/補助資料庫_full.csv}"
python3 build_site.py "$CSV"
# 再次確認沒有私人資料
if grep -Eq 'GetGrant|日報|紀錄檔|週期性補助預測|彙整報告|20260920|drive\.google|docs\.google|使用者|user_files' data.json data.js; then
  echo "ERROR: 偵測到私人資料，中止部署" >&2; exit 1
fi
git add -A
if git diff --cached --quiet; then
  echo "資料無變動，不需部署"; exit 0
fi
git -c user.name="${GIT_NAME:-tommyliu2009}" -c user.email="${GIT_EMAIL:-tommyliu2009@users.noreply.github.com}" \
  commit -qm "資料更新 $(TZ=Asia/Taipei date '+%Y-%m-%d %H:%M')"
git push -q origin main
echo "已部署：$(git log -1 --format=%s)"
