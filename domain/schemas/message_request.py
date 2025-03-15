from pydantic import BaseModel


# class StartConversationRequest(BaseModel):
#     telefone_usuario: str
#     nome_contato: str
#     email_contato: str
#     nome_empresa: str
#     setor_empresa: str
#     porte_empresa: str
#     localizacao_empresa: str
#     nome_projeto: str
#     descricao_projeto: str
#     objetivo_projeto: str
#     duracao_projeto: str
#     recursos_projeto: str
#     desafios_projeto: str
#     roteiro_file: UploadFile = None
#

class MessageRequest(BaseModel):
    to: str
    message: str
