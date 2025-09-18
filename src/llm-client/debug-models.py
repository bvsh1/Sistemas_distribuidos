import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()

def list_available_models():
    try:
        genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
        models = genai.list_models()
        
        print("Modelos disponibles:")
        for model in models:
            print(f"- {model.name}")
            print(f"  Supported methods: {model.supported_generation_methods}")
            print()
            
    except Exception as e:
        print(f"Error listando modelos: {e}")

if __name__ == "__main__":
    list_available_models()