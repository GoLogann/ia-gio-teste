from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_google_genai import ChatGoogleGenerativeAI

from dataprovider.api.base_llm_handler import BaseLLMHandler
from repository.configuracao_repository import ConfiguracaoRepository

from constantes_globais.enum.provedor import GOOGLE_AI


class GeminiHandler(BaseLLMHandler):
    def get_llm(self):
        try:
            configuracao_repo = ConfiguracaoRepository(self.db)
            configuracao = configuracao_repo.get_configuracao_by_provedor_nome(GOOGLE_AI)

            if not configuracao:
                raise Exception("Configuração para o provedor Google não encontrada")

            return ChatGoogleGenerativeAI(
                model="gemini-pro",
                google_api_key=configuracao.api_key,
                temperature=float(configuracao.temperatura)
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