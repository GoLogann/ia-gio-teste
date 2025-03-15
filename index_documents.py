import pymupdf as fitz
from langchain.text_splitter import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer
from qdrant_client.models import PointStruct
from database.qdrant_db import create_collection, get_qdrant_client

def extract_text_from_pdf(pdf_file):
    """
    Extrai texto de um arquivo PDF recebido como objeto binário.

    Args:
        pdf_file (bytes): O arquivo PDF.

    Returns:
        str: Texto extraído do PDF.
    """
    text = ""
    with fitz.open(stream=pdf_file, filetype="pdf") as pdf:
        for page_num in range(pdf.page_count):
            page = pdf[page_num]
            text += page.get_text("text")
    return text

def process_and_store_document(pdf_file, collection_name, vector_size=384, chunk_size=800, chunk_overlap=100):
    """
    Processa um PDF, gera embeddings e armazena em uma coleção específica no Qdrant.

    Args:
        pdf_file (bytes): O arquivo PDF.
        collection_name (str): Nome da coleção no Qdrant.
        vector_size (int): Tamanho do vetor.
        chunk_size (int): Tamanho de cada chunk de texto.
        chunk_overlap (int): Sobreposição entre chunks.
    """
    document_text = extract_text_from_pdf(pdf_file)
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    document_chunks = text_splitter.split_text(document_text)

    embeddings_model = SentenceTransformer('all-MiniLM-L6-v2')
    document_embeddings = [embeddings_model.encode(text) for text in document_chunks]

    client = get_qdrant_client()

    existing_collections = [collection.name for collection in client.get_collections().collections]
    if collection_name not in existing_collections:
        create_collection(client, collection_name, vector_size=len(document_embeddings[0]))

    for idx, (embedding, text) in enumerate(zip(document_embeddings, document_chunks)):
        client.upsert(
            collection_name=collection_name,
            points=[PointStruct(id=idx, vector=embedding, payload={"text": text})]
        )

