# Kubernetes Deployment Instructions

## TLS Configuration

To properly configure TLS for the ingress, follow these steps:

1. Generate the certificate chain:
   ```bash
   ./kubernetes/scripts/generate_cert_chain.sh
   ```

2. Base64 encode the certificate chain and private key:
   ```bash
   # For the certificate chain
   base64 -w 0 ./kubernetes/certs/certificate_chain.pem > ./kubernetes/certs/certificate_chain.base64
   
   # For the private key (replace with the actual path to your private key)
   base64 -w 0 ./path/to/private.key > ./kubernetes/certs/private_key.base64
   ```

3. Update the `kubernetes/br/prod/tls-secret.yaml` file with the base64 encoded values:
   ```yaml
   tls.crt: $(cat ./kubernetes/certs/certificate_chain.base64)
   tls.key: $(cat ./kubernetes/certs/private_key.base64)
   ```

4. Apply the TLS secret and updated ingress:
   ```bash
   kubectl apply -f kubernetes/br/prod/tls-secret.yaml
   kubectl apply -f kubernetes/br/prod/ingress.yaml
   ```

## Troubleshooting SSL/TLS Issues

If you encounter SSL/TLS issues with external services connecting to the application, check the following:

1. Verify that the certificate chain is complete and in the correct order:
   - Domain certificate first
   - Intermediate certificate(s) next
   - Root certificate(s) last

2. Ensure that the TLS protocol versions and cipher suites are compatible with the connecting service:
   - The ingress is configured to use TLSv1.2 and TLSv1.3
   - The cipher suite is set to HIGH:!aNULL:!MD5

3. Check the logs for SSL/TLS handshake errors:
   ```bash
   kubectl logs -f deployment/iagio-deployment
   ```

4. Test the SSL/TLS configuration using OpenSSL:
   ```bash
   openssl s_client -connect iagio-plataformagt.gtgroup.tech:443 -servername iagio-plataformagt.gtgroup.tech
   ```
