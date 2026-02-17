FROM python:3.11-slim

WORKDIR /app

# Instalar dependencias primero
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el resto del código
COPY . .

# Comando para iniciar
CMD gunicorn app:app --bind 0.0.0.0:$PORT
