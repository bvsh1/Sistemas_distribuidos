import pandas as pd
import json
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import os

class DataAnalyzer:
    def __init__(self, data_dir="analyze/data"):
        self.data_dir = data_dir
        self.setup_plotting()
    
    def setup_plotting(self):
        """Configurar estilo de plots"""
        plt.style.use('seaborn-v0_8')
        sns.set_palette("husl")
    
    def load_latest_data(self):
        """Cargar los datos más recientes"""
        files = {}
        for file_type in ['metrics', 'performance', 'cache_items']:
            pattern = f"{file_type}_*.csv" if file_type != 'cache_items' else f"{file_type}_*.json"
            matching_files = [f for f in os.listdir(self.data_dir) if f.startswith(file_type)]
            if matching_files:
                latest_file = sorted(matching_files)[-1]
                files[file_type] = os.path.join(self.data_dir, latest_file)
        
        data = {}
        
        # Cargar métricas
        if 'metrics' in files:
            data['metrics'] = pd.read_csv(files['metrics'])
            data['metrics']['timestamp'] = pd.to_datetime(data['metrics']['timestamp'])
        
        # Cargar performance
        if 'performance' in files:
            data['performance'] = pd.read_csv(files['performance'])
        
        # Cargar cache items
        if 'cache_items' in files:
            with open(files['cache_items'], 'r', encoding='utf-8') as f:
                data['cache_items'] = json.load(f)
        
        return data
    
    def analyze_metrics(self, metrics_df):
        """Analizar métricas temporales"""
        print("=== ANÁLISIS DE MÉTRICAS TEMPORALES ===")
        
        # Estadísticas básicas
        print(f"📈 Período de análisis: {len(metrics_df)} puntos")
        print(f"🎯 Hit Rate promedio: {metrics_df['hit_rate'].mean():.3f}")
        print(f"🎯 Hit Rate máximo: {metrics_df['hit_rate'].max():.3f}")
        print(f"🎯 Hit Rate mínimo: {metrics_df['hit_rate'].min():.3f}")
        print(f"📊 Total de requests: {metrics_df['total_requests'].iloc[-1]:,}")
        print(f"💾 Uso máximo del cache: {metrics_df['cache_size'].max()}/{metrics_df['max_cache_size'].iloc[0]}")
        
        # Tendencias
        metrics_df['time_minutes'] = (metrics_df['timestamp'] - metrics_df['timestamp'].min()).dt.total_seconds() / 60
        
        return metrics_df
    
    def analyze_performance(self, perf_df):
        """Analizar datos de performance"""
        print("\n=== ANÁLISIS DE PERFORMANCE ===")
        
        cache_hits = perf_df[perf_df['cache_hit'] == True]
        cache_misses = perf_df[perf_df['cache_hit'] == False]
        
        print(f"🔍 Total de queries testeadas: {len(perf_df)}")
        print(f"✅ Cache hits: {len(cache_hits)} ({len(cache_hits)/len(perf_df)*100:.1f}%)")
        print(f"❌ Cache misses: {len(cache_misses)} ({len(cache_misses)/len(perf_df)*100:.1f}%)")
        
        if len(cache_hits) > 0:
            print(f"⚡ Tiempo respuesta cache hits: {cache_hits['response_time'].mean():.3f}s")
        if len(cache_misses) > 0:
            print(f"⚡ Tiempo respuesta cache misses: {cache_misses['response_time'].mean():.3f}s")
        
        # Mejora de performance
        if len(cache_hits) > 0 and len(cache_misses) > 0:
            improvement = (cache_misses['response_time'].mean() - cache_hits['response_time'].mean()) / cache_misses['response_time'].mean() * 100
            print(f"🚀 Mejora con cache: {improvement:.1f}% más rápido")
        
        return perf_df
    
    def analyze_cache_items(self, cache_items):
        """Analizar items del cache"""
        if not cache_items or cache_items['total_items'] == 0:
            print("\n💾 Cache vacío")
            return
        
        items = cache_items['items']
        print(f"\n=== ANÁLISIS DEL CACHE ===")
        print(f"📦 Items en cache: {len(items)}")
        
        # Estadísticas de acceso
        access_counts = [item.get('access_count', 0) for item in items]
        response_lengths = [item.get('value_length', 0) for item in items]
        
        print(f"📊 Accesos promedio por item: {sum(access_counts)/len(access_counts):.1f}")
        print(f"📏 Longitud promedio de respuesta: {sum(response_lengths)/len(response_lengths):.0f} caracteres")
        print(f"🔢 Máximo de accesos: {max(access_counts) if access_counts else 0}")
        
        # Items más accedidos
        if access_counts:
            top_items = sorted(items, key=lambda x: x.get('access_count', 0), reverse=True)[:5]
            print(f"\n🏆 Top 5 items más accedidos:")
            for i, item in enumerate(top_items, 1):
                print(f"   {i}. {item['key']} (accesos: {item.get('access_count', 0)})")
    
    def create_visualizations(self, metrics_df, perf_df, cache_items):
        """Crear visualizaciones"""
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        fig.suptitle('Análisis del Sistema de Cache', fontsize=16, fontweight='bold')
        
        # 1. Evolución del Hit Rate
        if len(metrics_df) > 1:
            axes[0,0].plot(metrics_df['time_minutes'], metrics_df['hit_rate'] * 100, linewidth=2)
            axes[0,0].set_title('Evolución del Hit Rate')
            axes[0,0].set_xlabel('Tiempo (minutos)')
            axes[0,0].set_ylabel('Hit Rate (%)')
            axes[0,0].grid(True, alpha=0.3)
        
        # 2. Distribución de tiempos de respuesta
        if len(perf_df) > 0:
            cache_hits = perf_df[perf_df['cache_hit'] == True]['response_time']
            cache_misses = perf_df[perf_df['cache_hit'] == False]['response_time']
            
            data_to_plot = []
            labels = []
            if len(cache_hits) > 0:
                data_to_plot.append(cache_hits)
                labels.append('Cache Hits')
            if len(cache_misses) > 0:
                data_to_plot.append(cache_misses)
                labels.append('Cache Misses')
            
            if data_to_plot:
                axes[0,1].boxplot(data_to_plot, labels=labels)
                axes[0,1].set_title('Tiempos de Respuesta')
                axes[0,1].set_ylabel('Segundos')
        
        # 3. Uso del cache over time
        if len(metrics_df) > 1:
            axes[1,0].plot(metrics_df['time_minutes'], metrics_df['cache_size'], linewidth=2, color='orange')
            axes[1,0].axhline(y=metrics_df['max_cache_size'].iloc[0], color='red', linestyle='--', alpha=0.7, label='Límite')
            axes[1,0].set_title('Uso del Cache Over Time')
            axes[1,0].set_xlabel('Tiempo (minutos)')
            axes[1,0].set_ylabel('Items en Cache')
            axes[1,0].legend()
            axes[1,0].grid(True, alpha=0.3)
        
        # 4. Distribución de hits vs misses
        if len(metrics_df) > 0:
            last_stats = metrics_df.iloc[-1]
            hits_misses = [last_stats['hits'], last_stats['misses']]
            axes[1,1].pie(hits_misses, labels=['Hits', 'Misses'], autopct='%1.1f%%', startangle=90)
            axes[1,1].set_title('Distribución Hits vs Misses (Final)')
        
        plt.tight_layout()
        plt.savefig('analyze/analysis_report.png', dpi=300, bbox_inches='tight')
        plt.show()
    
    def generate_report(self, data):
        """Generar reporte completo"""
        print("=" * 50)
        print("📊 REPORTE DE ANÁLISIS DEL SISTEMA DE CACHE")
        print("=" * 50)
        
        if 'metrics' in data:
            metrics_df = self.analyze_metrics(data['metrics'])
        else:
            metrics_df = None
        
        if 'performance' in data:
            perf_df = self.analyze_performance(data['performance'])
        else:
            perf_df = None
        
        if 'cache_items' in data:
            self.analyze_cache_items(data['cache_items'])
        
        # Crear visualizaciones si hay datos suficientes
        if metrics_df is not None and perf_df is not None:
            self.create_visualizations(metrics_df, perf_df, data.get('cache_items'))
        
        print("\n" + "=" * 50)
        print("✅ ANÁLISIS COMPLETADO")
        print("=" * 50)

def main():
    analyzer = DataAnalyzer()
    
    # Cargar datos
    print("Cargando datos más recientes...")
    data = analyzer.load_latest_data()
    
    if not data:
        print("No se encontraron datos para analizar. Ejecuta primero extract_data.py")
        return
    
    # Generar reporte
    analyzer.generate_report(data)

if __name__ == "__main__":
    main()