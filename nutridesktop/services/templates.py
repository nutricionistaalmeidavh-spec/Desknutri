from __future__ import annotations
import re

TOKEN = re.compile(r"{{\s*([a-zA-Z0-9_.]+)\s*}}")

STYLE_PRESETS={
    'clean_clinical':{'label':'Clínico clean','accent':'145C57','soft':'EDF6F4','text':'26302E'},
    'minimal':{'label':'Minimal','accent':'303735','soft':'F6F7F7','text':'202725'},
    'modern_teal':{'label':'Moderno teal','accent':'0F6F68','soft':'E7F5F2','text':'173A36'},
    'materno_infantil':{'label':'Materno-infantil','accent':'8A5B79','soft':'F7EEF4','text':'4B3342'},
}


def render_template(content, context):
    def get(key):
        cur = context
        for part in key.split('.'):
            if isinstance(cur, dict):cur = cur.get(part, '')
            else:cur = getattr(cur, part, '')
        return '' if cur is None else str(cur)
    return TOKEN.sub(lambda m: get(m.group(1)), content)


DEFAULT_TEMPLATES = [
    ('Avaliação','Avaliação','Paciente: {{paciente.nome}}\nData: {{data}}\n\nAvaliação: {{conteudo}}','clean_clinical',''),
    ('Plano alimentar - Clínico clean','Plano','Paciente: {{paciente.nome}}\nData: {{data}}\n\nPlano/conduta: {{conteudo}}','clean_clinical',''),
    ('Plano alimentar - Minimal','Plano','Paciente: {{paciente.nome}}\n\n{{conteudo}}','minimal',''),
    ('Plano alimentar - Moderno teal','Plano','Paciente: {{paciente.nome}}\nData: {{data}}\n\n{{conteudo}}','modern_teal',''),
    ('Plano alimentar - Materno-infantil','Plano','Paciente: {{paciente.nome}}\nData: {{data}}\n\n{{conteudo}}','materno_infantil','materno_infantil'),
    ('Orientação','Orientação','Paciente: {{paciente.nome}}\nData: {{data}}\n\n{{conteudo}}','clean_clinical',''),
    ('Receita','Receita','Paciente: {{paciente.nome}}\nData: {{data}}\n\nReceita/orientação: {{conteudo}}','modern_teal',''),
    ('Evolução','Evolução','Paciente: {{paciente.nome}}\nData: {{data}}\n\nEvolução: {{conteudo}}','clean_clinical',''),
    ('Encaminhamento','Encaminhamento','Paciente: {{paciente.nome}}\nData: {{data}}\n\nEncaminho para: {{destino}}\nMotivo: {{conteudo}}','minimal',''),
    ('Relatório clínico','Relatório','Paciente: {{paciente.nome}}\nData: {{data}}\n\n{{conteudo}}','clean_clinical',''),
    ('Relatório moderno','Relatório','Paciente: {{paciente.nome}}\nData: {{data}}\n\n{{conteudo}}','modern_teal',''),
]


def seed(repo):
    existing={(r['nome'],r['tipo']) for r in repo.list()}
    for n,t,c,style,tags in DEFAULT_TEMPLATES:
        if (n,t) not in existing:repo.save(n,t,c,style_key=style,specialty_tags=tags)
    for typ in ('Plano','Relatório','Orientação','Receita'):
        if repo.default(typ) is None:
            rows=repo.list(typ)
            if rows:repo.set_default(rows[0]['id'],typ)
