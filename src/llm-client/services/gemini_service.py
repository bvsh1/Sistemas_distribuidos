import google.generativeai as genai
import time
import requests
from typing import Optional, Tuple
from config.settings import GeminiConfig

class GeminiService:
    def __init__(self):
        self.api_key = GeminiConfig.API_KEY
        self.model_name = GeminiConfig.MODEL_NAME
        self.timeout = GeminiConfig.TIMEOUT
        self.max_retries = GeminiConfig.MAX_RETRIES
        self.quota_exceeded = False
        self.quota_retry_after = 0
        
        if self.api_key and self.api_key.startswith('AIza'):
            try:
                genai.configure(api_key=self.api_key)
                self.model = genai.GenerativeModel(self.model_name)
                print(f"Gemini service configured with model: {self.model_name}")
            except Exception as e:
                print(f"Error configuring Gemini: {e}")
                self.api_key = None
        else:
            self.api_key = None
    
    def generate_response(self, question: str) -> Optional[str]:
        """Genera respuesta usando Gemini API con manejo de cuotas"""
        if self.quota_exceeded:
            if time.time() < self.quota_retry_after:
                wait_time = int(self.quota_retry_after - time.time())
                print(f"Quota exceeded. Retrying in {wait_time} seconds")
                return None
            else:
                self.quota_exceeded = False
        
        if not self.api_key:
            return None
        
        for attempt in range(self.max_retries):
            try:
                response = self.model.generate_content(
                    f"Responde la siguiente pregunta de manera concisa y precisa: {question}"
                )
                
                if response and response.text:
                    return response.text
                else:
                    print(f"Attempt {attempt + 1}: Empty response")
                    return None
                    
            except Exception as e:
                error_msg = str(e)
                print(f"Attempt {attempt + 1} failed: {error_msg}")
                
                # Manejar error de cuota excedida
                if "quota" in error_msg.lower() or "429" in error_msg:
                    self._handle_quota_error(error_msg)
                    return None
                
                # Manejar modelo no encontrado
                if "not found" in error_msg.lower() or "404" in error_msg:
                    if attempt == self.max_retries - 1:
                        return None
                    time.sleep(2 ** attempt)
                    continue
                
                # Otros errores
                if attempt < self.max_retries - 1:
                    time.sleep(2 ** attempt)
                else:
                    return None
        
        return None
    
    def _handle_quota_error(self, error_msg: str):
        """Manejar error de cuota excedida"""
        print("Quota exceeded. Switching to mock service for 1 hour")
        self.quota_exceeded = True
        self.quota_retry_after = time.time() + 3600  # Retry after 1 hour
        
        # Intentar extraer tiempo de retry del mensaje de error
        if "retry in" in error_msg:
            try:
                parts = error_msg.split("retry in")
                if len(parts) > 1:
                    time_part = parts[1].split("s")[0].strip()
                    retry_seconds = float(time_part)
                    self.quota_retry_after = time.time() + retry_seconds
                    print(f"Will retry in {retry_seconds} seconds")
            except:
                pass

class MockGeminiService:
    """Servicio mock para cuando Gemini no está disponible"""
    
    def __init__(self):
        self.responses = {
            "qué es un sistema distribuido": "Un sistema distribuido es un conjunto de computadoras independientes que aparecen como un sistema único y coherente para los usuarios. Permite la escalabilidad, tolerancia a fallos y distribución geográfica.",
            "qué es python": "Python es un lenguaje de programación interpretado, de alto nivel y de propósito general. Es conocido por su sintaxis clara y legible, y se usa ampliamente en desarrollo web, ciencia de datos, IA y automatización.",
            "qué es la inteligencia artificial": "La inteligencia artificial es el campo de la informática que se dedica a crear sistemas capaces de realizar tareas que normalmente requieren inteligencia humana, como el aprendizaje, el razonamiento y la percepción.",
            "qué es docker": "Docker es una plataforma de contenedorización que permite empaquetar aplicaciones y sus dependencias en contenedores ligeros y portables, garantizando consistencia entre entornos de desarrollo y producción.",
            "qué es machine learning": "Machine learning es una rama de la inteligencia artificial que se centra en desarrollar sistemas que pueden aprender de datos y mejorar su rendimiento sin ser programados explícitamente para cada tarea."
        }
    
    def generate_response(self, question: str) -> str:
        """Generar respuesta mock basada en palabras clave"""
        question_lower = question.lower()
        
        # Buscar respuesta predefinida
        for key, response in self.responses.items():
            if key in question_lower:
                return response
        
        # Respuesta genérica si no hay coincidencia
        return f"Respuesta simulada para: {question}. Esta es una respuesta de prueba del servicio mock, ya que la API de Gemini ha excedido su cuota gratuita. Para respuestas reales, configure una API key válida con cuota disponible."

# Servicio inteligente que cambia entre Gemini y Mock
class HybridGeminiService:
    def __init__(self):
        self.gemini_service = GeminiService()
        self.mock_service = MockGeminiService()
        self.use_mock = not self.gemini_service.api_key
    
    def generate_response(self, question: str) -> str:
        if self.use_mock:
            return self.mock_service.generate_response(question)
        
        gemini_response = self.gemini_service.generate_response(question)
        if gemini_response is not None:
            return gemini_response
        
        # Si Gemini falla, usar mock y marcar para usar mock temporalmente
        self.use_mock = True
        print("Switching to mock service due to Gemini API failures")
        return self.mock_service.generate_response(question)

# Usar el servicio híbrido
gemini_service = HybridGeminiService()