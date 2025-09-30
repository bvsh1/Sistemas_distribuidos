# run_analysis.ps1
Write-Host "=== ANÁLISIS COMPLETO DEL SISTEMA ===" -ForegroundColor Green

# Crear directorios necesarios
New-Item -ItemType Directory -Force -Path "analyze", "analyze/data"

Write-Host "`n1. Extrayendo datos del sistema..." -ForegroundColor Yellow
python analyze/extract_data.py

Write-Host "`n2. Analizando datos..." -ForegroundColor Yellow
python analyze/analyze_data.py

Write-Host "`n3. Generando reporte..." -ForegroundColor Yellow

# Mostrar archivos generados
Write-Host "`nARCHIVOS GENERADOS:" -ForegroundColor Cyan
Get-ChildItem "analyze/data" -File | Select-Object Name, Length, LastWriteTime

Write-Host "`n=== ANÁLISIS COMPLETADO ===" -ForegroundColor Green
Write-Host "Los reportes se guardaron en la carpeta 'analyze/'" -ForegroundColor White