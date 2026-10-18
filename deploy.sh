#!/usr/bin/env bash
# 補助王：從最新 CSV 重建資料並推送到 GitHub Pages
# 用法：./deploy.sh [CSV路徑]   (預設 /workspace/subsidy/補助資料庫.csv)
set -euo pipefail
cd "$(dirname "$0")"
CSV="${1:-/workspace/subsidy/補助資料庫_full.csv}"
python3 build_site.py "$CSV"
python3 build_geo.py || echo "GEO 優化（JSON-LD／靜態清單／llms.txt／sitemap）產生失敗或驗證有誤，請檢查"
python3 /workspace/shared-data/export_subsidies.py "$CSV" || echo "共用補助檔產生失敗（下游會退回直接讀 CSV）"
python3 /workspace/shared-data/ga_inject.py . || echo "⚠️ GA 程式碼補入或檢查有問題，請看上面訊息"   # GA4：所有頁面 <head> 補 gtag（2026-10-18）
# 再次確認沒有私人資料
if grep -Eq 'GetGrant|日報|紀錄檔|週期性補助預測|彙整報告|20260920|drive\.google|docs\.google|使用者|user_files' data.json data.js data_hist_*.js; then
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
