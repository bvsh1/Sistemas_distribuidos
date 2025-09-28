# Script de configuración para Kaggle - Versión PowerShell
Write-Host "Configurando Kaggle CLI..." -ForegroundColor Green

$kaggleDir = "$env:USERPROFILE\.kaggle"
if (!(Test-Path $kaggleDir)) {
    New-Item -ItemType Directory -Path $kaggleDir -Force
}

Write-Host "Por favor, sigue estos pasos:" -ForegroundColor Yellow
Write-Host "1. Ve a https://www.kaggle.com/account" -ForegroundColor White
Write-Host "2. Haz clic en 'Create New API Token'" -ForegroundColor White
Write-Host "3. Descarga el archivo kaggle.json" -ForegroundColor White
Write-Host "4. Mueve el archivo a: $kaggleDir\" -ForegroundColor White
Write-Host "" -ForegroundColor White
Write-Host "Después de descargar kaggle.json, ejecuta:" -ForegroundColor Yellow
Write-Host "icacls `"$kaggleDir\kaggle.json`" /inheritance:r" -ForegroundColor White
Write-Host "icacls `"$kaggleDir\kaggle.json`" /grant:r `"$env:USERNAME:(R)`"" -ForegroundColor White
Write-Host "" -ForegroundColor White
Write-Host "Luego podrás usar: .\datasets\download_dataset.ps1" -ForegroundColor Green