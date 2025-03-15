#!/bin/bash

# Directory containing the certificates
CERT_DIR="./kubernetes/certs"

# Output file for the certificate chain
OUTPUT_FILE="./kubernetes/certs/certificate_chain.pem"

# Ensure the output file is empty
> $OUTPUT_FILE

# Add the domain certificates first
cat $CERT_DIR/STAR_gtconsultoria_com_br.crt >> $OUTPUT_FILE
cat $CERT_DIR/STAR_gtgroup_gt.crt >> $OUTPUT_FILE
cat $CERT_DIR/STAR_gtgroup_tech.crt >> $OUTPUT_FILE

# Add the intermediate certificates
cat $CERT_DIR/SectigoRSADomainValidationSecureServerCA.crt >> $OUTPUT_FILE

# Add the root certificates
cat $CERT_DIR/USERTrustRSACertificationAuthority.crt >> $OUTPUT_FILE
cat $CERT_DIR/SHA-2RootUSERTrustRSACertificationAuthority.crt >> $OUTPUT_FILE

echo "Certificate chain generated at $OUTPUT_FILE"