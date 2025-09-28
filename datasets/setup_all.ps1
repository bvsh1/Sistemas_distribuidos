# Script maestro para configurar todos los datasets
Write-Host "CONFIGURACION COMPLETA DE DATASETS" -ForegroundColor Green
Write-Host "===================================" -ForegroundColor Green

# 1. Crear dataset de ejemplo
Write-Host "1. Creando dataset de ejemplo..." -ForegroundColor Yellow
.\datasets\download_dataset_fallback.ps1

# 2. Preprocesar datos
Write-Host "2. Preprocesando datos..." -ForegroundColor Yellow
.\datasets\preprocess.ps1

# 3. Verificar resultados
Write-Host "3. Verificando archivos creados..." -ForegroundColor Yellow
Get-ChildItem datasets -Recurse -File | Select-Object Name, Length

Write-Host "Configuracion de datasets completada!" -ForegroundColor Green
Write-Host "Los archivos estan listos en la carpeta 'datasets/'" -ForegroundColor Green