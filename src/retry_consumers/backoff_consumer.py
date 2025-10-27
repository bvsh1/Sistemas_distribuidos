import os
import time
import json
from kafka import KafkaConsumer, KafkaProducer
from kafka.errors import NoBrokersAvailable

# --- Configuración ---
KAFKA_BROKER = os.environ.get('KAFKA_BROKER', 'kafka:29092')
INPUT_TOPIC = 'errores_reintentables_backoff'
OUTPUT_TOPIC = 'preguntas_nuevas'
INITIAL_BACKOFF_SECONDS = int(os.environ.get('INITIAL_BACKOFF_SECONDS', 5))
MAX_WAIT_SECONDS = 300 # Límite de 5 minutos para no esperar eternamente

print("--- Iniciando Consumidor de Reintento (Backoff Exponencial) ---")
print(f"Broker Kafka: {KAFKA_BROKER}")
print(f"Tópico de entrada: {INPUT_TOPIC}")
print(f"Tópico de salida: {OUTPUT_TOPIC}")
print(f"Backoff inicial: {INITIAL_BACKOFF_SECONDS}s")

# --- Conexión a Kafka con reintentos ---
consumer = None
producer = None

while consumer is None or producer is None:
    try:
        if consumer is None:
            consumer = KafkaConsumer(
                INPUT_TOPIC,
                bootstrap_servers=[KAFKA_BROKER],
                auto_offset_reset='earliest',
                value_deserializer=lambda v: json.loads(v.decode('utf-8'))
            )
        if producer is None:
            producer = KafkaProducer(
                bootstrap_servers=[KAFKA_BROKER],
                value_serializer=lambda v: json.dumps(v).encode('utf-8')
            )
        print("Conexión a Kafka exitosa.")
    except NoBrokersAvailable:
        print("Esperando a que Kafka esté disponible... (5s)")
        time.sleep(5)

# --- Bucle principal ---
for message in consumer:
    try:
        data = message.value
        question_id = data.get('id', 'ID desconocido')
        # El llm_consumer debe haber incrementado este contador
        retry_count = data.get('retry_count', 1) 
        
        print(f"[REINTENTO-BACKOFF] Recibida pregunta {question_id} por sobrecarga (intento {retry_count}).")
        
        # 1. Calcular el tiempo de espera exponencial
        # Intento 1: 5 * (2^0) = 5s
        # Intento 2: 5 * (2^1) = 10s
        # Intento 3: 5 * (2^2) = 20s
        # Intento 4: 5 * (2^3) = 40s
        wait_time = INITIAL_BACKOFF_SECONDS * (2 ** (retry_count - 1))
        wait_time = min(wait_time, MAX_WAIT_SECONDS) # Aplicar el límite máximo
        
        print(f"[REINTENTO-BACKOFF] Esperando {wait_time} segundos...")
        time.sleep(wait_time)
        
        # 2. Re-enviar al tópico de preguntas nuevas
        producer.send(OUTPUT_TOPIC, data)
        producer.flush()
        
        print(f"[REINTENTO-BACKOFF] Pregunta {question_id} re-enviada a '{OUTPUT_TOPIC}'.")
        
    except Exception as e:
        print(f"[REINTENTO-BACKOFF] Error al procesar el mensaje: {e}")
