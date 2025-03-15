from functools import lru_cache

import redis
import json
from datetime import datetime, timedelta

from fastapi.logger import logger

from resources.datetime_config import time_now
from resources.redis.config import HOST, PORT, DB


class RedisHandler:
    def __init__(self, host=HOST, port=PORT, db=DB):
        self.redis = redis.Redis(host=host, port=port, db=db)
        self.session_timeout = timedelta(hours=1)

    @lru_cache()
    def get_redis_client(self):
        return self.redis.client()

    def set_session(self, session_id, data, ttl=3600):
        """
        Armazena dados da sessão no Redis com um TTL (em segundos).
        """
        session_id = session_id.strip()
        try:
            serialized_data = json.dumps(data, default=self.json_serializer)
            self.redis.setex(f"session:{session_id}", ttl, serialized_data)
        except TypeError as e:
            logger.error(f"Erro ao serializar dados da sessão: {e}")
            logger.debug(f"Dados da sessão: {data}")
            raise
    def get_session(self, session_id):
        """
        Recupera os dados da sessão do Redis.
        """
        session_data = self.redis.get(f"session:{session_id}")
        if session_data:
            session_data = json.loads(session_data)

            last_interaction = datetime.fromisoformat(session_data.get("last_interaction"))

            if time_now() - last_interaction > self.session_timeout:
                return None
            return session_data
        return None

    def mark_message_as_processed(self, message_id, ttl=1800):
        """
        Marca uma mensagem como processada, armazenando o ID no Redis com um TTL (30 minutos por padrão).
        """
        try:
            self.redis.setex(f"message:{message_id}", ttl, "processed")
            logger.info(f"Mensagem {message_id} marcada como processada.")
        except Exception as e:
            logger.error(f"Erro ao marcar mensagem {message_id} como processada: {e}")
            raise

    def check_processed_message(self, message_id):
        """
        Verifica se uma mensagem já foi processada.
        """
        try:
            return self.redis.exists(f"message:{message_id}") > 0
        except Exception as e:
            logger.error(f"Erro ao verificar mensagem {message_id}: {e}")
            raise

    @staticmethod
    def json_serializer(obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        if hasattr(obj, '__dict__'):
            return obj.__dict__
        return str(obj)

    @staticmethod
    def json_deserializer(dct):
        for key, value in dct.items():
            if isinstance(value, str):
                try:
                    dct[key] = datetime.fromisoformat(value)
                except ValueError:
                    pass
        return dct
