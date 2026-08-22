from __future__ import annotations
import importlib
import importlib.util
from datetime import date

from nutridesktop.data.database import Database
from nutridesktop.data.repositories import PatientRepository, AgendaRepository
from nutridesktop.version import SCHEMA_VERSION


def test_v5_schema_tracks_plan_delivery_state(tmp_path):
    db=Database(tmp_path/'ux.db')
    db.initialize()
    assert SCHEMA_VERSION >= 12
    with db.connect() as c:
        cols={r['name'] for r in c.execute('PRAGMA table_info(consultas)').fetchall()}
    assert {'objetivo','abordagem','plano_enviado_em','finalizada_em'} <= cols


def test_dashboard_reports_latest_completed_consultation_without_plan(tmp_path):
    db=Database(tmp_path/'ux.db'); db.initialize()
    pid=PatientRepository(db).create('Maria Silva','F','1998-04-10')
    ag=AgendaRepository(db)
    old=ag.create(pid,'2026-08-01','09:00',observacoes='antiga')
    ag.set_status(old,'Realizada')
    ag.mark_plan_sent(old,'2026-08-02T10:00:00')
    latest=ag.create(pid,'2026-08-20','10:00',observacoes='retorno')
    ag.set_status(latest,'Realizada')
    rows=ag.pending_plan_delivery()
    assert len(rows)==1
    assert rows[0]['id']==latest
    assert rows[0]['paciente_nome']=='Maria Silva'


def test_view_models_calculate_age_and_group_navigation():
    spec=importlib.util.find_spec('nutridesktop.ui.view_models')
    assert spec is not None
    vm=importlib.import_module('nutridesktop.ui.view_models')
    assert vm.age_on('2000-08-23',date(2026,8,22))==25
    assert vm.age_on('2000-08-22',date(2026,8,22))==26
    groups=vm.NAV_GROUPS
    assert list(groups)==['TRABALHO','CONTEÚDO','SISTEMA']
    assert groups['TRABALHO'][:3]==['Dashboard','Pacientes','Agenda']
    assert 'Crescimento WHO' not in sum(groups.values(),[])
    assert 'Materno-infantil' not in sum(groups.values(),[])


def test_friendly_error_hides_raw_network_details():
    spec=importlib.util.find_spec('nutridesktop.ui.view_models')
    assert spec is not None
    vm=importlib.import_module('nutridesktop.ui.view_models')
    msg=vm.friendly_error(ConnectionError('HTTPSConnectionPool(host=x): Max retries exceeded'))
    assert 'conexão' in msg.lower()
    assert 'HTTPSConnectionPool' not in msg



from pathlib import Path
import ast

ROOT=Path(__file__).resolve().parents[1]

def _src(rel):return (ROOT/rel).read_text(encoding='utf-8')


def test_design_system_and_branding_exist():
    spec=importlib.util.find_spec('nutridesktop.ui.design_system')
    assert spec is not None
    src=_src('nutridesktop/ui/design_system.py')
    assert '#0F5B55' in src
    assert 'class StatCard' in src and 'class EmptyState' in src
    main=_src('nutridesktop/ui/main_window.py')
    assert "setWindowTitle(f'NutriDesk " in main or 'setWindowTitle(f"NutriDesk ' in main
    assert 'nav_sections' in main


def test_new_patient_uses_human_sex_labels_and_date_picker():
    main=_src('nutridesktop/ui/main_window.py')
    assert 'QDateEdit' in main
    assert "['Feminino','Masculino']" in main or '[\'Feminino\', \'Masculino\']' in main


def test_patient_workspace_has_reduced_clinical_tabs():
    src=_src('nutridesktop/ui/patient_dialog.py')
    for label in ['Resumo','Consulta','Avaliações','Plano alimentar','Evolução','Arquivos']:
        assert f"'{label}'" in src or f'"{label}"' in src
    assert "addTab(self.profile_tab(),'Cadastro')" not in src


