"""
formulas.py - Fórmulas de avaliação antropométrica e gasto energético.

Fontes:
- Composição corporal: Jackson & Pollock (1978/1980), Durnin & Womersley (1974),
  Siri (1961), Brozek (1963), Deurenberg (1991)
- Gasto energético: Mifflin-St Jeor (1990), Harris-Benedict revisada (1984),
  Katch-McArdle, Cunningham (1980)
  [validação comparativa: Frankenfield et al., 2005, J Am Diet Assoc]
"""

import math


def siri(densidade):
    return (4.95 / densidade - 4.50) * 100


def brozek(densidade):
    return (4.57 / densidade - 4.142) * 100


def jp7(soma7, idade, sexo):
    if sexo == "M":
        return 1.112 - 0.00043499 * soma7 + 0.00000055 * soma7 ** 2 - 0.00028826 * idade
    else:
        return 1.097 - 0.00046971 * soma7 + 0.00000056 * soma7 ** 2 - 0.00012828 * idade


def jp3(soma3, idade, sexo):
    # Homens: peitoral + abdominal + coxa | Mulheres: tríceps + suprailíaca + coxa
    if sexo == "M":
        return 1.10938 - 0.0008267 * soma3 + 0.0000016 * soma3 ** 2 - 0.0002574 * idade
    else:
        return 1.0994921 - 0.0009929 * soma3 + 0.0000023 * soma3 ** 2 - 0.0001392 * idade


def durnin_womersley(soma4, idade, sexo):
    # soma4 = bíceps + tríceps + subescapular + suprailíaca
    tabela = {
        "M": [(19, 1.1620, 0.0630), (29, 1.1631, 0.0632), (39, 1.1422, 0.0544),
              (49, 1.1620, 0.0700), (200, 1.1715, 0.0779)],
        "F": [(19, 1.1549, 0.0678), (29, 1.1599, 0.0717), (39, 1.1423, 0.0632),
              (49, 1.1333, 0.0612), (200, 1.1339, 0.0645)],
    }
    for limite, c, m in tabela[sexo]:
        if idade <= limite:
            return c - m * math.log10(soma4)
    return None


def deurenberg(imc, idade, sexo):
    s = 1 if sexo == "M" else 0
    return (1.20 * imc) + (0.23 * idade) - (10.8 * s) - 5.4


def petroski4(soma4, idade, sexo, peso=None, altura_cm=None):
    """
    Petroski (1995) - equação de 4 dobras, validada para população brasileira.
    Homens: subescapular + tríceps + suprailíaca + panturrilha medial
    Mulheres: axilar média + suprailíaca + coxa + panturrilha medial (requer peso e altura)
    Fonte dos coeficientes: Petroski EL. Antropometria: técnicas e padronizações;
    conferido em calculadora especializada (medesportepapers.com.br/calculadoras/petroski-4-dobras),
    2026. Recomenda-se validar os coeficientes com a tese original antes de uso clínico extensivo.
    """
    if sexo == "M":
        return (1.10726863 - 0.00081201 * soma4 + 0.00000212 * soma4 ** 2
                - 0.00041761 * idade)
    else:
        if peso is None or altura_cm is None:
            return None
        return (1.03465850 - 0.00063129 * soma4 ** 2 - 0.000311 * idade
                - 0.00048890 * peso + 0.00051345 * altura_cm)


def tmb_mifflin(peso, altura_cm, idade, sexo):
    base = 10 * peso + 6.25 * altura_cm - 5 * idade
    return base + 5 if sexo == "M" else base - 161


def tmb_harris_benedict(peso, altura_cm, idade, sexo):
    if sexo == "M":
        return 88.362 + 13.397 * peso + 4.799 * altura_cm - 5.677 * idade
    else:
        return 447.593 + 9.247 * peso + 3.098 * altura_cm - 4.330 * idade


def tmb_katch_mcardle(massa_magra_kg):
    return 370 + 21.6 * massa_magra_kg


def tmb_cunningham(massa_magra_kg):
    return 500 + 22 * massa_magra_kg


FATORES_ATIVIDADE = {
    "Sedentário": 1.2,
    "Levemente ativo": 1.375,
    "Moderadamente ativo": 1.55,
    "Muito ativo": 1.725,
    "Extremamente ativo": 1.9,
}


