import os
import time
import json
import requests
from kafka import KafkaConsumer, KafkaProducer
from kafka.errors import NoBrokersAvailable

# --- Configuración ---
KAFKA_BROKER = os.environ.get('KAFKA_BROKER', 'kafka:29092')
LLM_SERVICE_URL = os.environ.get('LLM_SERVICE_URL', 'http://llm-service:5000/query')

INPUT_TOPIC = 'preguntas_nuevas'
SUCCESS_TOPIC = 'respuestas_exitosas_llm'
RETRY_DELAY_TOPIC = 'errores_reintentables_delay'    # Para error 429 (Rate Limit)
RETRY_BACKOFF_TOPIC = 'errores_reintentables_backoff'  # Para error 503 (Sobrecarga)

MAX_RETRIES = 5 # Límite máximo de reintentos por backoff

print("--- Iniciando Consumidor Principal del LLM ---")
print(f"Broker Kafka: {KAFKA_BROKER}")
print(f"URL del Servicio LLM: {LLM_SERVICE_URL}")
print(f"Tópico de entrada: {INPUT_TOPIC}")

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
print("Consumidor listo. Esperando mensajes...")
for message in consumer:
    try:
        pregunta_data = message.value
        question_id = pregunta_data.get('id', 'ID desconocido')
        question_text = pregunta_data.get('texto', 'Texto desconocido')
        
        print(f"\n[LLM-CONSUMER] Procesando pregunta {question_id}: {question_text[:50]}...")

        # 1. Llamar al servicio LLM (Flask)
        response = requests.post(LLM_SERVICE_URL, json={'question': question_text}, timeout=30)
        
        # 2. Analizar la respuesta del servicio
        
        # --- CASO 1: ÉXITO ---
        if response.status_code == 200:
            llm_response = response.json()
            resultado = {
                'pregunta_original': pregunta_data,
                'respuesta_llm': llm_response.get('response', ''),
                'source': llm_response.get('source', 'llm')
            }
            producer.send(SUCCESS_TOPIC, resultado)
            print(f"[LLM-CONSUMER] Éxito (200). Pregunta {question_id} enviada a '{SUCCESS_TOPIC}'.")
        
        # --- CASO 2: ERROR DE LÍMITE DE CUOTA (Rate Limit) ---
        elif response.status_code == 429:
            print(f"[LLM-CONSUMER] Error 429 (Rate Limit). Pregunta {question_id} enviada a '{RETRY_DELAY_TOPIC}'.")
            producer.send(RETRY_DELAY_TOPIC, pregunta_data)
        
        # --- CASO 3: ERROR DE SOBRECARGA (Server Overloaded) ---
        elif response.status_code == 503:
            retry_count = pregunta_data.get('retry_count', 0) + 1
            pregunta_data['retry_count'] = retry_count
            
            if retry_count <= MAX_RETRIES:
                print(f"[LLM-CONSUMER] Error 503 (Sobrecarga). Pregunta {question_id} enviada a '{RETRY_BACKOFF_TOPIC}' (Intento {retry_count}).")
                producer.send(RETRY_BACKOFF_TOPIC, pregunta_data)
            else:
                print(f"[LLM-CONSUMER] Error 503 (Sobrecarga). Pregunta {question_id} descartada tras {MAX_RETRIES} intentos.")
        
        # --- CASO 4: OTROS ERRORES ---
        else:
            print(f"[LLM-CONSUMER] Error HTTP no manejado: {response.status_code} - {response.text}")
            # Aquí podrías decidir enviar a un tópico de "mensajes fallidos" (dead-letter queue)
        
        producer.flush()

    except requests.exceptions.RequestException as e:
        print(f"[LLM-CONSUMER] Error de conexión al servicio LLM: {e}")
        # Reenviar para reintento con backoff podría ser una opción,
        # ya que el servicio LLM puede estar temporalmente caído.
        retry_count = pregunta_data.get('retry_count', 0) + 1
        pregunta_data['retry_count'] = retry_count
        if retry_count <= MAX_RETRIES:
             print(f"[LLM-CONSUMER] Reenviando a backoff por error de conexión.")
             producer.send(RETRY_BACKOFF_TOPIC, pregunta_data)
             producer.flush()
        else:
             print(f"[LLM-CONSUMER] Descartada por error de conexión tras {MAX_RETRIES} intentos.")

    except Exception as e:
        print(f"[LLM-CONSUMER] Error inesperado al procesar el mensaje: {e}")
