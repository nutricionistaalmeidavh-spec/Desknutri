from __future__ import annotations
from dataclasses import dataclass
import sqlite3
from nutridesktop.version import SCHEMA_VERSION

@dataclass(frozen=True)
class Migration:
    version:int; name:str; sql:str

MIGRATIONS=[
Migration(1,"base",r'''
CREATE TABLE IF NOT EXISTS schema_meta(version INTEGER NOT NULL);
INSERT INTO schema_meta(version) SELECT 0 WHERE NOT EXISTS(SELECT 1 FROM schema_meta);
CREATE TABLE IF NOT EXISTS pacientes(
 id INTEGER PRIMARY KEY AUTOINCREMENT,nome TEXT NOT NULL,sexo TEXT NOT NULL,data_nascimento TEXT,
 telefone TEXT,email TEXT,observacoes TEXT,criado_em TEXT DEFAULT CURRENT_TIMESTAMP, atualizado_em TEXT);
CREATE TABLE IF NOT EXISTS avaliacoes(
 id INTEGER PRIMARY KEY AUTOINCREMENT,paciente_id INTEGER NOT NULL,data TEXT NOT NULL,peso REAL,altura_cm REAL,idade REAL,imc REAL,
 dobra_triceps REAL,dobra_biceps REAL,dobra_subescapular REAL,dobra_suprailiaca REAL,dobra_abdominal REAL,dobra_coxa REAL,dobra_peitoral REAL,dobra_axilar REAL,dobra_panturrilha REAL,
 cintura REAL,quadril REAL,pescoco REAL,bia_pg REAL,bia_massa_magra REAL,pg_final REAL,origem_pg TEXT,massa_gorda REAL,massa_magra REAL,detalhes_pg TEXT,
 formula_tmb TEXT,tmb REAL,atividade TEXT,fator_atividade REAL,get_total REAL,ajuste_pct REAL,vet REAL,ptn_gkg REAL,ptn_g REAL,lip_pct REAL,lip_g REAL,cho_g REAL,observacoes TEXT,
 FOREIGN KEY(paciente_id) REFERENCES pacientes(id) ON DELETE CASCADE);
CREATE TABLE IF NOT EXISTS alimentos(id INTEGER PRIMARY KEY AUTOINCREMENT,categoria TEXT,descricao TEXT NOT NULL,kcal REAL,proteina REAL,lipideos REAL,carboidrato REAL,fibra REAL,calcio REAL,magnesio REAL,fosforo REAL,ferro REAL,sodio REAL,potassio REAL,cobre REAL,zinco REAL,tiamina REAL,riboflavina REAL,piridoxina REAL,niacina REAL,vitamina_c REAL,origem TEXT DEFAULT 'TACO');
CREATE TABLE IF NOT EXISTS planos(id INTEGER PRIMARY KEY AUTOINCREMENT,paciente_id INTEGER NOT NULL,nome TEXT,data TEXT,vet_meta REAL,observacoes TEXT,FOREIGN KEY(paciente_id) REFERENCES pacientes(id) ON DELETE CASCADE);
CREATE TABLE IF NOT EXISTS plano_itens(id INTEGER PRIMARY KEY AUTOINCREMENT,plano_id INTEGER NOT NULL,refeicao TEXT,alimento_id INTEGER,quantidade_g REAL,FOREIGN KEY(plano_id) REFERENCES planos(id) ON DELETE CASCADE,FOREIGN KEY(alimento_id) REFERENCES alimentos(id));
CREATE TABLE IF NOT EXISTS receitas(id INTEGER PRIMARY KEY AUTOINCREMENT,nome TEXT NOT NULL,categoria TEXT,tags TEXT,porcoes REAL DEFAULT 1,modo_preparo TEXT);
CREATE TABLE IF NOT EXISTS planos_modelo(id INTEGER PRIMARY KEY AUTOINCREMENT,nome TEXT NOT NULL,categoria TEXT,vet_alvo REAL,descricao TEXT);
CREATE TABLE IF NOT EXISTS planos_modelo_itens(id INTEGER PRIMARY KEY AUTOINCREMENT,modelo_id INTEGER NOT NULL,refeicao TEXT,alimento_id INTEGER,quantidade_g REAL,FOREIGN KEY(modelo_id) REFERENCES planos_modelo(id) ON DELETE CASCADE,FOREIGN KEY(alimento_id) REFERENCES alimentos(id));
CREATE TABLE IF NOT EXISTS anamneses_modelo(id INTEGER PRIMARY KEY AUTOINCREMENT,nome TEXT NOT NULL,conteudo TEXT);
CREATE TABLE IF NOT EXISTS receita_ingredientes(id INTEGER PRIMARY KEY AUTOINCREMENT,receita_id INTEGER NOT NULL,alimento_id INTEGER,quantidade_g REAL,FOREIGN KEY(receita_id) REFERENCES receitas(id) ON DELETE CASCADE,FOREIGN KEY(alimento_id) REFERENCES alimentos(id));
CREATE TABLE IF NOT EXISTS configuracoes(chave TEXT PRIMARY KEY,valor TEXT);
CREATE TABLE IF NOT EXISTS diretrizes(id INTEGER PRIMARY KEY AUTOINCREMENT,nome TEXT NOT NULL,fonte TEXT,pontos TEXT);
CREATE TABLE IF NOT EXISTS documentos_paciente(id INTEGER PRIMARY KEY AUTOINCREMENT,paciente_id INTEGER NOT NULL,tipo TEXT,nome_arquivo TEXT,caminho TEXT,data TEXT,FOREIGN KEY(paciente_id) REFERENCES pacientes(id) ON DELETE CASCADE);
CREATE TABLE IF NOT EXISTS anamneses_paciente(id INTEGER PRIMARY KEY AUTOINCREMENT,paciente_id INTEGER NOT NULL,nome_modelo TEXT,conteudo TEXT,data TEXT,tipo TEXT DEFAULT 'Estruturada',dados_json TEXT DEFAULT '{}',versao INTEGER DEFAULT 1,FOREIGN KEY(paciente_id) REFERENCES pacientes(id) ON DELETE CASCADE);
CREATE TABLE IF NOT EXISTS fotos_paciente(id INTEGER PRIMARY KEY AUTOINCREMENT,paciente_id INTEGER NOT NULL,data TEXT NOT NULL,observacao TEXT,caminho TEXT NOT NULL,FOREIGN KEY(paciente_id) REFERENCES pacientes(id) ON DELETE CASCADE);
CREATE TABLE IF NOT EXISTS consultas(id INTEGER PRIMARY KEY AUTOINCREMENT,paciente_id INTEGER NOT NULL,data TEXT,hora TEXT,status TEXT DEFAULT 'Agendada',observacoes TEXT,FOREIGN KEY(paciente_id) REFERENCES pacientes(id) ON DELETE CASCADE);
'''),
Migration(2,"audit_and_versions",r'''
CREATE TABLE IF NOT EXISTS audit_log(id INTEGER PRIMARY KEY AUTOINCREMENT,entity_type TEXT NOT NULL,entity_id INTEGER,action TEXT NOT NULL,created_at TEXT DEFAULT CURRENT_TIMESTAMP,details_json TEXT DEFAULT '{}');
CREATE TABLE IF NOT EXISTS avaliacao_revisoes(id INTEGER PRIMARY KEY AUTOINCREMENT,avaliacao_id INTEGER NOT NULL,versao INTEGER NOT NULL,snapshot_json TEXT NOT NULL,motivo TEXT,created_at TEXT DEFAULT CURRENT_TIMESTAMP,FOREIGN KEY(avaliacao_id) REFERENCES avaliacoes(id) ON DELETE CASCADE);
CREATE INDEX IF NOT EXISTS idx_avrev_avaliacao ON avaliacao_revisoes(avaliacao_id,versao);
'''),
Migration(3,"plan_versions_targets",r'''
CREATE TABLE IF NOT EXISTS plano_versoes(id INTEGER PRIMARY KEY AUTOINCREMENT,plano_id INTEGER NOT NULL,versao INTEGER NOT NULL,snapshot_json TEXT NOT NULL,created_at TEXT DEFAULT CURRENT_TIMESTAMP,FOREIGN KEY(plano_id) REFERENCES planos(id) ON DELETE CASCADE);
CREATE TABLE IF NOT EXISTS plano_metas(id INTEGER PRIMARY KEY AUTOINCREMENT,plano_id INTEGER NOT NULL,nutriente TEXT NOT NULL,meta REAL,unidade TEXT,limite_min REAL,limite_max REAL,UNIQUE(plano_id,nutriente),FOREIGN KEY(plano_id) REFERENCES planos(id) ON DELETE CASCADE);
CREATE TABLE IF NOT EXISTS refeicao_metas(id INTEGER PRIMARY KEY AUTOINCREMENT,plano_id INTEGER NOT NULL,refeicao TEXT NOT NULL,percentual_vet REAL,UNIQUE(plano_id,refeicao),FOREIGN KEY(plano_id) REFERENCES planos(id) ON DELETE CASCADE);
'''),
Migration(4,"templates_protocols",r'''
CREATE TABLE IF NOT EXISTS document_templates(id INTEGER PRIMARY KEY AUTOINCREMENT,nome TEXT NOT NULL,tipo TEXT NOT NULL,conteudo TEXT NOT NULL,ativo INTEGER DEFAULT 1,created_at TEXT DEFAULT CURRENT_TIMESTAMP,updated_at TEXT);
CREATE TABLE IF NOT EXISTS clinical_protocols(id INTEGER PRIMARY KEY AUTOINCREMENT,slug TEXT NOT NULL,versao TEXT NOT NULL,titulo TEXT NOT NULL,fonte TEXT,publico_alvo TEXT,conteudo TEXT NOT NULL,ativo INTEGER DEFAULT 1,created_at TEXT DEFAULT CURRENT_TIMESTAMP,UNIQUE(slug,versao));
'''),
Migration(5,"advanced_agenda",r'''
CREATE TABLE IF NOT EXISTS consulta_recorrencias(id INTEGER PRIMARY KEY AUTOINCREMENT,consulta_id INTEGER NOT NULL,frequencia TEXT,intervalo INTEGER DEFAULT 1,ate_data TEXT,FOREIGN KEY(consulta_id) REFERENCES consultas(id) ON DELETE CASCADE);
CREATE TABLE IF NOT EXISTS consulta_links(id INTEGER PRIMARY KEY AUTOINCREMENT,consulta_id INTEGER NOT NULL,tipo TEXT NOT NULL,entity_id INTEGER,FOREIGN KEY(consulta_id) REFERENCES consultas(id) ON DELETE CASCADE);
CREATE INDEX IF NOT EXISTS idx_consultas_data_status ON consultas(data,status);
'''),
Migration(6,"timeline",r'''
CREATE TABLE IF NOT EXISTS timeline_events(id INTEGER PRIMARY KEY AUTOINCREMENT,paciente_id INTEGER NOT NULL,event_type TEXT NOT NULL,event_date TEXT NOT NULL,title TEXT NOT NULL,entity_id INTEGER,metadata_json TEXT DEFAULT '{}',created_at TEXT DEFAULT CURRENT_TIMESTAMP,FOREIGN KEY(paciente_id) REFERENCES pacientes(id) ON DELETE CASCADE);
CREATE INDEX IF NOT EXISTS idx_timeline_patient_date ON timeline_events(paciente_id,event_date,id);
'''),
Migration(7,"security",r'''
CREATE TABLE IF NOT EXISTS security_state(id INTEGER PRIMARY KEY CHECK(id=1),pin_hash TEXT,auto_lock_minutes INTEGER DEFAULT 15,backup_encryption INTEGER DEFAULT 0,updated_at TEXT);
INSERT OR IGNORE INTO security_state(id,auto_lock_minutes,backup_encryption) VALUES(1,15,0);
'''),
Migration(8,"growth_measurements",r'''
CREATE TABLE IF NOT EXISTS growth_measurements(id INTEGER PRIMARY KEY AUTOINCREMENT,paciente_id INTEGER NOT NULL,data TEXT NOT NULL,idade_dias INTEGER NOT NULL,peso REAL,altura_cm REAL,imc REAL,waz REAL,haz REAL,bmiz REAL,wfhz REAL,source TEXT NOT NULL DEFAULT 'WHO',created_at TEXT DEFAULT CURRENT_TIMESTAMP,FOREIGN KEY(paciente_id) REFERENCES pacientes(id) ON DELETE CASCADE);
CREATE INDEX IF NOT EXISTS idx_growth_patient_date ON growth_measurements(paciente_id,data);
'''),
Migration(9,"release_management",r'''
CREATE TABLE IF NOT EXISTS app_update_history(id INTEGER PRIMARY KEY AUTOINCREMENT,from_version TEXT,to_version TEXT,status TEXT NOT NULL,manifest_url TEXT,details_json TEXT DEFAULT '{}',created_at TEXT DEFAULT CURRENT_TIMESTAMP);
CREATE INDEX IF NOT EXISTS idx_update_history_created ON app_update_history(created_at,id);
'''),
Migration(10,"backup_history",r'''
CREATE TABLE IF NOT EXISTS backup_history(id INTEGER PRIMARY KEY AUTOINCREMENT,path TEXT NOT NULL,created_at TEXT DEFAULT CURRENT_TIMESTAMP,sha256 TEXT,size_bytes INTEGER,status TEXT NOT NULL DEFAULT 'OK',encrypted INTEGER DEFAULT 0,trigger TEXT DEFAULT 'manual');
CREATE INDEX IF NOT EXISTS idx_backup_history_created ON backup_history(created_at,id);
'''),
Migration(11,"account_licensing",r'''
CREATE TABLE IF NOT EXISTS account_license_state(
 id INTEGER PRIMARY KEY CHECK(id=1),
 email TEXT,
 server_url TEXT,
 device_token_enc TEXT,
 last_refresh TEXT,
 last_error TEXT,
 updated_at TEXT
);
INSERT OR IGNORE INTO account_license_state(id) VALUES(1);
'''),
Migration(12,"consultation_workflow",r'''
ALTER TABLE consultas ADD COLUMN objetivo TEXT;
ALTER TABLE consultas ADD COLUMN abordagem TEXT;
ALTER TABLE consultas ADD COLUMN plano_enviado_em TEXT;
ALTER TABLE consultas ADD COLUMN finalizada_em TEXT;
'''),
Migration(13,"clinical_expansion_v6",r'''
CREATE TABLE IF NOT EXISTS lab_panels(
 id INTEGER PRIMARY KEY AUTOINCREMENT, paciente_id INTEGER NOT NULL, nome TEXT NOT NULL, data_coleta TEXT NOT NULL, laboratorio TEXT, observacoes TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP,
 FOREIGN KEY(paciente_id) REFERENCES pacientes(id) ON DELETE CASCADE);
CREATE INDEX IF NOT EXISTS idx_lab_panels_patient_date ON lab_panels(paciente_id,data_coleta,id);
CREATE TABLE IF NOT EXISTS lab_results(
 id INTEGER PRIMARY KEY AUTOINCREMENT, panel_id INTEGER NOT NULL, marker_name TEXT NOT NULL, value_numeric REAL, value_text TEXT, unit TEXT, ref_min REAL, ref_max REAL, flag TEXT, notes TEXT, needs_review INTEGER DEFAULT 0, reviewed_at TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP,
 FOREIGN KEY(panel_id) REFERENCES lab_panels(id) ON DELETE CASCADE);
CREATE INDEX IF NOT EXISTS idx_lab_results_marker ON lab_results(marker_name,panel_id);
CREATE TABLE IF NOT EXISTS patient_clinical_packs(
 id INTEGER PRIMARY KEY AUTOINCREMENT, paciente_id INTEGER NOT NULL, pack_slug TEXT NOT NULL, ativo INTEGER DEFAULT 1, activated_at TEXT DEFAULT CURRENT_TIMESTAMP, deactivated_at TEXT, UNIQUE(paciente_id,pack_slug),
 FOREIGN KEY(paciente_id) REFERENCES pacientes(id) ON DELETE CASCADE);
CREATE TABLE IF NOT EXISTS clinical_pack_records(
 id INTEGER PRIMARY KEY AUTOINCREMENT, paciente_id INTEGER NOT NULL, pack_slug TEXT NOT NULL, record_date TEXT NOT NULL, data_json TEXT NOT NULL DEFAULT '{}', notes TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP,
 FOREIGN KEY(paciente_id) REFERENCES pacientes(id) ON DELETE CASCADE);
CREATE INDEX IF NOT EXISTS idx_pack_records_patient_slug_date ON clinical_pack_records(paciente_id,pack_slug,record_date,id);
CREATE TABLE IF NOT EXISTS plano_substituicoes(
 id INTEGER PRIMARY KEY AUTOINCREMENT, plano_id INTEGER NOT NULL, plano_item_id INTEGER NOT NULL, alternative_food_id INTEGER NOT NULL, quantidade_g REAL NOT NULL, note TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP,
 FOREIGN KEY(plano_id) REFERENCES planos(id) ON DELETE CASCADE,
 FOREIGN KEY(plano_item_id) REFERENCES plano_itens(id) ON DELETE CASCADE,
 FOREIGN KEY(alternative_food_id) REFERENCES alimentos(id));
CREATE INDEX IF NOT EXISTS idx_plan_substitutions_plan ON plano_substituicoes(plano_id,plano_item_id);
CREATE TABLE IF NOT EXISTS manual_pending_actions(
 id INTEGER PRIMARY KEY AUTOINCREMENT, paciente_id INTEGER NOT NULL, kind TEXT NOT NULL, title TEXT NOT NULL, detail TEXT, severity TEXT DEFAULT 'media', due_date TEXT, resolved_at TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP,
 FOREIGN KEY(paciente_id) REFERENCES pacientes(id) ON DELETE CASCADE);
CREATE INDEX IF NOT EXISTS idx_manual_pending_open ON manual_pending_actions(resolved_at,paciente_id);
CREATE TABLE IF NOT EXISTS import_history(
 id INTEGER PRIMARY KEY AUTOINCREMENT, import_kind TEXT NOT NULL, source_name TEXT NOT NULL, total_rows INTEGER DEFAULT 0, imported_rows INTEGER DEFAULT 0, skipped_rows INTEGER DEFAULT 0, invalid_rows INTEGER DEFAULT 0, details_json TEXT DEFAULT '{}', created_at TEXT DEFAULT CURRENT_TIMESTAMP);
ALTER TABLE document_templates ADD COLUMN style_key TEXT DEFAULT 'clean_clinical';
ALTER TABLE document_templates ADD COLUMN specialty_tags TEXT DEFAULT '';
ALTER TABLE document_templates ADD COLUMN is_default INTEGER DEFAULT 0;
ALTER TABLE document_templates ADD COLUMN preview_json TEXT DEFAULT '{}';
'''),
]

