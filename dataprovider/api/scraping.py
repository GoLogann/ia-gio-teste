from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_openai.chat_models import ChatOpenAI
from typing import Callable
from dataprovider.api.base_llm_handler import BaseLLMHandler
from dataprovider.api.session_handler import get_session_history
from repository.configuracao_repository import ConfiguracaoRepository
from langchain_core.chat_history import BaseChatMessageHistory
from constantes_globais.enum.provedor import OPEN_AI
from langchain_core.runnables.history import RunnableWithMessageHistory

class ScrapingHandler(BaseLLMHandler):
    def __init__(self):
        super().__init__()
        self.questionnaire_state = {}
        self.embedding_function = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

    def get_llm(self):
        try:
            configuracao_repo = ConfiguracaoRepository(self.db)
            configuracao = configuracao_repo.get_configuracao_by_provedor_nome(OPEN_AI)

            if not configuracao:
                raise Exception("Configuração para o provedor OpenAI não encontrada")

            return ChatOpenAI(
                model="gpt-4o",
                openai_api_key=configuracao.api_key,
                temperature=float(configuracao.temperatura)
            )

        except Exception as e:
            raise Exception(str(e))

    def create_prompt(self, context: str = "") -> ChatPromptTemplate:
        return ChatPromptTemplate.from_messages(
            [
                ("system", context),
                MessagesPlaceholder(variable_name="history"),
                ("human", "{input}"),
            ]
        )

    def create_prompt_descricao_boards(self) -> ChatPromptTemplate:
        system_message = """
        Você é um assistente especializado em extrair e organizar informações sobre empresas. Quando receber o nome de uma empresa, siga estas etapas:

1. Extraia os seguintes dados:
   - **Breve Descrição:** Explique o que a empresa faz em poucas palavras.
   - **Características:** Liste qualidades principais e valores da empresa.
   - **Palavras-Chave:** Identifique palavras que melhor representam os serviços, produtos ou filosofia da empresa.
   - **Indústria:** Identifique o setor da economia em que a empresa opera, como Fintech, Software, Saúde, etc.

2. Organize os dados no seguinte formato:

**Empresa:** [Nome da Empresa]

**Breve Descrição:** [Descrição curta sobre o que a empresa faz.]

**Características:**  
- [Característica 1]  
- [Característica 2]  
- [Característica 3]  

**Palavras-Chave:** [Palavra-chave 1, Palavra-chave 2, Palavra-chave 3]  

**Indústria:** [Indústria principal da empresa]

4. Se não for possível acessar o site ou coletar informações completas, indique que os dados não foram encontrados.

Retorne as informações de forma clara e organizada."""

        return ChatPromptTemplate.from_messages(
            [
                ("system", system_message),
                MessagesPlaceholder(variable_name="history"),
                ("human", "{input}"),
            ]
        )

    def handle_question(self, question: list[str], session_id: str, *args, **kwargs):

        get_history_func: Callable[[None], BaseChatMessageHistory] = lambda _: get_session_history(session_id)

        prompt_template = self.create_prompt_descricao_boards()

        runnable = prompt_template | self.get_llm()
        with_message_history = RunnableWithMessageHistory(
            runnable,
            get_history_func,
            input_messages_key="input",
            history_messages_key="history",
        )
        full_prompt = f"Novo Resumo: {question}"
        response = with_message_history.invoke(
            {"input": full_prompt},
            config={"configurable": {"session_id": session_id}},
        )

        history = get_session_history(session_id)
        history_size = len(history.messages) if hasattr(history, 'messages') else 0

        return response, history_size