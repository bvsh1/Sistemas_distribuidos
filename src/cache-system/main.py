from flask import Flask, request, jsonify
import os
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

CACHE_POLICY = os.getenv('CACHE_POLICY', 'lru')

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy', 'service': 'cache-service'})

@app.route('/query', methods=['POST'])
def handle_query():
    try:
        data = request.get_json()
        question = data.get('question', 'test question')
        
        # Respuesta mock simple - sin llamar a LLM por ahora
        return jsonify({
            'question': question,
            'response': f"Mock response for: {question}",
            'source': 'cache',
            'cache_stats': {'hits': 0, 'misses': 1, 'hit_rate': 0}
        })
        
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/stats', methods=['GET'])
def get_stats():
    return jsonify({'hits': 0, 'misses': 0, 'hit_rate': 0})

if __name__ == '__main__':
    logger.info("Starting Cache Service")
    app.run(host='0.0.0.0', port=8000, debug=False)