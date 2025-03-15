from resources.config_loader import get_config

kafka_config = get_config("kafka")
KAFKA_BROKERS_URLS = kafka_config.get("brokersurls")
KAFKA_TOPICS = kafka_config.get("topic")

KAFKA_TOPIC_QUEUE_SENDING_MESSAGES = KAFKA_TOPICS.get("queuesendingmessages")
KAFKA_TOPIC_SEND_SWARM_CONTACT_GIO = KAFKA_TOPICS.get("sendswarmcontactgio")
KAFKA_TOPIC_DIALOGUES_SWARM_GIO = KAFKA_TOPICS.get("dialoguesswarmgio")