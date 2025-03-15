from resources.config_loader import get_config

db_config = get_config("db")
qdrant_config = get_config("qdrant")

DSN = db_config.get("connectionstring")
CLIENT_QDRANT = qdrant_config.get("qdrantclient")