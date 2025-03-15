import re
import uuid
from langchain_huggingface import HuggingFaceEmbeddings
from qdrant_client import QdrantClient
from sqlalchemy.orm import Session
from fastapi import Request
from constantes_globais.enum.contextos import get_identifier_by_number
from dataprovider.api.administrativo import substitute_values_in_script
from dataprovider.api.descricao import DescricaoHandler
from dataprovider.api.perplexity import PerplexityHandler
from dataprovider.api.anthropic import AnthropicHandler
from dataprovider.api.resumo import ResumoHandler
from dataprovider.api.scraping import ScrapingHandler
from dataprovider.api.session_handler import end_session
from domain.models.project_data import ProjectData
from domain.schemas.dialogo_schema import DialogoSchema, DialogoDetalheSchema
from repository.dialogo_repository import DialogoRepository, Pageable
from domain.models.dialogo import Dialogo
from domain.models.dialogo_detalhe import DialogoDetalhe
from domain.schemas.gio_schema import GioRequestSchema, GioDescricaoSchema, GioResumoSchema, GioScrapingSchema
from typing import List, Dict, Any
from uuid import uuid4
from pydantic import UUID4
from transformers import AutoTokenizer
from langchain_core.documents.base import Document
from dataprovider.api.chatgpt import ChatGPTHandler
from dataprovider.api.gemini import GeminiHandler
from constantes_globais.enum.rag import MAX_CHUNK_LENGTH, MAXLOGHISTORY
from resources.datetime_config import time_now
from utils.helpers import get_context_by_name
from utils.scraping import crawling_site
from constantes_globais.enum.tipo_dialogo import PROMPT_CRIATIVA, PROMPT_ESCAVADORA, PROMPT_CONTESTACAO, \
    PROMPT_PERPLEXITY, PROMPT_ANTHROPIC, PROMPT_DESCRICAO, PROMPT_RESUMO, PROMPT_SCRAPING


