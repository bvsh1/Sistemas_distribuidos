import requests
import time
import random
import json
import argparse
from distributions import TrafficDistributions

class TrafficGenerator:
    def __init__(self, cache_url: str = "http://cache-service:8000"):
        self.cache_url = cache_url
        self.request_count = 0
        self.success_count = 0
        
    def load_questions(self, dataset_path: str = "datasets/sample_questions.json", num_questions: int = 1000):
        """Cargar preguntas desde dataset o crear sample"""
        try:
            with open(dataset_path, 'r', encoding='utf-8') as f:
                questions = json.load(f)
                print(f"Cargadas {len(questions)} preguntas desde {dataset_path}")
                return questions[:num_questions]
        except FileNotFoundError:
            # Preguntas de ejemplo si no hay dataset
            sample_questions = [
                "¿Cuál es la capital de Chile?",
                "¿Cómo aprender programación?",
                "¿Qué es un sistema distribuido?",
                "¿Cuáles son los mejores lenguajes de programación?",
                "¿Cómo mejorar el rendimiento académico?",
                "¿Qué es la inteligencia artificial?",
                "¿Cómo cocinar pasta al dente?",
                "¿Cuáles son los planetas del sistema solar?",
                "¿Cómo invertir en la bolsa?",
                "¿Qué es el cambio climático?"
            ]
            print("Usando preguntas de ejemplo")
            return sample_questions * (num_questions // len(sample_questions) + 1)

    def send_query(self, question: str) -> bool:
        """Enviar pregunta al sistema de cache"""
        try:
            payload = {"question": question}
            response = requests.post(
                f"{self.cache_url}/query",
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                self.success_count += 1
                return True
            else:
                print(f"Error HTTP {response.status_code}: {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"Error de conexión: {e}")
            return False

    def generate_traffic(self, questions: list, distribution, duration: int = 60):
        """Generar tráfico según la distribución especificada"""
        print(f"Iniciando generación de tráfico por {duration} segundos...")
        print(f"Distribución: {distribution.__name__ if hasattr(distribution, '__name__') else 'custom'}")
        
        start_time = time.time()
        self.request_count = 0
        self.success_count = 0
        
        while time.time() - start_time < duration:
            # Seleccionar pregunta aleatoria
            question = random.choice(questions)
            
            # Enviar query
            success = self.send_query(question)
            self.request_count += 1
            
            # Log cada 10 requests
            if self.request_count % 10 == 0:
                success_rate = (self.success_count / self.request_count) * 100
                print(f"Requests: {self.request_count}, Éxito: {success_rate:.1f}%")
            
            # Esperar según la distribución
            wait_time = distribution()
            time.sleep(wait_time)
        
        # Reporte final
        self.print_report()

    def print_report(self):
        """Imprimir reporte de estadísticas"""
        success_rate = (self.success_count / self.request_count) * 100 if self.request_count > 0 else 0
        
        print("\n" + "="*50)
        print("REPORTE FINAL DEL GENERADOR DE TRÁFICO")
        print("="*50)
        print(f"Total de requests: {self.request_count}")
        print(f"Requests exitosos: {self.success_count}")
        print(f"Tasa de éxito: {success_rate:.1f}%")
        print("="*50)

def main():
    parser = argparse.ArgumentParser(description='Generador de tráfico para el sistema de QA')
    parser.add_argument('--distribution', type=str, default='poisson', 
                       choices=['constant', 'poisson', 'bursty', 'sinusoidal'],
                       help='Tipo de distribución de tráfico')
    parser.add_argument('--rate', type=float, default=2.0, 
                       help='Tasa promedio de requests por segundo')
    parser.add_argument('--duration', type=int, default=300,
                       help='Duración en segundos de la generación de tráfico')
    parser.add_argument('--dataset', type=str, default='datasets/sample_questions.json',
                       help='Ruta al dataset de preguntas')
    
    args = parser.parse_args()
    
    # Configurar distribución
    distributions = TrafficDistributions()
    if args.distribution == 'constant':
        dist_func = distributions.constant_rate(args.rate)
    elif args.distribution == 'poisson':
        dist_func = distributions.poisson_rate(args.rate)
    elif args.distribution == 'bursty':
        dist_func = distributions.bursty_traffic(args.rate)
    elif args.distribution == 'sinusoidal':
        dist_func = distributions.sinusoidal_rate(args.rate)
    else:
        dist_func = distributions.poisson_rate(args.rate)
    
    # Inicializar generador
    generator = TrafficGenerator()
    
    # Cargar preguntas
    questions = generator.load_questions(args.dataset)
    
    # Generar tráfico
    generator.generate_traffic(questions, dist_func, args.duration)

if __name__ == "__main__":
    main()