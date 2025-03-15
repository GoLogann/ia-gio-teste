import json
import re
import uuid
from json import JSONDecodeError
from uuid import uuid4, UUID
from fastapi import Request
from fastapi import WebSocket, WebSocketDisconnect
from fastapi.logger import logger
from pydantic import ValidationError
from qdrant_client.models import Filter, FieldCondition, MatchValue
from constantes_globais.enum.message_template import SUMMARY_TEMPLATE
from constantes_globais.enum.rag import MAXLOGHISTORY
from constantes_globais.enum.tipo_dialogo import PROMPT_INNOVATION_AWARD, PROMPT_ENXAME
from database.qdrant_db import create_collection, upsert_point, scroll_points
from dataprovider.api.session_handler import end_session
from domain.models import Dialogo, DialogoDetalhe
from domain.schemas.dialogo_schema import DialogoSchema, DialogoDetalheSchema
from domain.schemas.gio_schema import ComunicacaoEnxameContatoSchema, GioRequestSchemaInnovationAward
from domain.schemas.innovation_summary import InnovationSummary
from repository.base_repository import BaseRepository
from repository.chatbot_repository import ChatBotRepository
from repository.dialogo_repository import DialogoRepository
from resources.apache_kafka.config import KAFKA_BROKERS_URLS, KAFKA_TOPIC_DIALOGUES_SWARM_GIO
from resources.datetime_config import time_now
from services.dialogo_service import DialogoService
from services.embedding_service import EmbeddingService
from services.kafka_producer import KafkaProducerService
from services.redis_handler_service import RedisHandler
from services.sentence_transformers import SentenceTransformersEmbeddingClient
from services.user_context_service import UserContextService
from services.whatsapp_service import WhatsAppService
from utils.helpers import extrair_dados_resumo_new, salvar_resumo_projeto

from utils.whatsapp import upload_media, send_media_message, send_template_message


