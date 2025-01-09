FROM ubuntu:latest

# Instalar dependências básicas
RUN apt-get update && apt-get install -y \
    curl \
    zsh \
    git \
    python3 \
    python3-pip \
    tzdata \
    pkg-config \
    libmysqlclient-dev \
    gcc \
    g++ \
    python3-dev \
    libffi-dev \
    libssl-dev \
    redis-server \
    libpangocairo-1.0-0 \
    libcairo2 \
    libcairo2-dev \
    libpango-1.0-0 \
    libpango1.0-dev \
    libgdk-pixbuf2.0-0 \
    libgdk-pixbuf2.0-dev \
    shared-mime-info

# Instalar Oh-My-Zsh
RUN sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)" --unattended
RUN chsh -s $(which zsh)

# Configurar timezone
RUN ln -fs /usr/share/zoneinfo/America/Belem /etc/localtime
RUN echo "America/Belem" > /etc/timezone

# Definir diretório de trabalho
WORKDIR /app

# Instalar dependências do Python
COPY requirements.txt .
RUN pip install --break-system-packages --ignore-installed packaging -r requirements.txt

# Configurar shell
SHELL ["/bin/zsh", "-c"]

# Copiar o restante
