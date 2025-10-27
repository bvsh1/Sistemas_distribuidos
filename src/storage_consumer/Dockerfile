FROM python:3.9-slim

# 2. Establecer el directorio de trabajo dentro del contenedor
WORKDIR /app

# 3. Copiar el archivo de requerimientos desde la RAÍZ del proyecto
# El 'context' del build es esta carpeta (ej: src/retry_consumers)
# '..' sube a 'src'
# '../../' sube a la raíz del proyecto ('Sistemas_distribuidos')
COPY requirements.txt .

# 4. Instalar las dependencias
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copiar el CÓDIGO FUENTE de este servicio
# '.' se refiere al 'context' (la carpeta donde está este Dockerfile),
# así que copia todo el código de esta carpeta (ej: delay_consumer.py y backoff_consumer.py)
COPY ./src/storage_consumer /app