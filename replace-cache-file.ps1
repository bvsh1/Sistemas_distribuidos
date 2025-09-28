Write-Host "REEMPLAZANDO ARCHIVO COMPLETO DEL CACHE SERVICE" -ForegroundColor Green

# 1. Parar el servicio
docker-compose stop cache-service

# 2. Crear el archivo corregido
$correctCode = @"
from flask import Flask, request, jsonify
import requests
import os
import logging
from cache import CacheFactory, CachePolicy

app = Flask(__name__)

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuración
CACHE_POLICY = os.getenv('CACHE_POLICY', 'lru')
CACHE_SIZE = int(os.getenv('CACHE_SIZE', '1000'))
CACHE_TTL = int(os.getenv('CACHE_TTL', '3600'))
LLM_SERVICE_URL = os.getenv('LLM_SERVICE_URL', 'http://llm-service:5000')

# Inicializar caché
cache = CacheFactory.create_cache(
    policy=CACHE_POLICY,
    max_size=CACHE_SIZE,
    ttl=CACHE_TTL
)

def call_llm_service(question: str) -> dict:
    \"\"\"Llamar al servicio LLM para obtener respuesta real\"\"\"
    try:
        logger.info(f\"Calling LLM service: {question[:50]}...\")
        
        response = requests.post(
            f\"{LLM_SERVICE_URL}/generate\",
            json={\"question\": question},
            timeout=30
        )
        
        if response.status_code == 200:
            logger.info(\"LLM service responded successfully\")
            return response.json()
        else:
            logger.error(f\"LLM service error: {response.status_code}\")
            return {\"error\": f\"LLM service returned {response.status_code}\"}
            
    except requests.exceptions.ConnectionError:
        logger.error(\"Cannot connect to LLM service\")
        return {\"error\": \"LLM service unavailable\"}
    except requests.exceptions.Timeout:
        logger.error(\"LLM service timeout\")
        return {\"error\": \"LLM service timeout\"}
    except Exception as e:
        logger.error(f\"Error calling LLM service: {str(e)}\")
        return {\"error\": str(e)}

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'service': 'cache-service',
        'policy': CACHE_POLICY,
        'cache_stats': cache.stats()
    })

@app.route('/query', methods=['POST'])
def handle_query():
    try:
        data = request.get_json()
        if not data or 'question' not in data:
            return jsonify({'error': 'Question is required'}), 400
            
        question = data.get('question', '')
        if not question:
            return jsonify({'error': 'Question cannot be empty'}), 400
        
        logger.info(f\"Received question: {question[:50]}...\")
        
        # 1. Verificar caché
        cached_response = cache.get(question)
        if cached_response:
            logger.info(f\"Cache HIT for: {question[:30]}...\")
            response_data = {
                'question': question,
                'response': cached_response.get('response', ''),
                'source': 'cache',
                'service_type': cached_response.get('service_type', 'unknown'),
                'cache_stats': cache.stats()
            }
            return jsonify(response_data)
        
        logger.info(f\"Cache MISS for: {question[:30]}...\")
        
        # 2. Si no está en caché, llamar a LLM
        llm_response = call_llm_service(question)
        
        if 'error' in llm_response:
            logger.error(f\"LLM service failed: {llm_response['error']}\")
            return jsonify({'error': 'Failed to generate response'}), 500
        
        # 3. Guardar en caché
        cache_item = {
            'response': llm_response.get('response', ''),
            'service_type': llm_response.get('service_type', 'unknown')
        }
        cache.set(question, cache_item)
        
        # 4. Devolver respuesta
        response_data = {
            'question': question,
            'response': llm_response.get('response', ''),
            'source': 'llm',
            'service_type': llm_response.get('service_type', 'unknown'),
            'cache_stats': cache.stats()
        }
        
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f\"Error in handle_query: {str(e)}\")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/stats', methods=['GET'])
def get_stats():
    return jsonify(cache.stats())

@app.route('/reset', methods=['POST'])
def reset_cache():
    global cache
    cache = CacheFactory.create_cache(
        policy=CACHE_POLICY,
        max_size=CACHE_SIZE,
        ttl=CACHE_TTL
    )
    return jsonify({'message': 'Cache reset successfully'})

@app.route('/config', methods=['GET'])
def get_config():
    return jsonify({
        'policy': CACHE_POLICY,
        'max_size': CACHE_SIZE,
        'ttl': CACHE_TTL,
        'llm_service_url': LLM_SERVICE_URL
    })

if __name__ == '__main__':
    logger.info(f\"Starting Cache Service with {CACHE_POLICY.upper()} policy\")
    logger.info(f\"Cache size: {CACHE_SIZE}, TTL: {CACHE_TTL}s\")
    logger.info(f\"LLM Service URL: {LLM_SERVICE_URL}\")
    app.run(host='0.0.0.0', port=8000, debug=False, threaded=True)
"@

# Guardar el archivo corregido
$correctCode | Out-File -FilePath "src/cache-system/main.py" -Encoding UTF8

Write-Host "✅ Archivo reemplazado correctamente" -ForegroundColor Green

# 3. Reconstruir
Write-Host "Reconstruyendo servicio..." -ForegroundColor Yellow
docker-compose build cache-service

# 4. Iniciar
Write-Host "Iniciando servicio..." -ForegroundColor Yellow
docker-compose up -d cache-service

# 5. Verificar
Write-Host "Verificando versión corregida..." -ForegroundColor Yellow
Start-Sleep -Seconds 3

# Verificar que ahora tiene la función
docker-compose exec cache-service python -c "
import sys
try:
    with open('/app/main.py', 'r') as f:
        content = f.read()
        if 'def call_llm_service' in content:
            print('✅ VERSION CORRECTA - Función call_llm_service encontrada')
        else:
            print('❌ PROBLEMA - Función call_llm_service NO encontrada')
            
        if 'import requests' in content:
            print('✅ requests importado correctamente')
        else:
            print('❌ requests NO importado')
            
except Exception as e:
    print(f'Error: {e}')
"

Write-Host "`n🎉 Corrección completada. Ahora prueba el sistema:" -ForegroundColor Green
Write-Host ".\test-connection.ps1" -ForegroundColor Yellow