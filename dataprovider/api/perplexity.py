from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_community.chat_models import ChatPerplexity
from dataprovider.api.base_llm_handler import BaseLLMHandler
from repository.configuracao_repository import ConfiguracaoRepository

from constantes_globais.enum.provedor import PERPLEXITY_AI


class PerplexityHandler(BaseLLMHandler):
    def get_llm(self):
        try:
            configuracao_repo = ConfiguracaoRepository(self.db)
            configuracao = configuracao_repo.get_configuracao_by_provedor_nome(PERPLEXITY_AI)

            if not configuracao:
                raise Exception("Configuração para o provedor Google não encontrada")

            return ChatPerplexity(
                model="llama-3.1-sonar-small-128k-online",
                pplx_api_key = configuracao.api_key,
                temperature=0.7
            )

        except Exception as e:
            raise Exception(str(e))

    def create_prompt(self) -> ChatPromptTemplate:
        return ChatPromptTemplate.from_messages(
            [
                MessagesPlaceholder(variable_name="history"),
                ("human", "{input}"),
            ]
        )