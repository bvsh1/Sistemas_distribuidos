from flask import Flask, request, jsonify
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

@app.route('/health', methods=['GET'])
def health_check():
    logger.info("Health check requested")
    return jsonify({
        'status': 'healthy', 
        'service': 'llm-service',
        'port': 5000
    })

@app.route('/generate', methods=['POST'])
def generate_response():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
            
        question = data.get('question', '')
        if not question:
            return jsonify({'error': 'Question is required'}), 400
        
        logger.info(f"Received question: {question}")
        
        # Respuesta mock simple
        response_text = f"Mock response for: {question}"
        
        return jsonify({
            'question': question,
            'response': response_text,
            'status': 'success',
            'service_type': 'mock'
        })
            
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    logger.info("Starting LLM Service on port 5000")
    app.run(host='0.0.0.0', port=5000, debug=False)