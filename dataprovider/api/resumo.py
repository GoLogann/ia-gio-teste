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

class ResumoHandler(BaseLLMHandler):
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
        Você é um assistente especializado em gerar resumos de reuniões. 
        Ao receber uma descrição ou transcrição de uma reunião, sua tarefa é identificar os principais 
        pontos discutidos, decisões tomadas, ações atribuídas e qualquer informação relevante mencionada. 
        O resumo deve ser claro, organizado e adaptado para facilitar o entendimento rápido, destacando os 
        pontos principais da reunião. Estruture o resultado da seguinte forma:

        Tópicos Principais: Liste os assuntos mais importantes discutidos.
        Decisões Tomadas: Informe quais decisões foram confirmadas durante a reunião.
        Ações e Responsáveis: Liste as tarefas definidas e quem é responsável por cada uma delas.
        Observações Importantes: Inclua qualquer outro detalhe relevante.
        """

        return ChatPromptTemplate.from_messages(
            [
                ("system", system_message),
                MessagesPlaceholder(variable_name="history"),
                ("human", "{input}"),
            ]
        )

    def handle_question(self, question: str, session_id: str, *args, **kwargs):

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