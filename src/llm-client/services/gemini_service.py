import google.generativeai as genai
import requests
import time
from typing import Optional
from config.settings import GeminiConfig

class GeminiService:
    def __init__(self):
        GeminiConfig.validate_config()
        genai.configure(api_key=GeminiConfig.API_KEY)
        self.model = genai.GenerativeModel(GeminiConfig.MODEL_NAME)
        self.timeout = GeminiConfig.TIMEOUT
        
    def generate_response(self, question: str, max_retries: int = None) -> Optional[str]:
        """Genera respuesta usando Gemini API con manejo de errores"""
        max_retries = max_retries or GeminiConfig.MAX_RETRIES
        
        for attempt in range(max_retries):
            try:
                response = self.model.generate_content(
                    f"Responde la siguiente pregunta de manera concisa y precisa: {question}",
                    request_options={'timeout': self.timeout}
                )
                return response.text
                
            except Exception as e:
                print(f"Intento {attempt + 1} fallado: {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # Backoff exponencial
                else:
                    return None
        
        return None

# Singleton para reutilizar la conexión
gemini_service = GeminiService()