class ChatBotService:
    def __init__(self):
        self.redis_handler = RedisHandler()
        self.user_context_service = UserContextService()
        self.whatsapp_service = WhatsAppService()
        self.connections = []
        self.responses = {}

    async def start_conversation(self, roteiro: dict, db_client, qdrant_client):
        session_id = roteiro["telefone"]
        collection_name = f"cliente_{session_id}"

        create_collection(qdrant_client, collection_name=collection_name, vector_size=384)

        pontos = scroll_points(
            client=qdrant_client,
            collection_name=collection_name,
            limit=1
        )

        if not pontos:
            context = {
                "modelo": roteiro["modelo"],
                "id_comunicacao_enxame_contato": roteiro["id_comunicacao_enxame_contato"],
                "id_departamento": roteiro["id_departamento"],
                "email": roteiro["email"],
                "nome": roteiro["nome"],
                "id_dialogo": "",
            }
        else:
            if isinstance(pontos[0], dict):
                context = pontos[0].get("payload", {})
            elif hasattr(pontos[0], 'payload'):
                context = getattr(pontos[0], 'payload', {})
            else:
                context = {}

            if not isinstance(context, dict):
                context = {}

            context.setdefault("modelo", roteiro["modelo"])
            context.setdefault("id_comunicacao_enxame_contato", roteiro["id_comunicacao_enxame_contato"])
            context.setdefault("id_departamento", roteiro["id_departamento"])
            context.setdefault("email", roteiro["email"])
            context.setdefault("nome", roteiro["nome"])
            context.setdefault("id_dialogo", "")

        response = await self.user_context_service.gerar_mensagem_inicial_com_modelo(roteiro["telefone"], context)

        context["last_interaction"] = time_now().isoformat()

        repository = BaseRepository(db_client)
        dialogo_id = uuid4()
        dialogo = Dialogo(
            id=dialogo_id,
            tipo=4,
            id_usuario=UUID(roteiro["id_comunicacao_enxame_contato"]),
            criado=time_now()
        )
        dialogo_detalhe = DialogoDetalhe(
            id=uuid4(),
            id_dialogo=dialogo.id,
            pergunta="BOT INICIOU O CHAT",
            resposta=response.content,
            token=response.usage_metadata.get('total_tokens', 0)
        )

        dialogo.dialogoDetalhes = [dialogo_detalhe]
        repository.add(dialogo)
        context["id_dialogo"] = dialogo.id

        payload = context
        vector = [0.0] * 384
        point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, session_id))

        try:
            upsert_point(qdrant_client, collection_name, point_id, vector, payload)
            logger.info(f"Contexto salvo no Qdrant na coleção '{collection_name}'.")
        except Exception as e:
            logger.error(f"Erro ao salvar contexto no Qdrant: {e}")
            raise

        await send_template_message(to=roteiro["telefone"], template_name="start_chat")

    async def web_chat_enxame(self, gio: ComunicacaoEnxameContatoSchema, roteiro: dict, db, qdrant_client) -> DialogoSchema:
        session_id = gio.id_usuario
        collection_name = f"cliente_{session_id}"

        create_collection(qdrant_client, collection_name=collection_name, vector_size=384)

        pontos = scroll_points(
            client=qdrant_client,
            collection_name=collection_name,
            limit=1
        )

        if not pontos:
            context = {
                "modelo": roteiro["modelo"],
                "id_comunicacao_enxame_contato": roteiro["id_comunicacao_enxame_contato"],
                "id_departamento": roteiro["id_departamento"],
                "email": roteiro["email"],
                "nome": roteiro["nome"],
                "id_dialogo": "",
            }
        else:
            if isinstance(pontos[0], dict):
                context = pontos[0].get("payload", {})
            elif hasattr(pontos[0], 'payload'):
                context = getattr(pontos[0], 'payload', {})
            else:
                context = {}

            if not isinstance(context, dict):
                context = {}

            context.setdefault("modelo", roteiro["modelo"])
            context.setdefault("id_comunicacao_enxame_contato", roteiro["id_comunicacao_enxame_contato"])
            context.setdefault("id_departamento", roteiro["id_departamento"])
            context.setdefault("email", roteiro["email"])
            context.setdefault("nome", roteiro["nome"])
            context.setdefault("id_dialogo", "")

        repository = DialogoRepository(db)
        dialogo_service = DialogoService(db, qdrant_client)

        dialogo = None
        length_history_dialog_finished = 0
        original = gio.questao
        if gio.id_dialogo:
            dialogo, _ = repository.entity_exist(Dialogo, gio.id_dialogo.__str__())
            if dialogo:
                context_str = dialogo_service.processar_contexto(dialogo)
                full_prompt = f"{context_str}\n\nNova Pergunta: {gio.questao}"
                gio.questao = full_prompt
                length_history_dialog_finished = 3
        try:
            if gio.questao == "":
                gio.questao = "PODEMOS INICIAR"
            response, length_history = await self.user_context_service.generate_swarm_web_chat_model_response(gio, context)
        except ValueError as e:
            raise ValueError(str(e))

        ending_chat = False
        if original == "Não, somente isso!":
            ending_chat = True

        if length_history > MAXLOGHISTORY or length_history_dialog_finished > 2:
            ultimo_dialogo = (
                db.query(Dialogo)
                .filter_by(id_usuario=gio.id_usuario)
                .order_by(Dialogo.criado.desc())
                .first()
            )

            if ultimo_dialogo:
                dialogo_detalhes_ordenados = (
                    db.query(DialogoDetalhe)
                    .filter(DialogoDetalhe.id_dialogo == ultimo_dialogo.id)
                    .order_by(DialogoDetalhe.criado.asc())
                    .all()
                )
                ultimo_dialogo.dialogoDetalhes = dialogo_detalhes_ordenados

                pergunta = "Não, somente isso!" if gio.questao == "Não, somente isso!" else original
                resposta = (
                    "Muito obrigado por responder às perguntas e compartilhar as informações sobre o projeto!"
                    if gio.questao == "Não, somente isso!"
                    else (response if isinstance(response, str) else response.content)
                )

                dialogo_detalhe = DialogoDetalhe(
                    id=uuid.uuid4(),
                    id_dialogo=ultimo_dialogo.id,
                    pergunta=pergunta,
                    resposta=resposta,
                    token=response.usage_metadata['total_tokens'],
                    criado=time_now()
                )
                ultimo_dialogo.dialogoDetalhes.append(dialogo_detalhe)
                db.commit()
                dialogo = ultimo_dialogo
        else:
            if not dialogo and length_history != 0:
                dialogo = Dialogo(
                    id=uuid.uuid4(),
                    id_usuario=gio.id_usuario,
                    tipo=PROMPT_ENXAME,
                    criado=time_now()
                )
                db.add(dialogo)
                db.commit()
                db.refresh(dialogo)

            dialogo_detalhe = DialogoDetalhe(
                id=uuid.uuid4(),
                id_dialogo=dialogo.id,
                pergunta="Podemos iniciar",
                resposta=response.content,
                token=response.usage_metadata['total_tokens'],
                criado=time_now()
            )

            if dialogo:
                dialogo.dialogoDetalhes.append(dialogo_detalhe)
                db.commit()

        if not dialogo:
            raise ValueError("Não foi possível criar ou atualizar o diálogo.")

        dialogo_detalhes_ordenados = sorted(
            dialogo.dialogoDetalhes, key=lambda x: x.criado, reverse=False
        )

        dialogo_schema = await self.create_dialog_response_schema(dialogo, dialogo_detalhes_ordenados, ending_chat)

        if "Não, somente isso!" in gio.questao:
            context["id_dialogo"] = dialogo.id
            context["last_interaction"] = time_now().isoformat()
            vector = [0.0] * 384
            point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, session_id.__str__()))

            try:
                upsert_point(qdrant_client, collection_name, point_id, vector, context)
                logger.info(f"Contexto salvo no Qdrant na coleção '{collection_name}'.")
            except Exception as e:
                logger.error(f"Erro ao salvar contexto no Qdrant: {e}")
                raise

            try:
                resumo_data = extrair_dados_resumo_new(response.content)
                resumo = salvar_resumo_projeto(
                    db=db,
                    resumo_data=resumo_data,
                    is_confirmed=True,
                    dialogo_id=dialogo.id,
                    id_departamento=context.get("id_departamento"),
                    id_comunicacao_enxame_contato=context.get("id_comunicacao_enxame_contato")
                )

                kafka_producer = KafkaProducerService(KAFKA_BROKERS_URLS, KAFKA_TOPIC_DIALOGUES_SWARM_GIO)
                await kafka_producer.start()

                resumo_json = {
                    "id": str(resumo.id),
                    "idExecucaoComunicacaoEnxameContato": str(resumo.id_comunicacao_enxame_contato),
                    "idDialogo": str(resumo.dialog_id),
                    "nomeProjeto": resumo.nome_projeto,
                    "pesquisaRelacionada": resumo.pesquisa_relacionada,
                    "responsavel": resumo.responsavel,
                    "idDepartamentoResponsavel": resumo.id_departamento,
                    "objetivoProjeto": resumo.objetivo_projeto,
                    "beneficio": resumo.beneficio,
                    "diferencial": resumo.diferencial,
                    "marco": resumo.marco,
                    "desafio": resumo.desafio,
                    "metodologia": resumo.metodologia,
                    "proximoPasso": resumo.proximo_passo,
                    "detalheAdicional": resumo.detalhe_adicional,
                    "observacaoUsuario": resumo.observacao_usuario,
                    "aprovado": resumo.aprovado,
                    "ativo": None,
                    "criado": resumo.criado.isoformat(),
                    "atualizado": resumo.atualizado.isoformat(),
                }

                await kafka_producer.publish_message(resumo_json)
                await kafka_producer.stop()

                end_session(dialogo.id_usuario.__str__())
                context["id_dialogo"] = dialogo.id
                context["last_interaction"] = time_now().isoformat()
                vector = [0.0] * 384
                point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, session_id.__str__()))

                try:
                    upsert_point(qdrant_client, collection_name, point_id, vector, context)
                    logger.info(f"Contexto salvo no Qdrant na coleção '{collection_name}'.")
                except Exception as e:
                    logger.error(f"Erro ao salvar contexto no Qdrant: {e}")
                    raise
                return dialogo_schema

            except ValueError as e:
                logger.error(f"Erro ao processar resumo do projeto: {e}")
                raise ValueError(str(e))

        context["id_dialogo"] = dialogo.id
        context["last_interaction"] = time_now().isoformat()
        vector = [0.0] * 384
        point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, session_id.__str__()))

        try:
            upsert_point(qdrant_client, collection_name, point_id, vector, context)
            logger.info(f"Contexto salvo no Qdrant na coleção '{collection_name}'.")
        except Exception as e:
            logger.error(f"Erro ao salvar contexto no Qdrant: {e}")
            raise

        return dialogo_schema

    @staticmethod
    async def create_dialog_response_schema(dialogo, dialogo_detalhes_ordenados, end_session: bool):
        detalhes_schemas = []

        for detalhe in dialogo_detalhes_ordenados:
            if end_session and detalhe == dialogo_detalhes_ordenados[-1]:
                mensagem_agradecimento = "Muito obrigado pela disponibilidade em responder as perguntas!"
                resposta = mensagem_agradecimento
            else:
                resposta = detalhe.resposta

            detalhes_schemas.append(
                DialogoDetalheSchema(
                    id=detalhe.id,
                    idDialogo=dialogo.id,
                    pergunta=detalhe.pergunta,
                    resposta=resposta,
                    insight=detalhe.insight,
                    token=detalhe.token,
                    criado=detalhe.criado,
                )
            )

        dialogo_schema = DialogoSchema(
            id=dialogo.id,
            id_usuario=dialogo.id_usuario,
            tipo=dialogo.tipo,
            criado=dialogo.criado,
            dialogoDetalhes=detalhes_schemas
        )
        return dialogo_schema

    @staticmethod
    def process_document_to_answer_questions(text: str):
        base_context = """
        Analise o texto abaixo, faça uma analise linha a linha e identifique se o texto abaixo satisfaz cada pergunta 
        que precisa ser respondida, desde as perguntas gerais até as perguntas específicas. Caso responda todas as 
        perguntas pre estabelecidas com seus devidos enquadramentos mande para o usuário um resumo com todas as respostas 
        respondidas com base no texto abaixo. Caso não responda todas, informe que nem todas as perguntas foram respondidas e faça as perguntas que faltam ser respondidas. 
        
        TEXTO EXTRAIDO DO DOCUMENTO ENVIADO PELO CLIENTE/USUARIO:
        """

        return base_context + "\n\n" + text


    async def webchat_innovation_award(self, gio: GioRequestSchemaInnovationAward, present_document: bool, db, qdrant_client) -> dict:
        repository = DialogoRepository(db)
        dialogo_service = DialogoService(db, qdrant_client)
        dialogo = None
        original = gio.question
        if gio.dialogue_id:
            dialogo, _ = repository.entity_exist(Dialogo, gio.dialogue_id.__str__())
            if dialogo:
                context_str = dialogo_service.processar_contexto(dialogo)
                full_prompt = f"{context_str}\n\nNova Pergunta: {gio.question}"
                gio.question = full_prompt

        try:
            new_prompt = self.create_context(gio, db, qdrant_client)
            gio.question = new_prompt
            response, length_history = await self.user_context_service.generate_innovation_award_model_response(gio, db)
        except ValueError as e:
            raise ValueError(str(e))

        if present_document:
            gio.question = "documento enviado"
            length_history = 2

        progress = None
        if length_history > MAXLOGHISTORY:
            ultimo_dialogo = (
                db.query(Dialogo)
                .filter_by(id_usuario=gio.user_id)
                .order_by(Dialogo.criado.desc())
                .first()
            )

            if ultimo_dialogo:
                dialogo_detalhes_ordenados = (
                    db.query(DialogoDetalhe)
                    .filter(DialogoDetalhe.id_dialogo == ultimo_dialogo.id)
                    .order_by(DialogoDetalhe.criado.asc())
                    .all()
                )
                ultimo_dialogo.dialogoDetalhes = dialogo_detalhes_ordenados

                dialogo_detalhe = DialogoDetalhe(
                    id=uuid.uuid4(),
                    id_dialogo=ultimo_dialogo.id,
                    pergunta=original,
                    resposta=response.content,
                    token=response.usage_metadata['total_tokens'],
                    criado=time_now()
                )
                ultimo_dialogo.dialogoDetalhes.append(dialogo_detalhe)
                db.commit()
                dialogo = ultimo_dialogo
                gio.question = "adm: Responda quantos porcentos em float do questionario ja foi respondido. Exemplo: 50.0 ou 52.1"
                response_progress, _ = await self.user_context_service.generate_innovation_award_model_response(gio, db)
                progress = response_progress.content
        else:
            if not dialogo:
                dialogo = Dialogo(
                    id=uuid.uuid4(),
                    id_usuario=gio.user_id,
                    tipo=PROMPT_INNOVATION_AWARD,
                    criado=time_now()
                )
                db.add(dialogo)
                db.commit()
                db.refresh(dialogo)

            dialogo_detalhe = DialogoDetalhe(
                id=uuid.uuid4(),
                id_dialogo=dialogo.id,
                pergunta= gio.question if present_document else original,
                resposta=response.content,
                token=response.usage_metadata['total_tokens'],
                criado=time_now()
            )

            if dialogo:
                dialogo.dialogoDetalhes.append(dialogo_detalhe)
                db.commit()

        if not dialogo:
            raise ValueError("Não foi possível criar ou atualizar o diálogo.")

        dialogo_detalhes_ordenados = sorted(
            dialogo.dialogoDetalhes, key=lambda x: x.criado, reverse=False
        )

        dialogo_schema = await self.create_dialog_response_schema(dialogo, dialogo_detalhes_ordenados, False)

        summary = None
        if "#FINALIZADO" in response.content:
           summary = await self.generate_innovation_award_webchat_summary(dialogo.id, gio , db, qdrant_client)
           end_session(gio.user_id.__str__())
        return {
            "dialogo": dialogo_schema,
            "resumo": summary,
            "progress": progress
        }

    def create_context(self, gio: GioRequestSchemaInnovationAward, db, qdrant_client):
        dialogo_service = DialogoService(db, qdrant_client)
        embedding_service = EmbeddingService(embedding_client=SentenceTransformersEmbeddingClient())

        ultimo_dialogo = (
            db.query(Dialogo)
            .filter_by(id_usuario=gio.user_id)
            .order_by(Dialogo.criado.desc())
            .first()
        )

        context_str = ""
        relevant_history = ""

        if ultimo_dialogo:
            dialogo_detalhes_ordenados = (
                db.query(DialogoDetalhe)
                .filter(DialogoDetalhe.id_dialogo == ultimo_dialogo.id)
                .order_by(DialogoDetalhe.criado.asc())
                .all()
            )
            ultimo_dialogo.dialogoDetalhes = dialogo_detalhes_ordenados

            context_str = dialogo_service.processar_contexto(ultimo_dialogo)

            query_embedding = embedding_service.embedding_client.embed(gio.question)

            user_filter = Filter(
                must=[
                    FieldCondition(
                        key="dialogue_id",
                        match=MatchValue(value=str(ultimo_dialogo.id)),
                    )
                ]
            )

            search_results = qdrant_client.search(
                collection_name="chunks",
                query_vector=query_embedding,
                query_filter=user_filter,
                limit=6,
                score_threshold=0.5,
                with_payload=True,
                with_vectors=False
            )

            seen_content = set()
            relevant_chunks = []

            for result in search_results:
                if result.payload and result.score >= 0.5:
                    content = result.payload.get("page_content")
                    if content and content not in seen_content:
                        seen_content.add(content)
                        relevant_chunks.append(content)

            relevant_chunks = sorted(
                relevant_chunks,
                key=lambda x: next(r.score for r in search_results if r.payload.get("page_content") == x),
                reverse=True
            )[:6]

            relevant_history = "\n".join(relevant_chunks)

        full_prompt = f"""
        Use sempre os contextos ateriores para melhorar a sua pergnta e a contextualização dela, e fazer inferencias. 
        Contexto histórico relevante:
        {relevant_history}

        Última interação:
        {context_str}

        Nova pergunta:
        {gio.question}
        """

        return full_prompt

    async def generate_innovation_award_webchat_summary(self, dialogue_id: str, gio, db, qdrant_client):
        try:
            if not dialogue_id:
                logger.error("Dialogue ID is missing or invalid.")
                return "Dialogue ID is missing or invalid."

            if not gio:
                logger.error("Missing 'gio' object.")
                return "Missing 'gio' object."

            repository = DialogoRepository(db)
            dialogo_service = DialogoService(db, qdrant_client)

            dialogo, exists = repository.entity_exist(Dialogo, dialogue_id)
            if not exists or not dialogo:
                logger.error(f"Dialogue with ID {dialogue_id} not found.")
                return f"Dialogue with ID {dialogue_id} not found."

            context_str = dialogo_service.processar_contexto(dialogo)
            if not context_str:
                logger.error("Failed to process dialogue context.")
                return "Failed to process dialogue context."

            full_prompt = (
                f"{context_str}\n\n"
                "Nova Pergunta: Gere um resumo contendo todos os dados necessários para o "
                "Questionário de Avaliação do Prêmio de Inovação. Ele deve ser preenchido de acordo com as respostas do usuário.\n\n"
                f"Pontos que precisam de atenção:\n\n"
                f"o campo mod_especifico esta na parte do roteiro denominada de MODIFICADORES DE AREAS ESPECIFICAS\n\n"
                f"Template de resumo:\n{SUMMARY_TEMPLATE}\n\n"
                "Com os dados gerados no resumo, crie um JSON contendo os seguintes campos:\n"
                "{\n"
                '  "nivel_inovacao_p1": "O seu projeto de produto/processos/sistemas pode ser considerado uma novidade para qual público?",\n'
                '  "nivel_inovacao_p2": "Como você classifica as atividades realizadas pela sua empresa no desenvolvimento do projeto em questão?",\n'
                '  "nivel_inovacao_p3": "Como você classificaria o engajamento de sua empresa no desenvolvimento do projeto em questão?",\n'
                '  "nivel_inovacao_p4": "Como você avalia as novidades trazidas pelo seu projeto em comparação a outras alternativas disponíveis no mercado?",\n'
                '  "mod_ped_universidades": "Esse projeto realizou experimentos/testes/ensaios/desenvolvimentos em colaboração com Universidades?",\n'
                '  "mod_ped_icts": "Esse projeto realizou experimentos/testes/ensaios/desenvolvimentos em colaboração com ICT\'s?",\n'
                '  "mod_ped_parceiras": "Esse projeto realizou experimentos/testes/ensaios/desenvolvimentos em colaboração com empresas parceiras?",\n'
                '  "mod_inovacao_patente": "Esse projeto resultou em alguma forma de proteção de propriedade intelectual?",\n'
                '  "mod_inovacao_fomento": "Esse projeto foi aprovado para captação de recursos junto à organização de Fomento ao PDI (FINEP/BNDES)?",\n'
                '  "mod_inovacao_ldb": "Esse projeto foi submetido à LDB AC 2023?",\n'
                '  "mod_especifico": "Aréa do projeto"\n'
                "}\n\n"
                "Não me retorne o resumo, somente o JSON."
            )

            gio.question = full_prompt

            response, _ = await self.user_context_service.generate_innovation_award_model_response(gio, db)

            if not response or not hasattr(response, 'content'):
                logger.error("Invalid response from AI model.")
                return "Invalid response from AI model."

            json_match = re.search(r'\{.*\}', response.content, re.DOTALL)
            if not json_match:
                logger.error("No valid JSON found in response.")
                return "No valid JSON found in response."

            json_text = json_match.group(0)

            try:
                resumo_dict = json.loads(json_text)
            except JSONDecodeError as e:
                logger.error(f"Failed to parse JSON response: {e}")
                return "Failed to parse JSON response."

            try:
                innovation_summary = InnovationSummary(**resumo_dict)
            except ValidationError as e:
                logger.error(f"Validation error while creating InnovationSummary: {e}")
                return "Invalid data format in AI model response."

            additional_fields = {
                "nome_solicitante": gio.user_name if hasattr(gio, "user_name") else None,
                "nome_empresa": gio.company_name if hasattr(gio, "company_name") else None,
                "nome_projeto": gio.project_name if hasattr(gio, "project_name") else None,
                "area_projeto": gio.project_area if hasattr(gio, "project_area") else None,
                "valor_investimento": gio.investment_value if hasattr(gio, "investment_value") else None,
                "receita_operacional_liquida": gio.net_operational_revenue if hasattr(gio,
                                                                                      "net_operational_revenue") else None,
                "proporcao_pdi": gio.pdi_proportion if hasattr(gio, "pdi_proportion") else None,
            }

            for key, value in additional_fields.items():
                if value is not None:
                    setattr(innovation_summary, key, value)

            return innovation_summary

        except Exception as e:
            logger.exception(f"Unexpected error: {e}")
            return "An unexpected error occurred"

    @staticmethod
    def generate_innovation_award_summary_json(summary: str):
        try:
            json_data = {
                "nome_empresa": "",
                "nome_solicitante": "",
                "email_solicitante": "",
                "cnae": "",
                "setor_principal_atuacao": "",
                "resumo_projeto": "",
                "nome_projeto": "",
                "area_projeto": "",
                "valor_investimento": "",
                "receita_operacional_liquida": "",
                "proporcao_pdi": "",
                "nivel_inovacao_p1": "",
                "nivel_inovacao_p2": "",
                "nivel_inovacao_p3": "",
                "nivel_inovacao_p4": "",
                "mod_ped_universidades": "",
                "mod_ped_icts": "",
                "mod_ped_parceiras": "",
                "mod_inovacao_patente": "",
                "mod_inovacao_fomento": "",
                "mod_inovacao_ldb": "",
                "mod_especifico": ""
            }

            def capturar_resposta(pergunta, resumo):
                match = re.search(rf"Pergunta:\s*{re.escape(pergunta)}.*?Enquadramento:\s*(.*?)(?=\n|$)", resumo, re.DOTALL)
                return match.group(1).strip() if match else ""

            json_data["nivel_inovacao_p1"] = capturar_resposta("O seu projeto de produto/processos/sistemas pode ser considerado uma novidade para qual público?", summary)
            json_data["nivel_inovacao_p2"] = capturar_resposta("Como você classifica as atividades realizadas pela sua empresa no desenvolvimento do projeto em questão?", summary)
            json_data["nivel_inovacao_p3"] = capturar_resposta("Como você classificaria o engajamento de sua empresa no desenvolvimento do projeto em questão?", summary)
            json_data["nivel_inovacao_p4"] = capturar_resposta("Como você avalia as novidades trazidas pelo seu projeto em comparação a outras alternativas disponíveis no mercado?", summary)

            json_data["mod_ped_universidades"] = capturar_resposta("Esse projeto realizou experimentos/testes/ensaios/desenvolvimentos em colaboração com Universidades?", summary)
            json_data["mod_ped_icts"] = capturar_resposta("Esse projeto realizou experimentos/testes/ensaios/desenvolvimentos em colaboração com ICT's?", summary)
            json_data["mod_ped_parceiras"] = capturar_resposta("Esse projeto realizou experimentos/testes/ensaios/desenvolvimentos em colaboração com empresas parceiras?", summary)

            json_data["mod_inovacao_patente"] = capturar_resposta("Esse projeto resultou em alguma forma de proteção de propriedade intelectual?", summary)
            json_data["mod_inovacao_fomento"] = capturar_resposta("Esse projeto foi aprovado para captação de recursos junto à organização de Fomento ao PDI (FINEP/BNDES)?", summary)
            json_data["mod_inovacao_ldb"] = capturar_resposta("Esse projeto foi submetido à LDB AC 2023?", summary)

            match_area = re.search(r"Área:\s*(\S+)", summary)
            if match_area:
                json_data["mod_especifico"] = match_area.group(1).strip()

            return json_data
        except Exception as e:
            logger.error(f"Error decoding JSON: {e}")
            return None

    @staticmethod
    async def enviar_midia(telefone_usuario: str):
        file_path = "logo_gt.png"
        media_id = await upload_media(file_path)
        await send_media_message(telefone_usuario, media_id, "image")

    async def gerar_resposta(self, telefone_usuario: str, mensagem: str, context):
        """
        Gera uma resposta para o usuário utilizando o modelo de IA.

        Args:
            telefone_usuario (str): Número de telefone do usuário.
            Mensagem (str): Mensagem enviada pelo usuário.

        Returns:
            str: resposta gerada pelo modelo.
        """
        return await self.user_context_service.gerar_resposta_do_modelo(telefone_usuario, mensagem, context)

    async def notify_connections(self, telefone_usuario: str, direction: str, message: str):
        """
        Notifica conexões WebSocket sobre uma nova mensagem.

        Args:
            telefone_usuario (str): Número de telefone do usuário.
            direction (str): Direção da mensagem ('from_user' ou 'from_model').
            message (str): Conteúdo da mensagem.
        """
        logger.info(f"Notificando clientes sobre mensagem ({direction}) de {telefone_usuario}: {message}")
        notification = {
            "telefone_usuario": telefone_usuario,
            "direction": direction,
            "message": message
        }
        for connection in self.connections:
            if connection["filter"] is None or connection["filter"] == telefone_usuario:
                try:
                    await connection["socket"].send_json(notification)
                except WebSocketDisconnect:
                    self.connections.remove(connection)
                    logger.info("Conexão WebSocket desconectada durante o envio")

    async def websocket_endpoint(self, websocket: WebSocket, telefone_usuario: str = None):
        """
        Gerencia conexões WebSocket para comunicação em tempo real.

        Args:
            websocket (WebSocket): Conexão WebSocket.
            Telefone_usuario (str, opcional): Número de telefone do usuário conectado.
        """
        await websocket.accept()
        connection = {"socket": websocket, "filter": telefone_usuario}
        self.connections.append(connection)
        try:
            while True:
                await websocket.receive_text()
        except WebSocketDisconnect:
            self.connections.remove(connection)
            logger.info(f"Cliente desconectado do WebSocket ({telefone_usuario or 'todos'})")

    @staticmethod
    def get_respostas_usuario(id_comunicacao_enxame_contato: str, request: Request):
        chatbot_repository = ChatBotRepository(request.app.state.db_client)

        dialogo = chatbot_repository.get_dialogo_by_usuario(id_comunicacao_enxame_contato)
        if not dialogo:
            return {"error": "Diálogo não encontrado para o ID informado"}

        respostas = chatbot_repository.get_respostas_by_dialogo(dialogo.id)

        return {
            "id_dialogo": dialogo.id,
            "id_comunicacao_enxame_contato": id_comunicacao_enxame_contato,
            "criado": dialogo.criado,
            "detalhes": [
                {
                    "resposta": detalhe.resposta,
                    "criado": detalhe.criado
                }
                for detalhe in respostas
            ]
        }