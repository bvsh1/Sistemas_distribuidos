# test_cache_with_dataset.ps1
Write-Host "=== PRUEBA DEL SISTEMA DE CACHE CON DATASET REAL ===" -ForegroundColor Green

# 1. Verificar servicios
Write-Host "`n1. Verificando servicios..." -ForegroundColor Yellow

try {
    $llmHealth = Invoke-RestMethod -Uri "http://localhost:5000/health" -Method Get -ErrorAction Stop
    Write-Host "   LLM Service: $($llmHealth.status)" -ForegroundColor Green
} catch {
    Write-Host "   LLM Service: OFFLINE - Iniciando servicios..." -ForegroundColor Red
    docker-compose up -d
    Start-Sleep 15
}

try {
    $cacheHealth = Invoke-RestMethod -Uri "http://localhost:8000/health" -Method Get -ErrorAction Stop
    Write-Host "   Cache Service: $($cacheHealth.status)" -ForegroundColor Green
    Write-Host "   Cache Policy: $($cacheHealth.cache_policy)" -ForegroundColor White
    Write-Host "   Cache Size: $($cacheHealth.cache_size)" -ForegroundColor White
} catch {
    Write-Host "   Cache Service: OFFLINE" -ForegroundColor Red
    exit 1
}

# 2. Limpiar cache antes de la prueba
Write-Host "`n2. Limpiando cache..." -ForegroundColor Yellow
try {
    Invoke-RestMethod -Uri "http://localhost:8000/cache/clear" -Method Post -ErrorAction Stop
    Write-Host "   Cache limpiado" -ForegroundColor Green
} catch {
    Write-Host "   Error limpiando cache: $($_.Exception.Message)" -ForegroundColor Red
}

# 3. Estadísticas iniciales
Write-Host "`n3. Estadísticas iniciales del cache:" -ForegroundColor Yellow
try {
    $initialStats = Invoke-RestMethod -Uri "http://localhost:8000/cache/stats" -Method Get -ErrorAction Stop
    Write-Host "   Hits: $($initialStats.hits)" -ForegroundColor White
    Write-Host "   Misses: $($initialStats.misses)" -ForegroundColor White
    Write-Host "   Hit Rate: $([math]::Round($initialStats.hit_rate * 100, 2))%" -ForegroundColor White
} catch {
    Write-Host "   Error obteniendo estadísticas: $($_.Exception.Message)" -ForegroundColor Red
}

# 4. Ejecutar traffic-generator con el dataset
Write-Host "`n4. Ejecutando Traffic Generator con dataset real..." -ForegroundColor Yellow
docker-compose run --rm traffic-generator python main.py `
    --dataset datasets/yahoo_questions.json `
    --distribution poisson `
    --rate 3.0 `
    --duration 60 `
    --max-questions 50

# 5. Estadísticas finales del cache
Write-Host "`n5. Estadísticas finales del cache:" -ForegroundColor Yellow
Start-Sleep 5  # Esperar a que se completen las requests

try {
    $finalStats = Invoke-RestMethod -Uri "http://localhost:8000/cache/stats" -Method Get -ErrorAction Stop
    Write-Host "   Hits: $($finalStats.hits)" -ForegroundColor White
    Write-Host "   Misses: $($finalStats.misses)" -ForegroundColor White
    Write-Host "   Hit Rate: $([math]::Round($finalStats.hit_rate * 100, 2))%" -ForegroundColor White
    Write-Host "   Total Requests: $($finalStats.total_requests)" -ForegroundColor White
    Write-Host "   Cache Size: $($finalStats.current_size)/$($finalStats.max_size)" -ForegroundColor White
    
    # Calcular eficiencia
    if ($finalStats.total_requests -gt 0) {
        $efficiency = [math]::Round(($finalStats.hits / $finalStats.total_requests) * 100, 2)
        Write-Host "   Eficiencia del cache: $efficiency%" -ForegroundColor Cyan
    }
} catch {
    Write-Host "   Error obteniendo estadísticas finales: $($_.Exception.Message)" -ForegroundColor Red
}

# 6. Mostrar algunos items en cache
Write-Host "`n6. Items en cache (primeros 5):" -ForegroundColor Yellow
try {
    $cacheItems = Invoke-RestMethod -Uri "http://localhost:8000/cache/items" -Method Get -ErrorAction Stop
    if ($cacheItems.items.Count -gt 0) {
        $cacheItems.items[0..4] | ForEach-Object { 
            Write-Host "   - $($_.key) (accesos: $($_.access_count))" -ForegroundColor White 
        }
        Write-Host "   Total items en cache: $($cacheItems.total_items)" -ForegroundColor White
    } else {
        Write-Host "   Cache vacío" -ForegroundColor Gray
    }
} catch {
    Write-Host "   Error obteniendo items del cache: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "`n=== PRUEBA COMPLETADA ===" -ForegroundColor Green