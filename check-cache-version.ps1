Write-Host "VERIFICANDO VERSION DEL CACHE SERVICE" -ForegroundColor Green

# Verificar qué código está corriendo
Write-Host "Buscando 'Mock response' en el código ejecutándose..." -ForegroundColor Yellow
$result = docker-compose exec cache-service python -c "
import sys
try:
    with open('/app/main.py', 'r') as f:
        content = f.read()
        if 'Mock response' in content:
            print('❌ VERSION ANTIGUA - Todavía tiene Mock response')
        else:
            print('✅ VERSION CORRECTA - No tiene Mock response')
            
        # Buscar la función call_llm_service
        if 'def call_llm_service' in content:
            print('✅ Función call_llm_service encontrada')
        else:
            print('❌ Función call_llm_service NO encontrada')
            
except Exception as e:
    print(f'Error: {e}')
"
$result