# (Tu línea FROM python:3.x-slim o la que uses)
FROM python:3.9-slim

# ---- PASO 1: Instalar dependencias del SISTEMA ----
# Instala las herramientas (C, C++, Fortran) ANTES de pip.
# Estas son necesarias para numpy y scipy.
RUN apt-get update && apt-get install -y \
    build-essential \
    gfortran \
    libatlas-base-dev \
 && rm -rf /var/lib/apt/lists/*

# ---- PASO 2: Configurar el directorio de trabajo ----
WORKDIR /app

# ---- PASO 3: Copiar e instalar dependencias de PYTHON ----
# Copia el requirements.txt específico de este servicio
COPY src/traffic-generator/requirements.txt .

# Ahora pip install SÍ funcionará
RUN pip install --no-cache-dir -r requirements.txt

# ---- PASO 4: Copiar el código de la aplicación ----
# Copia el código que está en la misma carpeta que este Dockerfile
COPY src/traffic-generator/ .

# ---- PASO 5: Definir el comando ----
CMD ["python", "main.py"] # (O el nombre de tu script principal)