import os
import json
import logging
from pyflink.datastream import StreamExecutionEnvironment
from pyflink.datastream.connectors.kafka import FlinkKafkaConsumer, FlinkKafkaProducer
from pyflink.datastream.formats.json import JsonRowDeserializationSchema, JsonRowSerializationSchema
from pyflink.common.typeinfo import Types

# --- Configuración de Logging ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Configuración del Job ---
KAFKA_BROKER = os.getenv('KAFKA_BROKER', 'kafka:29092')
UMBRAL_CALIDAD = float(os.getenv('UMBRAL_CALIDAD', 0.75))
MAX_REGENERACIONES = int(os.getenv('MAX_REGENERACIONES', 3))

# --- Tópicos de Kafka ---
TOPIC_INPUT = 'respuestas_exitosas_llm'
TOPIC_VALIDADOS = 'resultados_validados_flink'
TOPIC_REGENERAR = 'preguntas_nuevas'

def calcular_score(respuesta_llm: str, pregunta_original: dict) -> float:
    """
    !!! IMPORTANTE !!!
    Esta es una función de ejemplo. Debes reemplazar esta lógica
    con tu propia función de cálculo de score desarrollada en la Tarea 1.
    
    Por ejemplo, podría ser una comparación de similitud de texto,
    análisis de sentimiento, etc.
    
    Aquí, simulamos un score basado en la longitud de la respuesta.
    """
    # Lógica de ejemplo: un score más alto para respuestas más largas.
    score = min(len(respuesta_llm) / 250.0, 1.0) 
    logger.info(f"Score calculado para pregunta ID {pregunta_original.get('id', 'N/A')}: {score:.2f}")
    return score

def quality_assurance_job():
    """
    Define y ejecuta el pipeline de procesamiento de flujos con PyFlink.
    """
    env = StreamExecutionEnvironment.get_execution_environment()
    # Define el JAR del conector de Kafka. Asegúrate de que la versión coincida con tu versión de Flink.
    env.add_jars("file:///opt/flink/jars/flink-sql-connector-kafka-1.17.1.jar")

    # --- Definición de Tipos para los Schemas ---
    # Esquema para el tópico de entrada (respuestas_exitosas_llm)
    input_type_info = Types.ROW_NAMED(
        ["pregunta_original", "respuesta_llm"],
        [Types.MAP(Types.STRING(), Types.STRING()), Types.STRING()]
    )
    # Esquema para el tópico de salida de validados
    output_validado_type_info = Types.ROW_NAMED(
        ["pregunta_original", "respuesta_llm", "score"],
        [Types.MAP(Types.STRING(), Types.STRING()), Types.STRING(), Types.FLOAT()]
    )
    # Esquema para el tópico de salida de regeneración
    output_regenerar_type_info = Types.ROW_NAMED(
        ["id", "texto", "retry_count", "regeneration_attempts"], # Asegúrate que coincida con el formato de tus preguntas
        [Types.STRING(), Types.STRING(), Types.INT(), Types.INT()]
    )

    # --- Source: Consumidor de Kafka ---
    kafka_source = FlinkKafkaConsumer(
        topics=TOPIC_INPUT,
        deserialization_schema=JsonRowDeserializationSchema.builder().type_info(input_type_info).build(),
        properties={'bootstrap.servers': KAFKA_BROKER, 'group.id': 'flink-quality-group'}
    )

    # --- Sinks: Productores de Kafka ---
    kafka_sink_validados = FlinkKafkaProducer(
        topic=TOPIC_VALIDADOS,
        serialization_schema=JsonRowSerializationSchema.builder().with_type_info(output_validado_type_info).build(),
        producer_config={'bootstrap.servers': KAFKA_BROKER}
    )
    kafka_sink_regenerar = FlinkKafkaProducer(
        topic=TOPIC_REGENERAR,
        serialization_schema=JsonRowSerializationSchema.builder().with_type_info(output_regenerar_type_info).build(),
        producer_config={'bootstrap.servers': KAFKA_BROKER}
    )

    # --- Lógica del Pipeline ---
    data_stream = env.add_source(kafka_source).name("KafkaSource_RespuestasLLM")

    def procesar_respuesta(mensaje):
        """
        Calcula score y decide si la respuesta es válida o necesita regeneración.
        """
        pregunta = mensaje['pregunta_original']
        respuesta = mensaje['respuesta_llm']
        score = calcular_score(respuesta, pregunta)
        
        intentos_regen = pregunta.get('regeneration_attempts', 0)

        if score >= UMBRAL_CALIDAD or intentos_regen >= MAX_REGENERACIONES:
            # Resultado es válido
            return ('VALIDO', {
                'pregunta_original': pregunta,
                'respuesta_llm': respuesta,
                'score': score
            })
        else:
            # Necesita regeneración
            pregunta['regeneration_attempts'] = intentos_regen + 1
            # Asegúrate que los campos coincidan con el type_info de regeneración
            pregunta_para_reenviar = {
                'id': pregunta.get('id'),
                'texto': pregunta.get('texto'),
                'retry_count': pregunta.get('retry_count', 0),
                'regeneration_attempts': pregunta['regeneration_attempts']
            }
            return ('REGENERAR', pregunta_para_reenviar)

    processed_stream = data_stream.map(procesar_respuesta, output_type=Types.TUPLE([Types.STRING(), Types.MAP(Types.STRING(), Types.OBJECT())]))
    
    # --- División del Stream ---
    # Stream para resultados validados
    stream_validados = processed_stream.filter(lambda x: x[0] == 'VALIDO').map(lambda x: x[1], output_type=output_validado_type_info)
    
    # Stream para preguntas a regenerar
    stream_regenerar = processed_stream.filter(lambda x: x[0] == 'REGENERAR').map(lambda x: x[1], output_type=output_regenerar_type_info)

    # --- Conectar los streams a los sinks ---
    stream_validados.add_sink(kafka_sink_validados).name("KafkaSink_Validados")
    stream_regenerar.add_sink(kafka_sink_regenerar).name("KafkaSink_Regenerar")
    
    # --- Ejecutar el Job ---
    env.execute("JobDeAseguramientoDeCalidad")

if __name__ == "__main__":
    quality_assurance_job()
