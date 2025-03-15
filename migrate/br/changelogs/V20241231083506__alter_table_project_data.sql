ALTER TABLE gio.project_data RENAME COLUMN project_name TO nome_projeto;
ALTER TABLE gio.project_data RENAME COLUMN research_field TO pesquisa_relacionada;
ALTER TABLE gio.project_data RENAME COLUMN responsible_name TO responsavel;
ALTER TABLE gio.project_data RENAME COLUMN responsible_area TO area_responsavel;
ALTER TABLE gio.project_data RENAME COLUMN project_goal TO objetivo_projeto;
ALTER TABLE gio.project_data RENAME COLUMN project_benefits TO beneficio;
ALTER TABLE gio.project_data RENAME COLUMN project_differentiator TO diferencial;
ALTER TABLE gio.project_data RENAME COLUMN milestone TO marco;
ALTER TABLE gio.project_data RENAME COLUMN road_blocks TO desafio;
ALTER TABLE gio.project_data RENAME COLUMN research_methods TO metodologia;
ALTER TABLE gio.project_data RENAME COLUMN next_steps TO proximo_passo;
ALTER TABLE gio.project_data RENAME COLUMN additional_details TO detalhe_adicional;
ALTER TABLE gio.project_data RENAME COLUMN user_observations TO observacao_usuario;
ALTER TABLE gio.project_data RENAME COLUMN is_confirmed TO aprovado;
ALTER TABLE gio.project_data RENAME COLUMN created_at TO criado;
ALTER TABLE gio.project_data RENAME COLUMN updated_at TO atualizado;

ALTER TABLE gio.project_data
ADD COLUMN id_departamento BIGINT,
ADD COLUMN id_comunicacao_enxame_contato UUID;

COMMENT ON COLUMN gio.project_data.id_departamento IS 'Identificador do departamento associado ao projeto';
COMMENT ON COLUMN gio.project_data.id_comunicacao_enxame_contato IS 'Identificador de comunicação de enxame para contato relacionado ao projeto';
