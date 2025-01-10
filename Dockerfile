FROM alpine:latest

# Instalar dependências básicas e do Python
RUN apk update && apk add --no-cache \
    zsh git python3 py3-pip tzdata pkgconfig \
    mysql-dev gcc musl-dev python3-dev libffi-dev openssl-dev

# Instalar dependências para WeasyPrint
RUN apk add --no-cache \
    cairo cairo-dev pango pango-dev gdk-pixbuf gdk-pixbuf-dev \
    fontconfig font-noto font-noto-cjk font-noto-emoji ttf-dejavu ttf-freefont

# Configurar timezone
RUN ln -fs /usr/share/zoneinfo/America/Belem /etc/localtime
RUN echo "America/Belem" > /etc/timezone

# Configurar FontConfig
RUN fc-cache -f -v

# Definir diretório de trabalho
WORKDIR /app

# Criar diretório para logs
RUN mkdir -p /app/logs

# Instalar dependências do Python
COPY requirements.txt .
RUN pip install --break-system-packages -r requirements.txt

# Copiar o restante do código
COPY . .

# Expor a porta
EXPOSE 8001
