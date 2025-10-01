# Análisis de Preguntas y Respuestas con LLM

## Descripción del Proyecto
Sistema distribuido para comparar respuestas generadas por LLM con respuestas humanas de Yahoo Answers.

## Integrantes del Grupo
- Sebastián Navarrete - sebastian.navarrete@mail.udp.cl
- Matias Aranda - matias.aranda1@mail.udp.cl

docker-compose build
docker-compose up -d
python3 main.py para ejecutar el programa
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

PARA LINUX
while true; do
    cacheStats=$(curl -s http://localhost:8000/cache/stats)
    evalStats=$(curl -s http://localhost:8000/evaluation/stats)

    clear
    echo "=== SISTEMA EN EJECUCION ==="
    echo "Cache - Requests: $(echo $cacheStats | jq '.total_requests')"
    echo "Cache - Hit Rate: $(echo $cacheStats | jq '.hit_rate')"
    echo "Cache - Hits: $(echo $cacheStats | jq '.hits'), Misses: $(echo $cacheStats | jq '.misses')"
    echo "Evaluation - Dataset: $(echo $evalStats | jq '.evaluation_dataset_size') preguntas"
    echo "Evaluation - Preguntas evaluadas: $(echo $evalStats | jq '.evaluated_questions')"
    echo "Ultima actualizacion: $(date +'%H:%M:%S')"
    sleep 10
done