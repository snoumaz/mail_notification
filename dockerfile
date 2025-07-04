FROM python:3.11-slim

# Establecer el directorio de trabajo dentro del contenedor
WORKDIR /app

# Copiar solo el script principal al directorio de trabajo /app
COPY main.py /app/

# Instalar las dependencias necesarias
RUN pip install --no-cache-dir python-dotenv python-telegram-bot transformers torch

# Comando para ejecutar el script
CMD ["python", "main.py"]
