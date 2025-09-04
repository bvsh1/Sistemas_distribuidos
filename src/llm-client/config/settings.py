import os
from dotenv import load_dotenv

load_dotenv()  # Carga variables del .env

class GeminiConfig:
    API_KEY = os.getenv('GEMINI_API_KEY')
    MODEL_NAME = os.getenv('GEMINI_MODEL', 'gemini-pro')
    TIMEOUT = int(os.getenv('REQUEST_TIMEOUT', 30))
    MAX_RETRIES = int(os.getenv('MAX_RETRIES', 3))
    
    @classmethod
    def validate_config(cls):
        if not cls.API_KEY:
            raise ValueError("GEMINI_API_KEY no está configurada")
        if not cls.API_KEY.startswith('AIza'):
            raise ValueError("Formato de API Key inválido")
        return True