from aiokafka import AIOKafkaConsumer
import json
from fastapi.logger import logger
from utils.whatsapp import send_message_to_whatsapp
from services.kafka_producer import KafkaProducerService

MAX_RETRIES = 5

class MessageQueueConsumer:
    def __init__(self, kafka_bootstrap_servers, topic):
        self.kafka_bootstrap_servers = kafka_bootstrap_servers
        self.topic = topic
        self.consumer = None

    async def start(self):
        self.consumer = AIOKafkaConsumer(
            self.topic,
            bootstrap_servers=self.kafka_bootstrap_servers,
            group_id="fila-envio-consumer"
        )
        await self.consumer.start()
        logger.info(f"Consumidor Kafka iniciado no tópico {self.topic}")

    async def stop(self):
        if self.consumer:
            await self.consumer.stop()
            logger.info("Consumidor Kafka parado.")

    async def process_messages(self):
        async for message in self.consumer:
            try:
                data = json.loads(message.value)
                telefone = data.get("telefone")
                resposta = data.get("resposta")
                retry_count = data.get("retry_count", 0)

                if not telefone or not resposta:
                    raise ValueError("Mensagem inválida recebida na fila.")

                try:
                    await send_message_to_whatsapp(telefone, resposta)
                    logger.info(f"Mensagem enviada com sucesso")
                except Exception as e:
                    logger.error(f"Erro ao enviar mensagem: {e}")

                    retry_count += 1

                    if retry_count <= MAX_RETRIES:
                        logger.info(f"Reenfileirando mensagem, tentativa {retry_count}")
                        data["retry_count"] = retry_count

                        producer = KafkaProducerService(self.kafka_bootstrap_servers, self.topic)
                        await producer.start()
                        await producer.publish_message(data)
                        await producer.stop()
                    else:
                        logger.error(f"Mensagem descartada após {MAX_RETRIES} tentativas")

            except Exception as e:
                logger.error(f"Erro ao processar mensagem da fila: {e}")
