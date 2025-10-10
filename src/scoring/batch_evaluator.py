# src/scoring/batch_evaluator.py
import json
import logging
from typing import List, Dict
from score_evaluator import ScoreEvaluator

class BatchEvaluator:
    def __init__(self):
        self.evaluator = ScoreEvaluator()
        self.logger = logging.getLogger(__name__)
    
    def evaluate_dataset(self, qa_pairs: List[Dict]) -> Dict:
        """
        Evalúa un conjunto completo de preguntas-respuestas
        """
        results = []
        total_score = 0
        
        for i, pair in enumerate(qa_pairs):
            try:
                evaluation = self.evaluator.calculate_comprehensive_score(
                    pair['expected_answer'], 
                    pair['llm_answer']
                )
                
                result = {
                    'question_id': i,
                    'question': pair['question'],
                    'expected_answer': pair['expected_answer'],
                    'llm_answer': pair['llm_answer'],
                    'evaluation': evaluation
                }
                
                results.append(result)
                total_score += evaluation['comprehensive_score']
                
                self.logger.info(f"Evaluada pregunta {i+1}/{len(qa_pairs)} - Score: {evaluation['comprehensive_score']}")
                
            except Exception as e:
                self.logger.error(f"Error evaluando pregunta {i}: {e}")
                continue
        
        # Estadísticas generales
        avg_score = total_score / len(results) if results else 0
        
        quality_distribution = {
            'Excellent': len([r for r in results if r['evaluation']['comprehensive_score'] >= 0.8]),
            'Good': len([r for r in results if 0.6 <= r['evaluation']['comprehensive_score'] < 0.8]),
            'Fair': len([r for r in results if 0.4 <= r['evaluation']['comprehensive_score'] < 0.6]),
            'Poor': len([r for r in results if 0.2 <= r['evaluation']['comprehensive_score'] < 0.4]),
            'Very Poor': len([r for r in results if r['evaluation']['comprehensive_score'] < 0.2])
        }
        
        return {
            'total_questions': len(qa_pairs),
            'evaluated_questions': len(results),
            'average_score': round(avg_score, 4),
            'quality_distribution': quality_distribution,
            'detailed_results': results
        }
    
    def save_evaluation_report(self, results: Dict, output_path: str):
        """Guarda el reporte de evaluación en un archivo JSON"""
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            self.logger.info(f"Reporte guardado en: {output_path}")
        except Exception as e:
            self.logger.error(f"Error guardando reporte: {e}")