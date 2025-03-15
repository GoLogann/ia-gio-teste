from resources.config_loader import get_config

whatsapp_config = get_config("whatsapp")

WHATSAPP_TOKEN = whatsapp_config.get("token")
WHATSAPP_PHONEID = whatsapp_config.get("phoneid")
MESSAGING_PRODUCT = whatsapp_config.get("messagingproduct")
RECIPIENT_TYPE = whatsapp_config.get("recipienttype")
VERIFICATION_TOKEN =  whatsapp_config.get("verificationtoken")