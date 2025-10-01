# src/scoring/score_evaluator.py
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from sentence_transformers import SentenceTransformer, util
import re
import logging

class ScoreEvaluator:
    def __init__(self):
        """Inicializa el evaluador de scores con métricas múltiples"""
        self.logger = logging.getLogger(__name__)
        self.spanish_stopwords = set()
        self.vectorizer = TfidfVectorizer()
        
        # Modelo de embeddings para similitud semántica
        try:
            self.embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
            self.embedding_available = True
            self.logger.info("Modelo de embeddings cargado correctamente")
        except Exception as e:
            self.logger.warning(f"No se pudo cargar el modelo de embeddings: {e}")
            self.embedding_available = False
        
        self.setup_nltk()
    
    def setup_nltk(self):
        """Configura los recursos de NLTK"""
        try:
            nltk.data.find('tokenizers/punkt')
        except LookupError:
            nltk.download('punkt', quiet=True)
        
        try:
            nltk.data.find('corpora/stopwords')
        except LookupError:
            nltk.download('stopwords', quiet=True)
        
        self.spanish_stopwords = set(stopwords.words('spanish'))
        self.vectorizer = TfidfVectorizer(stop_words=list(self.spanish_stopwords))
    
    def semantic_similarity(self, text1, text2):
        """Calcula similitud semántica usando embeddings (más preciso)"""
        if not self.embedding_available:
            return self.cosine_similarity_score(text1, text2)
        
        try:
            emb1 = self.embedding_model.encode(text1, convert_to_tensor=True)
            emb2 = self.embedding_model.encode(text2, convert_to_tensor=True)
            score = util.cos_sim(emb1, emb2)
            return float(score.item())
        except Exception as e:
            self.logger.error(f"Error en similitud semántica: {e}")
            return self.cosine_similarity_score(text1, text2)
    
    def cosine_similarity_score(self, text1, text2):
        """Calcula similitud coseno entre dos textos"""
        try:
            text1_clean = self.preprocess_text(text1)
            text2_clean = self.preprocess_text(text2)
            
            if not text1_clean or not text2_clean:
                return 0.0
            
            tfidf_matrix = self.vectorizer.fit_transform([text1_clean, text2_clean])
            similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])
            return float(similarity[0][0])
        except Exception as e:
            self.logger.error(f"Error en cosine similarity: {e}")
            return 0.0
    
    def jaccard_similarity(self, text1, text2):
        """Calcula similitud de Jaccard entre dos textos"""
        try:
            text1_clean = self.preprocess_text(text1)
            text2_clean = self.preprocess_text(text2)
            
            if not text1_clean or not text2_clean:
                return 0.0
                
            set1 = set(text1_clean.split())
            set2 = set(text2_clean.split())
            
            intersection = len(set1.intersection(set2))
            union = len(set1.union(set2))
            
            return intersection / union if union > 0 else 0.0
        except Exception as e:
            self.logger.error(f"Error en Jaccard similarity: {e}")
            return 0.0
    
    def length_ratio_score(self, text1, text2):
        """Evalúa la proporción de longitudes entre respuestas"""
        try:
            len1 = len(text1.split())
            len2 = len(text2.split())
            
            if len1 == 0 or len2 == 0:
                return 0.0
            
            ratio = min(len1, len2) / max(len1, len2)
            return ratio
        except Exception as e:
            self.logger.error(f"Error en length ratio: {e}")
            return 0.0
    
    def keyword_overlap(self, text1, text2):
        """Calcula el overlap de palabras clave importantes"""
        try:
            words1 = set(self.preprocess_text(text1).split())
            words2 = set(self.preprocess_text(text2).split())
            
            if not words1 or not words2:
                return 0.0
            
            overlap = len(words1.intersection(words2))
            return overlap / len(words1.union(words2))
        except Exception as e:
            self.logger.error(f"Error en keyword overlap: {e}")
            return 0.0
    
    def preprocess_text(self, text):
        """Preprocesa el texto para análisis"""
        if not text or not isinstance(text, str):
            return ""
        
        text = text.lower()
        text = re.sub(r'[^\w\s]', '', text)
        
        try:
            tokens = word_tokenize(text)
            tokens = [token for token in tokens if token not in self.spanish_stopwords and len(token) > 2]
        except:
            tokens = text.split()
            tokens = [token for token in tokens if token not in self.spanish_stopwords and len(token) > 2]
        
        return ' '.join(tokens)
    
    def calculate_comprehensive_score(self, original_answer, llm_answer):
        """Calcula un score compuesto considerando múltiples métricas"""
        try:
            # Métricas principales
            semantic_score = self.semantic_similarity(original_answer, llm_answer)
            jaccard_score = self.jaccard_similarity(original_answer, llm_answer)
            length_score = self.length_ratio_score(original_answer, llm_answer)
            keyword_score = self.keyword_overlap(original_answer, llm_answer)
            
            # Score compuesto (ponderado)
            comprehensive_score = (
                0.5 * semantic_score +   # Mayor peso a similitud semántica
                0.2 * jaccard_score +    # Peso medio a overlap léxico
                0.15 * length_score +    # Peso a proporción de longitud
                0.15 * keyword_score     # Peso a palabras clave
            )
            
            return {
                'comprehensive_score': round(comprehensive_score, 4),
                'semantic_similarity': round(semantic_score, 4),
                'jaccard_similarity': round(jaccard_score, 4),
                'length_ratio': round(length_score, 4),
                'keyword_overlap': round(keyword_score, 4),
                'quality_grade': self.get_quality_grade(comprehensive_score)
            }
        except Exception as e:
            self.logger.error(f"Error calculando score compuesto: {e}")
            return {
                'comprehensive_score': 0.0,
                'semantic_similarity': 0.0,
                'jaccard_similarity': 0.0,
                'length_ratio': 0.0,
                'keyword_overlap': 0.0,
                'quality_grade': 'Very Poor'
            }
    
    def get_quality_grade(self, score):
        """Convierte score numérico a calificación cualitativa"""
        if score >= 0.8:
            return 'Excellent'
        elif score >= 0.6:
            return 'Good'
        elif score >= 0.4:
            return 'Fair'
        elif score >= 0.2:
            return 'Poor'
        else:
            return 'Very Poor'