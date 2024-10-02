FROM ubuntu:latest

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
    redis-server


RUN sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)" --unattended
RUN chsh -s $(which zsh)

RUN ln -fs /usr/share/zoneinfo/America/Belem /etc/localtime
RUN echo "America/Belem" > /etc/timezone

WORKDIR /app

COPY requirements.txt .
RUN pip install --break-system-packages -r requirements.txt

SHELL ["/bin/zsh", "-c"]

COPY . .

EXPOSE 8000
