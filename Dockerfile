# Usar la imagen oficial de Rasa
FROM rasa/rasa:3.6.20

# Cambiar a usuario root para instalar dependencias si es necesario
USER root

# Copiar los archivos del proyecto al contenedor
COPY . /app

# Establecer el directorio de trabajo
WORKDIR /app

# Instalar dependencias adicionales si existen
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Entrenar el modelo durante la construcción de la imagen
RUN rasa train

# Cambiar al usuario no root predeterminado de Rasa
USER 1001

# Exponer el puerto 5005
EXPOSE 5005

# Copiar script de inicio
COPY start.sh /app/start.sh
RUN chmod +x /app/start.sh

# Comando para ejecutar el servidor Rasa usando el script
CMD ["/app/start.sh"]
