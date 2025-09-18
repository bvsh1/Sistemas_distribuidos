FROM python:3.9-slim

WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements.txt primero para aprovechar cache de Docker
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 📌 COPIAR solo los archivos de llm-client, no todo el proyecto
COPY . .

# Verificar que los archivos se copiaron correctamente
RUN echo "Contenido de /app:" && ls -la && \
    echo "Contenido de /app/config:" && ls -la config/ && \
    echo "Contenido de /app/services:" && ls -la services/

EXPOSE 5000

CMD ["python", "main.py"]