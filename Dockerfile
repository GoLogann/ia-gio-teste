FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    tzdata \
    ca-certificates \
    build-essential \
    gcc \
    pkg-config \
    libdbus-1-dev \
    libglib2.0-dev \
    libcairo2-dev \
    libpq-dev \
    openssl \
    curl && \
    ln -sf /usr/share/zoneinfo/America/Sao_Paulo /etc/localtime && \
    echo "America/Sao_Paulo" > /etc/timezone && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Copiar os certificados para o diretório correto
COPY kubernetes/certs/*.crt /usr/local/share/ca-certificates/
COPY kubernetes/certs/combined_certificates.pem /app/certs/combined_certificates.pem

# Atualizar os certificados CA
RUN update-ca-certificates

# Configuração do OpenSSL
RUN echo "openssl_conf = default_conf" >> /etc/ssl/openssl.cnf && \
    echo "" >> /etc/ssl/openssl.cnf && \
    echo "[default_conf]" >> /etc/ssl/openssl.cnf && \
    echo "ssl_conf = ssl_sect" >> /etc/ssl/openssl.cnf && \
    echo "" >> /etc/ssl/openssl.cnf && \
    echo "[ssl_sect]" >> /etc/ssl/openssl.cnf && \
    echo "system_default = system_default_sect" >> /etc/ssl/openssl.cnf && \
    echo "" >> /etc/ssl/openssl.cnf && \
    echo "[system_default_sect]" >> /etc/ssl/openssl.cnf && \
    echo "MinProtocol = TLSv1.2" >> /etc/ssl/openssl.cnf && \
    echo "MaxProtocol = TLSv1.3" >> /etc/ssl/openssl.cnf && \
    echo "CipherString = DEFAULT@SECLEVEL=2" >> /etc/ssl/openssl.cnf && \
    echo "Options = UnsafeLegacyRenegotiation" >> /etc/ssl/openssl.cnf

ENV SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt
ENV REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt
ENV CURL_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt
ENV TZ=America/Sao_Paulo
ENV PYTHONHTTPSVERIFY=1
ENV PYTHONPATH=/app
ENV OPENSSL_CONF=/etc/ssl/openssl.cnf

COPY requirements.txt .

RUN pip install --upgrade pip && \
    pip install --no-cache-dir protobuf==4.21.12 && \
    pip install --no-cache-dir google-ai-generativelanguage certifi -r requirements.txt

COPY . .

# Rodar a API com SSL usando o arquivo combinado
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "443", "--ssl-keyfile", "/app/certs/combined_certificates.pem", "--ssl-certfile", "/app/certs/combined_certificates.pem"]
