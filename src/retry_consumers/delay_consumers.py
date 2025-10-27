import os
import time
import json
from kafka import KafkaConsumer, KafkaProducer
from kafka.errors import NoBrokersAvailable

# --- Configuración ---
KAFKA_BROKER = os.environ.get('KAFKA_BROKER', 'kafka:29092')
INPUT_TOPIC = 'errores_reintentables_delay'
OUTPUT_TOPIC = 'preguntas_nuevas'
DELAY_SECONDS = int(os.environ.get('DELAY_SECONDS', 60))

print("--- Iniciando Consumidor de Reintento (Delay Fijo) ---")
print(f"Broker Kafka: {KAFKA_BROKER}")
print(f"Tópico de entrada: {INPUT_TOPIC}")
print(f"Tópico de salida: {OUTPUT_TOPIC}")
print(f"Tiempo de espera fijo: {DELAY_SECONDS}s")

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
        
        print(f"[REINTENTO-DELAY] Recibida pregunta {question_id} por límite de cuota.")
        
        # 1. Esperar el tiempo fijo
        print(f"[REINTENTO-DELAY] Esperando {DELAY_SECONDS} segundos...")
        time.sleep(DELAY_SECONDS)
        
        # 2. Re-enviar al tópico de preguntas nuevas
        producer.send(OUTPUT_TOPIC, data)
        producer.flush()
        
        print(f"[REINTENTO-DELAY] Pregunta {question_id} re-enviada a '{OUTPUT_TOPIC}'.")
        
    except Exception as e:
        print(f"[REINTENTO-DELAY] Error al procesar el mensaje: {e}")
