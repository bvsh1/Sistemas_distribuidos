from flask import Flask, request, jsonify
import os
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Servicio mock para cuando Gemini no está disponible
class MockGeminiService:
    def __init__(self):
        self.responses = {
            "python": "Python es un lenguaje de programación interpretado de alto nivel, conocido por su sintaxis clara y legible. Se usa en desarrollo web, ciencia de datos e IA.",
            "docker": "Docker es una plataforma de contenedorización que permite empaquetar aplicaciones y sus dependencias en contenedores portables.",
            "machine learning": "Machine learning es una rama de la IA que desarrolla sistemas que pueden aprender de datos y mejorar su rendimiento automáticamente.",
            "distributed systems": "Un sistema distribuido es un conjunto de computadoras independientes que aparecen como un sistema único para los usuarios."
        }
    
    def generate_response(self, question):
        question_lower = question.lower()
        for key, response in self.responses.items():
            if key in question_lower:
                return response
        return f"Respuesta simulada para: {question}. Este es un servicio mock para desarrollo."

# Intentar importar el servicio real de Gemini
try:
    from services.gemini_service import gemini_service
    logger.info("Gemini service imported successfully")
except ImportError as e:
    logger.warning(f"Using mock service - Import failed: {e}")
    gemini_service = MockGeminiService()
except Exception as e:
    logger.warning(f"Using mock service - Configuration failed: {e}")
    gemini_service = MockGeminiService()

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy', 
        'service': 'llm-service',
        'port': 5000,
        'version': '1.0'
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
        
        logger.info(f"Received question: {question[:50]}...")
        
        response = gemini_service.generate_response(question)
        
        return jsonify({
            'question': question,
            'response': response,
            'status': 'success'
        })
            
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    logger.info("Starting LLM Service on port 5000...")
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)