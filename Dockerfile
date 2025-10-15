# ===== Base =====
FROM python:3.11-alpine

# Dependências básicas + libs para compilar Python packages
RUN apk update && apk add --no-cache \
    bash zsh git build-base python3-dev musl-dev libffi-dev openssl-dev \
    cairo cairo-dev pango pango-dev gdk-pixbuf gdk-pixbuf-dev \
    fontconfig fontconfig-dev \
    ttf-dejavu ttf-freefont ttf-liberation ttf-droid tzdata \
    mariadb-dev mariadb-connector-c-dev pkgconfig

# Configurar timezone
RUN ln -fs /usr/share/zoneinfo/America/Belem /etc/localtime && echo "America/Belem" > /etc/timezone

# Atualizar cache de fontes
RUN fc-cache -f -v

# Diretório de trabalho
WORKDIR /app

# Criar diretórios necessários
RUN mkdir -p /app/logs /app/certs

# Copiar requirements e instalar dependências
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install --no-cache-dir --break-system-packages -r requirements.txt

# Copiar o restante do código
COPY . .

# Expor porta da aplicação
EXPOSE 8001

# Comando padrão para Daphne
CMD ["daphne", "-b", "0.0.0.0", "-p", "8001", "resolve_erp.asgi:application"]

