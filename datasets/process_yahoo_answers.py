import pandas as pd
import json
import os
import random
from pathlib import Path

def explore_dataset(file_path):
    """Explorar la estructura de un archivo CSV"""
    print(f"Explorando: {file_path}")
    try:
        df = pd.read_csv(file_path, nrows=10)
        print(f"   Columnas: {df.columns.tolist()}")
        print(f"   Forma: {df.shape}")
        print(f"   Tipos de datos:")
        for col in df.columns:
            print(f"     - {col}: {df[col].dtype}")
        print(f"   Ejemplo de contenido:")
        for i, row in df.iterrows():
            print(f"     Fila {i}: {dict(row)}")
        print()
        return df.columns.tolist()
    except Exception as e:
        print(f"   Error: {e}")
        return []

def process_yahoo_dataset():
    print("=== PROCESANDO DATASET YAHOO ANSWERS ===")
    
    raw_dir = Path("datasets/raw")
    
    # Verificar archivos
    files = list(raw_dir.glob("*.csv"))
    print(f"Archivos encontrados: {[f.name for f in files]}")
    
    # Explorar ambos archivos
    train_cols = explore_dataset(raw_dir / "train.csv")
    test_cols = explore_dataset(raw_dir / "test.csv")
    
    # Elegir el archivo a procesar (train.csv generalmente tiene más datos)
    file_to_process = raw_dir / "train.csv"
    print(f"Procesando: {file_to_process.name}")
    
    try:
        # Leer el archivo seleccionado
        print("Leyendo dataset...")
        
        # Primero identificar la columna de preguntas
        df_sample = pd.read_csv(file_to_process, nrows=100)
        
        # Buscar columnas potenciales para preguntas
        question_candidates = []
        for col in df_sample.columns:
            col_lower = col.lower()
            # Posibles nombres de columnas que contienen preguntas
            if any(keyword in col_lower for keyword in ['question', 'title', 'content', 'text', 'input', 'query']):
                question_candidates.append(col)
            elif df_sample[col].dtype == 'object' and df_sample[col].str.len().mean() > 10:
                question_candidates.append(col)
        
        print(f"Candidatos a columna de preguntas: {question_candidates}")
        
        if not question_candidates:
            # Usar la primera columna de texto
            for col in df_sample.columns:
                if df_sample[col].dtype == 'object':
                    question_candidates.append(col)
                    break
        
        question_col = question_candidates[0] if question_candidates else df_sample.columns[0]
        print(f"Usando columna: {question_col}")
        
        # Leer el dataset en chunks para manejar archivos grandes
        print("Procesando datos...")
        all_questions = []
        
        for chunk in pd.read_csv(file_to_process, usecols=[question_col], chunksize=5000):
            # Limpiar y filtrar preguntas en cada chunk
            chunk_questions = chunk[question_col].dropna().astype(str).tolist()
            
            for q in chunk_questions:
                q_clean = q.strip()
                # Filtrar preguntas por longitud y contenido
                if (20 <= len(q_clean) <= 500 and 
                    not q_clean.startswith('http') and
                    len(q_clean.split()) >= 3):  # Al menos 3 palabras
                    all_questions.append(q_clean)
            
            print(f"   Procesadas {len(all_questions)} preguntas...")
            
            # Limitar para no usar demasiada memoria
            if len(all_questions) >= 10000:
                break
        
        print(f"Total de preguntas recolectadas: {len(all_questions)}")
        
        if not all_questions:
            print("No se encontraron preguntas válidas")
            return False
        
        # Tomar muestra aleatoria
        sample_size = min(300, len(all_questions))
        sampled_questions = random.sample(all_questions, sample_size)
        
        # Guardar
        output_file = "datasets/yahoo_questions.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(sampled_questions, f, indent=2, ensure_ascii=False)
        
        print(f"Guardadas {len(sampled_questions)} preguntas en: {output_file}")
        
        # Mostrar ejemplos
        print("\nEJEMPLOS DE PREGUNTAS:")
        print("-" * 50)
        for i, q in enumerate(sampled_questions[:10]):
            print(f"{i+1:2d}. {q}")
        print("-" * 50)
        
        # Estadísticas
        avg_length = sum(len(q) for q in sampled_questions) / len(sampled_questions)
        avg_words = sum(len(q.split()) for q in sampled_questions) / len(sampled_questions)
        print(f"Estadísticas:")
        print(f"   - Longitud promedio: {avg_length:.1f} caracteres")
        print(f"   - Palabras promedio: {avg_words:.1f} palabras")
        print(f"   - Rango: {min(len(q) for q in sampled_questions)} - {max(len(q) for q in sampled_questions)} caracteres")
        
        return True
        
    except Exception as e:
        print(f"Error procesando el dataset: {e}")
        import traceback
        traceback.print_exc()
        return False

def create_fallback_dataset():
    """Crear dataset de ejemplo si falla el procesamiento"""
    sample_questions = [
        "What is the capital of France and what are its main tourist attractions?",
        "How does machine learning differ from traditional programming approaches?",
        "What are the main benefits of using Docker containers in software development?",
        "How can someone improve their problem-solving skills in computer programming?",
        "What is the difference between artificial intelligence and human intelligence?",
        "How do distributed systems handle network failures and maintain consistency?",
        "What are the best practices for designing scalable database architectures?",
        "How does cloud computing help reduce IT infrastructure costs for businesses?",
        "What are the key differences between Python and Java programming languages?",
        "How does the internet work from a technical perspective?"
    ]
    
    with open('datasets/yahoo_questions.json', 'w', encoding='utf-8') as f:
        json.dump(sample_questions, f, indent=2, ensure_ascii=False)
    
    print("Dataset de ejemplo creado: datasets/yahoo_questions.json")
    return sample_questions

if __name__ == "__main__":
    success = process_yahoo_dataset()
    
    if not success:
        print("\nCreando dataset de ejemplo como respaldo...")
        create_fallback_dataset()