#!/bin/bash

# Directory containing the certificates
CERT_DIR="./kubernetes/certs"

# Domain to generate certificate chain for
DOMAIN=$1

if [ -z "$DOMAIN" ]; then
  echo "Usage: $0 <domain>"
  echo "Example: $0 gtgroup.tech"
  exit 1
fi

# Output file for the certificate chain
OUTPUT_FILE="./kubernetes/certs/${DOMAIN}_chain.pem"

# Ensure the output file is empty
> $OUTPUT_FILE

# Add the domain certificate first
if [ "$DOMAIN" == "gtgroup.tech" ]; then
  cat $CERT_DIR/STAR_gtgroup_tech.crt >> $OUTPUT_FILE
elif [ "$DOMAIN" == "gtgroup.gt" ]; then
  cat $CERT_DIR/STAR_gtgroup_gt.crt >> $OUTPUT_FILE
elif [ "$DOMAIN" == "gtconsultoria.com.br" ]; then
  cat $CERT_DIR/STAR_gtconsultoria_com_br.crt >> $OUTPUT_FILE
else
  echo "Unknown domain: $DOMAIN"
  exit 1
fi

# Add the intermediate certificate
cat $CERT_DIR/SectigoRSADomainValidationSecureServerCA.crt >> $OUTPUT_FILE

# Add the root certificate
cat $CERT_DIR/USERTrustRSACertificationAuthority.crt >> $OUTPUT_FILE

echo "Certificate chain for $DOMAIN generated at $OUTPUT_FILE"