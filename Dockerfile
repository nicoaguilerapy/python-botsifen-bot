# Utiliza una imagen base de Python 3.11
FROM python:3.11

# Establece el directorio de trabajo
WORKDIR /app

# Copia tu código fuente al directorio de trabajo en el contenedor
COPY telegrambot.py /app
COPY requirements.txt /app

# Instala las dependencias necesarias
RUN pip install -r requirements.txt

# Ejecuta tu bot de Telegram cuando se inicie el contenedor
CMD ["python", "telegrambot.py"]
