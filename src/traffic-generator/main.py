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
        with open(dataset_path, 'r', encoding='utf-8-sig') as f:  # Cambiar a utf-8-sig
            questions = json.load(f)
            print(f"Loaded {len(questions)} questions from {dataset_path}")
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
        # Usar preguntas de ejemplo como fallback
        sample_questions = [
            "What is Python?",
            "What is Docker?",
            "What is machine learning?"
        ]
        print("Using fallback questions due to JSON error")
        return sample_questions

def send_query(cache_url, question):
    """Enviar pregunta al cache service"""
    try:
        payload = {"question": question}
        response = requests.post(
            f"{cache_url}/query",
            json=payload,
            timeout=10
        )
        
        if response.status_code == 200:
            return True
        else:
            print(f"Error: HTTP {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"Connection error: {e}")
        return False

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
    
    args = parser.parse_args()
    
    # Configuración
    CACHE_URL = os.getenv('CACHE_SERVICE_URL', 'http://cache-service:8000')
    
    print("=== Traffic Generator ===")
    print(f"Distribution: {args.distribution}")
    print(f"Rate: {args.rate} req/sec")
    print(f"Duration: {args.duration} seconds")
    print(f"Cache URL: {CACHE_URL}")
    
    # Cargar preguntas
    questions = load_questions(args.dataset)
    
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
    
    # Generar tráfico
    start_time = time.time()
    request_count = 0
    success_count = 0
    
    print("Starting traffic generation...")
    
    while time.time() - start_time < args.duration:
        # Seleccionar pregunta aleatoria
        question = random.choice(questions)
        
        # Enviar query
        success = send_query(CACHE_URL, question)
        request_count += 1
        if success:
            success_count += 1
        
        # Log cada 10 requests
        if request_count % 10 == 0:
            success_rate = (success_count / request_count) * 100
            print(f"Requests: {request_count}, Success: {success_rate:.1f}%")
        
        # Esperar según la distribución
        wait_time = dist_func()
        time.sleep(wait_time)
    
    # Reporte final
    success_rate = (success_count / request_count) * 100 if request_count > 0 else 0
    print("=== Traffic Generation Complete ===")
    print(f"Total requests: {request_count}")
    print(f"Successful: {success_count}")
    print(f"Success rate: {success_rate:.1f}%")
    print(f"Duration: {time.time() - start_time:.1f} seconds")

if __name__ == "__main__":
    main()