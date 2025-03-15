import traceback
from langchain.text_splitter import RecursiveCharacterTextSplitter

class DocumentProcessor:
    def __init__(self, chunk_size=1000, chunk_overlap=200):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def process_document_data(self, document_data):
        """
        Processa o texto de um documento (PDF ou DOCX) e divide em chunks.

        :param document_data: Texto do documento
        :return: Lista de chunks
        """
        chunks = []
        try:
            splitter = RecursiveCharacterTextSplitter(
                chunk_size=self.chunk_size, chunk_overlap=self.chunk_overlap
            )

            chunks = splitter.split_text(document_data)

        except Exception as e:
            print(f"Erro ao processar documento: {e}")
            print(traceback.format_exc())

        return chunks
