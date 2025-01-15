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
 
# Argumentos de build para executar `collectstatic` e `migrate`
ARG COLLECTSTATIC=false
ARG MIGRATE=false
 
# Executar `collectstatic` se habilitado
RUN if [ "$COLLECTSTATIC" = "true" ]; then \
        echo "Executando collectstatic"; \
        python manage.py collectstatic --noinput; \
    fi
 
# Executar `migrate` se habilitado
RUN if [ "$MIGRATE" = "true" ]; then \
        echo "Executando migrate"; \
        python manage.py migrate --noinput; \
    fi
 
# Expor a porta
EXPOSE 8001
 
# Comando de inicialização
CMD ["gunicorn", "resolve_erp.wsgi:application", "--bind", "0.0.0.0:8001"]