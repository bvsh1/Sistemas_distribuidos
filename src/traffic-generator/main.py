import argparse
import time
import random
import requests
import json
import sys
import os
from distributions import TrafficDistributions

def load_questions(dataset_path="datasets/yahoo_questions.json", num_questions=10000):
    try:
        with open(dataset_path, 'r', encoding='utf-8') as f:
            questions = json.load(f)
            print(f"Loaded {len(questions)} questions from {dataset_path}")
            
            if questions and isinstance(questions[0], str):
                return questions[:num_questions]
            elif questions and isinstance(questions[0], dict):
                if 'question' in questions[0]:
                    questions = [q['question'] for q in questions]
                elif 'text' in questions[0]:
                    questions = [q['text'] for q in questions]
                return questions[:num_questions]
            else:
                raise ValueError("Formato de dataset no reconocido")
            
    except FileNotFoundError:
        print(f"Dataset file {dataset_path} not found")
        return get_fallback_questions()[:num_questions]
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON from {dataset_path}: {e}")
        return get_fallback_questions()[:num_questions]

def get_fallback_questions():
    return [
        "What is Python?", "What is Docker?", "What is machine learning?",
        "What are distributed systems?", "How to learn programming?",
        "What is cloud computing?", "What is an API?", "How to deploy applications?",
        "What is artificial intelligence?", "What is data science?"
    ]

def send_query(cache_url, question):
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
            cache_hit = data.get('cache_hit', False)
            response_preview = data.get('response', '')[:80] + '...' if len(data.get('response', '')) > 80 else data.get('response', '')
            
            cache_status = "HIT" if cache_hit else "MISS"
            color_code = "\033[92m" if cache_hit else "\033[93m"  # Verde para HIT, Amarillo para MISS
            reset_code = "\033[0m"
            
            print(f"  [{color_code}{cache_status}{reset_code}] from {source}: {response_preview}")
            return True, cache_hit
        else:
            print(f"  Error: HTTP {response.status_code} - {response.text}")
            return False, False
            
    except requests.exceptions.RequestException as e:
        print(f"  Connection error: {e}")
        return False, False

def get_cache_stats(cache_url):
    try:
        response = requests.get(f"{cache_url}/cache/stats", timeout=5)
        if response.status_code == 200:
            return response.json()
    except:
        pass
    return None

def main():
    parser = argparse.ArgumentParser(description='Traffic Generator for QA System')
    parser.add_argument('--distribution', type=str, default='poisson', 
                       choices=['constant', 'poisson', 'bursty', 'sinusoidal'],
                       help='Traffic distribution type')
    parser.add_argument('--rate', type=float, default=2.0, 
                       help='Requests per second')
    parser.add_argument('--duration', type=int, default=60,
                       help='Duration in seconds')
    parser.add_argument('--dataset', type=str, default='datasets/yahoo_questions.json',
                       help='Path to questions dataset')
    parser.add_argument('--max-questions', type=int, default=50,
                       help='Maximum number of questions to use')
    
    args = parser.parse_args()
    
    CACHE_URL = os.getenv('CACHE_SERVICE_URL', 'http://localhost:8000')
    
    print("=== Traffic Generator with Cache ===")
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
    elif args.distribution == 'poisson':
        dist_func = distributions.poisson_rate(args.rate)
    elif args.distribution == 'bursty':
        dist_func = distributions.bursty_traffic(args.rate, burst_factor=5.0)
    elif args.distribution == 'sinusoidal':
        dist_func = distributions.sinusoidal_rate(args.rate, amplitude=0.5, period=60.0)
    else:
        dist_func = distributions.poisson_rate(args.rate)
    
    # Estadísticas
    start_time = time.time()
    request_count = 0
    success_count = 0
    cache_hits = 0
    cache_misses = 0
    
    print("Starting traffic generation...")
    print("Cache HIT = \033[92mGREEN\033[0m, Cache MISS = \033[93mYELLOW\033[0m")
    
    try:
        while time.time() - start_time < args.duration:
            # Seleccionar pregunta (con algo de repetición para probar cache)
            if random.random() < 0.3 and request_count > 10:  # 30% de repetir preguntas anteriores
                question = random.choice(questions[:min(10, len(questions))])
            else:
                question = random.choice(questions)
            
            print(f"Request {request_count + 1}: {question}")
            
            # Enviar query
            success, cache_hit = send_query(CACHE_URL, question)
            request_count += 1
            if success:
                success_count += 1
                if cache_hit:
                    cache_hits += 1
                else:
                    cache_misses += 1
            
            # Mostrar estadísticas cada 10 requests
            if request_count % 10 == 0:
                success_rate = (success_count / request_count) * 100
                cache_hit_rate = (cache_hits / (cache_hits + cache_misses)) * 100 if (cache_hits + cache_misses) > 0 else 0
                elapsed = time.time() - start_time
                
                print(f"\n--- Progress Report ---")
                print(f"Requests: {request_count}, Success: {success_rate:.1f}%")
                print(f"Cache Hits: {cache_hits}, Misses: {cache_misses}, Hit Rate: {cache_hit_rate:.1f}%")
                print(f"Elapsed: {elapsed:.1f}s")
                
                # Mostrar estadísticas del servidor cache
                stats = get_cache_stats(CACHE_URL)
                if stats:
                    print(f"Server Cache - Hits: {stats['hits']}, Misses: {stats['misses']}, Hit Rate: {stats['hit_rate']*100:.1f}%")
                print("-----------------------\n")
            
            # Esperar según la distribución
            wait_time = dist_func()
            time.sleep(wait_time)
    
    except KeyboardInterrupt:
        print("Traffic generation interrupted by user")
    
    # Reporte final
    success_rate = (success_count / request_count) * 100 if request_count > 0 else 0
    cache_hit_rate = (cache_hits / (cache_hits + cache_misses)) * 100 if (cache_hits + cache_misses) > 0 else 0
    actual_duration = time.time() - start_time
    actual_rate = request_count / actual_duration if actual_duration > 0 else 0
    
    print("\n=== Traffic Generation Complete ===")
    print(f"Total requests: {request_count}")
    print(f"Successful: {success_count} ({success_rate:.1f}%)")
    print(f"Cache Hits: {cache_hits}")
    print(f"Cache Misses: {cache_misses}")
    print(f"Cache Hit Rate: {cache_hit_rate:.1f}%")
    print(f"Actual duration: {actual_duration:.1f} seconds")
    print(f"Actual rate: {actual_rate:.2f} req/sec")
    
    # Estadísticas finales del servidor
    stats = get_cache_stats(CACHE_URL)
    if stats:
        print(f"\n=== Server Cache Statistics ===")
        print(f"Policy: {stats['policy']}")
        print(f"Size: {stats['current_size']}/{stats['max_size']}")
        print(f"Total Hits: {stats['hits']}")
        print(f"Total Misses: {stats['misses']}")
        print(f"Total Hit Rate: {stats['hit_rate']*100:.2f}%")

if __name__ == "__main__":
    main()