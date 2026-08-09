"""
dri.py - Valores de referência de ingestão diária (DRI/RDA - Institute of Medicine)
para os micronutrientes presentes na base TACO, usados para comparar o total do
plano alimentar com a recomendação do paciente.

Simplificação: valores para adultos (19-50 anos e 51+), por sexo. Não cobre
gestantes/lactantes nem crianças/adolescentes - se precisar desses grupos,
me avise que adiciono as faixas específicas.

Unidades: mg para todos, exceto quando indicado (compatível com as colunas da TACO).
"""

DRI_ADULTO = {
    "M": {
        "19-50": {
            "calcio": 1000, "magnesio": 400, "fosforo": 700, "ferro": 8, "sodio": 1500,
            "potassio": 3400, "cobre": 0.9, "zinco": 11, "tiamina": 1.2, "riboflavina": 1.3,
            "piridoxina": 1.3, "niacina": 16, "vitamina_c": 90,
        },
        "51+": {
            "calcio": 1200, "magnesio": 420, "fosforo": 700, "ferro": 8, "sodio": 1500,
            "potassio": 3400, "cobre": 0.9, "zinco": 11, "tiamina": 1.2, "riboflavina": 1.3,
            "piridoxina": 1.7, "niacina": 16, "vitamina_c": 90,
        },
    },
    "F": {
        "19-50": {
            "calcio": 1000, "magnesio": 310, "fosforo": 700, "ferro": 18, "sodio": 1500,
            "potassio": 2600, "cobre": 0.9, "zinco": 8, "tiamina": 1.1, "riboflavina": 1.1,
            "piridoxina": 1.3, "niacina": 14, "vitamina_c": 75,
        },
        "51+": {
            "calcio": 1200, "magnesio": 320, "fosforo": 700, "ferro": 8, "sodio": 1500,
            "potassio": 2600, "cobre": 0.9, "zinco": 8, "tiamina": 1.1, "riboflavina": 1.1,
            "piridoxina": 1.5, "niacina": 14, "vitamina_c": 75,
        },
    },
}

NOMES_NUTRIENTES = {
    "calcio": "Cálcio (mg)", "magnesio": "Magnésio (mg)", "fosforo": "Fósforo (mg)",
    "ferro": "Ferro (mg)", "sodio": "Sódio (mg)", "potassio": "Potássio (mg)",
    "cobre": "Cobre (mg)", "zinco": "Zinco (mg)", "tiamina": "Tiamina/B1 (mg)",
    "riboflavina": "Riboflavina/B2 (mg)", "piridoxina": "Piridoxina/B6 (mg)",
    "niacina": "Niacina (mg)", "vitamina_c": "Vitamina C (mg)",
}


def get_dri(sexo, idade):
    faixa = "19-50" if idade < 51 else "51+"
    return DRI_ADULTO[sexo][faixa]


def comparar_com_dri(totais_micro: dict, sexo, idade):
    """
    Recebe um dict {nutriente: valor_total_no_plano} e devolve uma lista de
    tuplas (nome_amigavel, valor_total, valor_dri, percentual, alerta_bool)
    ordenada colocando os nutrientes com maior déficit primeiro.
    """
    dri = get_dri(sexo, idade)
    linhas = []
    for chave, meta in dri.items():
        valor = totais_micro.get(chave, 0) or 0
        pct = (valor / meta * 100) if meta else 0
        alerta = pct < 70
        linhas.append((NOMES_NUTRIENTES[chave], valor, meta, pct, alerta))
    linhas.sort(key=lambda x: x[3])
    return linhas
