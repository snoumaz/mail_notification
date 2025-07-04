FROM python:3.11-slim

# Establecer el directorio de trabajo dentro del contenedor
WORKDIR /app

# Copiar requirements y instalar dependencias
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copiar archivos necesarios al contenedor
COPY main.py /app/
COPY sender_groups_exemple.json /app/

# Comando para ejecutar el script
CMD ["python", "main.py"]
