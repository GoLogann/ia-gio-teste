from aiokafka import AIOKafkaProducer
import json


class KafkaProducerService:
    def __init__(self, kafka_bootstrap_servers: str, topic: str):
        self.kafka_bootstrap_servers = kafka_bootstrap_servers
        self.topic = topic
        self.producer = None

    async def start(self):
        self.producer = AIOKafkaProducer(
            bootstrap_servers=self.kafka_bootstrap_servers
        )
        await self.producer.start()
        print(f"Produtor Kafka conectado ao tópico {self.topic}")

    async def stop(self):
        if self.producer:
            await self.producer.stop()
            print("Produtor Kafka parado.")

    async def publish_message(self, message: dict):
        try:
            message_json = json.dumps(message).encode("utf-8")
            await self.producer.send_and_wait(self.topic, message_json)
            print(f"Mensagem enviada ao tópico {self.topic}: {message}")
        except Exception as e:
            print(f"Erro ao publicar mensagem Kafka: {e}")