# Análisis de Preguntas y Respuestas con LLM

## Descripción del Proyecto
Sistema distribuido para comparar respuestas generadas por LLM con respuestas humanas de Yahoo Answers.

## Integrantes del Grupo
- Sebastián Navarrete - sebastian.navarrete@mail.udp.cl
- Matias Aranda - matias.aranda1@mail.udp.cl

docker-compose build
docker-compose up -d
python main.py para ejecutar el programa
en otra ventana ejecutar  while ($true) {
>>     try {
>>         $cacheStats = Invoke-RestMethod -Uri "http://localhost:8000/cache/stats" -Method Get
>>         $evalStats = Invoke-RestMethod -Uri "http://localhost:8000/evaluation/stats" -Method Get
>>
>>         Clear-Host
>>         Write-Host "=== SISTEMA EN EJECUCION ==="
>>         Write-Host "Cache - Requests: $($cacheStats.total_requests)"
>>         Write-Host "Cache - Hit Rate: $([math]::Round($cacheStats.hit_rate * 100, 2))%"
>>         Write-Host "Cache - Hits: $($cacheStats.hits), Misses: $($cacheStats.misses)"
>>         Write-Host "Evaluation - Dataset: $($evalStats.evaluation_dataset_size) preguntas"
>>         Write-Host "Evaluation - Preguntas evaluadas: $($evalStats.evaluated_questions)"
>>         Write-Host "Ultima actualizacion: $(Get-Date -Format 'HH:mm:ss')"
>>     } catch {
>>         Write-Host "Error de conexion"
>>     }
>>     Start-Sleep 10
>> }
para ver la información
