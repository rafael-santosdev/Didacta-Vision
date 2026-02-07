# Didacta-Vision — Django em produção com Gunicorn
# Banco padrão: SQLite (opção MySQL via variáveis de ambiente)

FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Dependências do sistema (imagens, libs para Pillow)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libjpeg62-turbo-dev \
    zlib1g-dev \
    libwebp-dev \
    && rm -rf /var/lib/apt/lists/*

# Dependências Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Código do projeto
COPY . .

# Entrypoint: remove CRLF se o arquivo veio do Windows (evita "bad interpreter")
RUN sed -i 's/\r$//' /app/entrypoint.sh 2>/dev/null || true

# Diretórios para volume (SQLite + media)
RUN mkdir -p /app/staticfiles /app/media /app/db

# Entrypoint executável
RUN chmod +x /app/entrypoint.sh

# Roda como root para escrever em volumes (sqlite_data, media_data)
# Para produção restrita, ajuste permissões do volume e use USER appuser
EXPOSE 8000

ENTRYPOINT ["/app/entrypoint.sh"]
