CREATE TABLE gio.project_data (
    id UUID PRIMARY KEY,
    project_name TEXT NOT NULL,
    research_field TEXT NOT NULL,
    responsible_name TEXT NOT NULL,
    dialog_id UUID NOT NULL,
    responsible_area TEXT,
    project_goal TEXT,
    project_benefits TEXT,
    project_differentiator TEXT,
    milestone TEXT,
    road_blocks TEXT,
    research_methods TEXT,
    next_steps TEXT,
    additional_details TEXT,
    user_observations TEXT,
    is_confirmed BOOLEAN,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_project_data_dialog FOREIGN KEY (dialog_id) REFERENCES dialogo (id)
);

COMMENT ON TABLE gio.project_data IS 'Tabela que armazena informações de projetos para acompanhamento e gestão de dados de pesquisa';

COMMENT ON COLUMN gio.project_data.id IS 'Identificador único do projeto';
COMMENT ON COLUMN gio.project_data.project_name IS 'Nome do projeto';
COMMENT ON COLUMN gio.project_data.research_field IS 'Campo de pesquisa relacionado ao projeto';
COMMENT ON COLUMN gio.project_data.responsible_name IS 'Nome do responsável pelo projeto';
COMMENT ON COLUMN gio.project_data.dialog_id IS 'Identificador do diálogo relacionado ao projeto, referência à tabela dialogo';
COMMENT ON COLUMN gio.project_data.responsible_area IS 'Área responsável pelo projeto';
COMMENT ON COLUMN gio.project_data.project_goal IS 'Objetivo principal do projeto';
COMMENT ON COLUMN gio.project_data.project_benefits IS 'Benefícios esperados do projeto';
COMMENT ON COLUMN gio.project_data.project_differentiator IS 'Diferenciais que destacam o projeto';
COMMENT ON COLUMN gio.project_data.milestone IS 'Marcos ou etapas importantes do projeto';
COMMENT ON COLUMN gio.project_data.road_blocks IS 'Principais bloqueios ou desafios do projeto';
COMMENT ON COLUMN gio.project_data.research_methods IS 'Métodos de pesquisa aplicados no projeto';
COMMENT ON COLUMN gio.project_data.next_steps IS 'Próximos passos planejados para o projeto';
COMMENT ON COLUMN gio.project_data.additional_details IS 'Detalhes adicionais sobre o projeto';
COMMENT ON COLUMN gio.project_data.user_observations IS 'Observações do usuário sobre o projeto';
COMMENT ON COLUMN gio.project_data.is_confirmed IS 'Indica se o projeto foi confirmado ou aprovado';
COMMENT ON COLUMN gio.project_data.created_at IS 'Data e hora de criação do registro do projeto';
COMMENT ON COLUMN gio.project_data.updated_at IS 'Data e hora da última atualização do registro do projeto';

