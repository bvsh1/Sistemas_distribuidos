# src/traffic-generator/convert_dataset.py
import pandas as pd
import json
import os

def convert_csv_to_json():
    """Convierte el dataset CSV a JSON"""
    csv_path = "datasets/raw/train.csv"
    json_path = "datasets/yahoo_questions.json"
    
    if not os.path.exists(csv_path):
        print(f"Error: No se encuentra {csv_path}")
        return
    
    df = pd.read_csv(csv_path)
    print(f"Procesando {len(df)} preguntas...")
    
    questions = []
    for i, row in df.iterrows():
        # Extraer pregunta según la estructura del dataset
        if 'Question_Title' in df.columns:
            question_text = str(row['Question_Title'])
            if 'Question_Content' in df.columns and pd.notna(row['Question_Content']):
                content = str(row['Question_Content'])
                if content and content != 'nan':
                    question_text += " " + content
        elif 'question_title' in df.columns:
            question_text = str(row['question_title'])
            if 'question_content' in df.columns and pd.notna(row['question_content']):
                content = str(row['question_content'])
                if content and content != 'nan':
                    question_text += " " + content
        else:
            # Usar primeras columnas de texto
            text_cols = [col for col in df.columns if df[col].dtype == 'object']
            if text_cols:
                question_text = str(row[text_cols[0]])
            else:
                continue
        
        question_text = question_text.strip()
        if question_text and question_text != 'nan':
            questions.append(question_text)
        
        if (i + 1) % 1000 == 0:
            print(f"Procesadas {i + 1} preguntas...")
    
    # Crear directorio si no existe
    os.makedirs('datasets', exist_ok=True)
    
    # Guardar las preguntas
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(questions, f, ensure_ascii=False, indent=2)
    
    print(f"Conversion completada: {len(questions)} preguntas guardadas en {json_path}")

if __name__ == "__main__":
    convert_csv_to_json()