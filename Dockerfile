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

COPY kubernetes/certs/SectigoRSADomainValidationSecureServerCA.crt /usr/local/share/ca-certificates/
COPY kubernetes/certs/USERTrustRSAAAACA.crt /usr/local/share/ca-certificates/
RUN update-ca-certificates

COPY kubernetes/certs/private.key /app/certs/private.key
COPY kubernetes/certs/combined_certificates.pem /app/certs/combined_certificates.pem

RUN chmod 400 /app/certs/private.key

RUN echo "openssl_conf = default_conf" >> /etc/ssl/openssl.cnf && \
    echo "[default_conf]" >> /etc/ssl/openssl.cnf && \
    echo "ssl_conf = ssl_sect" >> /etc/ssl/openssl.cnf && \
    echo "[ssl_sect]" >> /etc/ssl/openssl.cnf && \
    echo "system_default = system_default_sect" >> /etc/ssl/openssl.cnf && \
    echo "[system_default_sect]" >> /etc/ssl/openssl.cnf && \
    echo "MinProtocol = TLSv1.2" >> /etc/ssl/openssl.cnf && \
    echo "CipherString = DEFAULT@SECLEVEL=2" >> /etc/ssl/openssl.cnf

ENV SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt \
    REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt \
    CURL_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt \
    TZ=America/Sao_Paulo \
    PYTHONHTTPSVERIFY=1 \
    PYTHONPATH=/app \
    OPENSSL_CONF=/etc/ssl/openssl.cnf

COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir protobuf==4.21.12 && \
    pip install --no-cache-dir google-ai-generativelanguage certifi -r requirements.txt

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080", "--ssl-keyfile", "/app/certs/private.key", "--ssl-certfile", "/app/certs/combined_certificates.pem"]