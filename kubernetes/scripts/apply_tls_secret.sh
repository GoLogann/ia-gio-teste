#!/bin/bash

# Domain to generate certificate chain for
DOMAIN=$1
# Path to private key
PRIVATE_KEY=$2

if [ -z "$DOMAIN" ] || [ -z "$PRIVATE_KEY" ]; then
  echo "Usage: $0 <domain> <private_key_path>"
  echo "Example: $0 gtgroup.tech /path/to/private.key"
  exit 1
fi

# Generate the certificate chain
./kubernetes/scripts/generate_domain_cert_chain.sh $DOMAIN

# Base64 encode the certificate chain and private key
CERT_CHAIN_B64=$(base64 -w 0 ./kubernetes/certs/${DOMAIN}_chain.pem)
PRIVATE_KEY_B64=$(base64 -w 0 $PRIVATE_KEY)

# Create the TLS secret YAML
cat > kubernetes/br/prod/tls-secret.yaml << EOF
apiVersion: v1
kind: Secret
metadata:
  name: gtgroup-tls-secret
  namespace: plataformagt
type: kubernetes.io/tls
data:
  tls.crt: $CERT_CHAIN_B64
  tls.key: $PRIVATE_KEY_B64
EOF

echo "TLS secret YAML generated at kubernetes/br/prod/tls-secret.yaml"
echo "Apply the secret with: kubectl apply -f kubernetes/br/prod/tls-secret.yaml"