# Script de preprocesamiento - Versión simplificada sin pandas
Write-Host "Procesando dataset..." -ForegroundColor Green

# Verificar si existe el dataset
$datasetFile = "datasets\sample_yahoo_answers.csv"
if (!(Test-Path $datasetFile)) {
    Write-Host "No se encontro el dataset. Ejecuta download_dataset_fallback.ps1 primero" -ForegroundColor Red
    exit 1
}

Write-Host "Leyendo dataset..." -ForegroundColor Yellow
$csvContent = Get-Content $datasetFile

# Obtener preguntas de la segunda columna (question_title)
$questions = @()
foreach ($line in $csvContent[1..($csvContent.Length-1)]) {  # Saltar header
    $columns = $line -split ','
    if ($columns.Length -ge 2) {
        $questions += $columns[1]  # question_title es la segunda columna
    }
}

Write-Host "Encontradas $($questions.Length) preguntas" -ForegroundColor Green

# Crear array de preguntas para el generador de trafico
$sampleQuestions = @()
if ($questions.Length -gt 0) {
    # Usar las primeras 20 preguntas o todas si hay menos
    $count = [Math]::Min(20, $questions.Length)
    $sampleQuestions = $questions[0..($count-1)]
} else {
    # Preguntas por defecto si no se pudieron extraer
    $sampleQuestions = @(
        "What is Python?",
        "How to learn programming?",
        "What is Docker?",
        "What is machine learning?",
        "What is distributed systems?",
        "What is cloud computing?",
        "How to deploy applications?",
        "What is an API?",
        "Best programming practices?",
        "How to improve coding skills?"
    )
}

# Guardar como JSON
$jsonContent = $sampleQuestions | ConvertTo-Json
$jsonContent | Out-File -FilePath "datasets\sample_questions.json" -Encoding UTF8

Write-Host "Preguntas guardadas en datasets\sample_questions.json" -ForegroundColor Green
Write-Host "Cantidad: $($sampleQuestions.Length) preguntas" -ForegroundColor Green

# Mostrar algunas preguntas
Write-Host "Primeras 5 preguntas:" -ForegroundColor Yellow
for ($i = 0; $i -lt [Math]::Min(5, $sampleQuestions.Length); $i++) {
    Write-Host "  $($i+1). $($sampleQuestions[$i])"
}