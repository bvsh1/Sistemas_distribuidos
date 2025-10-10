# src/storage/main.py
from flask import Flask, request, jsonify
import logging
import os
from models import StorageManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Inicializar gestor de almacenamiento
storage = StorageManager()

@app.route('/health', methods=['GET'])
def health_check():
    stats = storage.get_stats()
    return jsonify({
        'status': 'healthy',
        'service': 'storage-service',
        'storage_stats': stats
    })

@app.route('/storage/save', methods=['POST'])
def save_qa_record():
    """Endpoint para guardar/actualizar registros QA"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        required_fields = ['question', 'expected_answer', 'llm_answer', 'quality_metrics']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        success = storage.save_qa_record(
            question=data['question'],
            expected_answer=data['expected_answer'],
            llm_answer=data['llm_answer'],
            quality_metrics=data['quality_metrics'],
            ask_count=data.get('ask_count', 1)
        )
        
        if success:
            logger.info(f"Registro guardado: {data['question'][:50]}...")
            return jsonify({'message': 'Record saved successfully'})
        else:
            return jsonify({'error': 'Failed to save record'}), 500
            
    except Exception as e:
        logger.error(f"Error in /storage/save: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/storage/record/<question>', methods=['GET'])
def get_qa_record(question):
    """Obtener un registro específico por pregunta"""
    try:
        record = storage.get_qa_record(question)
        if record:
            return jsonify(record)
        else:
            return jsonify({'error': 'Record not found'}), 404
            
    except Exception as e:
        logger.error(f"Error getting record: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/storage/records', methods=['GET'])
def get_all_records():
    """Obtener todos los registros (con límite)"""
    try:
        limit = request.args.get('limit', default=10000, type=int)
        records = storage.get_all_records(limit=limit)
        return jsonify({
            'total_records': len(records),
            'records': records
        })
        
    except Exception as e:
        logger.error(f"Error getting records: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/storage/stats', methods=['GET'])
def get_storage_stats():
    """Obtener estadísticas del almacenamiento"""
    try:
        stats = storage.get_stats()
        return jsonify(stats)
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/storage/count', methods=['GET'])
def get_record_count():
    """Obtener conteo de registros"""
    try:
        stats = storage.get_stats()
        return jsonify({'record_count': stats['total_records']})
    except Exception as e:
        logger.error(f"Error getting count: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    host = os.getenv('HOST', '0.0.0.0')
    port = int(os.getenv('STORAGE_PORT', 8081))
    
    logger.info(f"Starting Storage Service on {host}:{port}")
    app.run(host=host, port=port, debug=False)