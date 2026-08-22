from pathlib import Path
import csv
import pytest

from nutridesktop.data.database import Database
from nutridesktop.data.repositories import PatientRepository, AssessmentRepository, LabRepository, ImportHistoryRepository


def make_db(tmp_path):
    db=Database(tmp_path/'import.db');db.initialize();return db


def write_csv(path,rows):
    keys=list(rows[0])
    with open(path,'w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=keys);w.writeheader();w.writerows(rows)


def test_preview_and_apply_patient_import_with_duplicate_skip(tmp_path):
    from nutridesktop.services.import_center import preview_import,apply_import
    db=make_db(tmp_path);PatientRepository(db).create('Maria Silva','F','1990-01-01',telefone='16999991111',email='maria@example.com')
    path=tmp_path/'patients.csv'
    write_csv(path,[
        {'nome':'Maria Silva','sexo':'Feminino','data_nascimento':'1990-01-01','telefone':'16999991111','email':'maria@example.com'},
        {'nome':'João Souza','sexo':'Masculino','data_nascimento':'1988-05-10','telefone':'16988882222','email':'joao@example.com'},
        {'nome':'','sexo':'Feminino','data_nascimento':'2000-01-01','telefone':'','email':''},
    ])
    preview=preview_import('patients',path,db)
    assert preview.total_rows==3
    assert len(preview.rows)==1
    assert len(preview.skipped)==1
    assert len(preview.errors)==1
    result=apply_import(preview,db)
    assert result['imported']==1 and result['skipped']==1 and result['invalid']==1
    assert PatientRepository(db).list('João')[0]['email']=='joao@example.com'
    assert ImportHistoryRepository(db).list()[0]['import_kind']=='patients'


def test_assessment_and_lab_imports_resolve_patient_by_email(tmp_path):
    from nutridesktop.services.import_center import preview_import,apply_import
    db=make_db(tmp_path);pid=PatientRepository(db).create('Ana','F','1995-03-02',email='ana@example.com')
    assess=tmp_path/'assess.csv';write_csv(assess,[{'email':'ana@example.com','data':'2026-08-01','peso':'62.5','altura_cm':'165','imc':'22.96'}])
    result=apply_import(preview_import('assessments',assess,db),db)
    assert result['imported']==1 and AssessmentRepository(db).list(pid)[0]['peso']==62.5
    labs=tmp_path/'labs.csv';write_csv(labs,[{'email':'ana@example.com','data_coleta':'2026-08-02','painel':'Metabólico','marcador':'Glicemia','valor':'98','unidade':'mg/dL','ref_min':'70','ref_max':'99'}])
    result2=apply_import(preview_import('labs',labs,db),db)
    assert result2['imported']==1 and LabRepository(db).list_results(pid,'Glicemia')[0]['value_numeric']==98


def test_xlsx_patient_import(tmp_path):
    pd=pytest.importorskip('pandas');pytest.importorskip('openpyxl')
    from nutridesktop.services.import_center import preview_import
    db=make_db(tmp_path);path=tmp_path/'patients.xlsx'
    pd.DataFrame([{'Nome completo':'Carla Lima','Sexo':'F','Nascimento':'1992-04-05','E-mail':'carla@example.com'}]).to_excel(path,index=False)
    preview=preview_import('patients',path,db)
    assert preview.rows[0]['nome']=='Carla Lima'
    assert preview.rows[0]['email']=='carla@example.com'
