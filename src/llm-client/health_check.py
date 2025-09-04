import requests
import time

def check_service():
    max_retries = 10
    for i in range(max_retries):
        try:
            response = requests.get('http://localhost:5000/health', timeout=5)
            if response.status_code == 200:
                print("✅ Service is healthy!")
                return True
        except requests.exceptions.RequestException as e:
            print(f"❌ Attempt {i+1}/{max_retries}: {e}")
            time.sleep(2)
    return False

if __name__ == '__main__':
    check_service()