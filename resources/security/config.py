from resources.config_loader import get_config

security_config = get_config("security")

KEYCLOAK_CLIENT_ID = security_config.get("clientid")
KEYCLOAK_CLIENT_SECRET = security_config.get("clientsecret")
TOKEN_URL = security_config.get("tokenuri")
JWKS_URL = security_config.get("jwkuri")
