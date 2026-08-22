from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def src(p):return (ROOT/p).read_text(encoding='utf-8')


def test_patient_workspace_exposes_v6_contextual_tools():
    s=src('nutridesktop/ui/patient_dialog.py')
    for label in ['Exames laboratoriais','Packs clínicos','Comparação longitudinal','Enviar via WhatsApp','Gerar plano em PDF']:
        assert label in s
    assert 'QDesktopServices.openUrl' in s
    assert 'SIBO' in src('nutridesktop/ui/clinical_packs_dialog.py')


def test_dashboard_uses_smart_pending_actions():
    s=src('nutridesktop/ui/main_window.py')
    assert 'collect_pending_actions' in s
    assert 'Pendências inteligentes' in s


def test_library_and_settings_expose_import_and_template_defaults():
    s=src('nutridesktop/ui/main_window.py')
    assert 'Central de importação' in s
    assert 'Template padrão' in s
    assert 'style_key' in s
    assert 'ImportDialog' in s


def test_v6_dialog_modules_exist_with_expected_workflows():
    labs=src('nutridesktop/ui/labs_dialog.py');packs=src('nutridesktop/ui/clinical_packs_dialog.py');imp=src('nutridesktop/ui/import_dialog.py')
    assert 'Novo painel de exames' in labs and 'Marcar revisado' in labs
    assert 'Ativar pack' in packs and 'Salvar acompanhamento' in packs
    assert 'Pré-visualizar' in imp and 'Aplicar importação' in imp


def test_recipe_library_exposes_category_tags_and_preparation():
    s=src('nutridesktop/ui/main_window.py')
    for label in ['Categoria da receita','Tags','Modo de preparo']:
        assert label in s
