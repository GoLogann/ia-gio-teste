import json
from aiokafka import AIOKafkaConsumer
from fastapi.logger import logger
from services.chatbot_service import ChatBotService

from utils.helpers import extract_roteiro_from_html


class KafkaConsumerService:
    def __init__(self, kafka_bootstrap_servers: str, topic: str, db_client, qdrant_client):
        self.kafka_bootstrap_servers = kafka_bootstrap_servers
        self.topic = topic
        self.db_client = db_client
        self.qdrant_client = qdrant_client
        self.consumer = None
        self.chatbot_service = ChatBotService()

    async def start(self):
        self.consumer = AIOKafkaConsumer(
            self.topic,
            bootstrap_servers=self.kafka_bootstrap_servers,
            group_id="gio-consumer-group"
        )
        await self.consumer.start()
        logger.info(f"Consumidor Kafka conectado ao tópico {self.topic}")

    async def stop(self):
        if self.consumer:
            await self.consumer.stop()
            logger.info("Consumidor Kafka parado.")

    async def process_messages(self):
        try:
            async for message in self.consumer:
                logger.info(f"Mensagem recebida: {message.value}")
                await self.handle_message(message.value)
        except Exception as e:
            logger.error(f"Erro ao processar mensagens do Kafka: {e}")

    async def handle_message(self, message: bytes):
        try:
            data = json.loads(message.decode("utf-8"))
            id_comunicacao_enxame_contato = data.get("id")
            id_departamento = data.get("idDepartamento")
            nome = data.get("nome")
            telefone = data.get("telefone")
            email = data.get("email")
            atividades = data.get("atividades")
            status_contato = data.get("statusContato")
            modelo_ata_formatado = data.get("modeloAtaReuniaoFormatado")

            if not telefone or not nome or not modelo_ata_formatado:
                logger.warning("Dados incompletos: telefone, nome ou modelo ata ausente.")
                return

            modelo = ""
            if modelo_ata_formatado:
                modelo = extract_roteiro_from_html(modelo_ata_formatado)

            roteiro = {
                "id_comunicacao_enxame_contato": id_comunicacao_enxame_contato,
                "id_departamento": id_departamento,
                "nome": nome,
                "telefone": telefone,
                "email": email,
                "atividades": atividades,
                "status_contato": status_contato,
                "modelo": modelo,
            }

            await self.chatbot_service.start_conversation(roteiro, self.db_client, self.qdrant_client)

        except json.JSONDecodeError:
            logger.error("Erro ao decodificar mensagem Kafka. Mensagem inválida.")
        except Exception as e:
            logger.error(f"Erro ao processar mensagem Kafka: {e}")
