import asyncio
import logging
import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends
import uvicorn
from fastapi.logger import logger
from auth.auth import validate_jwt_token
from controller.router import router as api_router
from controller.external_route import external_router
from database.database import get_session
from database.qdrant_db import get_qdrant_client
from resources.apache_kafka.config import (
    KAFKA_BROKERS_URLS,
    KAFKA_TOPIC_SEND_SWARM_CONTACT_GIO,
    KAFKA_TOPIC_QUEUE_SENDING_MESSAGES
)
from resources.config_loader import get_config
from fastapi.middleware.cors import CORSMiddleware
from auth.setup import setup_auth_client
from auth.refresh_token import refresh_oauth_token
from services.kafka_consumer import KafkaConsumerService
from services.message_queue_consumer import MessageQueueConsumer

app_config = get_config("app")
http_config = get_config("http")
ENV = get_config('env')

logging.basicConfig(
    level=logging.DEBUG if ENV == 'dev' else logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Gerando Token...")
    oauth, token = setup_auth_client()
    app.state.oauth_client = oauth
    app.state.token = token

    logger.info("Iniciando serviço de renovação de token...")
    token_task = asyncio.create_task(refresh_oauth_token(app))

    logger.info("Iniciando Database...")
    db = get_session()
    qdrant_db = get_qdrant_client()
    app.state.db_client = db
    app.state.qdrant_client = qdrant_db

    # logger.info("Iniciando Kafka Consumer para processamento de dados...")
    # kafka_consumer = KafkaConsumerService(KAFKA_BROKERS_URLS, KAFKA_TOPIC_SEND_SWARM_CONTACT_GIO, db, qdrant_db)
    # await kafka_consumer.start()
    # kafka_task = asyncio.create_task(kafka_consumer.process_messages())
    #
    # logger.info("Iniciando Kafka Consumer para fila de envio...")
    # message_queue_consumer = MessageQueueConsumer(KAFKA_BROKERS_URLS, KAFKA_TOPIC_QUEUE_SENDING_MESSAGES)
    # await message_queue_consumer.start()
    # message_queue_task = asyncio.create_task(message_queue_consumer.process_messages())

    yield

    logger.info("Encerrando os recursos...")
    # kafka_task.cancel()
    # await kafka_consumer.stop()
    # message_queue_task.cancel()
    # await message_queue_consumer.stop()
    token_task.cancel()
    await db.close()

app = FastAPI(
    title=app_config.get('name', 'IA GIO'),
    version=app_config.get('version', '0.0.1'),
    lifespan=lifespan,
    docs_url=None,
    redoc_url=None,
    openapi_url=None
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, dependencies=[Depends(validate_jwt_token)])

app.include_router(external_router)

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(http_config.get('port', 8081)),
        reload=ENV == 'dev',
    )
