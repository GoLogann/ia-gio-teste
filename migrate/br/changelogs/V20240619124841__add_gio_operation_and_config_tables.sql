CREATE  TABLE dialogo (
                          id                   uuid  NOT NULL  ,
                          id_usuario           uuid  NOT NULL  ,
                          tipo                 integer  NOT NULL  ,
                          criado               timestamp    ,
                          CONSTRAINT pk_dialogo PRIMARY KEY ( id )
);

COMMENT ON TABLE dialogo IS 'Tabela que armazena as informações sobre pesquisas realizadas na Gio';

COMMENT ON COLUMN dialogo.id IS 'Identificador do registro';

COMMENT ON COLUMN dialogo.id_usuario IS 'Identificador de relacionamento';

COMMENT ON COLUMN dialogo.tipo IS 'Tipo de uso da Gio:
1 - Prompt Criativa
2 - Prompt Escavadora
3 - Prompt Contestação';

COMMENT ON COLUMN dialogo.criado IS 'Data de criação do registro';

CREATE  TABLE dialogo_detalhe (
                                  id                   uuid  NOT NULL  ,
                                  id_dialogo           uuid  NOT NULL  ,
                                  pergunta             text  NOT NULL  ,
                                  resposta             text  NOT NULL  ,
                                  insight              text    ,
                                  token                integer DEFAULT 0 NOT NULL  ,
                                  criado               timestamp    ,
                                  CONSTRAINT pk_dialogo_detalhe PRIMARY KEY ( id )
);

CREATE INDEX idx_dialogo_detalhe_01 ON dialogo_detalhe  ( id_dialogo );

ALTER TABLE dialogo_detalhe ADD CONSTRAINT fk_dialogo_detalhe_01 FOREIGN KEY ( id_dialogo ) REFERENCES dialogo( id );

COMMENT ON TABLE dialogo_detalhe IS 'Tabela que armazena as informações sobre os diálogos realizadas na Gio';

COMMENT ON COLUMN dialogo_detalhe.id IS 'Identificador do registro';

COMMENT ON COLUMN dialogo_detalhe.id_dialogo IS 'Identificador de relacionamento';

COMMENT ON COLUMN dialogo_detalhe.pergunta IS 'pergunta realizada para a Gio';

COMMENT ON COLUMN dialogo_detalhe.resposta IS 'Resposta recebida para a pergunta realizada';

COMMENT ON COLUMN dialogo_detalhe.insight IS 'Insight referente a pergunta realizada';

COMMENT ON COLUMN dialogo_detalhe.token IS 'Quantidade de tokens enviados na pergunta';

COMMENT ON COLUMN dialogo_detalhe.criado IS 'Data de criação do registro';

CREATE  TABLE provedor (
                           id                   uuid  NOT NULL  ,
                           nome                 varchar(200)  NOT NULL  ,
                           CONSTRAINT pk_provedor PRIMARY KEY ( id )
);

COMMENT ON TABLE provedor IS 'Tabela que armazena os dados dos provedores de IA utilizados pelo serviço';

COMMENT ON COLUMN provedor.id IS 'Identificador do registro';

COMMENT ON COLUMN provedor.nome IS 'Nome do Provedor';

CREATE  TABLE configuracao (
                               id                   uuid  NOT NULL  ,
                               id_provedor          uuid  NOT NULL  ,
                               temperatura          numeric(25,10) DEFAULT 0 NOT NULL  ,
                               api_key              text    ,
                               api_token            text    ,
                               url_base             text  NOT NULL  ,
                               CONSTRAINT pk_configuracao PRIMARY KEY ( id )
);

CREATE INDEX idx_configuracao_01 ON configuracao  ( id_provedor );

ALTER TABLE configuracao ADD CONSTRAINT fk_configuracao_01 FOREIGN KEY ( id_provedor ) REFERENCES provedor( id );

COMMENT ON TABLE configuracao IS 'Tabela que armazena as configurações de acordo com o tipo de provedor de dados de IA';

COMMENT ON COLUMN configuracao.id IS 'Identificador do registro';

COMMENT ON COLUMN configuracao.id_provedor IS 'Identificador de relacionamento';

COMMENT ON COLUMN configuracao.temperatura IS 'Nível da temperatura das consultas da IA';

COMMENT ON COLUMN configuracao.api_key IS 'Chave de acesso da API';

COMMENT ON COLUMN configuracao.api_token IS 'Token de Acesso da API';

COMMENT ON COLUMN configuracao.url_base IS 'URL base de consulta dos provedores de IA';

CREATE  TABLE provedor_modelo (
                                  id                   uuid  NOT NULL  ,
                                  id_provedor          uuid  NOT NULL  ,
                                  nome                 varchar(200)  NOT NULL  ,
                                  descricao            text  NOT NULL  ,
                                  CONSTRAINT pk_provedor_modelo PRIMARY KEY ( id )
);

CREATE INDEX idx_provedor_modelo_01 ON provedor_modelo  ( id_provedor );

ALTER TABLE provedor_modelo ADD CONSTRAINT fk_provedor_modelo_01 FOREIGN KEY ( id_provedor ) REFERENCES provedor( id );

COMMENT ON TABLE provedor_modelo IS 'Tabela que aramazena as informações dos modelos personalizados ou atuais usados pelos provedores de IA nas consultas';

COMMENT ON COLUMN provedor_modelo.id IS 'Identificador do registro';

COMMENT ON COLUMN provedor_modelo.id_provedor IS 'Identificador de relacionamento';

COMMENT ON COLUMN provedor_modelo.nome IS 'Nome do modelo';

COMMENT ON COLUMN provedor_modelo.descricao IS 'Descrição completa com o detalhamento do modelo';
