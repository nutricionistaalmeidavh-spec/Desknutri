import math,pytest
from nutridesktop.clinical.formulas import tmb_mifflin,tmb_harris,deurenberg,calcular_avaliacao_completa
from nutridesktop.clinical.dri_lifecycle import recommendations,stage_for

def test_mifflin_male_known_calculation(): assert tmb_mifflin(80,180,30,'M')==pytest.approx(1780)
def test_mifflin_female_known_calculation(): assert tmb_mifflin(60,165,30,'F')==pytest.approx(1320.25)
def test_deurenberg_independent_formula(): assert deurenberg(25,40,'M')==pytest.approx(23.0)
def test_complete_assessment_energy_and_macros():
    r=calcular_avaliacao_completa('M',30,80,180,{},atividade='Sedentário',ajuste_pct=0,ptn_gkg=1.5,lip_pct=30)
    assert r['imc']==pytest.approx(24.691358,rel=1e-5);assert r['tmb']==pytest.approx(1780);assert r['get_total']==pytest.approx(2136);assert r['ptn_g']==120
    assert r['lip_g']==pytest.approx(71.2,rel=.01);assert r['cho_g']>0
def test_dri_lifecycle_changes_by_stage():
    assert stage_for(8,'F')==('4-8','U');assert recommendations(30,'F')['ferro'].value==18;assert recommendations(30,'F',pregnant=True)['ferro'].value==27

def test_who_adapter_if_dependency_available():
    pytest.importorskip('pygrowthstandards')
    from nutridesktop.clinical.growth import assess
    r=assess('M',365,9.6,75.7)
    assert 'weight_age' in r and r['weight_age'] is not None
    assert -4<r['weight_age'].zscore<4 and 0<=r['weight_age'].percentile<=100

def test_dri_covers_infant_older_and_maternal_stages():
    assert stage_for(0.25,'M')==('0-6m','U')
    assert recommendations(0.25,'M')['calcio'].value==200
    assert stage_for(75,'M')==('71+','M')
    assert recommendations(17,'F',pregnant=True)['calcio'].value==1300
    assert recommendations(30,'F',lactating=True)['vitamina_c'].value==120
