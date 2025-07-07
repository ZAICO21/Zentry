# Imagen base
FROM python:3.10-slim

# Establece directorio de trabajo
WORKDIR /app

# Copia archivos al contenedor
COPY . .

# Instala dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Expone el puerto
EXPOSE 5000

# Comando para iniciar la app
CMD ["python", "app.py"]
