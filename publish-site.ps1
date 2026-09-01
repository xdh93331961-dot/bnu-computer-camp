param(
  [string]$Message = "Update computer exam learning site"
)

$ErrorActionPreference = "Stop"
$siteFiles = @("index.html", "style.css", "app.js")

git add -- $siteFiles
git diff --cached --quiet
if ($LASTEXITCODE -eq 0) {
  Write-Output "没有需要发布的网站改动。"
  exit 0
}

git commit -m $Message
git push origin main
Write-Output "已推送。GitHub Pages 将在几分钟内自动更新。"
