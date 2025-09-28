# Script para descargar dataset de Yahoo Answers - Versión PowerShell
Write-Host "Descargando dataset de Yahoo Answers..." -ForegroundColor Green

# Crear directorio si no existe
$DatasetDir = "datasets"
if (!(Test-Path $DatasetDir)) {
    New-Item -ItemType Directory -Path $DatasetDir -Force
}

# Verificar si kaggle está instalado
try {
    $kaggleCheck = kaggle --version 2>$null
    Write-Host "Kaggle CLI encontrado" -ForegroundColor Green
} catch {
    Write-Host "Kaggle CLI no está instalado" -ForegroundColor Red
    Write-Host "Instalando kaggle..." -ForegroundColor Yellow
    pip install kaggle
}

# Verificar API key
$kaggleConfig = "$env:USERPROFILE\.kaggle\kaggle.json"
if (!(Test-Path $kaggleConfig)) {
    Write-Host "API key de Kaggle no encontrada en $kaggleConfig" -ForegroundColor Red
    Write-Host "Configuración requerida:" -ForegroundColor Yellow
    Write-Host "1. Ve a https://www.kaggle.com/account" -ForegroundColor White
    Write-Host "2. Crea una nueva API token" -ForegroundColor White
    Write-Host "3. Guarda el archivo kaggle.json en $env:USERPROFILE\.kaggle\" -ForegroundColor White
    Write-Host "4. Ejecuta: .\datasets\setup_kaggle.ps1" -ForegroundColor White
    exit 1
}

# Descargar dataset
Write-Host "Descargando dataset..." -ForegroundColor Yellow
kaggle datasets download -d jarupula/yahoo-answers-dataset -p $DatasetDir

# Descomprimir
Write-Host "Descomprimiendo archivos..." -ForegroundColor Yellow
$zipFile = "$DatasetDir\yahoo-answers-dataset.zip"
if (Test-Path $zipFile) {
    Expand-Archive -Path $zipFile -DestinationPath "$DatasetDir\raw" -Force
    Remove-Item $zipFile
    Write-Host "Dataset descargado y descomprimido" -ForegroundColor Green
} else {
    Write-Host "No se pudo descargar el dataset" -ForegroundColor Red
}

Write-Host "Archivos disponibles:" -ForegroundColor Green
Get-ChildItem $DatasetDir -Recurse | Select-Object Name, Length