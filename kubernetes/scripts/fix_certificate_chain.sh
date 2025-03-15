#!/bin/bash

# Directory containing the certificates
CERT_DIR="./kubernetes/certs"

# Domain to generate certificate chain for
DOMAIN="gtgroup.tech"

# Output file for the certificate chain
OUTPUT_FILE="./kubernetes/certs/${DOMAIN}_fixed_chain.pem"

# Ensure the output file is empty
> $OUTPUT_FILE

# Add only the domain certificate for gtgroup.tech
cat $CERT_DIR/STAR_gtgroup_tech.crt >> $OUTPUT_FILE

# Add the intermediate certificate
cat $CERT_DIR/SectigoRSADomainValidationSecureServerCA.crt >> $OUTPUT_FILE

# Add the root certificate
cat $CERT_DIR/USERTrustRSACertificationAuthority.crt >> $OUTPUT_FILE

echo "Fixed certificate chain for $DOMAIN generated at $OUTPUT_FILE"