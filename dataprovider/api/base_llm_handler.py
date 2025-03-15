from abc import ABC, abstractmethod
from typing import Callable
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables.history import RunnableWithMessageHistory
from dataprovider.api.session_handler import get_session_history
from database.database import get_db

class BaseLLMHandler(ABC):
    def __init__(self):
        self.db = next(get_db())

    @abstractmethod
    def get_llm(self):
        pass

    @abstractmethod
    def create_prompt(self, *args, **kwargs) -> ChatPromptTemplate:
        pass

    def create_runnable(self, *args, **kwargs):
        prompt = self.create_prompt(*args, **kwargs)
        return prompt | self.get_llm()

    def handle_question(self, question: str, session_id: str, *args, **kwargs):
        """
        Lida com uma questão de um LLM usando um histórico de mensagens.
        """
        get_history_func: Callable[[None], BaseChatMessageHistory] = lambda _: get_session_history(session_id)

        runnable = self.create_runnable(*args, **kwargs)

        with_message_history = RunnableWithMessageHistory(
            runnable,
            get_history_func,
            input_messages_key="input",
            history_messages_key="history",
        )

        response = with_message_history.invoke(
            {"input": question},
            config={"configurable": {"session_id": session_id}},
        )

        history = get_session_history(session_id)
        history_size = len(history.messages) if hasattr(history, 'messages') else 0

        return response, history_size