def test_consultation_wizard_has_six_clinical_steps():
    spec=importlib.util.find_spec('nutridesktop.ui.consultation_dialog')
    assert spec is not None
    tree=ast.parse(_src('nutridesktop/ui/consultation_dialog.py'))
    value=None
    for n in tree.body:
        if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='CONSULTATION_STEPS' for t in n.targets):value=ast.literal_eval(n.value)
    assert value==['Dados da consulta','Anamnese','Avaliação','Plano alimentar','Orientações','Retorno']


def test_agenda_uses_calendar_and_settings_are_grouped():
    main=_src('nutridesktop/ui/main_window.py')
    assert 'QCalendarWidget' in main and "setObjectName('agendaCalendar')" in main
    assert "setObjectName('settingsTabs')" in main
    for label in ['Geral','Consultório','Relatórios','Segurança','Backup','Dados e portabilidade','Avançado']:
        assert f"'{label}'" in main or f'"{label}"' in main


def test_account_page_hides_server_configuration():
    src=_src('nutridesktop/ui/v4_main_window.py')
    account=src[src.index('    def account_page'):src.index('    def save_account_server') if '    def save_account_server' in src else len(src)]
    assert 'Servidor de licenças' not in account


def test_objective_distribution_uses_latest_completed_consultation_per_patient(tmp_path):
    db=Database(tmp_path/'objectives.db');db.initialize();p=PatientRepository(db);ag=AgendaRepository(db)
    a=p.create('A','F','1990-01-01');b=p.create('B','M','1990-01-01')
    c1=ag.create(a,'2026-08-01','09:00');ag.update_clinical_context(c1,'Saúde geral','');ag.set_status(c1,'Realizada')
    c2=ag.create(a,'2026-08-20','09:00');ag.update_clinical_context(c2,'Emagrecimento','');ag.set_status(c2,'Realizada')
    c3=ag.create(b,'2026-08-20','10:00');ag.update_clinical_context(c3,'Ganho de massa','');ag.set_status(c3,'Realizada')
    assert ag.objective_distribution()=={'Emagrecimento':1,'Ganho de massa':1}


def test_patient_can_mark_latest_pending_plan_as_sent(tmp_path):
    db=Database(tmp_path/'sent.db');db.initialize();p=PatientRepository(db);ag=AgendaRepository(db)
    pid=p.create('Paciente','F','1990-01-01')
    cid=ag.create(pid,'2026-08-20','09:00');ag.set_status(cid,'Realizada')
    assert ag.latest_pending_plan(pid)['id']==cid
    ag.mark_latest_plan_sent(pid,'2026-08-22T16:00:00')
    assert ag.latest_pending_plan(pid) is None


def test_v5_installer_and_visible_brand_use_nutridesk():
    iss=_src('NutriDesktop.iss')
    assert '#define MyAppName "NutriDesk"' in iss
    assert '#define MyAppVersion "6.0.0"' in iss
    assert 'Description: "Abrir NutriDesk"' in iss
    main=_src('nutridesktop/ui/main_window.py')
    assert 'NutriDesk Backup (*.nbak)' in main
    assert 'NutriDesktop Backup (*.nbak)' not in main
    assert 'Preciso de suporte com o NutriDesk.' in _src('nutridesktop/core/config.py')


def test_schema_11_database_migrates_to_consultation_workflow(tmp_path):
    from nutridesktop.data.migrations import migrate,current_version
    db=Database(tmp_path/'migrate11.db')
    with db.connect() as c:
        migrate(c,11)
        assert current_version(c)==11
        migrate(c,12)
        assert current_version(c)==12
        cols={r['name'] for r in c.execute('PRAGMA table_info(consultas)').fetchall()}
    assert {'objetivo','abordagem','plano_enviado_em','finalizada_em'} <= cols


def test_online_account_actions_expose_loading_feedback():
    src=_src('nutridesktop/ui/v4_main_window.py')
    assert 'Verificando licença…' in src
    assert 'self.account_feedback' in src
