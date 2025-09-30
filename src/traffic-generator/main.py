import argparse
import time
import random
import requests
import json
import sys
import os
from distributions import TrafficDistributions

def load_questions(dataset_path="datasets/sample_questions.json", num_questions=50):
    """Cargar preguntas desde el dataset"""
    try:
        with open(dataset_path, 'r', encoding='utf-8') as f:
            questions = json.load(f)
            print(f"Loaded {len(questions)} questions from {dataset_path}")
            
            # Si es una lista de objetos, extraer el texto
            if questions and isinstance(questions[0], dict):
                if 'question' in questions[0]:
                    questions = [q['question'] for q in questions]
                elif 'text' in questions[0]:
                    questions = [q['text'] for q in questions]
            
            return questions[:num_questions]
            
    except FileNotFoundError:
        print(f"Dataset file {dataset_path} not found")
        # Preguntas de ejemplo si no hay dataset
        sample_questions = [
            "What is Python?",
            "What is Docker?",
            "What is machine learning?",
            "What are distributed systems?",
            "How to learn programming?",
            "What is cloud computing?",
            "What is an API?",
            "How to deploy applications?",
            "What is artificial intelligence?",
            "What is data science?"
        ]
        print("Using sample questions")
        return sample_questions
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON from {dataset_path}: {e}")
        sample_questions = ["What is Python?", "What is Docker?", "What is machine learning?"]
        print("Using fallback questions due to JSON error")
        return sample_questions

def send_query(cache_url, question):
    """Enviar pregunta al cache service"""
    try:
        payload = {"question": question}
        response = requests.post(
            f"{cache_url}/query",
            json=payload,
            timeout=15
        )
        
        if response.status_code == 200:
            data = response.json()
            source = data.get('source', 'unknown')
            response_preview = data.get('response', '')[:50] + '...' if len(data.get('response', '')) > 50 else data.get('response', '')
            print(f"  Response from {source}: {response_preview}")
            return True
        else:
            print(f"  Error: HTTP {response.status_code} - {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"  Connection error: {e}")
        return False
def load_questions(dataset_path="datasets/yahoo_questions.json", num_questions=50):
    """Cargar preguntas desde el dataset de Yahoo Answers"""
    try:
        with open(dataset_path, 'r', encoding='utf-8') as f:
            questions = json.load(f)
            print(f"Loaded {len(questions)} questions from {dataset_path}")
            
            # Si es una lista de strings, usarla directamente
            if questions and isinstance(questions[0], str):
                return questions[:num_questions]
            
            # Si es una lista de objetos, extraer el texto
            elif questions and isinstance(questions[0], dict):
                if 'question' in questions[0]:
                    questions = [q['question'] for q in questions]
                elif 'text' in questions[0]:
                    questions = [q['text'] for q in questions]
                elif 'title' in questions[0]:
                    questions = [q['title'] for q in questions]
                elif 'content' in questions[0]:
                    questions = [q['content'] for q in questions]
                
                return questions[:num_questions]
            else:
                raise ValueError("Formato de dataset no reconocido")
            
    except FileNotFoundError:
        print(f"Dataset file {dataset_path} not found, trying sample dataset...")
        # Intentar con dataset de muestra
        return load_questions("datasets/sample_questions.json", num_questions)
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON from {dataset_path}: {e}")
        print("Using fallback questions...")
        return get_fallback_questions()[:num_questions]

def get_fallback_questions():
    """Preguntas de respaldo si todo falla"""
    return [
        "What is Python?", "What is Docker?", "What is machine learning?",
        "What are distributed systems?", "How to learn programming?",
        "What is cloud computing?", "What is an API?", "How to deploy applications?",
        "What is artificial intelligence?", "What is data science?"
    ]

def main():
    parser = argparse.ArgumentParser(description='Traffic Generator for QA System')
    parser.add_argument('--distribution', type=str, default='poisson', 
                       choices=['constant', 'poisson', 'bursty', 'sinusoidal'],
                       help='Traffic distribution type')
    parser.add_argument('--rate', type=float, default=2.0, 
                       help='Requests per second')
    parser.add_argument('--duration', type=int, default=60,
                       help='Duration in seconds')
    parser.add_argument('--dataset', type=str, default='datasets/sample_questions.json',
                       help='Path to questions dataset')
    parser.add_argument('--max-questions', type=int, default=50,
                       help='Maximum number of questions to use')
    
    args = parser.parse_args()
    
    # Configuración
    CACHE_URL = os.getenv('CACHE_SERVICE_URL', 'http://cache-service:8000')
    
    print("=== Traffic Generator ===")
    print(f"Distribution: {args.distribution}")
    print(f"Rate: {args.rate} req/sec")
    print(f"Duration: {args.duration} seconds")
    print(f"Cache URL: {CACHE_URL}")
    print(f"Dataset: {args.dataset}")
    
    # Cargar preguntas
    questions = load_questions(args.dataset, args.max_questions)
    print(f"Loaded {len(questions)} questions")
    
    # Configurar distribución
    distributions = TrafficDistributions()
    if args.distribution == 'constant':
        dist_func = distributions.constant_rate(args.rate)
        print("Using constant distribution")
    elif args.distribution == 'poisson':
        dist_func = distributions.poisson_rate(args.rate)
        print("Using Poisson distribution")
    elif args.distribution == 'bursty':
        dist_func = distributions.bursty_traffic(args.rate, burst_factor=5.0)
        print("Using bursty distribution")
    elif args.distribution == 'sinusoidal':
        dist_func = distributions.sinusoidal_rate(args.rate, amplitude=0.5, period=60.0)
        print("Using sinusoidal distribution")
    else:
        dist_func = distributions.poisson_rate(args.rate)
        print("Defaulting to Poisson distribution")
    
    # Generar tráfico
    start_time = time.time()
    request_count = 0
    success_count = 0
    
    print("Starting traffic generation...")
    
    try:
        while time.time() - start_time < args.duration:
            # Seleccionar pregunta aleatoria
            question = random.choice(questions)
            
            print(f"Request {request_count + 1}: {question}")
            
            # Enviar query
            success = send_query(CACHE_URL, question)
            request_count += 1
            if success:
                success_count += 1
            
            # Log cada 5 requests
            if request_count % 5 == 0:
                success_rate = (success_count / request_count) * 100
                elapsed = time.time() - start_time
                print(f"Progress: {request_count} requests, {success_rate:.1f}% success, {elapsed:.1f}s elapsed")
            
            # Esperar según la distribución
            wait_time = dist_func()
            print(f"Waiting {wait_time:.2f}s...")
            time.sleep(wait_time)
    
    except KeyboardInterrupt:
        print("Traffic generation interrupted by user")
    
    # Reporte final
    success_rate = (success_count / request_count) * 100 if request_count > 0 else 0
    actual_duration = time.time() - start_time
    actual_rate = request_count / actual_duration if actual_duration > 0 else 0
    
    print("=== Traffic Generation Complete ===")
    print(f"Total requests: {request_count}")
    print(f"Successful: {success_count}")
    print(f"Success rate: {success_rate:.1f}%")
    print(f"Actual duration: {actual_duration:.1f} seconds")
    print(f"Actual rate: {actual_rate:.2f} req/sec")

if __name__ == "__main__":
    main()