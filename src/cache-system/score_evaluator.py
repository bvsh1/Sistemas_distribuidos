# src/scoring/score_evaluator.py
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
import re
import logging

class ScoreEvaluator:
    def __init__(self):
        """Inicializa el evaluador de scores con métricas múltiples"""
        self.logger = logging.getLogger(__name__)
        self.spanish_stopwords = set()
        self.vectorizer = TfidfVectorizer()
        self.setup_nltk()
    
    def setup_nltk(self):
        """Configura los recursos de NLTK con manejo robusto de errores"""
        try:
            # Intentar descargar recursos si no están disponibles
            try:
                nltk.data.find('tokenizers/punkt')
            except LookupError:
                self.logger.info("Descargando recursos punkt...")
                nltk.download('punkt', quiet=True)
            
            try:
                nltk.data.find('corpora/stopwords')
            except LookupError:
                self.logger.info("Descargando recursos stopwords...")
                nltk.download('stopwords', quiet=True)
            
            # Configurar stopwords en español
            self.spanish_stopwords = set(stopwords.words('spanish'))
            self.vectorizer = TfidfVectorizer(stop_words=list(self.spanish_stopwords))
            
            self.logger.info("Recursos NLTK configurados correctamente")
            
        except Exception as e:
            self.logger.warning(f"Error configurando NLTK, usando modo simple: {e}")
            self.fallback_mode = True
    
    def simple_tokenize(self, text):
        """Tokenización simple sin NLTK como fallback"""
        if not text or not isinstance(text, str):
            return []
        
        # Limpieza básica
        text = text.lower()
        text = re.sub(r'[^\w\s]', '', text)
        
        # Tokenización por espacios
        tokens = text.split()
        
        # Filtrar stopwords básicas
        basic_stopwords = {'de', 'la', 'que', 'el', 'en', 'y', 'a', 'los', 'del', 'se', 'las', 'por', 'un', 'para', 'con', 'no', 'una', 'su', 'al', 'lo', 'como', 'más', 'pero', 'sus', 'le', 'ya', 'o', 'este', 'sí', 'porque', 'esta', 'entre', 'cuando', 'muy', 'sin', 'sobre', 'también', 'me', 'hasta', 'hay', 'donde', 'quien', 'desde', 'todo', 'nos', 'durante', 'todos', 'uno', 'les', 'ni', 'contra', 'otros', 'ese', 'eso', 'ante', 'ellos', 'e', 'esto', 'mí', 'antes', 'algunos', 'qué', 'unos', 'yo', 'otro', 'otras', 'otra', 'él', 'tanto', 'esa', 'estos', 'mucho', 'quienes', 'nada', 'muchos', 'cual', 'poco', 'ella', 'estar', 'estas', 'algunas', 'algo', 'nosotros', 'mi', 'mis', 'tú', 'te', 'ti', 'tu', 'tus', 'ellas', 'nosotras', 'vosotros', 'vosotras', 'os', 'mío', 'mía', 'míos', 'mías', 'tuyo', 'tuya', 'tuyos', 'tuyas', 'suyo', 'suya', 'suyos', 'suyas', 'nuestro', 'nuestra', 'nuestros', 'nuestras', 'vuestro', 'vuestra', 'vuestros', 'vuestras', 'esos', 'esas', 'estoy', 'estás', 'está', 'estamos', 'estáis', 'están', 'esté', 'estés', 'estemos', 'estéis', 'estén', 'estaré', 'estarás', 'estará', 'estaremos', 'estaréis', 'estarán', 'estaría', 'estarías', 'estaríamos', 'estaríais', 'estarían', 'estaba', 'estabas', 'estábamos', 'estabais', 'estaban', 'estuve', 'estuviste', 'estuvo', 'estuvimos', 'estuvisteis', 'estuvieron', 'estuviera', 'estuvieras', 'estuviéramos', 'estuvierais', 'estuvieran', 'estuviese', 'estuvieses', 'estuviésemos', 'estuvieseis', 'estuviesen', 'estando', 'estado', 'estada', 'estados', 'estadas', 'estad', 'he', 'has', 'ha', 'hemos', 'habéis', 'han', 'haya', 'hayas', 'hayamos', 'hayáis', 'hayan', 'habré', 'habrás', 'habrá', 'habremos', 'habréis', 'habrán', 'habría', 'habrías', 'habríamos', 'habríais', 'habrían', 'había', 'habías', 'habíamos', 'habíais', 'habían', 'hube', 'hubiste', 'hubo', 'hubimos', 'hubisteis', 'hubieron', 'hubiera', 'hubieras', 'hubiéramos', 'hubierais', 'hubieran', 'hubiese', 'hubieses', 'hubiésemos', 'hubieseis', 'hubiesen', 'habiendo', 'habido', 'habida', 'habidos', 'habidas', 'soy', 'eres', 'es', 'somos', 'sois', 'son', 'sea', 'seas', 'seamos', 'seáis', 'sean', 'seré', 'serás', 'será', 'seremos', 'seréis', 'serán', 'sería', 'serías', 'seríamos', 'seríais', 'serían', 'era', 'eras', 'éramos', 'erais', 'eran', 'fui', 'fuiste', 'fue', 'fuimos', 'fuisteis', 'fueron', 'fuera', 'fueras', 'fuéramos', 'fuerais', 'fueran', 'fuese', 'fueses', 'fuésemos', 'fueseis', 'fuesen', 'sintiendo', 'sentido', 'sentida', 'sentidos', 'sentidas', 'siente', 'sentid', 'tengo', 'tienes', 'tiene', 'tenemos', 'tenéis', 'tienen', 'tenga', 'tengas', 'tengamos', 'tengáis', 'tengan', 'tendré', 'tendrás', 'tendrá', 'tendremos', 'tendréis', 'tendrán', 'tendría', 'tendrías', 'tendríamos', 'tendríais', 'tendrían', 'tenía', 'tenías', 'teníamos', 'teníais', 'tenían', 'tuve', 'tuviste', 'tuvo', 'tuvimos', 'tuvisteis', 'tuvieron', 'tuviera', 'tuvieras', 'tuviéramos', 'tuvierais', 'tuvieran', 'tuviese', 'tuvieses', 'tuviésemos', 'tuvieseis', 'tuviesen', 'teniendo', 'tenido', 'tenida', 'tenidos', 'tenidas', 'tened'}
        
        tokens = [token for token in tokens if token not in basic_stopwords and len(token) > 2]
        
        return tokens
    
    def preprocess_text(self, text):
        """Preprocesa el texto para análisis con fallback"""
        if not text or not isinstance(text, str):
            return ""
        
        try:
            # Convertir a minúsculas y eliminar caracteres especiales
            text = text.lower()
            text = re.sub(r'[^\w\s]', '', text)
            
            # Intentar tokenización con NLTK, fallback a simple
            try:
                tokens = word_tokenize(text)
                tokens = [token for token in tokens if token not in self.spanish_stopwords and len(token) > 2]
            except:
                tokens = self.simple_tokenize(text)
            
            return ' '.join(tokens)
            
        except Exception as e:
            self.logger.error(f"Error en preprocesamiento, usando texto limpio: {e}")
            # Fallback: solo limpieza básica
            text = text.lower()
            text = re.sub(r'[^\w\s]', '', text)
            return text
    
    def cosine_similarity_score(self, text1, text2):
        """Calcula similitud coseno entre dos textos"""
        try:
            # Preprocesar textos
            text1_clean = self.preprocess_text(text1)
            text2_clean = self.preprocess_text(text2)
            
            if not text1_clean or not text2_clean:
                return 0.0
            
            # Vectorizar y calcular similitud
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
    
    def calculate_comprehensive_score(self, original_answer, llm_answer):
        """Calcula un score compuesto considerando múltiples métricas"""
        try:
            cosine_score = self.cosine_similarity_score(original_answer, llm_answer)
            jaccard_score = self.jaccard_similarity(original_answer, llm_answer)
            length_score = self.length_ratio_score(original_answer, llm_answer)
            
            # Score compuesto (ponderado)
            comprehensive_score = (
                0.6 * cosine_score +  # Mayor peso a similitud semántica
                0.3 * jaccard_score + # Peso medio a overlap léxico
                0.1 * length_score    # Peso menor a proporción de longitud
            )
            
            return {
                'comprehensive_score': round(comprehensive_score, 4),
                'cosine_similarity': round(cosine_score, 4),
                'jaccard_similarity': round(jaccard_score, 4),
                'length_ratio': round(length_score, 4)
            }
        except Exception as e:
            self.logger.error(f"Error calculando score compuesto: {e}")
            return {
                'comprehensive_score': 0.0,
                'cosine_similarity': 0.0,
                'jaccard_similarity': 0.0,
                'length_ratio': 0.0
            }