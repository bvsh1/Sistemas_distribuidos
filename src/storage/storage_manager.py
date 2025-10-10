# storage/storage_manager.py
import sqlite3
import json
import pandas as pd
from datetime import datetime
import logging
import os

class StorageManager:
    def __init__(self, db_path='data/yahoo_answers_analysis.db'):
        """Inicializa el gestor de almacenamiento"""
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
        self.setup_database()
    
    def setup_database(self):
        """Crea la estructura de la base de datos"""
        try:
            # Crear directorio si no existe
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS questions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    question_id INTEGER UNIQUE,
                    question_title TEXT,
                    question_content TEXT,
                    original_answer TEXT,
                    llm_answer TEXT,
                    comprehensive_score REAL,
                    cosine_similarity REAL,
                    jaccard_similarity REAL,
                    length_ratio REAL,
                    access_count INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS cache_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    hit_rate REAL,
                    miss_rate REAL,
                    cache_size INTEGER,
                    distribution_type TEXT
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS system_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    module TEXT,
                    level TEXT,
                    message TEXT
                )
            ''')
            
            conn.commit()
            conn.close()
            self.logger.info("Base de datos inicializada correctamente")
            
        except Exception as e:
            self.logger.error(f"Error inicializando base de datos: {e}")
    
    def store_question_response(self, question_data, score_data, access_count=1):
        """Almacena una pregunta con sus respuestas y scores"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Verificar si la pregunta ya existe
            cursor.execute(
                'SELECT id, access_count FROM questions WHERE question_id = ?',
                (question_data['question_id'],)
            )
            
            existing_record = cursor.fetchone()
            
            if existing_record:
                # Actualizar registro existente
                cursor.execute('''
                    UPDATE questions 
                    SET access_count = access_count + ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE question_id = ?
                ''', (access_count, question_data['question_id']))
            else:
                # Insertar nuevo registro
                cursor.execute('''
                    INSERT INTO questions (
                        question_id, question_title, question_content,
                        original_answer, llm_answer, comprehensive_score,
                        cosine_similarity, jaccard_similarity, length_ratio,
                        access_count
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    question_data['question_id'],
                    question_data['question_title'],
                    question_data['question_content'],
                    question_data['original_answer'],
                    question_data['llm_answer'],
                    score_data['comprehensive_score'],
                    score_data['cosine_similarity'],
                    score_data['jaccard_similarity'],
                    score_data['length_ratio'],
                    access_count
                ))
            
            conn.commit()
            conn.close()
            self.logger.debug(f"Pregunta {question_data['question_id']} almacenada/actualizada")
            return True
            
        except Exception as e:
            self.logger.error(f"Error almacenando pregunta: {e}")
            return False
    
    def store_cache_metrics(self, hit_rate, miss_rate, cache_size, distribution_type):
        """Almacena métricas del sistema de cache"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO cache_metrics (hit_rate, miss_rate, cache_size, distribution_type)
                VALUES (?, ?, ?, ?)
            ''', (hit_rate, miss_rate, cache_size, distribution_type))
            
            conn.commit()
            conn.close()
            self.logger.info(f"Métricas de cache almacenadas: Hit Rate {hit_rate:.3f}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error almacenando métricas de cache: {e}")
            return False
    
    def get_question_stats(self):
        """Obtiene estadísticas generales de las preguntas"""
        try:
            conn = sqlite3.connect(self.db_path)
            
            stats = {}
            
            # Estadísticas básicas
            stats['total_questions'] = pd.read_sql(
                'SELECT COUNT(*) as count FROM questions', conn
            ).iloc[0]['count']
            
            stats['average_score'] = pd.read_sql(
                'SELECT AVG(comprehensive_score) as avg_score FROM questions', conn
            ).iloc[0]['avg_score']
            
            stats['total_accesses'] = pd.read_sql(
                'SELECT SUM(access_count) as total FROM questions', conn
            ).iloc[0]['total']
            
            stats['top_accessed'] = pd.read_sql('''
                SELECT question_id, question_title, access_count 
                FROM questions 
                ORDER BY access_count DESC 
                LIMIT 10
            ''', conn)
            
            stats['score_distribution'] = pd.read_sql('''
                SELECT 
                    CASE 
                        WHEN comprehensive_score >= 0.8 THEN 'Excelente (0.8-1.0)'
                        WHEN comprehensive_score >= 0.6 THEN 'Bueno (0.6-0.79)'
                        WHEN comprehensive_score >= 0.4 THEN 'Regular (0.4-0.59)'
                        ELSE 'Bajo (0.0-0.39)'
                    END as score_range,
                    COUNT(*) as count
                FROM questions
                GROUP BY score_range
                ORDER BY score_range
            ''', conn)
            
            conn.close()
            return stats
            
        except Exception as e:
            self.logger.error(f"Error obteniendo estadísticas: {e}")
            return {}
    
    def export_to_csv(self, filename='data/yahoo_analysis_export.csv'):
        """Exporta los datos a CSV para análisis externo"""
        try:
            conn = sqlite3.connect(self.db_path)
            
            df = pd.read_sql('''
                SELECT 
                    question_id,
                    question_title,
                    question_content,
                    original_answer,
                    llm_answer,
                    comprehensive_score,
                    cosine_similarity,
                    jaccard_similarity,
                    length_ratio,
                    access_count,
                    created_at
                FROM questions
            ''', conn)
            
            os.makedirs('data', exist_ok=True)
            df.to_csv(filename, index=False, encoding='utf-8')
            conn.close()
            
            self.logger.info(f"Datos exportados a {filename}")
            return f"Datos exportados a {filename}"
            
        except Exception as e:
            self.logger.error(f"Error exportando datos: {e}")
            return f"Error en exportación: {e}"