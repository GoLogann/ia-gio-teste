import uuid

from fastapi import Request, HTTPException, Response
from fastapi.logger import logger

from database.qdrant_db import upsert_point, get_point, scroll_points
from domain.models import Dialogo, DialogoDetalhe
from resources.apache_kafka.config import (
    KAFKA_BROKERS_URLS,
    KAFKA_TOPIC_QUEUE_SENDING_MESSAGES,
    KAFKA_TOPIC_DIALOGUES_SWARM_GIO
)
from resources.datetime_config import time_now
from resources.whatsapp.config import VERIFICATION_TOKEN
from services.dialogo_service import DialogoService
from services.kafka_producer import KafkaProducerService
from services.redis_handler_service import RedisHandler
from services.user_context_service import UserContextService
from utils.helpers import salvar_resumo_projeto, extrair_dados_resumo_new
from utils.whatsapp import send_message_to_whatsapp, send_template_message


class WhatsAppService:
    def __init__(self):
        self.user_context_service = UserContextService()
        self.redis_handler = RedisHandler()

    async def verify_webhook(self, request: Request):
        """
        Verifica o webhook do WhatsApp para confirmar a assinatura.
        """
        hub_mode = request.query_params.get("hub.mode")
        hub_verify_token = request.query_params.get("hub.verify_token")
        hub_challenge = request.query_params.get("hub.challenge")

        if hub_mode == "subscribe" and hub_verify_token == VERIFICATION_TOKEN:
            return Response(content=hub_challenge, media_type="text/plain")
        else:
            raise HTTPException(status_code=403, detail="Token de verificação inválido")

    async def process_webhook(self, request: Request, chatbot_service):
        try:
            try:
                data = await request.json()
                logger.info(f"Mensagem recebida do WhatsApp: {data}")
            except Exception as e:
                logger.error(f"Erro ao carregar o JSON do webhook: {e}")
                return {"status": "Erro ao carregar JSON"}

            try:
                entry = data.get("entry", [])[0]
                if not entry:
                    logger.error("Entrada 'entry' ausente ou vazia no payload.")
                    return {"status": "Erro ao processar JSON: entrada 'entry' ausente"}

                changes = entry.get("changes", [])[0]
                if not changes:
                    logger.error("Mudanças 'changes' ausentes ou vazias no payload.")
                    return {"status": "Erro ao processar JSON: 'changes' ausente"}

                value = changes.get("value", {})
                mensagens = value.get("messages", [])
                statuses = value.get("statuses", [])

                for mensagem in mensagens:
                    message_id = mensagem.get("id")

                    if self.redis_handler.check_processed_message(message_id):
                        logger.info(f"Mensagem {message_id} já processada. Ignorando.")
                        return {"status": f"Mensagem {message_id} já processada e ignorada"}

                    self.redis_handler.mark_message_as_processed(message_id)

            except (KeyError, IndexError) as e:
                logger.error(f"Erro ao extrair dados da mensagem: {e}")
                return {"status": "Erro ao extrair dados da mensagem"}

            if statuses:
                try:
                    status = statuses[0]
                    errors = status.get("errors", [])
                    if errors:
                        error = errors[0]
                        if error.get("title") == "Re-engagement message":
                            recipient_id = status.get("recipient_id")
                            logger.warning(
                                f"Erro de reengajamento para o número {recipient_id}: {error.get('message')}"
                            )
                            try:
                                numero = self.user_context_service.normalize_telefone(recipient_id)
                                session_id = numero
                                collection_name = f"cliente_{session_id}"

                                pontos = scroll_points(
                                    client=request.app.state.qdrant_client,
                                    collection_name=collection_name,
                                    limit=1
                                )

                                if pontos:
                                    if isinstance(pontos[0], dict):
                                        context = pontos[0].get("payload", {})
                                    elif hasattr(pontos[0], "payload"):
                                        context = getattr(pontos[0], 'payload', {})
                                    else:
                                        context = {}
                                else:
                                    context = {}

                                is_new_conversation = not context.get("history") or len(context["history"]) == 1 and \
                                                      context["history"][0].get("from") == "model"

                                if is_new_conversation:
                                    template_name = "start_chat"
                                    logger.info(f"Enviando template de boas-vindas para {recipient_id}")
                                else:
                                    template_name = "start_chat"
                                    logger.info(f"Enviando template de continuidade para {recipient_id}")

                                await send_template_message(to=numero, template_name=template_name)
                                logger.info(
                                    f"Mensagem de template '{template_name}' enviada com sucesso para {recipient_id}."
                                )

                                context.setdefault("context", [])
                                context.setdefault("history", [])
                                context["context"].append(
                                    {"from": "model", "message": f"Enviado template: {template_name}"})
                                context["history"].append(
                                    {"from": "model", "message": f"Template enviado: {template_name}"})

                                point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, session_id))
                                vector = [0.0] * 384
                                upsert_point(
                                    client=request.app.state.qdrant_client,
                                    collection_name=collection_name,
                                    point_id=point_id,
                                    vector=vector,
                                    payload=context
                                )

                                return {"status": f"Template '{template_name}' enviado"}
                            except Exception as e:
                                logger.error(f"Erro ao processar mensagem de template para {recipient_id}: {e}")
                                return {"status": "Erro ao enviar mensagem de template"}

                    logger.warning(f"Erro desconhecido no status: {errors}")
                    return {"status": "Erro desconhecido no status"}
                except Exception as e:
                    logger.error(f"Erro ao processar status: {e}")
                    return {"status": "Erro ao processar status"}

            if not mensagens:
                logger.info("Nenhuma mensagem para processar.")
                return {"status": "Nenhuma mensagem"}

            try:
                mensagem = mensagens[0]
                texto_mensagem = mensagem.get("text", {}).get("body", "")
                telefone_usuario = mensagem.get("from", "")

                if not texto_mensagem or not telefone_usuario:
                    raise ValueError("Mensagem ou número de telefone inválido.")
            except Exception as e:
                logger.error(f"Erro ao processar dados da mensagem: {e}")
                return {"status": "Erro ao processar dados da mensagem"}

            try:
                session_id = self.user_context_service.normalize_telefone(telefone_usuario)
                logger.info(f"Número de telefone normalizado: {session_id}")
            except Exception as e:
                logger.error(f"Erro ao normalizar o número de telefone: {e}")
                return {"status": "Erro ao normalizar o número de telefone"}

            try:
                collection_name = f"cliente_{session_id}"
                point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, session_id))

                context = get_point(
                    client=request.app.state.qdrant_client,
                    collection_name=collection_name,
                    point_id=point_id
                )

                if not context:
                    logger.warning(
                        f"Nenhum dado encontrado para o cliente '{telefone_usuario}' na coleção '{collection_name}'.")
                    return {"status": "Contexto não encontrado"}

                logger.info(f"Contexto do cliente recuperado: {context}")
            except Exception as e:
                logger.error(f"Erro ao recuperar contexto do cliente no Qdrant: {e}")
                return {"status": "Erro ao recuperar contexto"}

            try:
                db = request.app.state.db_client
                id_dialogo = context.get("id_dialogo")

                if not id_dialogo:
                    logger.error("id_dialogo não encontrado no contexto.")
                    return {"status": "Erro: id_dialogo não encontrado no contexto"}

                ultimo_dialogo = (
                    db.query(Dialogo)
                    .filter(Dialogo.id == id_dialogo)
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

                    dialogo_service = DialogoService(db=db, qdrant_client=request.app.state.qdrant_client)
                    context_str = dialogo_service.processar_contexto(ultimo_dialogo)
                    full_prompt = f"{context_str}\n\nNova Pergunta: {texto_mensagem}"

                    resposta = await chatbot_service.gerar_resposta(session_id, full_prompt, context)

                    dialogo_detalhe = DialogoDetalhe(
                        id=uuid.uuid4(),
                        id_dialogo=ultimo_dialogo.id,
                        pergunta=texto_mensagem,
                        resposta=resposta.content,
                        token=resposta.usage_metadata['total_tokens'],
                        criado=time_now()
                    )
                    ultimo_dialogo.dialogoDetalhes.append(dialogo_detalhe)
                    db.commit()

            except Exception as e:
                logger.error(f"Erro ao gerar resposta do chatbot: {e}")
                return {"status": "Erro ao gerar resposta"}

            if "Resumo do Projeto" in resposta.content:
                resumo_data = extrair_dados_resumo_new(resposta.content)
                resumo = salvar_resumo_projeto(
                    db=db,
                    resumo_data=resumo_data,
                    is_confirmed=True,
                    dialogo_id=ultimo_dialogo.id,
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

            try:
                if not resposta.content:
                    logger.warning("Nenhuma resposta para enviar.")
                else:
                    kafka_producer = KafkaProducerService(KAFKA_BROKERS_URLS, KAFKA_TOPIC_QUEUE_SENDING_MESSAGES)
                    await kafka_producer.start()
                    await kafka_producer.publish_message({
                        "telefone": telefone_usuario,
                        "resposta": resposta.content,
                        "retry_count": 0
                    })
                    await kafka_producer.stop()

                    logger.info(f"Resposta adicionada à fila para o telefone {telefone_usuario}: {resposta.content}")
                    return {"status": "Resposta adicionada à fila"}
            except Exception as e:
                logger.error(f"Erro ao enviar mensagem ao WhatsApp: {e}")
                return {"status": "Erro ao enviar mensagem"}

        except Exception as e:
            logger.error(f"Erro geral ao processar mensagem: {e}")
            return {"status": "Erro ao processar mensagem"}

        return {"status": "Mensagem processada"}

    async def enviar_mensagem(self, numero: str, mensagem: str):
        """
        Envia uma mensagem via WhatsApp.
        """
        logger.info(f"Enviando mensagem para {numero}: {mensagem}")
        await send_message_to_whatsapp(numero, mensagem)
        logger.info(f"Mensagem enviada com sucesso para {numero}")
