from resources.config_loader import get_config

api_config = get_config("api")

ADMINISTRATIVOURL = api_config.get("administrativourl")
AUTHMANAGERURL = api_config.get("authmanagerurl")
WHATSAPPURL = api_config.get("whatsappurl")
