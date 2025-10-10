# src/scoring/run_Evaluation.py (CORREGIDO)
import json
import logging
import requests
from batch_evaluator import BatchEvaluator

def get_llm_answer(question):
    """Obtener respuesta del LLM para una pregunta"""
    try:
        response = requests.post(
            "http://localhost:5000/query",
            json={"question": question},
            timeout=30
        )
        if response.status_code == 200:
            return response.json().get('response', '')
        else:
            return f"Error: {response.status_code}"
    except Exception as e:
        return f"Error: {str(e)}"

def main():
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    # Dataset de prueba (sin respuestas esperadas reales)
    qa_pairs = [
        {
            "question": "¿Qué es Python?",
            "expected_answer": "Python es un lenguaje de programación interpretado de alto nivel y de propósito general.",
            "llm_answer": "Python es un lenguaje de programación que se interpreta y es multipropósito."
        },
        {
            "question": "¿Qué es machine learning?",
            "expected_answer": "El machine learning es una rama de la inteligencia artificial que permite a las computadoras aprender sin ser programadas explícitamente.",
            "llm_answer": "Machine learning es un campo de la IA donde las máquinas aprenden patrones de datos."
        },
        {
            "question": "¿Qué es Docker?",
            "expected_answer": "Docker es una plataforma que permite desarrollar, enviar y ejecutar aplicaciones en contenedores.",
            "llm_answer": "Docker es una herramienta para crear y gestionar contenedores de aplicaciones."
        }
    ]
    
    # Ejecutar evaluación
    evaluator = BatchEvaluator()
    results = evaluator.evaluate_dataset(qa_pairs)
    
    print(f"\n=== RESULTADOS DE EVALUACIÓN ===")
    print(f"Preguntas evaluadas: {results['evaluated_questions']}")
    print(f"Score promedio: {results['average_score']:.3f}")
    print(f"Distribución de calidad: {results['quality_distribution']}")
    
    # Mostrar resultados detallados
    print(f"\n--- Resultados Detallados ---")
    for result in results['detailed_results']:
        score = result['evaluation']['comprehensive_score']
        grade = result['evaluation']['quality_grade']
        print(f"Pregunta: {result['question'][:50]}...")
        print(f"  Score: {score:.3f} ({grade})")

if __name__ == '__main__':
    main()