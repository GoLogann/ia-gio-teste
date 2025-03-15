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


class DescricaoHandler(BaseLLMHandler):
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
        Você é um assistente inteligente de gestão de projetos. Quando alguém fornecer um título e uma breve descrição de uma tarefa, sua tarefa é expandir essas informações, gerando uma descrição mais detalhada e estruturada.

        Título da Tarefa: {title}
            Descrição Breve: {brief_description}

        Sua descrição deve incluir:
        - Uma introdução clara explicando o objetivo da tarefa.
        - Passos detalhados que descrevem o que deve ser feito.
        - Os resultados esperados ao final da tarefa.
        - Qualquer ferramenta, recurso ou habilidade necessária para a execução da tarefa.
        - Prazo ou data limite, se aplicável.

        Seja claro, objetivo e forneça uma descrição completa para que qualquer membro da equipe possa entender a tarefa com clareza.
        """

        return ChatPromptTemplate.from_messages(
            [
                ("system", system_message),
                MessagesPlaceholder(variable_name="history"),
                ("human", "{input}"),
            ]
        )

    def handle_question(self, question: str, session_id: str, *args, **kwargs):
        return super().handle_question(question, session_id, *args, **kwargs)

    def handle_question_bot(self, question: str, session_id: str, *args, **kwargs):

        get_history_func: Callable[[None], BaseChatMessageHistory] = lambda _: get_session_history(session_id)

        prompt_template = self.create_prompt_descricao_boards()

        runnable = prompt_template | self.get_llm()
        with_message_history = RunnableWithMessageHistory(
            runnable,
            get_history_func,
            input_messages_key="input",
            history_messages_key="history",
        )
        full_prompt = f"Nova Tarefa: {question}"
        response = with_message_history.invoke(
            {"input": full_prompt},
            config={"configurable": {"session_id": session_id}},
        )

        history = get_session_history(session_id)
        history_size = len(history.messages) if hasattr(history, 'messages') else 0

        return response, history_size