def calcular_avaliacao_completa(sexo, idade, peso, altura_cm, dobras: dict,
                                 formula_tmb, atividade, ajuste_pct, ptn_gkg, lip_pct,
                                 bia_pg=None):
    """
    Recebe os dados brutos e devolve um dicionário com todos os resultados
    calculados (composição corporal, TMB, GET, VET, macros).
    dobras: dict com chaves triceps, biceps, subescapular, suprailiaca,
            abdominal, coxa, peitoral, axilar, panturrilha (valores em mm ou None)
    bia_pg: % de gordura medido por bioimpedância, se o usuário tiver o aparelho (opcional)
    """
    altura_m = altura_cm / 100
    imc = peso / (altura_m ** 2)

    d = dobras
    resultados_pg = {}

    if all(d.get(k) is not None for k in ["peitoral", "axilar", "triceps", "subescapular",
                                           "abdominal", "suprailiaca", "coxa"]):
        soma7 = sum(d[k] for k in ["peitoral", "axilar", "triceps", "subescapular",
                                    "abdominal", "suprailiaca", "coxa"])
        dens = jp7(soma7, idade, sexo)
        resultados_pg["Jackson & Pollock 7 dobras"] = siri(dens)

    if sexo == "M" and all(d.get(k) is not None for k in ["peitoral", "abdominal", "coxa"]):
        soma3 = d["peitoral"] + d["abdominal"] + d["coxa"]
        dens = jp3(soma3, idade, sexo)
        resultados_pg["Jackson & Pollock 3 dobras"] = siri(dens)
    elif sexo == "F" and all(d.get(k) is not None for k in ["triceps", "suprailiaca", "coxa"]):
        soma3 = d["triceps"] + d["suprailiaca"] + d["coxa"]
        dens = jp3(soma3, idade, sexo)
        resultados_pg["Jackson & Pollock 3 dobras"] = siri(dens)

    if all(d.get(k) is not None for k in ["biceps", "triceps", "subescapular", "suprailiaca"]):
        soma4 = d["biceps"] + d["triceps"] + d["subescapular"] + d["suprailiaca"]
        dens = durnin_womersley(soma4, idade, sexo)
        if dens:
            resultados_pg["Durnin & Womersley"] = brozek(dens)

    if sexo == "M" and all(d.get(k) is not None for k in ["subescapular", "triceps", "suprailiaca", "panturrilha"]):
        soma4p = d["subescapular"] + d["triceps"] + d["suprailiaca"] + d["panturrilha"]
        dens = petroski4(soma4p, idade, sexo)
        if dens:
            resultados_pg["Petroski 4 dobras (BR)"] = siri(dens)
    elif sexo == "F" and all(d.get(k) is not None for k in ["axilar", "suprailiaca", "coxa", "panturrilha"]):
        soma4p = d["axilar"] + d["suprailiaca"] + d["coxa"] + d["panturrilha"]
        dens = petroski4(soma4p, idade, sexo, peso=peso, altura_cm=altura_cm)
        if dens:
            resultados_pg["Petroski 4 dobras (BR)"] = siri(dens)

    resultados_pg["Deurenberg (estimativa por IMC)"] = deurenberg(imc, idade, sexo)

    if bia_pg is not None:
        resultados_pg["Bioimpedância (informado)"] = bia_pg

    metodos_dobras = {k: v for k, v in resultados_pg.items()
                       if "Deurenberg" not in k and "Bioimpedância" not in k}
    if bia_pg is not None:
        pg_final = bia_pg
        origem_pg = "Bioimpedância (valor informado pelo aparelho)"
    elif metodos_dobras:
        pg_final = sum(metodos_dobras.values()) / len(metodos_dobras)
        origem_pg = f"média de {len(metodos_dobras)} método(s) com dobras"
    else:
        pg_final = resultados_pg["Deurenberg (estimativa por IMC)"]
        origem_pg = "Deurenberg (nenhuma dobra completa preenchida)"

    massa_gorda = peso * pg_final / 100
    massa_magra = peso - massa_gorda

    if formula_tmb == "Mifflin-St Jeor":
        tmb = tmb_mifflin(peso, altura_cm, idade, sexo)
    elif formula_tmb == "Harris-Benedict":
        tmb = tmb_harris_benedict(peso, altura_cm, idade, sexo)
    elif formula_tmb == "Katch-McArdle":
        tmb = tmb_katch_mcardle(massa_magra)
    else:
        tmb = tmb_cunningham(massa_magra)

    fator = FATORES_ATIVIDADE[atividade]
    get_total = tmb * fator
    vet = get_total * (1 + ajuste_pct / 100)

    ptn_g = ptn_gkg * peso
    ptn_kcal = ptn_g * 4
    lip_kcal = vet * (lip_pct / 100)
    lip_g = lip_kcal / 9
    cho_kcal = vet - ptn_kcal - lip_kcal
    cho_g = cho_kcal / 4

    return {
        "imc": imc,
        "resultados_pg": resultados_pg,
        "pg_final": pg_final,
        "origem_pg": origem_pg,
        "massa_gorda": massa_gorda,
        "massa_magra": massa_magra,
        "tmb": tmb,
        "fator_atividade": fator,
        "get_total": get_total,
        "vet": vet,
        "ptn_g": ptn_g,
        "ptn_kcal": ptn_kcal,
        "lip_g": lip_g,
        "lip_kcal": lip_kcal,
        "cho_g": cho_g,
        "cho_kcal": cho_kcal,
    }
