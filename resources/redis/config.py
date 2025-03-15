from resources.config_loader import get_config

whatsapp_config = get_config("redis")

HOST = whatsapp_config.get("host")
PORT = whatsapp_config.get("port")
DB = whatsapp_config.get("db")