# 補助王

純靜態網站（HTML/CSS/JS），無後端。`index.html` 在根目錄，所有路徑皆為相對路徑，可直接部署到 GitHub Pages / Netlify / Cloudflare Pages。

## 每日更新
    python3 build_site.py [CSV路徑]   # 預設 /workspace/subsidy/補助資料庫.csv
產生 `data.json` 與 `data.js`（頁面讀 data.js，因此用 file:// 直接開也可以）。

## 部署
    ./deploy.sh   # 重建 + commit + push（GitHub Pages 自動更新）

## 本機預覽
    python3 -m http.server 8080
