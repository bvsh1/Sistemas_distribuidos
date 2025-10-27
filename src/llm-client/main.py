from flask import Flask, request, jsonify
import logging
import requests
import os
from dotenv import load_dotenv

load_dotenv()

# --- Configuración de Logging ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)

# --- Configuración de Gemini ---
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"

def call_gemini_api(question: str) -> requests.Response:
    """
    Función interna que realiza la llamada a la API de Gemini.
    Devuelve el objeto de respuesta completo para que el llamador
    pueda inspeccionar el status_code y el JSON.
    """
    if not GEMINI_API_KEY:
        # Si la API Key no está, no podemos hacer nada. Lanzamos una excepción.
        raise ValueError("Error: GEMINI_API_KEY no está configurada.")

    url = f"{GEMINI_URL}?key={GEMINI_API_KEY}"
    
    body = {
        "contents": [{"parts": [{"text": question}]}],
        "generationConfig": {
            "temperature": 0.3,
            "maxOutputTokens": 500,
            "topP": 0.8
        }
    }
    
    logger.info(f"Enviando pregunta a Gemini: {question[:50]}...")
    # Realizamos la llamada y devolvemos la respuesta directamente
    response = requests.post(url, json=body, headers={"Content-Type": "application/json"}, timeout=45)
    return response

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy', 
        'service': 'llm-service',
        'llm_provider': 'gemini',
        'model': 'gemini-1.5-flash'
    })

@app.route('/query', methods=['POST'])
def query():
    try:
        data = request.get_json()
        if not data or 'question' not in data:
            return jsonify({'error': 'La pregunta es requerida en el JSON body'}), 400
        
        question = data['question']
        logger.info(f"Query recibido: {question[:50]}...")
        
        # Llamamos a nuestra función interna
        gemini_response = call_gemini_api(question)
        
        # Propagamos el error si la API de Gemini falló.
        # Esto es CLAVE para que el consumidor de Kafka sepa qué hacer.
        gemini_response.raise_for_status()
        
        response_data = gemini_response.json()
        
        # Extraemos la respuesta del LLM del JSON
        if (response_data.get('candidates') and 
            response_data['candidates'][0].get('content') and
            response_data['candidates'][0]['content'].get('parts')):
            
            answer = response_data['candidates'][0]['content']['parts'][0]['text']
            return jsonify({'source': 'llm', 'response': answer}), 200
        else:
            logger.error("Estructura de respuesta inesperada de Gemini")
            return jsonify({'error': 'No se pudo obtener una respuesta del modelo'}), 500

    except ValueError as ve:
        logger.error(f"Error de configuración: {str(ve)}")
        return jsonify({'error': str(ve)}), 500
    except requests.exceptions.HTTPError as http_err:
        # Si gemini_response.raise_for_status() falla, entramos aquí.
        # Devolvemos el mismo error que nos dio Gemini.
        status_code = http_err.response.status_code
        logger.warning(f"Error HTTP {status_code} de la API de Gemini.")
        return jsonify({'error': f'Error de la API de Gemini: {http_err.response.text}'}), status_code
    except requests.exceptions.RequestException as req_err:
        logger.error(f"Error de conexión con Gemini: {str(req_err)}")
        return jsonify({'error': f'Error de conexión: {str(req_err)}'}), 503 # Service Unavailable
    except Exception as e:
        logger.error(f"Error inesperado en /query: {str(e)}")
        return jsonify({'error': f'Error interno del servicio: {str(e)}'}), 500

if __name__ == '__main__':
    if not GEMINI_API_KEY:
        logger.warning("GEMINI_API_KEY no encontrada en las variables de entorno.")
    else:
        logger.info("GEMINI_API_KEY cargada exitosamente.")
    
    app.run(host='0.0.0.0', port=5000, debug=False)
