# 1. Usar una versión oficial y ligera de Python
FROM python:3.10-slim

# 2. Configurar el directorio de trabajo
WORKDIR /app

# 3. Copiar los archivos de tu proyecto al contenedor
COPY . .

# 4. Instalar las librerías de Python directamente
# Modifica solo esta línea en tu Dockerfile:
RUN pip install --no-cache-dir streamlit supabase python-dotenv
# Modifica la línea de instalación para que quede exactamente así:
RUN pip install --no-cache-dir streamlit supabase python-dotenv openpyxl pandas


# 5. Exponer el puerto de Streamlit
EXPOSE 8501

# 6. Comando para arrancar la aplicación
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
