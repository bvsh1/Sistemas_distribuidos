# main.py (VERSIÓN CON SCORING)
import sys
import os
import subprocess
import requests
import json
import time

def evaluate_quality(qa_pairs):
    """Evalúa la calidad de las respuestas usando el scoring service"""
    try:
        print("📊 Ejecutando evaluación de calidad...")
        
        response = requests.post(
            "http://localhost:8080/evaluate/batch",
            json={"qa_pairs": qa_pairs},
            timeout=30
        )
        
        if response.status_code == 200:
            results = response.json()
            avg_score = results['results_summary']['average_score']
            distribution = results['results_summary']['quality_distribution']
            
            print(f"✅ Evaluación completada:")
            print(f"   Score promedio: {avg_score:.3f}")
            print(f"   Distribución: {distribution}")
            
            return results
        else:
            print(f"❌ Error en evaluación: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Error conectando al scoring service: {e}")
        return None

def run_system_with_evaluation():
    """Ejecuta el sistema completo CON evaluación de calidad"""
    
    dataset_path = "datasets/yahoo_questions.json"
    
    # Verificar dataset
    if not os.path.exists(dataset_path):
        print("Convirtiendo dataset...")
        convert_script = os.path.join('src', 'traffic-generator', 'convert_dataset.py')
        if os.path.exists(convert_script):
            result = subprocess.run([sys.executable, convert_script], capture_output=True, text=True)
            if result.returncode != 0:
                print("Error en conversion:", result.stderr)
        else:
            print("Creando dataset de ejemplo...")
            create_sample_dataset()
    
    print("🎯 Iniciando sistema CON evaluación de calidad")
    
    # Para evaluación, necesitamos un dataset con preguntas Y respuestas esperadas
    evaluation_dataset = load_evaluation_dataset()
    
    distributions = [
        ('poisson', '1.0'),    # Tasas reducidas para evitar rate limits
        ('constant', '0.5')
    ]
    
    all_qa_pairs = []
    
    for distribution, rate in distributions:
        print(f"\n📈 Probando distribución: {distribution} con tasa: {rate}")
        
        traffic_generator_path = os.path.join('src', 'traffic-generator', 'main.py')
        
        cmd = [
            sys.executable, 
            traffic_generator_path,
            '--distribution', distribution,
            '--rate', rate,
            '--duration', '30',  # Reducido para pruebas
            '--dataset', dataset_path,
            '--max-questions', '50'  # Reducido para pruebas
        ]
        
        print("Ejecutando:", ' '.join(cmd))
        result = subprocess.run(cmd)
        
        if result.returncode == 0:
            print(f"✅ Distribución {distribution} completada")
            
            # Recolectar respuestas del LLM para evaluación
            qa_pairs = collect_llm_responses_for_evaluation(evaluation_dataset)
            all_qa_pairs.extend(qa_pairs)
            
        else:
            print(f"❌ Distribución {distribution} tuvo errores")
        
        time.sleep(10)  # Espera entre distribuciones
    
    # Ejecutar evaluación final
    if all_qa_pairs:
        print(f"\n🔍 Evaluando {len(all_qa_pairs)} pares pregunta-respuesta...")
        evaluate_quality(all_qa_pairs)
    else:
        print("⚠️ No se recolectaron datos para evaluación")

def load_evaluation_dataset():
    """Carga dataset de evaluación con preguntas y respuestas esperadas"""
    # Este es un ejemplo - necesitas tu dataset real con respuestas esperadas
    evaluation_data = [
        {
            "question": "¿Qué es Python?",
            "expected_answer": "Python es un lenguaje de programación interpretado, de alto nivel y de propósito general."
        },
        {
            "question": "¿Qué es machine learning?", 
            "expected_answer": "El machine learning es una rama de la inteligencia artificial que permite a las computadoras aprender sin ser programadas explícitamente."
        },
        {
            "question": "¿Qué es Docker?",
            "expected_answer": "Docker es una plataforma que permite desarrollar, enviar y ejecutar aplicaciones en contenedores."
        }
    ]
    
    print(f"📁 Dataset de evaluación cargado: {len(evaluation_data)} preguntas")
    return evaluation_data

def collect_llm_responses_for_evaluation(evaluation_dataset):
    """Obtiene respuestas del LLM para las preguntas de evaluación"""
    qa_pairs = []
    
    print("🔄 Recolectando respuestas del LLM para evaluación...")
    
    for item in evaluation_dataset[:5]:  # Limitar a 5 para prueba
        try:
            # Hacer la pregunta al cache/LLM
            response = requests.post(
                "http://localhost:8000/query",
                json={"question": item["question"]},
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                llm_answer = data.get('response', '')
                source = data.get('source', 'unknown')
                
                qa_pairs.append({
                    "question": item["question"],
                    "expected_answer": item["expected_answer"],
                    "llm_answer": llm_answer
                })
                
                print(f"  ✅ {item['question'][:30]}... → {source}")
                
            time.sleep(2)  # Rate limiting
            
        except Exception as e:
            print(f"  ❌ Error obteniendo respuesta: {e}")
    
    return qa_pairs

def create_sample_dataset():
    """Crea dataset de ejemplo si no existe"""
    import json
    os.makedirs('datasets', exist_ok=True)
    
    sample_questions = []
    for i in range(100):
        sample_questions.append(f"Pregunta de ejemplo {i+1} sobre temas variados")
    
    with open("datasets/yahoo_questions.json", 'w', encoding='utf-8') as f:
        json.dump(sample_questions, f, ensure_ascii=False, indent=2)
    
    print("Dataset de ejemplo creado con 100 preguntas")

if __name__ == "__main__":
    # Verificar que los servicios estén ejecutándose
    try:
        response = requests.get("http://localhost:8080/health", timeout=5)
        if response.status_code == 200:
            print("🎯 Scoring service detectado - ejecutando con evaluación")
            run_system_with_evaluation()
        else:
            print("⚠️ Scoring service no disponible - ejecutando sin evaluación")
            run_system_with_real_questions()
    except:
        print("⚠️ Scoring service no disponible - ejecutando sin evaluación")
        run_system_with_real_questions()