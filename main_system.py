# main_system.py
import pandas as pd
import logging
from scoring import ScoreEvaluator
from storage import StorageManager

class AnalysisSystem:
    def __init__(self, db_path='data/yahoo_answers_analysis.db'):
        """Sistema principal de análisis"""
        self.score_evaluator = ScoreEvaluator()
        self.storage_manager = StorageManager(db_path)
        self.setup_logging()
    
    def setup_logging(self):
        """Configura el sistema de logging"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
    def process_question(self, question_data, llm_answer, access_count=1):
        """Procesa una pregunta completa: evalúa score y almacena"""
        try:
            self.logger.info(f"Procesando pregunta ID: {question_data['question_id']}")
            
            # Calcular scores
            score_data = self.score_evaluator.calculate_comprehensive_score(
                question_data['original_answer'],
                llm_answer
            )
            
            # Preparar datos para almacenamiento
            storage_data = {
                'question_id': question_data['question_id'],
                'question_title': question_data.get('question_title', ''),
                'question_content': question_data.get('question_content', ''),
                'original_answer': question_data['original_answer'],
                'llm_answer': llm_answer
            }
            
            # Almacenar en base de datos
            success = self.storage_manager.store_question_response(
                storage_data, score_data, access_count
            )
            
            if success:
                self.logger.info(f"Pregunta {question_data['question_id']} procesada. Score: {score_data['comprehensive_score']:.3f}")
                
                return {
                    'success': True,
                    'question_id': question_data['question_id'],
                    'scores': score_data
                }
            else:
                return {
                    'success': False,
                    'error': 'Error almacenando en base de datos'
                }
            
        except Exception as e:
            self.logger.error(f"Error procesando pregunta: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def generate_report(self):
        """Genera un reporte completo del análisis"""
        try:
            stats = self.storage_manager.get_question_stats()
            
            report = {
                'resumen_general': {
                    'total_preguntas_procesadas': stats.get('total_questions', 0),
                    'score_promedio': round(stats.get('average_score', 0), 3),
                    'total_accesos': stats.get('total_accesses', 0),
                    'preguntas_mas_accedidas': stats.get('top_accessed', pd.DataFrame()).to_dict('records')
                },
                'distribucion_scores': stats.get('score_distribution', pd.DataFrame()).to_dict('records')
            }
            
            return report
            
        except Exception as e:
            self.logger.error(f"Error generando reporte: {e}")
            return {'error': str(e)}
    
    def export_data(self, filename='data/analysis_export.csv'):
        """Exporta los datos a CSV"""
        return self.storage_manager.export_to_csv(filename)

# Ejemplo de uso
if __name__ == "__main__":
    # Inicializar sistema
    system = AnalysisSystem()
    
    # Ejemplo de datos de pregunta
    sample_question = {
        'question_id': 1,
        'question_title': '¿Cómo aprender programación?',
        'question_content': 'Quiero aprender programación desde cero, ¿por dónde debo empezar?',
        'original_answer': 'Te recomiendo empezar con Python, es un lenguaje sencillo con mucha demanda. Puedes usar plataformas como freeCodeCamp o Coursera.'
    }
    
    # Respuesta simulada del LLM
    llm_response = 'Para aprender programación desde cero, sugiero comenzar con Python por su sintaxis clara. Utiliza recursos online como Codecademy o edX para cursos gratuitos.'
    
    # Procesar pregunta
    result = system.process_question(sample_question, llm_response)
    print("Resultado del procesamiento:", result)
    
    # Generar reporte
    report = system.generate_report()
    print("Reporte:", report)
    
    # Exportar datos
    export_result = system.export_data()
    print("Exportación:", export_result)