import os
from dotenv import load_dotenv

load_dotenv()  # Carga variables del .env

class GeminiConfig:
    API_KEY = os.getenv('GEMINI_API_KEY')
    MODEL_NAME = os.getenv('GEMINI_MODEL', 'gemini-1.0-pro')  # ✅ Modelo actualizado
    TIMEOUT = int(os.getenv('REQUEST_TIMEOUT', 30))
    MAX_RETRIES = int(os.getenv('MAX_RETRIES', 3))
    
    @classmethod
    def validate_config(cls):
        if not cls.API_KEY:
            print("Warning: GEMINI_API_KEY not configured, using mock service")
            return False
        if not cls.API_KEY.startswith('AIza'):
            print("Warning: Invalid API Key format, using mock service")
            return False
        
        # Verificar que la API key sea válida
        try:
            import google.generativeai as genai
            genai.configure(api_key=cls.API_KEY)
            models = genai.list_models()
            print(f"API Key válida. Modelos disponibles: {len(list(models))}")
            return True
        except Exception as e:
            print(f"Error validando API Key: {e}")
            return False