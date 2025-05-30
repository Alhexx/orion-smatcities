# Usa uma imagem oficial leve do Python
FROM python:3.9-slim-buster

# Define o diretório de trabalho dentro do contêiner
WORKDIR /app

# Copia o arquivo de requisitos e instala as dependências
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia o script do adaptador para o diretório de trabalho
COPY open_meteo_to_orion.py .

# Comando para executar o script quando o contêiner iniciar
CMD ["python", "open_meteo_to_orion.py"]