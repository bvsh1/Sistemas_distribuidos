# src/scoring/main.py
from flask import Flask, request, jsonify
import logging
import os
import json
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Resultados en memoria (no persisten)
evaluation_results = {}

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy', 
        'service': 'scoring-service',
        'version': '1.0',
        'storage': 'in-memory'
    })

@app.route('/evaluate/batch', methods=['POST'])
def evaluate_batch():
    """Endpoint para evaluación por lotes - resultados en memoria"""
    try:
        from batch_evaluator import BatchEvaluator
        
        data = request.get_json()
        if not data or 'qa_pairs' not in data:
            return jsonify({'error': 'Se requiere qa_pairs en el JSON'}), 400
        
        evaluator = BatchEvaluator()
        results = evaluator.evaluate_dataset(data['qa_pairs'])
        
        # Guardar en memoria (no en disco)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        evaluation_results[timestamp] = results
        
        return jsonify({
            'message': 'Evaluación completada',
            'results_id': timestamp,
            'results_summary': {
                'total_questions': results['total_questions'],
                'evaluated_questions': results['evaluated_questions'],
                'average_score': results['average_score'],
                'quality_distribution': results['quality_distribution']
            }
        })
        
    except Exception as e:
        logger.error(f"Error en evaluación por lotes: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/evaluate/single', methods=['POST'])
def evaluate_single():
    """Endpoint para evaluación individual"""
    try:
        from score_evaluator import ScoreEvaluator
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
            
        expected_answer = data.get('expected_answer', '')
        llm_answer = data.get('llm_answer', '')
        
        if not expected_answer or not llm_answer:
            return jsonify({'error': 'expected_answer y llm_answer son requeridos'}), 400
        
        evaluator = ScoreEvaluator()
        evaluation = evaluator.calculate_comprehensive_score(expected_answer, llm_answer)
        
        return jsonify({
            'expected_answer': expected_answer,
            'llm_answer': llm_answer,
            'evaluation': evaluation
        })
        
    except Exception as e:
        logger.error(f"Error en evaluación individual: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/evaluate/results/<result_id>', methods=['GET'])
def get_results(result_id):
    """Obtener resultados guardados en memoria"""
    if result_id in evaluation_results:
        return jsonify(evaluation_results[result_id])
    else:
        return jsonify({'error': 'Resultado no encontrado'}), 404

@app.route('/evaluate/results', methods=['GET'])
def list_results():
    """Listar todos los resultados en memoria"""
    return jsonify({
        'stored_results': list(evaluation_results.keys()),
        'total_evaluations': len(evaluation_results)
    })

if __name__ == '__main__':
    host = os.getenv('HOST', '0.0.0.0')
    port = int(os.getenv('SCORING_PORT', 8080))
    
    logger.info(f"Starting Scoring Service on {host}:{port}")
    logger.info("Storage: In-memory (non-persistent)")
    app.run(host=host, port=port, debug=False)