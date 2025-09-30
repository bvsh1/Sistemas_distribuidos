from flask import Flask, request, jsonify
import requests
import logging
import os
import time
from cache import Cache, CachePolicy
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Configuración
LLM_SERVICE_URL = os.getenv('LLM_SERVICE_URL', 'http://llm-service:5000')
CACHE_SIZE = int(os.getenv('CACHE_SIZE', 100))
CACHE_POLICY = os.getenv('CACHE_POLICY', 'LRU')

# Mapear string a enum de política de cache
policy_map = {
    'LRU': CachePolicy.LRU,
    'LFU': CachePolicy.LFU,
    'FIFO': CachePolicy.FIFO
}

try:
    cache_policy = policy_map.get(CACHE_POLICY.upper(), CachePolicy.LRU)
    cache = Cache(max_size=CACHE_SIZE, policy=cache_policy)
    logger.info(f"Cache initialized with policy: {cache_policy.value}, size: {CACHE_SIZE}")
except Exception as e:
    logger.error(f"Error initializing cache: {e}")
    cache = Cache(max_size=CACHE_SIZE, policy=CachePolicy.LRU)

@app.route('/health', methods=['GET'])
def health_check():
    logger.info("Health check requested")
    try:
        stats = cache.get_stats()
        return jsonify({
            'status': 'healthy',
            'service': 'cache-service',
            'cache_size': CACHE_SIZE,
            'cache_policy': CACHE_POLICY,
            'cache_stats': stats
        })
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return jsonify({
            'status': 'error',
            'service': 'cache-service',
            'error': str(e)
        }), 500

@app.route('/query', methods=['POST'])
def query():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
            
        question = data.get('question', '').strip()
        if not question:
            return jsonify({'error': 'Question is required'}), 400
        
        logger.info(f"Received question: {question}")
        
        # Verificar si está en cache
        cached_response = cache.get(question)
        if cached_response:
            logger.info(f"Cache HIT for question: {question}")
            return jsonify({
                'source': 'cache',
                'response': cached_response,
                'cache_hit': True
            })
        
        logger.info(f"Cache MISS for question: {question}")
        
        # Consultar al LLM service
        try:
            start_time = time.time()
            llm_response = requests.post(
                f"{LLM_SERVICE_URL}/query",
                json={'question': question},
                timeout=30
            )
            response_time = time.time() - start_time
            
            if llm_response.status_code == 200:
                llm_data = llm_response.json()
                response_text = llm_data.get('response', '')
                
                # Guardar en cache
                cache.put(question, response_text)
                
                logger.info(f"LLM response time: {response_time:.2f}s")
                
                return jsonify({
                    'source': 'llm',
                    'response': response_text,
                    'cache_hit': False,
                    'response_time': round(response_time, 2)
                })
            else:
                logger.error(f"LLM service error: {llm_response.status_code} - {llm_response.text}")
                return jsonify({
                    'source': 'error',
                    'response': f'Error: LLM service returned {llm_response.status_code}',
                    'cache_hit': False
                }), 500
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Error connecting to LLM service: {e}")
            return jsonify({
                'source': 'error',
                'response': f'Error: Could not connect to LLM service - {str(e)}',
                'cache_hit': False
            }), 500
            
    except Exception as e:
        logger.error(f"Error in /query: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/cache/stats', methods=['GET'])
def cache_stats():
    try:
        stats = cache.get_stats()
        return jsonify(stats)
    except Exception as e:
        logger.error(f"Error getting cache stats: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/cache/clear', methods=['POST'])
def clear_cache():
    try:
        cache.clear()
        logger.info("Cache cleared")
        return jsonify({'message': 'Cache cleared successfully'})
    except Exception as e:
        logger.error(f"Error clearing cache: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/cache/items', methods=['GET'])
def cache_items():
    try:
        items = cache.get_items()
        return jsonify({
            'total_items': len(items),
            'items': items
        })
    except Exception as e:
        logger.error(f"Error getting cache items: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    host = os.getenv('HOST', '0.0.0.0')
    port = int(os.getenv('CACHE_PORT', 8000))
    
    logger.info(f"Starting Cache Service on {host}:{port}")
    logger.info(f"Cache policy: {CACHE_POLICY}, Size: {CACHE_SIZE}")
    logger.info(f"LLM Service URL: {LLM_SERVICE_URL}")
    
    app.run(host=host, port=port, debug=False)