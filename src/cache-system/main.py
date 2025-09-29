from flask import Flask, request, jsonify
import os
import logging

app = Flask(__name__)

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuracion
CACHE_POLICY = os.getenv('CACHE_POLICY', 'lru')
CACHE_SIZE = int(os.getenv('CACHE_SIZE', '1000'))
LLM_SERVICE_URL = os.getenv('LLM_SERVICE_URL', 'http://localhost:5000')

# Importar requests con manejo de errores
try:
    import requests
    requests_available = True
    logger.info("Requests library imported successfully")
except ImportError:
    requests_available = False
    logger.error("Requests library not available")

# Importar cache con manejo de errores
try:
    from cache import CacheFactory, CachePolicy
    cache = CacheFactory.create_cache(policy=CACHE_POLICY, max_size=CACHE_SIZE)
    logger.info("Cache initialized successfully")
except Exception as e:
    logger.error("Error initializing cache: %s", e)
    # Crear un cache mock como fallback
    class MockCache:
        def get(self, key): 
            return None
        def set(self, key, value): 
            pass
        def stats(self): 
            return {'hits': 0, 'misses': 0, 'hit_rate': 0, 'size': 0}
    cache = MockCache()

def call_llm_service(question):
    """Llamar al servicio LLM para obtener respuesta real"""
    if not requests_available:
        return {"error": "Requests library not available"}
    
    try:
        logger.info("Calling LLM service: %s...", question[:50])
        
        response = requests.post(
            f"{LLM_SERVICE_URL}/generate",
            json={"question": question},
            timeout=30
        )
        
        if response.status_code == 200:
            logger.info("LLM service responded successfully")
            return response.json()
        else:
            logger.error("LLM service error: %s", response.status_code)
            return {"error": f"LLM service returned {response.status_code}"}
            
    except Exception as e:
        logger.error("Error calling LLM service: %s", str(e))
        return {"error": str(e)}

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'service': 'cache-service',
        'policy': CACHE_POLICY
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
        
        logger.info("Received question: %s...", question[:50])
        
        # 1. Verificar cache
        cached_response = cache.get(question)
        if cached_response:
            logger.info("Cache HIT for: %s...", question[:30])
            return jsonify({
                'question': question,
                'response': cached_response.get('response', ''),
                'source': 'cache',
                'cache_stats': cache.stats()
            })
        
        logger.info("Cache MISS for: %s...", question[:30])
        
        # 2. Si no esta en cache, llamar a LLM
        llm_response = call_llm_service(question)
        
        if 'error' in llm_response:
            # Si falla el LLM, devolver respuesta mock
            mock_response = f"Response for: {question} [LLM service unavailable]"
            cache.set(question, {'response': mock_response})
            return jsonify({
                'question': question,
                'response': mock_response,
                'source': 'fallback',
                'cache_stats': cache.stats()
            })
        
        # 3. Guardar en cache
        cache.set(question, {'response': llm_response.get('response', '')})
        
        # 4. Devolver respuesta
        return jsonify({
            'question': question,
            'response': llm_response.get('response', ''),
            'source': 'llm',
            'cache_stats': cache.stats()
        })
        
    except Exception as e:
        logger.error("Error in handle_query: %s", str(e))
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/stats', methods=['GET'])
def get_stats():
    return jsonify(cache.stats())

if __name__ == '__main__':
    logger.info("Starting Cache Service with %s policy", CACHE_POLICY)
    app.run(host='0.0.0.0', port=8000, debug=False)
