from flask import Flask, request, jsonify
import logging
import requests
import os
from dotenv import load_dotenv

# Cargar variables del entorno
load_dotenv()

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Configuración de Gemini
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
GEMINI_URL = "https://generativelanguage.googleapis.com/v1/models/gemini-2.0-flash:generateContent"

def query_gemini(question):
    """Función para consultar la API de Gemini"""
    try:
        url = f"{GEMINI_URL}?key={GEMINI_API_KEY}"
        
        body = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": question
                        }
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.3,
                "maxOutputTokens": 500,
                "topP": 0.8
            }
        }
        
        logger.info(f"Enviando pregunta a Gemini: {question}")
        response = requests.post(url, json=body, headers={"Content-Type": "application/json"}, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        
        # Extraer la respuesta de Gemini
        if (data.get('candidates') and 
            len(data['candidates']) > 0 and 
            data['candidates'][0].get('content') and
            data['candidates'][0]['content'].get('parts') and
            len(data['candidates'][0]['content']['parts']) > 0):
            
            answer = data['candidates'][0]['content']['parts'][0]['text']
            return answer
        else:
            logger.error("Estructura de respuesta inesperada de Gemini")
            return "Error: No se pudo obtener respuesta del modelo"
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Error de conexión con Gemini: {str(e)}")
        return f"Error de conexión: {str(e)}"
    except Exception as e:
        logger.error(f"Error procesando respuesta de Gemini: {str(e)}")
        return f"Error interno: {str(e)}"

@app.route('/health', methods=['GET'])
def health_check():
    logger.info("Health check requested")
    return jsonify({
        'status': 'healthy', 
        'service': 'llm-service',
        'port': 5000,
        'llm_provider': 'gemini',
        'model': 'gemini-2.0-flash'
    })

@app.route('/query', methods=['POST', 'GET'])
def query():
    """Endpoint principal para consultas"""
    try:
        if request.method == 'GET':
            return jsonify({
                'message': 'Use POST method with JSON body: {"question": "your question"}',
                'example': 'curl -X POST http://localhost:5000/query -H "Content-Type: application/json" -d "{\"question\": \"What is AI?\"}"'
            })
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
            
        question = data.get('question', '')
        if not question:
            return jsonify({'error': 'Question is required'}), 400
        
        logger.info(f"Query received: {question}")
        
        # Verificar API key
        if not GEMINI_API_KEY:
            logger.error("GEMINI_API_KEY no configurada")
            return jsonify({
                'source': 'cache',
                'response': 'Response for: ' + question + ' [LLM service unavailable - API key missing]'
            }), 500
        
        # Consultar Gemini
        response_text = query_gemini(question)
        
        return jsonify({
            'source': 'llm',
            'response': response_text
        })
            
    except Exception as e:
        logger.error(f"Error in /query: {str(e)}")
        return jsonify({
            'source': 'cache',
            'response': f'Response for: {question if "question" in locals() else "unknown"} [LLM service error: {str(e)}]'
        }), 500

@app.route('/generate', methods=['POST'])
def generate_response():
    """Endpoint alternativo"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
            
        question = data.get('question', '')
        if not question:
            return jsonify({'error': 'Question is required'}), 400
        
        logger.info(f"Generate received: {question}")
        
        # Verificar que tenemos la API key
        if not GEMINI_API_KEY:
            return jsonify({
                'question': question,
                'response': "Error: API key no configurada",
                'status': 'error',
                'service_type': 'gemini'
            }), 500
        
        # Consultar Gemini
        response_text = query_gemini(question)
        
        return jsonify({
            'question': question,
            'response': response_text,
            'status': 'success',
            'service_type': 'gemini',
            'model': 'gemini-2.0-flash'
        })
            
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    # Verificar configuración al iniciar
    if not GEMINI_API_KEY:
        logger.warning("GEMINI_API_KEY no encontrada en variables de entorno")
    else:
        logger.info("GEMINI_API_KEY cargada correctamente")
    
    logger.info("Starting LLM Service with Gemini integration on port 5000")
    print("=== Servicio Flask iniciado ===")
    print("URL: http://localhost:5000")
    print("Endpoints disponibles:")
    print("  GET  http://localhost:5000/health")
    print("  POST http://localhost:5000/query")
    print("  POST http://localhost:5000/generate")
    print("===============================")
    
    app.run(host='0.0.0.0', port=5000, debug=False)