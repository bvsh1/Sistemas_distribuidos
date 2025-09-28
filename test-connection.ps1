# Probar una pregunta nueva (debería llamar al LLM)
$body = @{question = "What is the capital of France?"} | ConvertTo-Json
$response = Invoke-RestMethod -Uri "http://localhost:8000/query" -Method Post -Body $body -ContentType "application/json"

Write-Host "Fuente: $($response.source)"  # Debería decir 'llm'
Write-Host "Respuesta: $($response.response)"  # Debería ser respuesta del LLM