class DialogoService:
    def __init__(self, db: Session, qdrant_client: QdrantClient):
        self.db = db
        self.repository = DialogoRepository(db)
        self.qdrant_client = qdrant_client
        self.embedding_function = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        self.chatgpt_handler = ChatGPTHandler()
        self.descricao_handler = DescricaoHandler()

    def verificar_finalizacao_conversa(self, response_text: str) -> bool:
        return "#concluido" in response_text

    def extrair_dados_resumo(self, resumo_texto: str) -> dict:
        expected_fields = {
            "Nome do Projeto": "project_name",
            "Linha de PD&I": "research_field",
            "Responsável": "responsible_name",
            "Área do Responsável": "responsible_area",
            "Objetivo Geral da Atividade": "project_goal",
            "Benefícios Obtidos com o Projeto": "project_benefits",
            "Diferencial do Projeto": "project_differentiator",
            "Marcos Principais": "milestone",
            "Dificuldades Enfrentadas": "road_blocks",
            "Metodologia e Métodos": "research_methods",
            "Perspectivas Futuras": "next_steps",
            "Detalhes Adicionais": "additional_details",
            "Observações": "user_observations"
        }

        resumo_texto = resumo_texto.split('---')[0]
        resumo_data = {field: "" for field in expected_fields.values()}
        current_field = None

        responsavel_match = re.search(r"Responsável:\s*(.+?)(?:\s*-|$)(?:\s*Área do Responsável:\s*(.*))?", resumo_texto)
        if responsavel_match:
            resumo_data["responsible_name"] = responsavel_match.group(1).strip()
            if responsavel_match.group(2):
                resumo_data["responsible_area"] = responsavel_match.group(2).strip()

        for line in resumo_texto.splitlines():
            line = line.strip()

            if "Responsável:" in line or "Área do Responsável:" in line:
                continue

            matched_field = next((field for title, field in expected_fields.items() if title in line), None)
            if matched_field:
                current_field = matched_field
                content = line.split(":", 1)[-1].strip().lstrip("*")
                resumo_data[current_field] = content
            elif current_field and line:
                resumo_data[current_field] += f" {line.strip().lstrip('*')}"

        resumo_data = {k: v.strip() for k, v in resumo_data.items() if v}

        print("Extracted resumo_data:", resumo_data)
        return resumo_data


    def salvar_resumo_projeto(self, resumo_data: dict, is_confirmed: bool, dialogo_id: str):
        existing_project_data = self.db.query(ProjectData).filter_by(dialog_id=dialogo_id).first()

        if existing_project_data:
            existing_project_data.updated_at = time_now()
            existing_project_data.is_confirmed = is_confirmed
            for key, value in resumo_data.items():
                setattr(existing_project_data, key, value)
        else:
            project_data = ProjectData(
                id=uuid.uuid4(),
                dialog_id=dialogo_id,
                created_at=time_now(),
                updated_at=time_now(),
                is_confirmed=is_confirmed,
                **resumo_data
            )
            self.db.add(project_data)

        self.db.commit()

    def perguntando_gio_enxame(self, gio: GioRequestSchema) -> DialogoSchema:
        dialogo = None
        try:
            response, lengthHistory = self.chatgpt_handler.handle_question_bot(
                question=gio.questao, session_id=str(gio.id_usuario)
            )
        except ValueError as e:
            raise ValueError(str(e))

        if lengthHistory > MAXLOGHISTORY:
            ultimo_dialogo = (
                self.db.query(Dialogo)
                .filter_by(id_usuario=gio.id_usuario)
                .order_by(Dialogo.criado.desc())
                .first()
            )

            if ultimo_dialogo:
                dialogo_detalhes_ordenados = (
                    self.db.query(DialogoDetalhe)
                    .filter(DialogoDetalhe.id_dialogo == ultimo_dialogo.id)
                    .order_by(DialogoDetalhe.criado.asc())
                    .all()
                )
                ultimo_dialogo.dialogoDetalhes = dialogo_detalhes_ordenados

                dialogo_detalhe = DialogoDetalhe(
                    id=uuid.uuid4(),
                    id_dialogo=ultimo_dialogo.id,
                    pergunta=gio.questao,
                    resposta=response.content,
                    token=response.usage_metadata['total_tokens'],
                    criado=time_now()
                )
                ultimo_dialogo.dialogoDetalhes.append(dialogo_detalhe)
                self.db.commit()
                dialogo = ultimo_dialogo
        else:
            if not dialogo:
                dialogo = Dialogo(
                    id=uuid.uuid4(),
                    id_usuario=gio.id_usuario,
                    tipo=4,
                    criado=time_now()
                )
                self.db.add(dialogo)
                self.db.commit()
                self.db.refresh(dialogo)

            dialogo_detalhe = DialogoDetalhe(
                id=uuid.uuid4(),
                id_dialogo=dialogo.id,
                pergunta=gio.questao,
                resposta=response.content,
                token=response.usage_metadata['total_tokens'],
                criado=time_now()
            )

            if dialogo:
                dialogo.dialogoDetalhes.append(dialogo_detalhe)
                self.db.commit()

        if not dialogo:
            raise ValueError("Não foi possível criar ou atualizar o diálogo.")

        dialogo_detalhes_ordenados = sorted(
            dialogo.dialogoDetalhes, key=lambda x: x.criado, reverse=False
        )

        detalhes_schemas = [
            DialogoDetalheSchema(
                id=detalhe.id,
                idDialogo=dialogo.id,
                pergunta=detalhe.pergunta,
                resposta=detalhe.resposta,
                insight=detalhe.insight,
                token=detalhe.token,
                criado=detalhe.criado,
            ) for detalhe in dialogo_detalhes_ordenados
        ]

        dialogo_schema = DialogoSchema(
            id=dialogo.id,
            id_usuario=dialogo.id_usuario,
            tipo=dialogo.tipo,
            criado=dialogo.criado,
            dialogoDetalhes=detalhes_schemas
        )

        return dialogo_schema

    def perguntar_gio_criativa(self, gio: GioRequestSchema) -> DialogoSchema:
        """
        Cria um novo diálogo ou atualiza um existente, para uma pergunta de Gio Criativa.
        """
        dialogo = None

        full_prompt = gio.questao
        if gio.id_dialogo:
            dialogo, _ = self.repository.entity_exist(Dialogo, gio.id_dialogo.__str__())

            if dialogo:
                context_str = self.processar_contexto(dialogo)
                full_prompt = f"{context_str}\n\nNova Pergunta: {gio.questao}"

        try:
            response, length_history = self._gerar_resposta(full_prompt, gio.id_usuario, tipo=PROMPT_CRIATIVA)
        except ValueError as e:
            raise ValueError(str(e))

        if length_history > MAXLOGHISTORY:
            ultimo_dialogo = (
                self.db.query(Dialogo)
                .filter_by(id_usuario=gio.id_usuario)
                .order_by(Dialogo.criado.desc())
                .first()
            )

            if ultimo_dialogo:
                dialogo_detalhes_ordenados = (
                    self.db.query(DialogoDetalhe)
                    .filter(DialogoDetalhe.id_dialogo == ultimo_dialogo.id)
                    .order_by(DialogoDetalhe.criado.asc())
                    .all()
                )
                ultimo_dialogo.dialogoDetalhes = dialogo_detalhes_ordenados

                dialogo_detalhe = DialogoDetalhe(
                    id=uuid.uuid4(),
                    id_dialogo=ultimo_dialogo.id,
                    pergunta=gio.questao,
                    resposta=response.content,
                    token=response.usage_metadata['total_tokens'],
                    criado=time_now()
                )
                ultimo_dialogo.dialogoDetalhes.append(dialogo_detalhe)
                self.db.commit()
                dialogo = ultimo_dialogo
        else:
            if not dialogo:
                dialogo = Dialogo(
                    id=uuid.uuid4(),
                    id_usuario=gio.id_usuario,
                    tipo=PROMPT_CRIATIVA,
                    criado=time_now()
                )
                self.db.add(dialogo)
                self.db.commit()
                self.db.refresh(dialogo)

            dialogo_detalhe = DialogoDetalhe(
                id=uuid.uuid4(),
                id_dialogo=dialogo.id,
                pergunta=gio.questao,
                resposta=response.content,
                token=response.usage_metadata['total_tokens'],
                criado=time_now()
            )

            if dialogo:
                dialogo.dialogoDetalhes.append(dialogo_detalhe)
                self.db.commit()

        if not dialogo:
            raise ValueError("Não foi possível criar ou atualizar o diálogo.")

        dialogo_detalhes_ordenados = sorted(
            dialogo.dialogoDetalhes, key=lambda x: x.criado, reverse=False
        )

        detalhes_schemas = [
            DialogoDetalheSchema(
                id=detalhe.id,
                idDialogo=dialogo.id,
                pergunta=detalhe.pergunta,
                resposta=detalhe.resposta,
                insight=detalhe.insight,
                token=detalhe.token,
                criado=detalhe.criado,
            ) for detalhe in dialogo_detalhes_ordenados
        ]

        dialogo_schema = DialogoSchema(
            id=dialogo.id,
            id_usuario=dialogo.id_usuario,
            tipo=dialogo.tipo,
            criado=dialogo.criado,
            dialogoDetalhes=detalhes_schemas
        )

        return dialogo_schema

    def perguntar_gio_escavadora(self, gio: GioRequestSchema) -> DialogoSchema:
        """
        Implementa a lógica para perguntas ao Gio Escavadora.
        """
        if not gio.questao:
            raise ValueError("Questão é obrigatória")

        dialogo = None

        try:
            response, length_history = self._gerar_resposta(gio.questao, gio.id_usuario, tipo=PROMPT_ESCAVADORA)
        except ValueError as e:
            raise ValueError(str(e))

        if length_history > MAXLOGHISTORY:
            ultimo_dialogo = (
                self.db.query(Dialogo)
                .filter_by(id_usuario=gio.id_usuario)
                .order_by(Dialogo.criado.desc())
                .first()
            )

            if ultimo_dialogo:
                dialogo_detalhes_ordenados = (
                    self.db.query(DialogoDetalhe)
                    .filter(DialogoDetalhe.id_dialogo == ultimo_dialogo.id)
                    .order_by(DialogoDetalhe.criado.asc())
                    .all()
                )
                ultimo_dialogo.dialogoDetalhes = dialogo_detalhes_ordenados

                dialogo_detalhe = DialogoDetalhe(
                    id=uuid.uuid4(),
                    id_dialogo=ultimo_dialogo.id,
                    pergunta=gio.questao,
                    resposta=response.content,
                    token=response.usage_metadata['total_tokens'],
                    criado=time_now()
                )
                ultimo_dialogo.dialogoDetalhes.append(dialogo_detalhe)
                self.db.commit()
                dialogo = ultimo_dialogo
        else:
            if not dialogo:
                dialogo = Dialogo(
                    id=uuid.uuid4(),
                    id_usuario=gio.id_usuario,
                    tipo=PROMPT_ESCAVADORA,
                    criado=time_now()
                )
                self.db.add(dialogo)
                self.db.commit()
                self.db.refresh(dialogo)

            dialogo_detalhe = DialogoDetalhe(
                id=uuid.uuid4(),
                id_dialogo=dialogo.id,
                pergunta=gio.questao,
                resposta=response.content,
                token=response.usage_metadata['total_tokens'],
                criado=time_now()
            )

            if dialogo:
                dialogo.dialogoDetalhes.append(dialogo_detalhe)
                self.db.commit()

        if not dialogo:
            raise ValueError("Não foi possível criar ou atualizar o diálogo.")

        dialogo_detalhes_ordenados = sorted(
            dialogo.dialogoDetalhes, key=lambda x: x.criado, reverse=False
        )

        detalhes_schemas = [
            DialogoDetalheSchema(
                id=detalhe.id,
                idDialogo=dialogo.id,
                pergunta=detalhe.pergunta,
                resposta=detalhe.resposta,
                insight=detalhe.insight,
                token=detalhe.token,
                criado=detalhe.criado,
            ) for detalhe in dialogo_detalhes_ordenados
        ]

        dialogo_schema = DialogoSchema(
            id=dialogo.id,
            id_usuario=dialogo.id_usuario,
            tipo=dialogo.tipo,
            criado=dialogo.criado,
            dialogoDetalhes=detalhes_schemas
        )

        return dialogo_schema

    def perguntando_gio_perplexity(self, gio: GioRequestSchema) -> Any:
        """Implementação da integração do Perplexity"""
        if not gio.questao:
            raise ValueError("Questão é obrigatória")

        try:
            resposta, length_history = self._gerar_resposta(gio.questao, gio.id_usuario, tipo=PROMPT_PERPLEXITY)
        except ValueError as e:
            raise ValueError(str(e))

        return resposta.content

    def perguntando_gio_anthropic(self, gio: GioRequestSchema) -> DialogoSchema:
        """Implementação da integração do Anthropic"""
        try:
            resposta, length_history = self._gerar_resposta(gio.questao, gio.id_usuario, tipo=PROMPT_ANTHROPIC)
        except ValueError as e:
            raise ValueError(str(e))
        return resposta.content

    def perguntar_descricao(self, gio: GioDescricaoSchema) -> Any:
        try:
            resposta, length_history = self._gerar_resposta(gio.titulo, gio.id_usuario, tipo=PROMPT_DESCRICAO)
        except ValueError as e:
            raise ValueError(str(e))
        return resposta.content

    def gerar_resumo(self, gio: GioResumoSchema) -> Any:
        try:
            resposta, length_history = self._gerar_resposta(gio.transcricao, gio.id_usuario, tipo=PROMPT_RESUMO)
        except ValueError as e:
            raise ValueError(str(e))
        return resposta.content

    def gerar_scraping_info(self, gio: GioScrapingSchema) -> Any:
        try:
            textos = str(crawling_site(gio.url))
            resposta, length_history = self._gerar_resposta(textos, gio.id_usuario, tipo=PROMPT_SCRAPING)
        except ValueError as e:
            raise ValueError(str(e))
        return resposta.content

    def perguntar_gio_contestacao(self, gio: GioRequestSchema, request: Request) -> DialogoSchema:
        try:
            gio.questao = substitute_values_in_script(request, gio)
            response, _ = self._gerar_resposta(gio.questao, gio.id_usuario, tipo=PROMPT_ESCAVADORA)
        except ValueError as e:
            raise ValueError(str(e))

        dialogo = Dialogo(
            id=uuid.uuid4(),
            id_usuario=gio.id_usuario,
            tipo=PROMPT_CONTESTACAO,
        )

        dialogo_detalhe = DialogoDetalhe(
            id=uuid.uuid4(),
            pergunta=gio.questao,
            resposta=response.content,
            token=response.usage_metadata['total_tokens'],
        )

        dialogo.dialogoDetalhes.append(dialogo_detalhe)

        self.db.add(dialogo)
        self.db.commit()
        self.db.refresh(dialogo)

        end_session(str(gio.id_usuario))

        detalhes_schemas = [
            DialogoDetalheSchema(
                id=detalhe.id,
                idDialogo=dialogo.id,
                pergunta=detalhe.pergunta,
                resposta=detalhe.resposta,
                insight=detalhe.insight,
                token=detalhe.token,
                criado=detalhe.criado,
            ) for detalhe in dialogo.dialogoDetalhes
        ]

        dialogo_schema = DialogoSchema(
            id=dialogo.id,
            id_usuario=dialogo.id_usuario,
            tipo=dialogo.tipo,
            criado=dialogo.criado,
            dialogoDetalhes=detalhes_schemas
        )

        return dialogo_schema

    def listar_historico(self, page_size: int, page: int, sort: str, filtro: Dict) -> Pageable:
        """
        Lista o histórico dos diálogos com paginação e ordenação.
        """
        return self.repository.listar_historico_dialogo(page_size=page_size, page=page, order_by=sort, filtro=filtro)


    def _get_or_create_dialogo(self, id_usuario: UUID4, tipo: int) -> Dialogo:
        """
        Busca o último diálogo do usuário ou cria um novo.
        """
        last_dialogo_id = self.repository.get_last_dialogo_by_user(id_usuario, tipo)
        if last_dialogo_id:
            dialogo = self.repository.get_dialogo_by_id(last_dialogo_id)
            if dialogo:
                return dialogo

        novo_dialogo = Dialogo(
            id=uuid4(),
            id_usuario=id_usuario,
            tipo=tipo,
            criado=time_now()
        )
        return novo_dialogo

    def _create_dialogo_detalhe(self, id_dialogo: UUID4, pergunta: str, resposta: str) -> DialogoDetalhe:
        """
        Cria um novo detalhe de diálogo.
        """
        return DialogoDetalhe(
            id=uuid4(),
            id_dialogo=id_dialogo,
            pergunta=pergunta,
            resposta=resposta,
            criado=time_now()
        )

    def _gerar_resposta(self, prompt: str, id_usuario: uuid.UUID, tipo: int) -> [Any, int]:
        """
        Gera uma resposta com base no prompt fornecido.
        """
        try:
            context_type = get_identifier_by_number(1)
            system_message = get_context_by_name(self.db, context_type)

            chatgpt_handler = ChatGPTHandler()
            gemini_handler = GeminiHandler()
            perplexity_handler = PerplexityHandler()
            anthropic_handler = AnthropicHandler()
            descricao_handler = DescricaoHandler()
            resumo_handler = ResumoHandler()
            scraping_handler = ScrapingHandler()

            handlers = {
                PROMPT_ESCAVADORA: lambda: gemini_handler.handle_question(question=prompt, session_id=str(id_usuario)),
                PROMPT_CRIATIVA: lambda: chatgpt_handler.handle_question(question=prompt, session_id=str(id_usuario),
                                                                         context=system_message),
                PROMPT_CONTESTACAO: lambda: chatgpt_handler.handle_question(question=prompt, session_id=str(id_usuario),
                                                                            context=system_message),
                PROMPT_PERPLEXITY: lambda: perplexity_handler.handle_question(question=prompt, session_id=str(id_usuario)),
                PROMPT_ANTHROPIC: lambda: anthropic_handler.handle_question(question=prompt, session_id=str(id_usuario)),
                PROMPT_DESCRICAO: lambda: descricao_handler.handle_question(question=prompt, session_id=str(id_usuario)),
                PROMPT_RESUMO: lambda: resumo_handler.handle_question(question=prompt, session_id=str(id_usuario)),
                PROMPT_SCRAPING: lambda: scraping_handler.handle_question(question=prompt, session_id=str(id_usuario))
            }

            handle_function = handlers.get(tipo)

            if not handle_function:
                raise ValueError(f"Tipo inválido: {tipo}")

            response, lengthHistory = handle_function()

            return response, lengthHistory

        except Exception as e:
            raise ValueError(f"Erro ao invocar o modelo: {str(e)}")

    def processar_contexto(self, dialogo: Dialogo) -> str:
        """
        Processa o contexto do diálogo existente para formar um prompt com a história do diálogo.

        Args:
            dialogo: Objeto Dialogo contendo as informações do diálogo.

        Returns:
            str: Texto processado representando a história do diálogo.
        """

        if not dialogo.dialogoDetalhes:
            return ""

        docs_str = "\n\n".join(
            [f"Pergunta: {detalhe.pergunta}\nResposta: {detalhe.resposta}" for detalhe in dialogo.dialogoDetalhes])

        tokenizer = AutoTokenizer.from_pretrained("bert-base-uncased")

        input_ids = tokenizer.encode(docs_str, return_tensors="pt")

        chunks = []
        for i in range(0, input_ids.shape[1], MAX_CHUNK_LENGTH):
            chunk = input_ids[:, i:i + MAX_CHUNK_LENGTH]
            chunks.append(tokenizer.decode(chunk[0], skip_special_tokens=True))

        docs = [Document(page_content=chunk) for chunk in chunks]
        docs_content = [doc.page_content for doc in docs]

        embeddings = self.embedding_function.embed_documents(docs_content)
        self._inserir_embeddings(dialogo.id, docs_content, embeddings)

        return docs_str

    def _inserir_embeddings(self, dialogo_id: UUID4, docs_content: List[str], embeddings: List[List[float]]):
        """
        Insere os embeddings no Qdrant para facilitar buscas futuras.
        """
        points = []
        for i, embedding in enumerate(embeddings):
            points.append({
                "id": i,
                "vector": embedding,
                "payload": {
                    "page_content": docs_content[i],
                    "dialogue_id": str(dialogo_id),
                }
            })

        self.qdrant_client.upsert(collection_name="chunks", points=points)
