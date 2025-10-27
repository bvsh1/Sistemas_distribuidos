import json
import logging
import os
import sys
from kafka import KafkaConsumer
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

# --- Configuración de Logging ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Configuración de Kafka ---
KAFKA_BROKER = os.getenv('KAFKA_BROKER', 'kafka:29092')
TOPIC_INPUT = 'resultados_validados_flink'

# --- Configuración de MongoDB ---
MONGO_URL = os.getenv('MONGO_URL', 'mongodb://localhost:27017/')
MONGO_DATABASE = os.getenv('MONGO_DATABASE', 'qa_system')
MONGO_COLLECTION = os.getenv('MONGO_COLLECTION', 'results')

# --- Conexión a Servicios ---
def connect_to_mongo():
    """Intenta conectarse a MongoDB y devuelve el cliente."""
    try:
        logger.info(f"Conectando a MongoDB en {MONGO_URL}...")
        client = MongoClient(MONGO_URL, serverSelectionTimeoutMS=5000)
        # Forzar una conexión para verificar que el servidor está disponible
        client.admin.command('ping')
        logger.info("✅ Conexión a MongoDB exitosa.")
        return client
    except ConnectionFailure as e:
        logger.error(f"❌ No se pudo conectar a MongoDB: {e}")
        sys.exit(1)

def connect_to_kafka():
    """Intenta conectarse a Kafka y devuelve el consumidor."""
    try:
        logger.info(f"Conectando a Kafka en {KAFKA_BROKER}...")
        consumer = KafkaConsumer(
            TOPIC_INPUT,
            bootstrap_servers=KAFKA_BROKER,
            value_deserializer=lambda v: json.loads(v.decode('utf-8')),
            auto_offset_reset='earliest',
            group_id='storage-mongo-group'
        )
        logger.info("Conexión a Kafka exitosa.")
        return consumer
    except Exception as e:
        logger.error(f"No se pudo conectar a Kafka: {e}")
        sys.exit(1)

def save_to_db(collection, result):
    """
    Guarda el resultado en la colección de MongoDB usando el ID de la pregunta
    como identificador único para evitar duplicados.
    """
    try:
        question_id = result.get('pregunta_original', {}).get('id')
        if not question_id:
            logger.warning("Mensaje recibido sin ID de pregunta. Omitiendo.")
            return

        # El filtro para encontrar el documento
        filter_query = {'question_id': question_id}

        # Los datos a insertar o actualizar
        update_data = {
            '$set': {
                'question_text': result.get('pregunta_original', {}).get('texto'),
                'llm_answer': result.get('respuesta_llm'),
                'score': result.get('score'),
                'last_updated': {'$currentDate': {'type': 'timestamp'}}
            }
        }
        
        # update_one con upsert=True insertará si no existe, o actualizará si ya existe.
        update_result = collection.update_one(filter_query, update_data, upsert=True)

        if update_result.upserted_id:
            logger.info(f"📄 Nuevo resultado INSERTADO para question_id: {question_id}")
        elif update_result.matched_count > 0:
            logger.info(f"🔄 Resultado ACTUALIZADO para question_id: {question_id}")
            
    except Exception as e:
        logger.error(f"Error guardando en MongoDB para question_id {question_id}: {e}")

# --- Bucle Principal ---
if __name__ == "__main__":
    mongo_client = connect_to_mongo()
    db = mongo_client[MONGO_DATABASE]
    collection = db[MONGO_COLLECTION]
    
    kafka_consumer = connect_to_kafka()

    logger.info(f"Escuchando el tópico '{TOPIC_INPUT}' para persistir en MongoDB...")

    for message in kafka_consumer:
        final_result = message.value
        save_to_db(collection, final_result)
