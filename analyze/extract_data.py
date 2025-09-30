import json
import requests
import pandas as pd
import time
from datetime import datetime
import os

class DataExtractor:
    def __init__(self, cache_url="http://localhost:8000", llm_url="http://localhost:5000"):
        self.cache_url = cache_url
        self.llm_url = llm_url
        self.data_dir = "analyze/data"
        os.makedirs(self.data_dir, exist_ok=True)
    
    def get_cache_stats(self):
        """Obtener estadísticas del cache"""
        try:
            response = requests.get(f"{self.cache_url}/cache/stats", timeout=5)
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            print(f"Error obteniendo stats del cache: {e}")
        return None
    
    def get_cache_items(self):
        """Obtener items del cache"""
        try:
            response = requests.get(f"{self.cache_url}/cache/items", timeout=5)
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            print(f"Error obteniendo items del cache: {e}")
        return None
    
    def get_health_status(self):
        """Obtener estado de salud de los servicios"""
        services = {}
        for service, url in [('cache', self.cache_url), ('llm', self.llm_url)]:
            try:
                response = requests.get(f"{url}/health", timeout=5)
                services[service] = response.json() if response.status_code == 200 else None
            except:
                services[service] = None
        return services
    
    def test_query_performance(self, questions, sample_size=10):
        """Medir performance de queries"""
        results = []
        sample_questions = questions[:sample_size] if len(questions) > sample_size else questions
        
        for i, question in enumerate(sample_questions):
            try:
                start_time = time.time()
                response = requests.post(
                    f"{self.cache_url}/query",
                    json={"question": question},
                    timeout=30
                )
                response_time = time.time() - start_time
                
                if response.status_code == 200:
                    data = response.json()
                    results.append({
                        'question': question,
                        'response_time': response_time,
                        'source': data.get('source', 'unknown'),
                        'cache_hit': data.get('cache_hit', False),
                        'response_length': len(data.get('response', ''))
                    })
                else:
                    results.append({
                        'question': question,
                        'response_time': response_time,
                        'source': 'error',
                        'cache_hit': False,
                        'response_length': 0
                    })
                
                print(f"Tested {i+1}/{len(sample_questions)}: {response_time:.2f}s")
                
            except Exception as e:
                print(f"Error testing query: {e}")
                results.append({
                    'question': question,
                    'response_time': -1,
                    'source': 'error',
                    'cache_hit': False,
                    'response_length': 0
                })
        
        return results
    
    def collect_metrics_over_time(self, duration=300, interval=10):
        """Recolectar métricas durante un período de tiempo"""
        metrics = []
        start_time = time.time()
        end_time = start_time + duration
        
        print(f"Recolectando métricas por {duration} segundos...")
        
        while time.time() < end_time:
            try:
                timestamp = datetime.now().isoformat()
                
                # Obtener stats del cache
                cache_stats = self.get_cache_stats()
                health_status = self.get_health_status()
                
                if cache_stats:
                    metric = {
                        'timestamp': timestamp,
                        'hits': cache_stats['hits'],
                        'misses': cache_stats['misses'],
                        'hit_rate': cache_stats['hit_rate'],
                        'total_requests': cache_stats['total_requests'],
                        'cache_size': cache_stats['current_size'],
                        'max_cache_size': cache_stats['max_size'],
                        'cache_policy': cache_stats['policy']
                    }
                    metrics.append(metric)
                    print(f"[{timestamp}] Hit Rate: {cache_stats['hit_rate']:.3f}")
                
                time.sleep(interval)
                
            except KeyboardInterrupt:
                print("Interrumpido por usuario")
                break
            except Exception as e:
                print(f"Error recolectando métricas: {e}")
                time.sleep(interval)
        
        return metrics
    
    def save_data(self, metrics, performance_data, cache_items, filename_suffix=""):
        """Guardar todos los datos recolectados"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        suffix = f"_{filename_suffix}" if filename_suffix else ""
        
        # Guardar métricas temporales
        if metrics:
            metrics_df = pd.DataFrame(metrics)
            metrics_file = f"{self.data_dir}/metrics_{timestamp}{suffix}.csv"
            metrics_df.to_csv(metrics_file, index=False)
            print(f"Métricas guardadas: {metrics_file}")
        
        # Guardar datos de performance
        if performance_data:
            perf_df = pd.DataFrame(performance_data)
            perf_file = f"{self.data_dir}/performance_{timestamp}{suffix}.csv"
            perf_df.to_csv(perf_file, index=False)
            print(f"Datos de performance guardados: {perf_file}")
        
        # Guardar items del cache
        if cache_items:
            cache_file = f"{self.data_dir}/cache_items_{timestamp}{suffix}.json"
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_items, f, indent=2, ensure_ascii=False)
            print(f"Items del cache guardados: {cache_file}")
        
        return {
            'metrics_file': metrics_file if metrics else None,
            'performance_file': perf_file if performance_data else None,
            'cache_file': cache_file if cache_items else None
        }

def main():
    extractor = DataExtractor()
    
    # Cargar preguntas de prueba
    try:
        with open('datasets/10000_sample.json', 'r', encoding='utf-8') as f:
            questions = json.load(f)
        print(f"Loaded {len(questions)} questions for testing")
    except:
        print("No se pudo cargar el dataset de preguntas")
        questions = ["What is AI?", "What is machine learning?", "What is Python?"]
    
    print("=== EXTRACCIÓN DE DATOS DEL SISTEMA ===")
    
    # 1. Recolectar métricas durante 5 minutos
    print("\n1. Recolectando métricas en tiempo real...")
    metrics = extractor.collect_metrics_over_time(duration=300, interval=15)
    
    # 2. Test de performance
    print("\n2. Ejecutando tests de performance...")
    performance_data = extractor.test_query_performance(questions, sample_size=20)
    
    # 3. Obtener items del cache
    print("\n3. Obteniendo items del cache...")
    cache_items = extractor.get_cache_items()
    
    # 4. Guardar todos los datos
    print("\n4. Guardando datos...")
    files = extractor.save_data(metrics, performance_data, cache_items, "full_analysis")
    
    # 5. Resumen
    print("\n=== RESUMEN DE DATOS EXTRAÍDOS ===")
    if metrics:
        hit_rates = [m['hit_rate'] for m in metrics]
        avg_hit_rate = sum(hit_rates) / len(hit_rates)
        print(f"Métricas recolectadas: {len(metrics)} puntos")
        print(f"Hit Rate promedio: {avg_hit_rate:.3f}")
    
    if performance_data:
        cache_hits = sum(1 for p in performance_data if p['cache_hit'])
        avg_response_time = sum(p['response_time'] for p in performance_data if p['response_time'] > 0) / len(performance_data)
        print(f"Tests de performance: {len(performance_data)} queries")
        print(f"Cache hits en test: {cache_hits}/{len(performance_data)}")
        print(f"Tiempo respuesta promedio: {avg_response_time:.2f}s")
    
    if cache_items:
        print(f"Items en cache: {cache_items.get('total_items', 0)}")
    
    print(f"\nDatos guardados en: analyze/data/")

if __name__ == "__main__":
    main()