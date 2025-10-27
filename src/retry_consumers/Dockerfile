# --- Dockerfile Genérico para Servicios Python ---
# Este archivo debe ir DENTRO de: src/retry_consumers/Dockerfile

# 1. Usar una imagen base ligera de Python
FROM python:3.9-slim

# 2. Establecer el directorio de trabajo dentro del contenedor
WORKDIR /app

# 3. Copiar el archivo de requerimientos (desde la raíz)
COPY requirements.txt .

# 4. Instalar las dependencias
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copiar el CÓDIGO FUENTE de este servicio
# ¡Esta línea es la correcta para ESTE servicio!
COPY ./src/retry_consumers /app