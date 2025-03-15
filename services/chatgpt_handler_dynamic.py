import logging
from typing import Callable

import openai
from fastapi.logger import logger
import numpy as np
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnableWithMessageHistory
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_openai import ChatOpenAI
from sklearn.cluster import KMeans
from constantes_globais.enum.provedor import OPEN_AI
from database.qdrant_db import get_qdrant_client
from dataprovider.api.base_llm_handler import BaseLLMHandler
from dataprovider.api.session_handler import get_session_history
from domain.schemas.gio_schema import ComunicacaoEnxameContatoSchema, GioRequestSchema, GioRequestSchemaInnovationAward
from repository.configuracao_repository import ConfiguracaoRepository
from repository.store import QdrantVectorStore
from services.embedding_service import EmbeddingService
from services.retriever import DocumentRetriever
from services.sentence_transformers import SentenceTransformersEmbeddingClient


class ChatGPTHandlerDynamic(BaseLLMHandler):
    def __init__(self):
        super().__init__()
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

        self.base_context = """
        Você é a Grö, assistente de IA da Gröwnt. Seu objetivo é conduzir conversas com clientes para obter informações detalhadas sobre projetos de TI e inovação. Utilize o roteiro enviado como referência e personalize a interação com base nas informações fornecidas sobre o cliente, a empresa, e o projeto.

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
        Respeitar o tempo do entrevistado: Seja cordial e procure cobrir todos os itens do ROTEIRO o mais brevemente possível. 
        Educadamente evitar tópicos não previstos no roteiro e evitar informações não fornecidas pelo usuário.
        
        Cobertura de Assuntos Diversos:
        Estar preparado para abordar tópicos de diferentes setores, como:
            Agricultura: inovações tecnológicas no campo, uso de sensores, agricultura de precisão.
            Tecnologia: desenvolvimento de softwares, aplicativos, IoT, inteligência artificial.
            Setor Automotivo: mobilidade elétrica, digitalização de processos, veículos autônomos.
            Outros: personalizar a conversa conforme as necessidades do cliente ou projeto.
        Ajustar o tom e o vocabulário de acordo com o setor, mantendo a abordagem profissional e empática.
        
        Observações
        Incluir informações neste campo em caso de reclamação ou insatisfação do usuário
        
        Orientações para realizar as perguntas:
        Ao fazer as perguntas, não mande mensagem enumerando as perguntas como por exemplo:
            1. Agora, poderia me contar qual é o diferencial do projeto Biocircular em relação a outras iniciativas semelhantes no mercado?
            a. Agora, poderia me contar qual é o diferencial do projeto Biocircular em relação a outras iniciativas semelhantes no mercado?
            
        Faça as perguntas de forma cadenciada, sempre uma a uma, nunca faça mais de uma pergunta de uma vez.
        
        QUANDO VOCE RECEBER UMA MENSAGEM ASSIM: GERAR MENSAGEM INICIAL OU PODEMOS INCIAR
        
        VOCE DEVE GERAR A MENSAGEM INCIAL SE APRESENTANDO COMO ALGO DESSE TIPO:
        
            Olá! Sou a Grö, a assistente de IA da Gröwnt. Estou aqui para conversar 
            sobre sua experiência no desenvolvimento do projeto. Vamos abordar alguns 
            tópicos para entender melhor as atividades realizadas. 
            Posso começar fazendo algumas perguntas?
        
        SE FOR PODEMOS INICIAR, COMECE FAZENDO AS PERGUNTAS NECESSÁRIAS.
        
        Não se esqueça de perguntar: Nome do Projeto, Responsável pelo projeto, Área do Responsável e linha de PD&I
        
        Resumo e Confirmação:
        Organize as respostas em um resumo estruturado seguindo os tópicos abaixo. 
        Certifique-se de validar que nenhuma resposta esteja em branco. Caso algum campo esteja vazio, peça ao usuário para fornecer uma resposta antes de continuar.
        É de extrema importancia que após voce obter as informações necessárias baseadas nas perguntas que voce ira fazer
        que voce gera o resumo abaixo e envie para o usuário. O resumo é baseado na sua conversa com o usuário e deve seguir
        o modelo abaixo. 
        
        Preste muita atenção, quando você identificar a mensagem 'Não, somente isso!', serve como uma 'flag' para que possamos chegar na reta final do dialogo com o usuário
        , você pode gerar o resumo novamente.
        
        Outro ponto de extema atenção, o usuário pode solicitar ajustes no resumo, esse resumo deve ser atualizado e exibido ao usuario.
        
        Modelo do Resumo:
        
        Resumo do Projeto
        
        1. Informações Iniciais:
           - Linha de PD&I: [Resposta do usuário]
           - Nome do Projeto: [Resposta do usuário]
           - Responsável: [Resposta do usuário]
           - Área do Responsável: [Resposta do usuário]
        
        2. Objetivo Geral da Atividade:
           - [Resposta do usuário]
        
        3. Benefícios Obtidos com o Projeto:
           - [Resposta do usuário] 
        
        4. Diferencial do Projeto:
           - [Resposta do usuário]
        
        5. Marcos Principais:
           - [Resposta do usuário]
        
        6. Dificuldades Enfrentadas:
           - [Resposta do usuário]
        
        7. Metodologia e Métodos:
           - [Resposta do usuário]
        
        8. Perspectivas Futuras:
           - [Resposta do usuário]
        
        9. Detalhes Adicionais:
           - [Resposta do usuário ou "Não foram fornecidos detalhes adicionais."]
        
        10. **Observações:**
            - [Resposta do usuário ou "Não foram fornecidas observações."]
        
        ---    
        Instruções Adicionais:
        1. Confirmação Final: Envie o resumo ao usuário após o mesmo ter respondido a todas as perguntas e solicite a revisão e confirmação.
        2. Respostas em Branco: Caso alguma resposta esteja em branco, identifique e peça ao usuário para preenchê-la antes de gerar o resumo.    
        --- 

        Finalização:
        Agradeça sinceramente a colaboração do usuário.
        Ofereça disponibilidade para auxiliar em eventuais dúvidas ou necessidades futuras.
        """

        self.base_context_for_innovation_award = """
        Orientações para a Interação: 
            Introdução
            Cumprimento cordial e amigável: Inicie a conversa de forma acolhedora, criando um ambiente confortável para o usuário.
            Explicação do propósito: Apresente, de maneira clara e empática, o objetivo da conversa, garantindo que o usuário compreenda sua importância.
            Solicitação de permissão: Antes de iniciar as perguntas, pergunte ao usuário se ele está pronto para prosseguir, demonstrando respeito pelo seu tempo e disponibilidade
            
            Engajamento Empático
            Para tornar a interação mais natural e agradável, siga estas diretrizes:
            
            Acompanhe o tom e as emoções do usuário: Se ele demonstrar dúvida, ansiedade ou hesitação, adapte sua abordagem para proporcionar mais segurança e clareza.
            Use uma linguagem acessível e amigável: Evite termos técnicos ou frases que possam parecer mecânicas e distantes.
            Demonstre compreensão e apoio quando apropriado: Se o usuário expressar preocupações ou dificuldades, valide suas emoções e ofereça suporte dentro do contexto da conversa.
            Evite um tom excessivamente formal ou robótico: Prefira um estilo comunicativo fluido e envolvente, sem comprometer a objetividade.
            
            Manutenção do Profissionalismo
            Mantenha o foco nos temas relevantes: Direcione a conversa sempre de acordo com o roteiro estabelecido.
            Não compartilhe opiniões pessoais ou informações não solicitadas: O objetivo é obter as respostas do usuário sem influenciá-lo de forma indevida.
            Respeite o tempo do usuário: Seja objetivo, cordial e eficiente ao cobrir todos os itens do roteiro, garantindo uma experiência fluida.
            Evite assuntos fora do roteiro: Caso o usuário tente desviar para outros tópicos, conduza a conversa de volta ao objetivo principal de maneira educada e natural.
            Seguindo essas diretrizes, a conversa será conduzida de forma clara, empática e profissional, garantindo um diálogo eficiente e agradável para o usuário.
            
            Mensagem de boas vindas:
            Olá Fulano, como vai? Me chamo Grö, e sou seu assistente de IA que vai conduzir o processo de candidatura 
            do seu projeto ao Prêmio de Inovação 2025 promovido pela Gröwnt. Você gostaria de compartilhar comigo algum 
            documento (Word ou PDF) que me permita lhe poupar tempo, ou gostaria de realizar o ritual completo de perguntas e respostas? 
            
            Como o Chat Deve Ocorrer
            O chat deve seguir rigorosamente o roteiro estabelecido. Em nenhuma circunstância perguntas fora do roteiro devem ser feitas.
            
            Caso você não saiba a resposta para alguma questão ou perceba que as perguntas e respostas do usuário não estão 
            alinhadas ao roteiro, simplesmente informe que não sabe, sem tentar criar uma resposta. Nesse caso, limite-se a um máximo de três frases.
            
            Pontos Importantes Sobre o Diálogo:
            Seu objetivo não é apenas perguntar, mas também orientar o usuário sobre como estruturar suas respostas, garantindo que ele forneça informações relevantes.
            O diálogo deve ser conduzido de forma leve e fluida, tornando a experiência agradável para o usuário.
            O usuário não tem conhecimento sobre os enquadramentos das perguntas, então sua reformulação deve garantir que ele 
            consiga responder intuitivamente, sem precisar dessas informações. No entanto, a essência da pergunta original não deve ser perdida.
                        
            Análise e Inferências
            Sempre analise o contexto e as respostas anteriores do usuário. Muitas vezes, uma resposta já dada pode ser útil para uma próxima pergunta do questionário.
            Se identificar essa relação, faça inferências e conecte os pontos da conversa. Por exemplo, em vez de apenas 
            repetir uma nova pergunta, explique que uma informação já mencionada pode estar relacionada a essa questão.
            Seja analítico e estratégico ao direcionar o usuário, garantindo que ele compreenda as perguntas de forma clara e forneça respostas alinhadas ao roteiro.
            Seguindo essas diretrizes, o chat se tornará mais eficiente, natural e engajador, garantindo que as informações coletadas sejam precisas e úteis.
            
            Roteiro de Perguntas Gerais
            As perguntas abaixo devem ser feitas com o objetivo de classificar as respostas dentro das categorias predefinidas para cada pergunta. 
            Caso a resposta do usuário não se encaixe em nenhuma das categorias disponíveis, a pergunta deve ser reformulada e feita novamente.
            
            É essencial que as respostas estejam alinhadas com os enquadramentos estabelecidos, mas sem que essas categorias 
            sejam reveladas diretamente ao usuário. No entanto, você pode esclarecer eventuais dúvidas do usuário com base nesses enquadramentos.
            
            Antes de formular uma pergunta do roteiro, siga estas diretrizes para garantir uma abordagem mais natural e contextualizada:
            
            Reformule a pergunta original de maneira coerente, sem alterar seu significado, para que o usuário possa responder de forma intuitiva, sem precisar conhecer os enquadramentos.
            Forneça um contexto relevante antes de fazer a pergunta. Isso ajuda o usuário a compreender melhor o propósito da questão e a formular uma resposta mais precisa.
            Se possível, faça inferências com base no que já foi discutido no chat. Isso significa conectar a pergunta ao contexto da conversa, sugerindo que um ponto previamente mencionado pode estar relacionado à questão que será feita.
            Evite perguntas diretas e isoladas. Em vez disso, integre-as ao fluxo da conversa, tornando o questionamento mais natural e fluido.
            Seguindo essas diretrizes, as respostas do usuário terão maior qualidade e precisão, facilitando o enquadramento correto sem que ele perceba a estrutura por trás das perguntas.
             
            A seguir, estão as perguntas gerais:
            
                Perguntas Gerais: 
                
                AVALIAÇÃO DO NIVEL DE INOVAÇÃO
        
                Pergunta: O seu projeto de produto/processos/ sistemas pode ser considerado uma novidade para qual público?
                Enquadramentos:
                    Traz uma novidade no contexto da empresa e adaptado para as necessidades da mesma, embora trate-se de um produto/processo/sistema amplamente disponível em empresas concorrentes.
                    O produto/processo/sistema em questão já existe, mas está disponível apenas a poucos players do mercado, com margens para ajustes a contextos específicos.
                    A solução proposta é uma novidade para todo um segmento específico do mercado.
                    Trata-se de um produto/processo/serviço cujo desenvolvimento de uma solução própria ainda é inédito no Brasil.
                    Trata-se de um produto/processo/serviço cujo desenvolvimento de uma solução própria ainda é inédito em âmbito internacional.
                    
                Pergunta: Como você classifica as atividades realizadas pela sua empresa no desenvolvimento do projeto em questão?
                Enquadramentos:                
                Foram realizados testes/experimentos/ensaios para validar uma solução ofertada por um fornecedor de tecnologia
                Foram realizados testes/experimentos/ensaios e desenvolvimentos específicos para adequar uma solução ofertada por um fornecedor de tecnologia ao contexto da empresa e seu mercado.
                No processo de desenvolvimento do produto/processo/sistema, a empresa atuou na elaboração de conceito, benchmarking, revisão de literatura científica, mas não realizou testes/experimentos/ensaios
                No processo de desenvolvimento do produto/processo/sistema, a empresa atuou na elaboração de conceito, benchmarking, revisão de literatura científica e realizou ou coordenou a realização de testes/experimentos/ensaios em diferentes escalas (ex. da bancada ao indústrial, ou do MVP ao Software)
                No processo de desenvolvimento do produto/processo/sistema, a empresa atuou na elaboração de conceito, benchmarking, revisão de literatura científica e realizou ou coordenou a realização de testes/experimentos/ensaios em diferentes escalas e pesquisadores de dedicação exclusiva.
                
                para a pergunta abaixo essa seria uma sugestao de reformulação:
                Como sua empresa contribuiu para o desenvolvimento do projeto? Ela definiu necessidades, buscou soluções
                tecnológicas, estabeleceu parcerias ou contou com um time interno de inovação? Me conte um pouco sobre esse envolvimento.
                Pergunta: Como você classificaria o engajamento de sua empresa no desenvolvimento do projeto em questão?
                Enquadramentos:
                A empresa atuou na definição das necessidades chave e procedeu com a busca e aquisição de soluções tecnológicas para as mesmas.
                A empresa definiu as necessidades chave e buscou parceiros estabelescidos no mercado para o desenvolvimento de solução específica.
                A empresa empregou colaboradores de forma parcial ao desenvolvimento de conceito e buscou parceiros, em especial inventores e startups, para o desenvolvimento propriamente dito da solução (produto/processo/sistema).
                A empresa empregou colaboradores de forma parcial ao desenvolvimento da solução (produto/processo/sistema) sem contar com um departamento de Pesquisa e Desenvolvimento estruturado.
                A empresa empregou colaboradores de um departamento de Pesquisa e Desenvolvimento próprio para desenvolvimento da solução (produto/processo/sistema).
                A empresa tem uma política de inovação bem definida, com profissionais dedicados ao desenvolvimento de soluções e integração com o ambiente de inovação.
                
                Pergunta: Como você avalia as novidades trazidas pelo seu projeto em comparação a outras alternativas disponíveis no mercado?
                Enquadramentos
                Ajustes e calibrações que preservam as mesmas características funcionais e componentes de produtos/processos ou sistemas, embora incrementem produtividade/eficiência, ou reduzam custo.
                Adição de características/funcionalidades/módulos novos a um produto/processo ou sistema, de maneira a gerar melhoria significativa em seu desempenho ou percepção de valor.
                Criação de um produto/processo ou sistema composto por elementos bastante distintos ou com diferenças generalizadas para outras soluções disponíveis concorrentes ou aplicadas para as mesmas demandas.
                Criação de um produto/processo ou sistema radicalmente distinto de quaisquer outros disponíveis no mercado, a ponto de levar a hábitos de consumo, culturas empresariais ou ambientes produtivos completamente inéditos, bem como levar ao declínio de quaisquer tecnologias concorrentes no momento.
                                
                MODIFICADORES NIVEL DE P&D
                
                Pergunta: Esse projeto realizou experimentos/testes/ensaios/desenvolvimentos em colaboração com Universidades?
                a. Se sim, quais?.
                Pergunta: Esse projeto realizou experimentos/testes/ensaios/desenvolvimentos em colaboração com ICT's?
                a. Se sim, quais?.
                Pergunta: Esse projeto realizou experimentos/testes/ensaios/desenvolvimento em colaboração com empresas parceiras?
                a. Se sim, quais?.
                
                MODIFICADORES NIVEL DE INOVAÇÃO
                
                Pergunta: Esse projeto resultou em alguma forma de proteção de propriedade intelectual?
                a. Caso sim, esse projeto resultou em pedido de patente?.
                Pergunta: Esse projeto foi aprovado para captação de recursos junto à organização de Fomento ao PDI (FINEP/BNDES)?
                Pergunta: Esse projeto foi submetido à LDB AC 2023 ou 2024?
        
         Roteiro de perguntas especificas: 
            Após realizar todas as perguntas gerais e todas estiverem sido respondidas e estiverem dentro do seu equadramento
            pergunte ao usuário sobre as questões especicas. 
            
            MODIFICADORES DE AREAS ESPECIFICAS
                {pergunta_especifica}
                            
        Finalização:
            Quando o usuário responder a todas as perguntas gerais e especificas agradeça sinceramente a colaboração do usuário.
            A mensagem de finalização após responder todas as perguntas gerais e especificas deve conter uma flag de finalização.
            A flag de finalização deve ser um #FINALIZADO ao final do texto de agradecimento mencionado anteriomente quando o
            usuário responde a todas as pergutas. Além disso, não fale que esta a disposição para receber novas perguntas. 
            Só agradeça e ponto e deseje boa sorte.
        """


    def get_llm(self):
        try:
            configuracao_repo = ConfiguracaoRepository(self.db)
            configuracao = configuracao_repo.get_configuracao_by_provedor_nome(OPEN_AI)

            if not configuracao:
                raise Exception("Configuração para o provedor OpenAI não encontrada")

            return ChatOpenAI(
                model="gpt-4o",
                openai_api_key=configuracao.api_key,
                temperature=0.4
            )

        except Exception as e:
            raise Exception(str(e))

    def create_prompt(self, background: str, roteiro: str) -> ChatPromptTemplate:
        context = self.base_context + background + roteiro
        return ChatPromptTemplate.from_messages(
            [
                ("system", context),
                MessagesPlaceholder(variable_name="history"),
                ("human", "{input}"),
            ]
        )
    @staticmethod
    def create_prompt_innovation_award_chat(background: str) -> ChatPromptTemplate:
        return ChatPromptTemplate.from_messages(
            [
                ("system", background),
                ("system", "Mensagens rotuladas como adm, você pode quebrar as regras do roteiro, "
                           "mas apenas para retorna o quanto falta para terminar o dialogo em um "
                           "numero float que vai de 0.0 a 100.0 baseando no total de perguntas e "
                           "nas perguntas que ja foram respondidas."),
                MessagesPlaceholder(variable_name="history"),
                ("human", "{input}"),
            ]
        )

    def handle_question_bot(self, question: str, session_id: str, roteiro, background):
        c = get_qdrant_client()

        contexto_frascati, contexto_lei_bem = "", ""
        if self.requer_documento(question, "frascati"):
            contexto_frascati = self.search_context_in_qdrant(
                question, "documentos_frascati", c, self.embedding_function
            )

        if self.requer_documento(question, "lei_bem"):
            contexto_lei_bem = self.search_context_in_qdrant(
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

        prompt_template = self.create_prompt(background, roteiro)

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

    async def web_chat_swarm(self, gio: ComunicacaoEnxameContatoSchema, roteiro):
        error_id = str(uuid.uuid4())
        logger.info(f"Iniciando web_chat_swarm. Error ID: {error_id}")

        try:
            if not gio or not gio.questao or not roteiro:
                logger.error(f"Parâmetros inválidos. Error ID: {error_id}")
                return "Entrada inválida. Por favor, verifique os dados.", 0

            logger.debug("Inicializando componentes...")
            vector_store = QdrantVectorStore()
            if not vector_store:
                logger.error(f"Falha na inicialização do Vector Store. Error ID: {error_id}")
                return "Erro de configuração do sistema.", 0

            retriever = DocumentRetriever(vector_store)
            embedding_service = EmbeddingService(embedding_client=SentenceTransformersEmbeddingClient())

            contexto_frascati, contexto_lei_bem = "", ""

            try:
                if self.requer_documento(gio.questao, "frascati"):
                    logger.info("Processando Frascati...")
                    query_embedding = embedding_service.embedding_client.embed(gio.questao)
                    if not query_embedding:
                        logger.warning(f"Embedding vazio para Frascati. Error ID: {error_id}")

                    contexto_frascati = retriever.retrieve_relevant_documents(
                        collection_name="documentos_frascati",
                        query_embedding=query_embedding,
                    )
                    logger.debug(
                        f"Contexto Frascati recuperado: {len(contexto_frascati) if contexto_frascati else 0} elementos")

                if self.requer_documento(gio.questao, "lei_bem"):
                    logger.info("Processando Lei Bem...")
                    query_embedding = embedding_service.embedding_client.embed(gio.questao)
                    if not query_embedding:
                        logger.warning(f"Embedding vazio para Lei Bem. Error ID: {error_id}")

                    contexto_lei_bem = retriever.retrieve_relevant_documents(
                        collection_name="documentos_lei_bem",
                        query_embedding=query_embedding,
                    )
                    logger.debug(
                        f"Contexto Lei Bem recuperado: {len(contexto_lei_bem) if contexto_lei_bem else 0} elementos")

            except Exception as e:
                logger.error(f"Erro na recuperação de contexto: {str(e)}. Error ID: {error_id}", exc_info=True)
                contexto_frascati = contexto_lei_bem = ""

            contexto = "Informações Relevantes:\n"
            contextos_encontrados = 0

            if contexto_frascati:
                contexto += f"Manual Frascati:\n{contexto_frascati}\n"
                contextos_encontrados += 1
            if contexto_lei_bem:
                contexto += f"Guia Prático da Lei do Bem:\n{contexto_lei_bem}\n"
                contextos_encontrados += 1

            if contextos_encontrados == 0:
                logger.warning(f"Nenhum contexto encontrado. Error ID: {error_id}")
                contexto += "Nenhum contexto adicional foi recuperado para esta pergunta."

            full_prompt = f"{contexto}\n\nNova Pergunta: {gio.questao}"

            try:
                get_history_func: Callable[[None], BaseChatMessageHistory] = lambda _: get_session_history(
                    gio.id_usuario.__str__())

                logger.info("Criando template de prompt...")
                prompt_template = self.create_prompt("", roteiro)
                if not prompt_template:
                    logger.error(f"Template de prompt inválido. Error ID: {error_id}")
                    return "Erro na configuração do serviço.", 0

                runnable = prompt_template | self.get_llm()
                with_message_history = RunnableWithMessageHistory(
                    runnable,
                    get_history_func,
                    input_messages_key="input",
                    history_messages_key="history",
                )

                logger.info("Invocando modelo...")
                response = with_message_history.invoke(
                    {"input": full_prompt},
                    config={"configurable": {"session_id": gio.id_usuario.__str__()}},
                )

                if not response or not getattr(response, 'content', None):
                    logger.error(f"Resposta inválida do modelo. Error ID: {error_id}")
                    return "Não foi possível gerar uma resposta no momento.", 0

            except openai.RateLimitError as rate_error:
                logger.critical(f"Erro de limite de taxa da OpenAI: {rate_error}. Error ID: {error_id}")
                return "Nossa capacidade de resposta está temporariamente sobrecarregada. Por favor, tente novamente em alguns instantes.", 0

            except Exception as e:
                logger.error(f"Erro na execução do modelo: {str(e)}. Error ID: {error_id}", exc_info=True)
                return "Erro interno ao processar sua solicitação.", 0

            try:
                history = get_session_history(gio.id_usuario.__str__())
                history_size = len(history.messages) if hasattr(history, 'messages') else 0
                logger.debug(f"Tamanho do histórico: {history_size}")
            except Exception as e:
                logger.error(f"Erro ao recuperar histórico: {str(e)}. Error ID: {error_id}")
                history_size = 0

            return response, history_size

        except Exception as e:
            logger.critical(f"Erro crítico: {str(e)}. Error ID: {error_id}", exc_info=True)
            return f"Desculpe, ocorreu um erro inesperado. (ID: {error_id})", 0

    def handle_question_innovation_award(self, gio: GioRequestSchemaInnovationAward, specific_question: str):
        get_history_func: Callable[[None], BaseChatMessageHistory] = lambda _: get_session_history(
            gio.user_id.__str__())

        substituicoes = {
            "{nome_empresa}": gio.company_name or "",
            "{pergunta_especifica}": specific_question or "",
        }

        try:
            base_context_for_innovation_award_after_replace = self.base_context_for_innovation_award
            for placeholder, valor in substituicoes.items():
                safe_value = str(valor) if valor is not None else ""
                base_context_for_innovation_award_after_replace = base_context_for_innovation_award_after_replace.replace(
                    placeholder, safe_value)
        except Exception as e:
            logging.error(f"Error in base context processing: {str(e)}")
            raise ValueError("Error preparing conversation context")

        prompt_template = self.create_prompt_innovation_award_chat(base_context_for_innovation_award_after_replace)

        runnable = prompt_template | self.get_llm()
        with_message_history = RunnableWithMessageHistory(
            runnable,
            get_history_func,
            input_messages_key="input",
            history_messages_key="history",
        )

        response = with_message_history.invoke(
            {"input": gio.question},
            config={"configurable": {"session_id": gio.user_id.__str__()}},
        )

        history = get_session_history(gio.user_id.__str__())
        history_size = len(history.messages) if hasattr(history, 'messages') else 0

        return response, history_size
    def generate_answer_based_on_document_for_innovation_award(self, user_id: str, question: str, relevant_docs):
        get_history_func: Callable[[None], BaseChatMessageHistory] = lambda _: get_session_history(user_id)

        prompt_template = ChatPromptTemplate.from_messages(
            [
                ("system","Você deve avaliar criteriosamente o contexto e a pergunta para da a resposta."),

                MessagesPlaceholder(variable_name="history"),

                ("human", "{input}"),
            ]
        )

        runnable = prompt_template | self.get_llm()
        with_message_history = RunnableWithMessageHistory(
            runnable,
            get_history_func,
            input_messages_key="input",
            history_messages_key="history",
        )

        prompt = (
            f"Se a resposta não estiver no contexto, responda que não há informações suficientes.\n\n"
            f"Contexto:\n{relevant_docs}\n\n"
            f"Pergunta: {question}\n\n"
            f"Resposta:"
        )
        response = with_message_history.invoke(
            {"input": prompt},
            config={"configurable": {"session_id": user_id}},
        )

        history = get_session_history(user_id)
        history_size = len(history.messages) if hasattr(history, 'messages') else 0

        return response.content, history_size

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

    @staticmethod
    def search_context_in_qdrant(question, collection_name, client, embeddings_model, top_k=10, clusters=3):
        question_embedding = embeddings_model.embed_query(question)

        if question_embedding is None or np.isnan(question_embedding).any():
            question_embedding = np.nan_to_num(question_embedding)

        response = client.search(
            collection_name=collection_name,
            query_vector=question_embedding,
            limit=top_k
        )

        texts = [item.payload["text"] for item in response]
        embeddings = [item.vector if item.vector is not None else np.zeros(len(question_embedding)) for item in
                      response]

        embeddings = np.array(embeddings, dtype=float)

        if np.isnan(embeddings).any():
            raise ValueError("Embeddings contain NaN values.")

        if embeddings.ndim == 1:
            embeddings = embeddings.reshape(-1, 1)

        if len(embeddings) < clusters:
            return " ".join(texts)

        kmeans = KMeans(n_clusters=clusters)
        kmeans.fit(embeddings)

        cluster_centers = kmeans.cluster_centers_
        selected_texts = []
        for center in cluster_centers:
            closest_idx = np.argmin([np.linalg.norm(center - emb) for emb in embeddings])
            selected_texts.append(texts[closest_idx])

        return " ".join(selected_texts)