def current_version(conn: sqlite3.Connection) -> int:
    try:
        row=conn.execute("SELECT version FROM schema_meta LIMIT 1").fetchone(); return int(row[0]) if row else 0
    except sqlite3.OperationalError: return 0

def _column_exists(conn, table, column):
    return column in {r[1] for r in conn.execute(f"PRAGMA table_info({table})")}

def _ensure_legacy_columns(conn):
    additions={
      "pacientes":{"atualizado_em":"TEXT"},
      "planos":{"parent_plan_id":"INTEGER","version_no":"INTEGER DEFAULT 1","status":"TEXT DEFAULT 'Ativo'"},
      "plano_itens":{"receita_id":"INTEGER","quantidade_porcoes":"REAL"},
      "consultas":{"tipo":"TEXT DEFAULT 'Consulta'","retorno_de_id":"INTEGER","duracao_min":"INTEGER DEFAULT 60"},
      "documentos_paciente":{"managed":"INTEGER DEFAULT 0","sha256":"TEXT"},
    }
    for table, cols in additions.items():
        try:
            for col, decl in cols.items():
                if not _column_exists(conn,table,col): conn.execute(f"ALTER TABLE {table} ADD COLUMN {col} {decl}")
        except sqlite3.OperationalError: pass

def migrate(conn:sqlite3.Connection,target=SCHEMA_VERSION):
    conn.execute("PRAGMA foreign_keys=ON")
    v=current_version(conn)
    for m in MIGRATIONS:
        if v < m.version <= target:
            conn.executescript(m.sql)
            conn.execute("UPDATE schema_meta SET version=?",(m.version,)); conn.commit(); v=m.version
    _ensure_legacy_columns(conn); conn.commit()
    if v != target: raise RuntimeError(f"Schema esperado {target}, encontrado {v}")
    return v
