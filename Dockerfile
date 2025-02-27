FROM alpine:latest

# Instalar dependências básicas e do Python
RUN apk update && apk add --no-cache \
    zsh git python3 py3-pip tzdata pkgconfig \
    mysql-dev gcc musl-dev python3-dev libffi-dev openssl-dev

# Instalar dependências para WeasyPrint e fontes
RUN apk add --no-cache \
    cairo cairo-dev pango pango-dev gdk-pixbuf gdk-pixbuf-dev \
    fontconfig fontconfig-dev \
    ttf-dejavu ttf-freefont font-noto font-noto-cjk font-noto-emoji \
    ttf-liberation ttf-droid

# Configurar timezone
RUN ln -fs /usr/share/zoneinfo/America/Belem /etc/localtime
RUN echo "America/Belem" > /etc/timezone

# Atualizar cache de fontes
RUN fc-cache -f -v

# Verificar fontes instaladas (para depuração)
RUN fc-list

# Definir diretório de trabalho
WORKDIR /app

# Criar diretório para logs
RUN mkdir -p /app/logs

# Instalar dependências do Python
COPY requirements.txt .
RUN pip install --break-system-packages -r requirements.txt

# Copiar o restante do código
COPY . .

# Instalar o Celery (caso não esteja no requirements.txt)
#RUN pip install celery


# Expor a porta
EXPOSE 8001

# Adicionar o comando para iniciar o Celery junto com o Django
CMD ["sh", "-c", "celery -A resolve_erp worker --loglevel=info"]