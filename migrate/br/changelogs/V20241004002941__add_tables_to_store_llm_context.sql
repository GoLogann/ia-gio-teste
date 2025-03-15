CREATE TABLE contexto_modelo (
    id                  uuid NOT NULL,
    id_provedor_modelo  uuid NOT NULL,
    nome                varchar(200) NOT NULL,
    contexto            text NOT NULL,
    criado              timestamp,
    CONSTRAINT pk_contexto_modelo PRIMARY KEY (id)
);

COMMENT ON TABLE contexto_modelo IS 'Tabela que armazena os contextos (system messages) usados nos modelos llm';

COMMENT ON COLUMN contexto_modelo.id IS 'Identificador do registro';

COMMENT ON COLUMN contexto_modelo.id_provedor_modelo IS 'Identificador do modelo do provedor para o qual o contexto se aplica';

COMMENT ON COLUMN contexto_modelo.nome IS 'Nome do contexto para identificação';

COMMENT ON COLUMN contexto_modelo.contexto IS 'Mensagem de contexto (system message) a ser utilizada';

COMMENT ON COLUMN contexto_modelo.criado IS 'Data de criação do registro';

CREATE INDEX idx_contexto_modelo_01 ON contexto_modelo (id_provedor_modelo);

ALTER TABLE contexto_modelo ADD CONSTRAINT fk_contexto_modelo_01 FOREIGN KEY (id_provedor_modelo) REFERENCES provedor_modelo (id);
