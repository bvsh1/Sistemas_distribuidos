from flask import Flask, request, jsonify
import logging
import requests
import os
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Configuración de Gemini
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
GEMINI_URL = "https://generativelanguage.googleapis.com/v1/models/gemini-2.0-flash:generateContent"

def query_gemini(question):
    try:
        if not GEMINI_API_KEY:
            return "Error: GEMINI_API_KEY not configured"
            
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
        
        logger.info(f"Sending question to Gemini: {question}")
        response = requests.post(url, json=body, headers={"Content-Type": "application/json"}, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        
        if (data.get('candidates') and 
            len(data['candidates']) > 0 and 
            data['candidates'][0].get('content') and
            data['candidates'][0]['content'].get('parts') and
            len(data['candidates'][0]['content']['parts']) > 0):
            
            answer = data['candidates'][0]['content']['parts'][0]['text']
            return answer
        else:
            logger.error("Unexpected response structure from Gemini")
            return "Error: Could not get response from model"
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Gemini connection error: {str(e)}")
        return f"Connection error: {str(e)}"
    except Exception as e:
        logger.error(f"Error processing Gemini response: {str(e)}")
        return f"Internal error: {str(e)}"

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
    try:
        if request.method == 'GET':
            return jsonify({
                'message': 'Use POST method with JSON body: {"question": "your question"}'
            })
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
            
        question = data.get('question', '')
        if not question:
            return jsonify({'error': 'Question is required'}), 400
        
        logger.info(f"Query received: {question}")
        
        if not GEMINI_API_KEY:
            logger.error("GEMINI_API_KEY not configured")
            return jsonify({
                'source': 'cache',
                'response': 'Response for: ' + question + ' [LLM service unavailable - API key missing]'
            }), 500
        
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

if __name__ == '__main__':
    if not GEMINI_API_KEY:
        logger.warning("GEMINI_API_KEY not found in environment variables")
    else:
        logger.info("GEMINI_API_KEY loaded successfully")
    
    host = os.getenv('HOST', '0.0.0.0')
    port = int(os.getenv('LLM_PORT', 5000))
    
    logger.info(f"Starting LLM Service on {host}:{port}")
    app.run(host=host, port=port, debug=False)