param(
  [string]$Message = "Update computer exam learning site"
)

$siteFiles = @("index.html", "style.css", "app.js")
git add -- $siteFiles
git commit -m $Message
git push origin main
Write-Output "Pushed. GitHub Pages will update automatically."
