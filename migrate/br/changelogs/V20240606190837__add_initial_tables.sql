CREATE  TABLE anexo (
                        id                   uuid  NOT NULL  ,
                        nome                 varchar(255)  NOT NULL  ,
                        chave                varchar(255)  NOT NULL  ,
                        caminho              text  NOT NULL  ,
                        mime                 varchar(250)    ,
                        criado               timestamp    ,
                        CONSTRAINT pk_anexo_id PRIMARY KEY ( id )
);

COMMENT ON TABLE anexo IS 'Tabela que armazena as informações dos anexos em formato de bytes.';

COMMENT ON COLUMN anexo.id IS 'Identificador da tabela';

COMMENT ON COLUMN anexo.nome IS 'Nome do anexo';

COMMENT ON COLUMN anexo.chave IS 'Chave que define a localização do arquivo no bucket.';

COMMENT ON COLUMN anexo.caminho IS 'Indicação do caminho de armazenamento do arquivo';

COMMENT ON COLUMN anexo.mime IS 'Tipo de exibição do arquivo (MimeType)';

COMMENT ON COLUMN anexo.criado IS 'Data de criação do anexo';