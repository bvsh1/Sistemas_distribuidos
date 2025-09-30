# test-connection.ps1 (modificado para puerto 5000)
$body = @{question = "What is the capital of France?"} | ConvertTo-Json
$response = Invoke-RestMethod -Uri "http://localhost:5000/query" -Method Post -Body $body -ContentType "application/json"

Write-Host "Fuente: $($response.source)"  # Ahora dirá 'llm'
Write-Host "Respuesta: $($response.response)"  # Respuesta real de Gemini