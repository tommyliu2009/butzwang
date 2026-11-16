#!/usr/bin/env bash
# 補助王：從最新 CSV 重建資料並推送到 GitHub Pages
# 用法：./deploy.sh [CSV路徑]   (預設 /workspace/subsidy/補助資料庫.csv)
set -euo pipefail
cd "$(dirname "$0")"
source /workspace/handoff/repo_lock.sh butzwang butzwang   # 程式鎖＋AI 鎖（RULES §7、§14，2026-10-20）
CSV="${1:-/workspace/subsidy/補助資料庫_full.csv}"
T=/workspace/subsidy/tools
# 2026-11-15：今天還沒抓過來源就先抓一次（官方列表頁→候選清單 fetch_日期/candidates_auto.json；不自動寫入 CSV），頁尾「最後抓取來源」讀 last_fetch.json
if ! grep -q "\"date\": \"$(TZ=Asia/Taipei date +%F)\"" /workspace/subsidy/last_fetch.json 2>/dev/null; then
  timeout 600 python3 $T/daily_fetch.py || echo "⚠️ 來源抓取失敗（不影響部署）"
fi
python3 $T/bz_maintain.py "$CSV" || echo "⚠️ CSV 維護（受理開始日／狀態轉換／過去年度改列歷史／層級）失敗，請檢查"
[ "${SKIP_LINKCHECK:-0}" = 1 ] || timeout 1200 python3 $T/link_check.py "$CSV" || echo "⚠️ 每日連結檢查失敗或逾時（不影響部署）"
python3 build_site.py "$CSV"
python3 build_geo.py || echo "GEO 優化（JSON-LD／靜態清單／llms.txt／sitemap）產生失敗或驗證有誤，請檢查"
python3 /workspace/shared-data/export_subsidies.py "$CSV" || echo "共用補助檔產生失敗（下游會退回直接讀 CSV）"
python3 /workspace/shared-data/ga_inject.py . || echo "⚠️ GA 程式碼補入或檢查有問題，請看上面訊息"   # GA4：所有頁面 <head> 補 gtag（2026-10-18）
python3 /workspace/shared-data/matrix/matrix_apply.py . || { [ $? -eq 2 ] && { echo "⛔ 聯智↔仁禾隔離檢查失敗，中止部署" >&2; exit 1; }; echo "⚠️ 矩陣區塊產生有問題（不影響部署）"; }   # 矩陣網站：相關網站、延伸閱讀、問診、GEO（2026-10-24）
# 再次確認沒有私人資料
# 2026-11-15：「使用者」「日報」「紀錄檔」只會在備註欄出現，build_site.py 已在備註欄過濾；正式名稱如「長期照顧服務使用者自付額補助」不再誤擋
if grep -Eq 'GetGrant|週期性補助預測|彙整報告|20260920|drive\.google|docs\.google|user_files' data.json data.js data_hist_*.js; then
  echo "ERROR: 偵測到私人資料，中止部署" >&2; exit 1
fi
git add -A
if git diff --cached --quiet; then
  echo "資料無變動，不需部署"; bash themes/grantking/deploy_gk.sh || echo "⚠️ 獎補助資訊網部署失敗"; bash /workspace/rd-subsidy/deploy.sh || echo "⚠️ 研發補助王部署失敗"; exit 0
fi
git -c user.name="${GIT_NAME:-tommyliu2009}" -c user.email="${GIT_EMAIL:-tommyliu2009@users.noreply.github.com}" \
  commit -qm "資料更新 $(TZ=Asia/Taipei date '+%Y-%m-%d %H:%M')"
git push -q origin main
echo "已部署：$(git log -1 --format=%s)"
(sleep 60; python3 /workspace/shared-data/indexnow.py www.subsidyking.tw /workspace/butzwang) || true   # 2026-11-16 GEO#5：IndexNow（失敗不影響部署）
bash themes/grantking/deploy_gk.sh || echo "⚠️ 獎補助資訊網部署失敗，請檢查"   # 獎補助資訊網（2026-10-24）
bash /workspace/rd-subsidy/deploy.sh || echo "⚠️ 研發補助王部署失敗，請檢查"   # 研發補助王 web20（2026-10-24）
