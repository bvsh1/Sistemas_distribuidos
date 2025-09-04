from flask import Flask, request, jsonify
import os
import sys

# Agregar el path para importar módulos locales
sys.path.append('/app')

try:
    from services.gemini_service import gemini_service
    print("✅ Gemini service imported successfully")
except ImportError as e:
    print(f"❌ Import error: {e}")
    # Crear un servicio mock para testing
    class MockGeminiService:
        def generate_response(self, question):
            return f"Respuesta mock para: {question}"
    gemini_service = MockGeminiService()

app = Flask(__name__)

@app.route('/health', methods=['GET'])
def health_check():
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
        
        print(f"Received question: {question[:50]}...")
        
        response = gemini_service.generate_response(question)
        
        if response:
            return jsonify({
                'question': question,
                'response': response,
                'status': 'success'
            })
        else:
            return jsonify({'error': 'Failed to generate response'}), 500
            
    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("Starting LLM Service on port 5000...")
    app.run(host='0.0.0.0', port=5000, debug=False)