from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from resources.database.config import DSN

engine = create_engine(DSN)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_session():
    """
    Retorna uma nova instância da sessão do banco de dados.
    Essa função pode ser usada para inicializar o banco no contexto do lifespan.
    """
    return SessionLocal()

def get_db():
    """
    Função para obter uma sessão do banco de dados para uso em requisições.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
