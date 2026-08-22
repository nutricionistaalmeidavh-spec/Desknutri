from nutridesktop.version import CLINICAL_CONTENT_VERSION
DEFAULT_PROTOCOLS=[
{"slug":"adult-assessment","version":CLINICAL_CONTENT_VERSION,"title":"Avaliação nutricional do adulto","source":"NutriDesk - referências rastreáveis por método","target":"Adultos","content":"Registrar método antropométrico, contexto clínico e limitações. Evitar interpretar estimativas isoladas como diagnóstico."},
{"slug":"who-growth","version":"WHO-2006-2007","title":"Crescimento infantil e adolescente","source":"WHO Child Growth Standards 2006; WHO Growth Reference 2007","target":"0-19 anos","content":"Usar z-score por sexo e idade; interpretar conjuntamente peso/idade, estatura/idade, IMC/idade e, até 5 anos, peso/comprimento ou altura quando aplicável."},
]
def seed(repo):
    for p in DEFAULT_PROTOCOLS: repo.save(p["slug"],p["version"],p["title"],p["source"],p["target"],p["content"])
