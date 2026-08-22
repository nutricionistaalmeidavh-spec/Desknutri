from pathlib import Path
from nutridesktop.data.database import Database
from nutridesktop.data.repositories import PatientRepository,PlanRepository,TemplateRepository
from nutridesktop.services.templates import seed,STYLE_PRESETS


def make_db(tmp_path):
    db=Database(tmp_path/'templates.db');db.initialize();return db


def test_visual_templates_seed_and_default_selection(tmp_path):
    db=make_db(tmp_path);repo=TemplateRepository(db);seed(repo)
    plans=repo.list('Plano')
    assert len(plans)>=4
    assert {r['style_key'] for r in plans} >= {'clean_clinical','minimal','modern_teal','materno_infantil'}
    selected=plans[-1];repo.set_default(selected['id'],'Plano')
    defaults=[r for r in repo.list('Plano') if r['is_default']==1]
    assert len(defaults)==1 and defaults[0]['id']==selected['id']
    assert repo.default('Plano')['id']==selected['id']


def test_legacy_template_save_remains_compatible(tmp_path):
    db=make_db(tmp_path);repo=TemplateRepository(db)
    tid=repo.save('Legado','Orientação','Paciente: {{paciente.nome}}')
    row=next(r for r in repo.list('Orientação') if r['id']==tid)
    assert row['style_key']=='clean_clinical'


def test_generate_styled_plan_pdf(tmp_path):
    from nutridesktop.services.plan_documents import generate_plan_pdf
    db=make_db(tmp_path);pid=PatientRepository(db).create('Maria','F','1990-01-01')
    with db.transaction() as c:
        food=c.execute("INSERT INTO alimentos(descricao,kcal,proteina,lipideos,carboidrato) VALUES('Arroz integral',124,2.6,1,25.8)").lastrowid
    plans=PlanRepository(db);plan=plans.create(pid,'Plano de acompanhamento',1800);plans.add_food(plan,'Almoço',food,120)
    templates=TemplateRepository(db);seed(templates);tpl=next(r for r in templates.list('Plano') if r['style_key']=='modern_teal');templates.set_default(tpl['id'],'Plano')
    out=tmp_path/'plano.pdf';path=generate_plan_pdf(pid,plan,out,database=db)
    assert path.exists() and path.stat().st_size>1000


def test_plan_substitution_can_be_persisted_and_rendered(tmp_path):
    db=make_db(tmp_path);pid=PatientRepository(db).create('P','F','1990-01-01')
    with db.transaction() as c:
        a=c.execute("INSERT INTO alimentos(descricao,kcal,proteina) VALUES('Arroz',130,2.5)").lastrowid
        b=c.execute("INSERT INTO alimentos(descricao,kcal,proteina) VALUES('Batata',86,1.7)").lastrowid
    plans=PlanRepository(db);plan=plans.create(pid,'Plano',1800);plans.add_food(plan,'Almoço',a,100);base=plans.items(plan)[0]
    sid=plans.add_substitution(plan,base['id'],b,151.2,'equivalência energética aproximada')
    rows=plans.substitutions(plan)
    assert rows[0]['id']==sid and rows[0]['alternative_name']=='Batata'


def test_plan_revision_preserves_saved_substitutions(tmp_path):
    db=make_db(tmp_path);pid=PatientRepository(db).create('P2','F','1990-01-01')
    with db.transaction() as c:
        a=c.execute("INSERT INTO alimentos(descricao,kcal) VALUES('Arroz',130)").lastrowid
        b=c.execute("INSERT INTO alimentos(descricao,kcal) VALUES('Batata',86)").lastrowid
    plans=PlanRepository(db);plan=plans.create(pid,'Plano',1800);plans.add_food(plan,'Almoço',a,100);base=plans.items(plan)[0];plans.add_substitution(plan,base['id'],b,151.2)
    revised=plans.create_revision(plan)
    subs=plans.substitutions(revised)
    assert len(subs)==1 and subs[0]['alternative_name']=='Batata'


def test_recipe_metadata_is_preserved_for_richer_library(tmp_path):
    from nutridesktop.data.repositories import RecipeRepository
    db=make_db(tmp_path);repo=RecipeRepository(db)
    rid=repo.create('Panqueca','Café da manhã',2,'Misture e asse.','proteica,rápida')
    row=next(r for r in repo.list() if r['id']==rid)
    assert row['categoria']=='Café da manhã'
    assert row['tags']=='proteica,rápida'
    assert row['modo_preparo']=='Misture e asse.'
