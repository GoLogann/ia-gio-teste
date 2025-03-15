from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_community.chat_models import ChatAnthropic
from dataprovider.api.base_llm_handler import BaseLLMHandler
from repository.configuracao_repository import ConfiguracaoRepository
from constantes_globais.enum.provedor import ANTHROPIC_AI


class AnthropicHandler(BaseLLMHandler):
    def get_llm(self):
        try:
            configuracao_repo = ConfiguracaoRepository(self.db)
            configuracao = configuracao_repo.get_configuracao_by_provedor_nome(ANTHROPIC_AI)

            if not configuracao:
                raise Exception("Configuração para o provedor Google não encontrada")

            return ChatAnthropic(
                model="claude-3-5-sonnet-20240620",
                temperature=0.7,
                api_key = configuracao.api_key
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