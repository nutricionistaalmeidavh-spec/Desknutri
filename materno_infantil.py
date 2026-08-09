"""
materno_infantil.py - Referências de DRI para gestação/lactação e a
calculadora de ganho de peso gestacional recomendado (IOM, 2009 - ainda a
referência internacional mais usada na prática clínica).
"""

# Ganho de peso gestacional total recomendado, por categoria de IMC pré-gestacional
# Fonte: Institute of Medicine (IOM), 2009 - referência adotada pelo Ministério da Saúde/BR
FAIXAS_GANHO_PESO = [
    ("Baixo peso (IMC < 18,5)", 12.5, 18.0),
    ("Peso adequado (IMC 18,5-24,9)", 11.5, 16.0),
    ("Sobrepeso (IMC 25,0-29,9)", 7.0, 11.5),
    ("Obesidade (IMC ≥ 30,0)", 5.0, 9.0),
]


def faixa_ganho_peso(imc_pre_gestacional):
    if imc_pre_gestacional < 18.5:
        return FAIXAS_GANHO_PESO[0]
    elif imc_pre_gestacional < 25.0:
        return FAIXAS_GANHO_PESO[1]
    elif imc_pre_gestacional < 30.0:
        return FAIXAS_GANHO_PESO[2]
    else:
        return FAIXAS_GANHO_PESO[3]


# Incrementos de energia e alguns micronutrientes-chave na gestação/lactação
# (acréscimos sobre a necessidade da mulher adulta não-gestante; valores de
# referência DRI/IOM amplamente usados na prática clínica)
INCREMENTOS = {
    "Gestação - 1º trimestre": {"kcal": 0, "proteina_g_dia_extra": 1, "ferro_mg": 27, "acido_folico_mcg": 600, "calcio_mg": 1000},
    "Gestação - 2º trimestre": {"kcal": 340, "proteina_g_dia_extra": 10, "ferro_mg": 27, "acido_folico_mcg": 600, "calcio_mg": 1000},
    "Gestação - 3º trimestre": {"kcal": 452, "proteina_g_dia_extra": 25, "ferro_mg": 27, "acido_folico_mcg": 600, "calcio_mg": 1000},
    "Lactação (0-6 meses)": {"kcal": 500, "proteina_g_dia_extra": 25, "ferro_mg": 9, "acido_folico_mcg": 500, "calcio_mg": 1000},
}

PONTOS_CHAVE = [
    "Ácido fólico: suplementação de 400-600 mcg/dia idealmente iniciada antes da concepção, para prevenção de defeitos de tubo neural.",
    "Ferro: necessidade aumenta significativamente na gestação (DRI de 27mg/dia); triagem de anemia é rotina no pré-natal.",
    "Cálcio: manter 1000mg/dia; se ingestão dietética for baixa, considerar suplementação conforme orientação médica.",
    "Ganho de peso gestacional deve ser monitorado por trimestre, não só no total - ganho muito rápido ou insuficiente merece reavaliação.",
    "Evitar: álcool (sem nível seguro estabelecido), peixes com alto teor de mercúrio (ex: tubarão, espadarte) em excesso, embutidos/frios malconservados e queijos não pasteurizados (risco de listeria).",
    "Aleitamento materno exclusivo é recomendado até os 6 meses (OMS), com necessidade calórica e proteica elevada da lactante durante esse período.",
    "Cafeína: manter abaixo de ~200mg/dia na gestação (aprox. 1-2 xícaras de café) é a orientação mais adotada na prática.",
]


def calcular_incremento(fase):
    return INCREMENTOS.get(fase)
