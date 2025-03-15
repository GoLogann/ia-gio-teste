from fastapi import HTTPException, UploadFile, File, APIRouter, Depends
from typing import Dict, Any
from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.exceptions import ResponseHandlingException, UnexpectedResponse
from constantes_globais.apiuri import QDRANT_URI_V2
from database.qdrant_db import get_qdrant_client
from domain.schemas.qdrant import CollectionData
from index_documents import process_and_store_document

qdrant = APIRouter()

@qdrant.post(QDRANT_URI_V2 + "/collections/{collection_name}/add_pdf", response_model=Dict[str, Any])
async def add_pdf_to_collection(
        collection_name: str,
        file: UploadFile = File(...),
        vector_size: int = 384,
):
    """
    Adiciona um PDF processado ao Qdrant, criando embeddings e armazenando na coleção.
    """
    try:
        pdf_content = await file.read()
        process_and_store_document(pdf_content, collection_name, vector_size=vector_size)
        return {"message": f"Documento adicionado à coleção '{collection_name}' com sucesso!"}
    except (ResponseHandlingException, UnexpectedResponse) as e:
        raise HTTPException(status_code=500, detail="Erro na comunicação com o Qdrant: " + str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Erro ao processar o PDF: " + str(e))


@qdrant.post(QDRANT_URI_V2 + "/collections/create", response_model=Dict[str, Any])
async def create_collection(data: CollectionData, qdrant_client: QdrantClient = Depends(get_qdrant_client),):
    """
    Cria uma nova coleção no Qdrant.
    """
    existing_collections = qdrant_client.get_collections().collections
    if any(col.name == data.collection_name for col in existing_collections):
        raise HTTPException(status_code=400, detail=f"A coleção '{data.collection_name}' já existe.")

    try:
        qdrant_client.create_collection(
            collection_name=data.collection_name,
            vectors_config=models.VectorParams(
                size=data.vector_size,
                distance=data.distance_metric
            )
        )
        return {"message": f"Coleção '{data.collection_name}' criada com sucesso!"}
    except (ResponseHandlingException, UnexpectedResponse) as e:
        raise HTTPException(status_code=500, detail="Erro ao criar coleção no Qdrant: " + str(e))


@qdrant.get(QDRANT_URI_V2 + "/collections/list", response_model=Dict[str, Any])
async def list_collections(qdrant_client: QdrantClient = Depends(get_qdrant_client)):
    """
    Lista todas as coleções no Qdrant.
    """
    try:
        collections = qdrant_client.get_collections().collections
        collection_names = [collection.name for collection in collections]
        return {"collections": collection_names}
    except (ResponseHandlingException, UnexpectedResponse) as e:
        raise HTTPException(status_code=500, detail="Erro ao listar coleções: " + str(e))

@qdrant.delete(QDRANT_URI_V2 + "/collections/{collection_name}", response_model=Dict[str, Any])
async def delete_collection(collection_name: str, qdrant_client: QdrantClient = Depends(get_qdrant_client)):
    """
    Deleta uma coleção específica no Qdrant.
    """
    try:
        qdrant_client.delete_collection(collection_name)
        return {"status": "success", "message": f"Coleção '{collection_name}' deletada com sucesso."}
    except (ResponseHandlingException, UnexpectedResponse) as e:
        raise HTTPException(status_code=500, detail=f"Erro ao deletar coleção '{collection_name}': {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro inesperado ao deletar coleção '{collection_name}': {str(e)}")