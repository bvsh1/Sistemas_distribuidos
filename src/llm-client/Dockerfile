FROM python:3.9-slim

WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements.txt primero para aprovechar cache de Docker
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar solo los archivos necesarios
COPY main.py .

# Verificar que los archivos se copiaron correctamente
RUN echo "Contenido de /app:" && ls -la

EXPOSE 5000

CMD ["python", "main.py"]