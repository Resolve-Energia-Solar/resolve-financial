FROM alpine:latest

# Instalar dependências básicas e do Python
RUN apk update && apk add --no-cache \
    zsh git python3 py3-pip tzdata pkgconfig \
    mysql-dev gcc musl-dev python3-dev libffi-dev openssl-dev

# Instalar dependências para WeasyPrint
RUN apk add --no-cache \
    cairo cairo-dev pango pango-dev gdk-pixbuf gdk-pixbuf-dev

SHELL ["/bin/zsh", "-c"]

# Configurar shell zsh
RUN sh -c "$(wget -O- https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)"

# Configurar timezone
RUN ln -fs /usr/share/zoneinfo/America/Belem /etc/localtime
RUN echo "America/Belem" > /etc/timezone

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
