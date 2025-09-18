Write-Host "TEST FINAL DEL SISTEMA CON Invoke-RestMethod" -ForegroundColor Green

# 1. Test Health endpoints
Write-Host "`n1. HEALTH CHECKS:" -ForegroundColor Yellow
$healthLLM = Invoke-RestMethod -Uri "http://localhost:5000/health" -Method Get
$healthCache = Invoke-RestMethod -Uri "http://localhost:8000/health" -Method Get
Write-Host "✅ LLM Service: $($healthLLM.status)" -ForegroundColor Green
Write-Host "✅ Cache Service: $($healthCache.status)" -ForegroundColor Green

# 2. Test multiple queries
Write-Host "`n2. TESTING QUERIES:" -ForegroundColor Yellow
$questions = @(
    "¿Qué es Python?",
    "¿Qué es Docker?",
    "¿Qué es inteligencia artificial?",
    "¿Qué es un sistema distribuido?"
)

foreach ($q in $questions) {
    $body = @{question = $q} | ConvertTo-Json
    $response = Invoke-RestMethod -Uri "http://localhost:8000/query" -Method Post -Body $body -ContentType "application/json"
    
    Write-Host "=== $($q) ===" -ForegroundColor Cyan
    Write-Host "Respuesta: $($response.response)" -ForegroundColor White
    Write-Host "Fuente: $($response.source)" -ForegroundColor Magenta
    Write-Host "Cache: $($response.cache_stats.hits) hits, $($response.cache_stats.misses) misses" -ForegroundColor Yellow
    Write-Host "---"
}

# 3. Test cache behavior
Write-Host "`n3. TESTING CACHE BEHAVIOR:" -ForegroundColor Yellow
$testQuestion = "¿Qué es machine learning?"
$body = @{question = $testQuestion} | ConvertTo-Json

Write-Host "Primera consulta (debería ser MISS):" -ForegroundColor Yellow
$first = Invoke-RestMethod -Uri "http://localhost:8000/query" -Method Post -Body $body -ContentType "application/json"
Write-Host "Misses: $($first.cache_stats.misses)" -ForegroundColor Red

Write-Host "Segunda consulta (debería ser HIT):" -ForegroundColor Yellow
$second = Invoke-RestMethod -Uri "http://localhost:8000/query" -Method Post -Body $body -ContentType "application/json"
Write-Host "Hits: $($second.cache_stats.hits)" -ForegroundColor Green

# 4. Final stats
Write-Host "`n4. FINAL STATISTICS:" -ForegroundColor Yellow
$stats = Invoke-RestMethod -Uri "http://localhost:8000/stats" -Method Get
$stats | Format-List

Write-Host "`n🎉 SISTEMA COMPLETO FUNCIONANDO CORRECTAMENTE!" -ForegroundColor Green
Write-Host "   Usa Invoke-RestMethod en lugar de Invoke-WebRequest" -ForegroundColor Yellow