from __future__ import annotations
from copy import deepcopy

SIBO_STATUSES=('suspeito_registrado','encaminhado','confirmado_por_registro_externo','resolvido')

PACK_DEFINITIONS={
    'materno_infantil':{
        'label':'Materno-infantil',
        'fields':['fase','dpp','idade_gestacional_semanas','peso_pre_gestacional','altura_cm','peso_atual','lactacao','fase_introducao_alimentar','paciente_relacionado_id','observacoes'],
        'defaults':{'fase':'gestacao','lactacao':False,'fase_introducao_alimentar':'','observacoes':''},
    },
    'esportiva':{
        'label':'Nutrição esportiva',
        'fields':['modalidade','frequencia_semanal','volume_treino','horarios_treino','estrategia_pre','estrategia_intra','estrategia_pos','meta_hidratacao_ml','objetivos_performance','observacoes'],
        'defaults':{'modalidade':'','frequencia_semanal':0,'meta_hidratacao_ml':None,'observacoes':''},
    },
    'metabolica':{
        'label':'Obesidade / Metabólica',
        'fields':['condicoes','meta_peso','meta_cintura','pressao_arterial','barreiras','metas_comportamentais','observacoes'],
        'defaults':{'condicoes':[],'barreiras':[],'metas_comportamentais':[],'observacoes':''},
    },
    'renal':{
        'label':'Nutrição renal',
        'fields':['condicao_renal','estagio_registrado','proteina_meta_g','sodio_meta_mg','potassio_meta_mg','fosforo_meta_mg','liquidos_meta_ml','observacoes'],
        'defaults':{'condicao_renal':'','estagio_registrado':'','observacoes':''},
    },
    'bariatrica':{
        'label':'Bariátrica',
        'fields':['status_cirurgico','data_cirurgia','tipo_cirurgia','fase_consistencia','suplementos','intolerancias','sintomas','observacoes'],
        'defaults':{'status_cirurgico':'pre_operatorio','suplementos':[],'intolerancias':[],'sintomas':[],'observacoes':''},
    },
    'gastrointestinal':{
        'label':'Gastrointestinal',
        'fields':['bristol','evacuacoes_dia','refluxo','constipacao','diarreia','intolerancias','fase_fodmap','sintomas','alimento_sintoma','observacoes'],
        'defaults':{'bristol':4,'evacuacoes_dia':None,'refluxo':False,'constipacao':False,'diarreia':False,'intolerancias':[],'fase_fodmap':'','sintomas':[],'alimento_sintoma':'','observacoes':''},
    },
    'sibo':{
        'label':'SIBO',
        'fields':['status','subtipo_documentado','teste_externo','tratamento_informado','fase_dietetica','gatilhos','reintroducoes','score_sintomas','observacoes'],
        'defaults':{'status':'suspeito_registrado','subtipo_documentado':'','teste_externo':'','tratamento_informado':'','fase_dietetica':'','gatilhos':[],'reintroducoes':[],'score_sintomas':0,'observacoes':''},
    },
}


def pack_defaults(slug):
    if slug not in PACK_DEFINITIONS:raise KeyError(slug)
    return deepcopy(PACK_DEFINITIONS[slug]['defaults'])
