# src/cache-system/main.py
from flask import Flask, request, jsonify
import requests
import logging
import os
import time
import json
from cache import Cache, CachePolicy
from dotenv import load_dotenv

# Importar el evaluador de scores
import sys
sys.path.append('../scoring')
from score_evaluator import ScoreEvaluator

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Configuración
LLM_SERVICE_URL = os.getenv('LLM_SERVICE_URL', 'http://llm-service:5000')
CACHE_SIZE = int(os.getenv('CACHE_SIZE', 100000))
CACHE_POLICY = os.getenv('CACHE_POLICY', 'LRU')

# Inicializar cache y evaluador
policy_map = {
    'LRU': CachePolicy.LRU,
    'LFU': CachePolicy.LFU,
    'FIFO': CachePolicy.FIFO
}

try:
    cache_policy = policy_map.get(CACHE_POLICY.upper(), CachePolicy.LRU)
    cache = Cache(max_size=CACHE_SIZE, policy=cache_policy)
    score_evaluator = ScoreEvaluator()
    logger.info(f"Cache initialized with policy: {cache_policy.value}, size: {CACHE_SIZE}")
except Exception as e:
    logger.error(f"Error initializing cache: {e}")
    cache = Cache(max_size=CACHE_SIZE, policy=CachePolicy.LRU)
    score_evaluator = ScoreEvaluator()

# Cargar dataset de evaluación si existe
QA_DATASET = {}
try:
    with open('datasets/qa_evaluation_10000.json', 'r', encoding='utf-8') as f:
        qa_data = json.load(f)
        for item in qa_data:
            QA_DATASET[item['question']] = {
                'expected_answer': item['expected_answer'],
                'category': item['category'],
                'id': item['id']
            }
    logger.info(f"Loaded FULL QA evaluation dataset: {len(QA_DATASET)} pairs")
except FileNotFoundError:
    logger.warning("QA evaluation dataset not found, trying fallback dataset")
    try:
        with open('datasets/qa_evaluation.json', 'r', encoding='utf-8') as f:
            qa_data = json.load(f)
            for item in qa_data:
                QA_DATASET[item['question']] = {
                    'expected_answer': item['expected_answer'],
                    'category': item['category'],
                    'id': item['id']
                }
        logger.info(f"Loaded fallback QA dataset: {len(QA_DATASET)} pairs")
    except FileNotFoundError:
        logger.warning("No QA dataset available")
except Exception as e:
    logger.error(f"Error loading QA dataset: {e}")

def get_quality_grade(score):
    """Convertir score numérico a calificación cualitativa"""
    if score >= 0.8:
        return 'Excellent'
    elif score >= 0.6:
        return 'Good'
    elif score >= 0.4:
        return 'Fair'
    elif score >= 0.2:
        return 'Poor'
    else:
        return 'Very Poor'

def evaluate_response_quality(question, llm_response):
    """Evaluar la calidad de la respuesta del LLM comparando con respuesta esperada"""
    if question not in QA_DATASET:
        return {
            'evaluated': False,
            'reason': 'Question not in evaluation dataset'
        }
    
    qa_data = QA_DATASET[question]
    expected_answer = qa_data['expected_answer']
    evaluation = score_evaluator.calculate_comprehensive_score(expected_answer, llm_response)
    
    return {
        'evaluated': True,
        'expected_answer': expected_answer,
        'category': qa_data['category'],
        'question_id': qa_data['id'],
        'evaluation_metrics': evaluation,
        'quality_score': evaluation['comprehensive_score'],
        'quality_grade': get_quality_grade(evaluation['comprehensive_score'])
    }

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
            'cache_stats': stats,
            'evaluation_dataset_size': len(QA_DATASET)
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
                
                # Evaluar calidad de la respuesta (solo si es miss)
                quality_evaluation = evaluate_response_quality(question, response_text)
                
                # Guardar en cache
                cache.put(question, response_text)
                
                logger.info(f"LLM response time: {response_time:.2f}s")
                
                response_data = {
                    'source': 'llm',
                    'response': response_text,
                    'cache_hit': False,
                    'response_time': round(response_time, 2)
                }
                
                # Incluir evaluación de calidad si está disponible
                if quality_evaluation['evaluated']:
                    response_data['quality_evaluation'] = quality_evaluation
                    logger.info(f"Quality evaluation: {quality_evaluation['quality_score']:.3f} ({quality_evaluation['quality_grade']})")
                
                return jsonify(response_data)
            else:
                logger.error(f"LLM service error: {llm_response.status_code}")
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

@app.route('/evaluation/stats', methods=['GET'])
def evaluation_stats():
    """Endpoint para obtener estadísticas de evaluación"""
    try:
        # Calcular algunas estadísticas básicas
        evaluated_count = 0
        quality_scores = []
        
        # En una implementación real, aquí almacenarías las evaluaciones históricas
        # Por ahora retornamos estadísticas básicas del dataset
        
        return jsonify({
            'evaluation_dataset_size': len(QA_DATASET),
            'evaluated_questions': evaluated_count,
            'average_quality_score': sum(quality_scores) / len(quality_scores) if quality_scores else 0,
            'message': 'Evaluation system active'
        })
    except Exception as e:
        logger.error(f"Error getting evaluation stats: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/evaluation/results', methods=['GET'])
def evaluation_results():
    """Endpoint para obtener resultados de evaluación detallados"""
    try:
        # En una implementación completa, aquí retornarías evaluaciones almacenadas
        sample_evaluations = []
        
        # Ejemplo de estructura de datos de evaluación
        return jsonify({
            'total_evaluations': len(sample_evaluations),
            'evaluations': sample_evaluations,
            'message': 'Evaluation results endpoint'
        })
    except Exception as e:
        logger.error(f"Error getting evaluation results: {e}")
        return jsonify({'error': str(e)}), 500

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

@app.route('/evaluation/test', methods=['POST'])
def test_evaluation():
    """Endpoint para probar el sistema de evaluación con una pregunta específica"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
            
        question = data.get('question', '').strip()
        test_response = data.get('test_response', '').strip()
        
        if not question or not test_response:
            return jsonify({'error': 'Question and test_response are required'}), 400
        
        # Evaluar la respuesta de prueba
        evaluation = evaluate_response_quality(question, test_response)
        
        return jsonify({
            'question': question,
            'test_response': test_response,
            'evaluation': evaluation
        })
        
    except Exception as e:
        logger.error(f"Error in test evaluation: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    host = os.getenv('HOST', '0.0.0.0')
    port = int(os.getenv('CACHE_PORT', 8000))
    
    logger.info(f"Starting Cache Service on {host}:{port}")
    logger.info(f"Cache policy: {CACHE_POLICY}, Size: {CACHE_SIZE}")
    logger.info(f"LLM Service URL: {LLM_SERVICE_URL}")
    logger.info(f"Quality evaluation: {'ENABLED' if QA_DATASET else 'DISABLED'}")
    
    app.run(host=host, port=port, debug=False)