# main.py
import sys
import os
import subprocess

def run_system_with_real_questions():
    """Ejecuta el sistema con 2 distribuciones distintas"""
    
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
    
    print("Iniciando sistema con 2 distribuciones distintas")
    
    # Usar solo 2 distribuciones validas
    distributions = [
        ('poisson', '3.0'),    # Distribucion Poisson - mas realista
        ('constant', '2.0')    # Distribucion Constante - baseline
    ]
    
    for distribution, rate in distributions:
        print(f"Probando distribucion: {distribution} con tasa: {rate}")
        
        traffic_generator_path = os.path.join('src', 'traffic-generator', 'main.py')
        
        cmd = [
            sys.executable, 
            traffic_generator_path,
            '--distribution', distribution,
            '--rate', rate,
            '--duration', '60',
            '--dataset', dataset_path,
            '--max-questions', '10000'
        ]
        
        print("Ejecutando:", ' '.join(cmd))
        result = subprocess.run(cmd)
        
        if result.returncode == 0:
            print(f"Distribucion {distribution} completada exitosamente")
        else:
            print(f"Distribucion {distribution} tuvo errores")

def create_sample_dataset():
    """Crea dataset de ejemplo si no existe"""
    import json
    os.makedirs('datasets', exist_ok=True)
    
    sample_questions = []
    for i in range(1000):
        sample_questions.append(f"Pregunta de ejemplo {i+1} sobre temas variados de tecnologia y educacion")
    
    with open("datasets/yahoo_questions.json", 'w', encoding='utf-8') as f:
        json.dump(sample_questions, f, ensure_ascii=False, indent=2)
    
    print("Dataset de ejemplo creado con 1000 preguntas")

if __name__ == "__main__":
    run_system_with_real_questions()