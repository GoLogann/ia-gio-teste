import os
import re
import unicodedata
import uuid
from typing import Tuple, Dict, Any, Optional

from PyPDF2 import PdfReader
from bs4 import BeautifulSoup
from langchain_community.document_loaders import PyPDFLoader, UnstructuredWordDocumentLoader
from sqlalchemy.orm import Session

from domain.models import DialogoDetalhe
from domain.models.contexto_modelo import ContextoModelo
from domain.models.project_data import ProjectData
from repository.contexto_modelo_repository import ContextoModeloRepository
from resources.datetime_config import time_now
from docx import Document

def processar_parametros(size: int, page: int, sort: str) -> Tuple[int, int, str]:
    size = size if size > 0 else 10
    page = page + 1 if page >= 0 else 1

    if not sort:
        sort = 'criado DESC'
    else:
        splitered = sort.split(',')
        if len(splitered) == 2:
            sort = f"{formatar_camel_case_para_snake_case(splitered[0])} {splitered[1]}"
        else:
            sort = 'criado DESC'

    return size, page, sort



def formatar_camel_case_para_snake_case(camel_case_str: str) -> str:
    import re
    snake_case_str = re.sub('([A-Z])', r'_\1', camel_case_str).lower()
    if snake_case_str.startswith('_'):
        snake_case_str = snake_case_str[1:]
    return snake_case_str


def get_context_by_name(db: Session, nome_contexto: str) -> Optional[str]:
    contexto_repo = ContextoModeloRepository(db)
    contexto_modelo: Optional[ContextoModelo] = contexto_repo.get_contexto_by_nome(nome_contexto)

    if contexto_modelo:
        return contexto_modelo.contexto
    else:
        return None


def detalhe_to_dict(detalhe: DialogoDetalhe) -> Dict[str, Any]:
    return {
        "id": detalhe.id,
        "id_dialogo": detalhe.id_dialogo,
        "pergunta": detalhe.pergunta,
        "resposta": detalhe.resposta,
        "insight": detalhe.insight,
        "token": detalhe.token,
        "criado": detalhe.criado.isoformat()
    }

def extract_roteiro_from_html(html_content: str) -> str:
    """
    Extrai tópicos e perguntas de um HTML estruturado e retorna um texto formatado.

    Args:
        html_content (str): Conteúdo HTML como string.

    Returns:
        str: Texto formatado com tópicos e suas perguntas.
    """
    try:
        soup = BeautifulSoup(html_content, "html.parser")

        roteiro = {}
        current_topic = None

        for tag in soup.find_all(["h2", "ul"]):
            if tag.name == "h2":
                current_topic = tag.get_text(strip=True)
                roteiro[current_topic] = []
            elif tag.name == "ul" and current_topic:
                for li in tag.find_all("li"):
                    question = li.get_text(strip=True)
                    if question:
                        roteiro[current_topic].append(question)

        formatted_text = ""
        for topic, questions in roteiro.items():
            formatted_text += f"\n{topic}\n"
            for i, question in enumerate(questions, 1):
                formatted_text += f"  {i}. {question}\n"

        return formatted_text.strip()

    except Exception as e:
        print(f"Erro ao processar o HTML: {e}")
        return ""

def extrair_dados_resumo(resumo_texto: str) -> dict:
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

    responsavel_match = re.search(r"Responsável:\s*(.+?)(?:\s*-|$)(?:\s*Área do Responsável:\s*(.*))?",
                                      resumo_texto)
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

def salvar_resumo_projeto(db, resumo_data: dict, is_confirmed: bool, dialogo_id: str, id_departamento: int, id_comunicacao_enxame_contato: str):
    existing_project_data = db.query(ProjectData).filter_by(dialog_id=dialogo_id).first()

    if existing_project_data:
        existing_project_data.atualizado = time_now()
        existing_project_data.aprovado = is_confirmed
        for key, value in resumo_data.items():
            setattr(existing_project_data, key, value)
        existing_project_data.id_departamento = id_departamento
        existing_project_data.id_comunicacao_enxame_contato = id_comunicacao_enxame_contato
        db.commit()
        db.refresh(existing_project_data)
        return existing_project_data
    else:
        project_data = ProjectData(
            id=uuid.uuid4(),
            dialog_id=dialogo_id,
            criado=time_now(),
            atualizado=time_now(),
            aprovado=is_confirmed,
            id_departamento=id_departamento,
            id_comunicacao_enxame_contato=id_comunicacao_enxame_contato,
            **resumo_data
        )
        db.add(project_data)
        db.commit()
        db.refresh(project_data)
        return project_data


def extrair_dados_resumo_new(resumo_texto: str) -> dict:
    expected_fields = {
        "Linha de PD&I": "pesquisa_relacionada",
        "Nome do Projeto": "nome_projeto",
        "Responsável": "responsavel",
        "Área do Responsável": "area_responsavel",
        "Objetivo Geral da Atividade": "objetivo_projeto",
        "Benefícios Obtidos com o Projeto": "beneficio",
        "Diferencial do Projeto": "diferencial",
        "Marcos Principais": "marco",
        "Dificuldades Enfrentadas": "desafio",
        "Metodologia e Métodos": "metodologia",
        "Perspectivas Futuras": "proximo_passo",
        "Detalhes Adicionais": "detalhe_adicional",
        "Observações": "observacao_usuario"
    }

    resumo_data = {field: "" for field in expected_fields.values()}
    current_field = None

    responsavel_match = re.search(
        r"Responsável:\s*(.+?)(?:\s*-|$)(?:\s*Área do Responsável:\s*(.*))?",
        resumo_texto
    )
    if responsavel_match:
        resumo_data["responsavel"] = responsavel_match.group(1).strip()
        if responsavel_match.group(2):
            resumo_data["area_responsavel"] = responsavel_match.group(2).strip()

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


def extract_text_from_file(file_path):
    ext = os.path.splitext(file_path)[1].lower()

    if ext == '.pdf':
        try:
            reader = PdfReader(file_path)
            return " ".join(page.extract_text() for page in reader.pages if page.extract_text() is not None)
        except Exception as e:
            raise ValueError(f"Erro ao processar o arquivo PDF: {str(e)}")

    elif ext == '.docx':
        try:
            doc = Document(file_path)
            return " ".join(paragraph.text for paragraph in doc.paragraphs)
        except Exception as e:
            raise ValueError(f"Erro ao processar o arquivo DOCX: {str(e)}")

    else:
        raise ValueError(f"Formato de arquivo {ext} não suportado.")


def process_file_for_rag(file_path):
    ext = os.path.splitext(file_path)[1].lower()
    try:
        if ext == '.pdf':
            loader = PyPDFLoader(file_path)
        elif ext == '.docx':
            loader = UnstructuredWordDocumentLoader(file_path)
        else:
            raise ValueError(f"Formato de arquivo {ext} não suportado.")

        documents = loader.load()
        text = " ".join(doc.page_content for doc in documents)

        text = preprocess_text(text)
        return text

    except Exception as e:
        print(f"Erro ao processar o arquivo {file_path}: {str(e)}")
        raise


def preprocess_text(text):
    text = text.lower()
    text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('utf-8')
    text = re.sub(r'[^\w\s.,!?]', ' ', text)
    text = " ".join(text.split())

    return text