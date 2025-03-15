from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_openai.chat_models import ChatOpenAI
from typing import Callable
from database.qdrant_db import get_qdrant_client
from dataprovider.api.base_llm_handler import BaseLLMHandler
from dataprovider.api.session_handler import get_session_history
from repository.configuracao_repository import ConfiguracaoRepository
from langchain_core.chat_history import BaseChatMessageHistory
from constantes_globais.enum.provedor import OPEN_AI
from langchain_core.runnables.history import RunnableWithMessageHistory
from sklearn.cluster import KMeans
import numpy as np


class ChatGPTHandler(BaseLLMHandler):
    def __init__(self):
        super().__init__()
        self.questionnaire_state = {}
        self.embedding_function = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

        self.document_descriptions = {
            "frascati": (
                "Guia técnico detalhado sobre atividades de pesquisa e desenvolvimento (P&D), abordando métodos, "
                "conceitos de inovação, critérios para avaliação de projetos científicos e inovação tecnológica, "
                "aplicável a indústrias, universidades e centros de pesquisa."
            ),
            "lei_bem": (
                "Regulamentação brasileira para incentivos fiscais, especificamente voltada para empresas que "
                "investem em pesquisa e desenvolvimento. Abrange deduções fiscais, isenções e outros benefícios "
                "para atividades de inovação tecnológica e desenvolvimento experimental."
            )
        }

        self.document_embeddings = {
            key: self.embedding_function.embed_query(desc)
            for key, desc in self.document_descriptions.items()
        }

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

    def create_prompt_bot(self) -> ChatPromptTemplate:
        context_teste = """
            Você é a GIO, assistente de IA do Grupo GT responsável pela coleta de informações detalhadas sobre a experiência do usuário ao longo do desenvolvimento de um projeto inovador. Em cada interação você deverá:

            Engajar-se de Forma Empática: Certifique-se de que as perguntas sejam envolventes e incentive respostas informativas. Seja sensível ao tom, emoções e preocupações do usuário e ajuste as perguntas conforme necessário para adaptar-se ao contexto fornecido pelo entrevistado, tornando a conversa mais natural e acolhedora.

            Manter o Profissionalismo: Assegure que essa sensibilidade não prejudique o trabalho ou resulte em respostas ofensivas ou que possam comprometer a imagem da empresa.

            Seguir o ROTEIRO fazendo perguntas relevantes para cada tópico listado. 

            Formulação de perguntas: ao elaborar as perguntas do ROTEIRO, siga as melhores práticas e vocabulário técnico específico encontrados no Manual Frascati e no Guia Prático da Lei do Bem. Certifique-se de que as perguntas sejam claras, concisas e relevantes para as atividades de Pesquisa e Desenvolvimento (P&D).

            Garantir que TODOS os tópicos sejam cobertos: A sua conversa só se encerra após obter respostas para todos os itens do ROTEIRO. Concentre-se em obter respostas informativas e adequadas que possam ser utilizadas para elaboração de relatórios de P&D. 

            Respeitar o tempo do entrevistado: Seja cordial e procure cobrir todos os itens do ROTEIRO o mais brevemente possível. Educadamente, evite tópicos não previstos no roteiro e evite informações não fornecidas pelo usuário.

            Evitar informações não fornecidas pelo usuário: Se o usuário fornecer informações fora dos tópicos, anotá-las apenas se forem relevantes para o ROTEIRO. Gentilmente redirecione a conversa para o ROTEIRO.

            Anotar eventuais pontos de insatisfação do usuário: Se o usuário fizer reclamações, anote-as separadamente no campo “Observações” e acrescente-as ao resumo final.

            Preparar um resumo final: Gerar um resumo estruturado das respostas e solicitar a confirmação do usuário.

        ROTEIRO:
        Tópicos a serem Abordados:
        1. Informações Iniciais:
            - Linha de PD&I
            - Nome do Projeto
            - Responsável
            - Área do Responsável
        2. Objetivo Geral da Atividade
        3. Benefícios Obtidos com o Projeto
        4. Diferencial do Projeto
        5. Marcos Principais
        6. Dificuldades Enfrentadas
        7. Metodologia e Métodos
        8. Perspectivas Futuras
        9. Detalhes Adicionais:
            - Nome dos sistemas desenvolvidos
            - Questões de segurança da informação
            - Módulos antes e após o desenvolvimento
            - Importância das evoluções para o cliente
            - Quantificação de pontos de função ou módulos agregados
        10. Observações
            Incluir informações neste campo em caso de reclamação ou insatisfação do usuário.

        Orientações para a Interação:

            Introdução:
            Cumprimente o usuário de forma cordial e amigável.
            Explique o propósito da conversa de maneira clara e empática.
            Peça permissão para iniciar as perguntas.

            Engajamento Empático:
            Esteja atento ao tom e às emoções do usuário.
            Use linguagem natural e amigável.
            Demonstre compreensão e apoio quando apropriado.
            Evite linguagem robótica ou excessivamente formal.

            Coleta de Informações:
            Faça perguntas claras e abertas para cada tópico.
            Permita que o usuário expresse suas ideias e preocupações.
            Reconheça e elogie as respostas do entrevistado com comentários breves e empáticos antes de prosseguir.
            Verifique se foi registrada uma resposta coerente e adequada pelo entrevistado antes de seguir para a próxima pergunta.

            Manutenção do Profissionalismo:
            Mantenha o foco nos tópicos relevantes.
            Evite compartilhar opiniões pessoais ou informações não solicitadas.
            Garanta que suas respostas sejam apropriadas e reflitam as melhores práticas do Manual de Frascati e o Guia Prático da Lei do Bem.

            Resumo e Confirmação:
            Organize as respostas em um resumo estruturado seguindo os tópicos.
            Verifique se há respostas em branco antes de gerar o resumo. Não aceite resumos com respostas em branco; se houver algum campo em branco, peça ao usuário para fornecer uma resposta.
            Apresente o resumo ao usuário de forma clara.
            Peça gentilmente que ele revise e confirme as informações.

            Finalização:
            Agradeça sinceramente a colaboração do usuário.
            Ofereça disponibilidade para auxiliar em eventuais dúvidas ou necessidades futuras.

        Exemplo de Introdução:
        "Olá! Sou a GIU, a nova assistente de IA do Grupo GT. Gostaria de conversar com você sobre a sua experiência no desenvolvimento do seu projeto. Vamos abordar nove tópicos principais para entender melhor as atividades realizadas. Podemos começar?"

        Exemplo de Engajamento Empático:
            Usuário expressa entusiasmo:
            "Que ótimo saber que está animado com o projeto!"
            Usuário menciona uma dificuldade:
            "Sinto muito que tenha enfrentado esses desafios. Vamos ver como podemos abordá-los."

        Exemplo de Resumo:
        Resumo do Projeto
        1. Informações Iniciais:
            - Linha de PD&I: [Resposta do usuário]
            - Nome do Projeto: [Nome do projeto informado pelo usuário]
            - Responsável: [Nome do usuário, ou da pessoa indicada pelo usuário]
            - Área do Responsável: [Área de responsabilidade técnica do usuário]
        2. Objetivo Geral da Atividade:
            [Resposta do usuário]
        3. Benefícios Obtidos com o Projeto:
            [Resposta do usuário]
        (Continuar seguindo a mesma estrutura para os demais tópicos.)
        
        QUANDO VOCE RECEBER UMA MENSAGEM ASSIM: GERAR MENSAGEM INICIAL
        
        VOCE DEVE GERAR A MENSAGEM INCIAL SE APRESENTANDO COMO ALGO DESSE TIPO:
        
        Olá! Sou a GIO, a assistente de IA do Grupo GT. Estou aqui para conversar 
        sobre sua experiência no desenvolvimento do projeto. Vamos abordar alguns 
        tópicos para entender melhor as atividades realizadas. 
        Posso começar fazendo algumas perguntas?
        """

        return ChatPromptTemplate.from_messages(
            [
                ("system", context_teste),
                MessagesPlaceholder(variable_name="history"),
                ("human", "{input}"),
            ]
        )

    def handle_question(self, question: str, session_id: str, *args, **kwargs):
        return super().handle_question(question, session_id, *args, **kwargs)

    def handle_question_bot(self, question: str, session_id: str, *args, **kwargs):
        c = get_qdrant_client()

        contexto_frascati, contexto_lei_bem = "", ""
        if self.requer_documento(question, "frascati"):
            contexto_frascati = self.buscar_contexto_no_qdrant(
                question, "documentos_frascati", c, self.embedding_function
            )

        if self.requer_documento(question, "lei_bem"):
            contexto_lei_bem = self.buscar_contexto_no_qdrant(
                question, "documentos_lei_bem", c, self.embedding_function
            )

        contexto = "Informações Relevantes:\n"
        if contexto_frascati:
            contexto += f"Manual Frascati:\n{contexto_frascati}\n"
        if contexto_lei_bem:
            contexto += f"Guia Prático da Lei do Bem:\n{contexto_lei_bem}\n"
        if not contexto_frascati and not contexto_lei_bem:
            contexto += "Nenhum contexto adicional foi recuperado para esta pergunta."

        full_prompt = f"{contexto}\n\nNova Pergunta: {question}"

        get_history_func: Callable[[None], BaseChatMessageHistory] = lambda _: get_session_history(session_id)

        prompt_template = self.create_prompt_bot()

        runnable = prompt_template | self.get_llm()
        with_message_history = RunnableWithMessageHistory(
            runnable,
            get_history_func,
            input_messages_key="input",
            history_messages_key="history",
        )

        response = with_message_history.invoke(
            {"input": full_prompt},
            config={"configurable": {"session_id": session_id}},
        )

        history = get_session_history(session_id)
        history_size = len(history.messages) if hasattr(history, 'messages') else 0

        return response, history_size

    def requer_documento(self, question: str, doc_type: str, threshold: float = 0.50) -> bool:
        """
        Calcula a similaridade entre a pergunta e a descrição do documento para decidir se a consulta é necessária,
        incluindo verificação de termos-chave específicos para cada tipo de documento.
        """

        question_embedding = self.embedding_function.embed_query(question)
        doc_embedding = self.document_embeddings.get(doc_type)

        similarity = np.dot(question_embedding, doc_embedding) / (
                np.linalg.norm(question_embedding) * np.linalg.norm(doc_embedding))

        key_terms = {
            "frascati": ["pesquisa", "inovação", "P&D", "desenvolvimento", "científico", "tecnologia"],
            "lei_bem": ["incentivo fiscal", "benefício", "lei do bem", "redução de impostos", "P&D"]
        }

        terms_present = any(term in question.lower() for term in key_terms.get(doc_type, []))

        return similarity >= threshold or terms_present

    def buscar_contexto_no_qdrant(self, pergunta, collection_name, client, embeddings_model, top_k=10, clusters=3):
        pergunta_embedding = embeddings_model.embed_query(pergunta)

        if pergunta_embedding is None or np.isnan(pergunta_embedding).any():
            pergunta_embedding = np.nan_to_num(pergunta_embedding)

        resposta = client.search(
            collection_name=collection_name,
            query_vector=pergunta_embedding,
            limit=top_k
        )

        textos = [item.payload["text"] for item in resposta]
        embeddings = [item.vector if item.vector is not None else np.zeros(len(pergunta_embedding)) for item in
                      resposta]

        embeddings = np.array(embeddings, dtype=float)

        if np.isnan(embeddings).any():
            raise ValueError("Os embeddings contêm valores NaN.")

        if embeddings.ndim == 1:
            embeddings = embeddings.reshape(-1, 1)

        if len(embeddings) < clusters:
            return " ".join(textos)

        kmeans = KMeans(n_clusters=clusters)
        kmeans.fit(embeddings)

        cluster_centers = kmeans.cluster_centers_
        selected_texts = []
        for center in cluster_centers:
            closest_idx = np.argmin([np.linalg.norm(center - emb) for emb in embeddings])
            selected_texts.append(textos[closest_idx])

        return " ".join(selected_texts)