# src/storage/models.py
import sqlite3
import json
from datetime import datetime
from typing import Dict, List, Optional

class StorageManager:
    def __init__(self, db_path: str = "storage/qa_storage.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Inicializa la base de datos y crea las tablas si no existen"""
        import os
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Tabla principal de preguntas-respuestas
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS qa_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question TEXT UNIQUE NOT NULL,
                expected_answer TEXT NOT NULL,
                llm_answer TEXT NOT NULL,
                quality_score REAL DEFAULT 0.0,
                ask_count INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Tabla de historial de métricas (para tracking de cambios)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS quality_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question_id INTEGER,
                comprehensive_score REAL,
                semantic_similarity REAL,
                jaccard_similarity REAL,
                length_ratio REAL,
                keyword_overlap REAL,
                quality_grade TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (question_id) REFERENCES qa_records (id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def save_qa_record(self, question: str, expected_answer: str, llm_answer: str, 
                      quality_metrics: Dict, ask_count: int = 1) -> bool:
        """Guarda o actualiza un registro pregunta-respuesta"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Verificar si la pregunta ya existe
            cursor.execute(
                "SELECT id, ask_count FROM qa_records WHERE question = ?", 
                (question,)
            )
            existing = cursor.fetchone()
            
            if existing:
                # Actualizar registro existente
                record_id, current_count = existing
                cursor.execute('''
                    UPDATE qa_records 
                    SET llm_answer = ?, quality_score = ?, ask_count = ?, updated_at = ?
                    WHERE id = ?
                ''', (
                    llm_answer, 
                    quality_metrics.get('comprehensive_score', 0.0),
                    current_count + 1,
                    datetime.now(),
                    record_id
                ))
            else:
                # Insertar nuevo registro
                cursor.execute('''
                    INSERT INTO qa_records 
                    (question, expected_answer, llm_answer, quality_score, ask_count)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    question,
                    expected_answer,
                    llm_answer,
                    quality_metrics.get('comprehensive_score', 0.0),
                    ask_count
                ))
                record_id = cursor.lastrowid
            
            # Guardar métricas detalladas en historial
            cursor.execute('''
                INSERT INTO quality_metrics 
                (question_id, comprehensive_score, semantic_similarity, 
                 jaccard_similarity, length_ratio, keyword_overlap, quality_grade)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                record_id,
                quality_metrics.get('comprehensive_score', 0.0),
                quality_metrics.get('semantic_similarity', 0.0),
                quality_metrics.get('jaccard_similarity', 0.0),
                quality_metrics.get('length_ratio', 0.0),
                quality_metrics.get('keyword_overlap', 0.0),
                quality_metrics.get('quality_grade', 'Unknown')
            ))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            print(f"Error guardando registro: {e}")
            return False
    
    def get_qa_record(self, question: str) -> Optional[Dict]:
        """Obtiene un registro por pregunta"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT question, expected_answer, llm_answer, quality_score, ask_count
                FROM qa_records WHERE question = ?
            ''', (question,))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                return {
                    'question': result[0],
                    'expected_answer': result[1],
                    'llm_answer': result[2],
                    'quality_score': result[3],
                    'ask_count': result[4]
                }
            return None
            
        except Exception as e:
            print(f"Error obteniendo registro: {e}")
            return None
    
    def get_all_records(self, limit: int = 10000) -> List[Dict]:
        """Obtiene todos los registros (hasta el límite especificado)"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT question, expected_answer, llm_answer, quality_score, ask_count
                FROM qa_records 
                ORDER BY ask_count DESC 
                LIMIT ?
            ''', (limit,))
            
            records = []
            for row in cursor.fetchall():
                records.append({
                    'question': row[0],
                    'expected_answer': row[1],
                    'llm_answer': row[2],
                    'quality_score': row[3],
                    'ask_count': row[4]
                })
            
            conn.close()
            return records
            
        except Exception as e:
            print(f"Error obteniendo registros: {e}")
            return []
    
    def get_stats(self) -> Dict:
        """Obtiene estadísticas del almacenamiento"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM qa_records")
            total_records = cursor.fetchone()[0]
            
            cursor.execute("SELECT AVG(quality_score) FROM qa_records")
            avg_score = cursor.fetchone()[0] or 0.0
            
            cursor.execute("SELECT SUM(ask_count) FROM qa_records")
            total_asks = cursor.fetchone()[0] or 0
            
            conn.close()
            
            return {
                'total_records': total_records,
                'average_quality_score': round(avg_score, 4),
                'total_questions_asked': total_asks
            }
            
        except Exception as e:
            print(f"Error obteniendo estadísticas: {e}")
            return {}