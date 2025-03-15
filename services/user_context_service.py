import re
import uuid
from datetime import timedelta
from collections import defaultdict
from fastapi.logger import logger

from constantes_globais.enum.contextos import get_identifier_by_number
from domain.schemas.gio_schema import ComunicacaoEnxameContatoSchema, GioRequestSchemaInnovationAward
from resources.datetime_config import time_now
from services.chatgpt_handler_dynamic import ChatGPTHandlerDynamic
from utils.helpers import get_context_by_name


class UserContextService:
    def __init__(self):
        self.user_context = defaultdict(lambda: {"context": [], "history": [], "last_interaction": time_now()})
        self.session_timeout = timedelta(hours=1)

    def ensure_user_context(self, telefone_usuario: str):
        telefone_usuario = self.normalize_telefone(telefone_usuario)
        if telefone_usuario not in self.user_context or \
                time_now() - self.user_context[telefone_usuario]["last_interaction"] > self.session_timeout:
            self.reset_user_context(telefone_usuario)

    def add_to_user_context(self, telefone_usuario: str, mensagem: str):
        telefone_usuario = self.normalize_telefone(telefone_usuario)
        self.ensure_user_context(telefone_usuario)

        if mensagem not in self.user_context[telefone_usuario]["context"]:
            self.user_context[telefone_usuario]["context"].append(mensagem)
        self.user_context[telefone_usuario]["last_interaction"] = time_now()

    def update_user_context(self, telefone_usuario: str, novo_contexto: list):
        """
        Atualiza o contexto do usuário.

        Args:
            telefone_usuario (str): Número de telefone do usuário.
            novo_contexto (list): Novo contexto a ser definido.
        """
        self.ensure_user_context(telefone_usuario)
        self.user_context[telefone_usuario]["context"] = novo_contexto
        self.user_context[telefone_usuario]["last_interaction"] = time_now()

    def add_to_history(self, telefone_usuario: str, mensagem: str, origem: str = "user"):
        telefone_usuario = self.normalize_telefone(telefone_usuario)
        self.ensure_user_context(telefone_usuario)

        if not any(entry["message"] == mensagem and entry["from"] == origem
                   for entry in self.user_context[telefone_usuario]["history"]):
            self.user_context[telefone_usuario]["history"].append({"from": origem, "message": mensagem})

        self.user_context[telefone_usuario]["last_interaction"] = time_now()

    def reset_user_context(self, telefone_usuario: str):
        telefone_usuario = self.normalize_telefone(telefone_usuario)
        self.user_context[telefone_usuario] = {
            "context": [],
            "history": [],
            "last_interaction": time_now(),
            "id_dialogo": None,
        }

    @staticmethod
    def normalize_telefone(telefone: str) -> str:
        """
        Normaliza o número de telefone para o formato correto, adicionando o '9' após o DDD, se necessário.
        """
        telefone = re.sub(r"[^\d]", "", telefone)

        if len(telefone) == 12 and telefone[4] != "9":
            telefone = telefone[:4] + "9" + telefone[4:]

        return telefone

    @staticmethod
    async def gerar_mensagem_inicial_com_modelo(telefone_usuario: str, context):
        """
        Gera a mensagem inicial utilizando o modelo de IA.

        Args:
            telefone_usuario (str): Número de telefone do usuário.

        Returns:
            str: mensagem inicial gerada.
        """
        try:
            chatgpt_handler = ChatGPTHandlerDynamic()
            modelo = context.get("modelo", "")
            cliente = context.get("nome", "Cliente")
            resposta_inicial, _ = chatgpt_handler.handle_question_bot(
                "GERAR MENSAGEM INICIAL", telefone_usuario, modelo, cliente
            )

            return resposta_inicial
        except Exception as e:
            logger.error(f"Erro ao gerar mensagem inicial com o modelo: {e}")
            return "Desculpe, houve um erro ao iniciar a conversa."

    @staticmethod
    async def gerar_resposta_do_modelo(telefone_usuario: str, mensagem: str, context):
        try:
            chatgpt_handler = ChatGPTHandlerDynamic()
            modelo = context.get("modelo", "")
            cliente = context.get("nome", "Cliente")
            resposta_inicial, _ = chatgpt_handler.handle_question_bot(
                mensagem, telefone_usuario, modelo, cliente
            )

            return resposta_inicial
        except Exception as e:
            logger.error(f"Erro ao gerar mensagem inicial com o modelo: {e}")
            return "Desculpe, houve um erro ao iniciar a conversa."

    @staticmethod
    async def generate_swarm_web_chat_model_response(gio: ComunicacaoEnxameContatoSchema, context):
        logger.info(f"Iniciando generate_swarm_web_chat_model_response.")

        try:
            if not gio or not gio.questao:
                logger.error(f"Parâmetros inválidos.")
                return "Entrada inválida. Por favor, verifique os dados.", 0

            modelo = context.get("modelo", "")
            if not modelo:
                logger.error(f"Modelo não especificado no contexto.")
                return "Configuração do modelo não encontrada.", 0

            chatgpt_handler = ChatGPTHandlerDynamic()

            try:
                response, length_history = await chatgpt_handler.web_chat_swarm(gio, modelo)

                if isinstance(response, str):
                    logger.warning(f"Resposta de erro retornada.")
                    return response, length_history

                return response, length_history

            except Exception as e:
                logger.error(f"Erro na chamada web_chat_swarm: {str(e)}.", exc_info=True)
                return "Erro no processamento da conversa.", 0

        except Exception as e:
            logger.critical(f"Erro crítico no generate_swarm: {str(e)}.", exc_info=True)
            return f"Falha crítica no sistema. Erro: {str(e)}.", 0

    @staticmethod
    async def generate_innovation_award_model_response(gio: GioRequestSchemaInnovationAward, db):
        try:
            chatgpt_handler = ChatGPTHandlerDynamic()
            context_type = get_identifier_by_number(gio.specific_context_identifier)
            context_specific_question = get_context_by_name(db, context_type)
            response, length_history = chatgpt_handler.handle_question_innovation_award(gio, context_specific_question)

            return response, length_history
        except Exception as e:
            logger.error(f"Erro ao gerar mensagem inicial com o modelo: {e}")
            return "Desculpe, houve um erro ao iniciar a conversa."
