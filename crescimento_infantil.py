"""
crescimento_infantil.py - Referência simplificada de crescimento (peso/altura por
idade), baseada nos valores medianos (P50) dos Padrões de Crescimento Infantil da
OMS (2006/2007), adotados pela Sociedade Brasileira de Pediatria.

IMPORTANTE - LIMITAÇÃO CONHECIDA: esta é uma aproximação para triagem rápida em
consultório, usando apenas a mediana (P50) e uma faixa aproximada de normalidade
(±2 desvios-padrão estimados por um coeficiente de variação típico). Ela NÃO
substitui o gráfico oficial da OMS/SBP com curvas LMS reais, que devem ser usados
para diagnóstico formal de desnutrição, baixa estatura ou obesidade infantil.
"""

# idade em meses -> peso mediano (kg)
PESO_P50_MESES = {
    "M": {0: 3.3, 3: 6.4, 6: 7.9, 9: 8.9, 12: 9.6, 18: 10.9, 24: 12.2,
          36: 14.3, 48: 16.3, 60: 18.3, 72: 20.5, 96: 25.4, 120: 31.2,
          144: 37.9, 168: 47.5, 192: 56.0, 216: 62.0},
    "F": {0: 3.2, 3: 5.8, 6: 7.3, 9: 8.2, 12: 8.9, 18: 10.2, 24: 11.5,
          36: 13.9, 48: 15.9, 60: 18.0, 72: 20.2, 96: 25.0, 120: 31.9,
          144: 39.9, 168: 47.6, 192: 52.9, 216: 54.4},
}

# idade em meses -> altura/estatura mediana (cm)
ALTURA_P50_MESES = {
    "M": {0: 49.9, 3: 61.4, 6: 67.6, 9: 72.0, 12: 75.7, 18: 82.3, 24: 87.1,
          36: 96.1, 48: 103.3, 60: 110.0, 72: 116.0, 96: 127.3, 120: 137.8,
          144: 149.1, 168: 163.5, 192: 171.5, 216: 175.2},
    "F": {0: 49.1, 3: 59.8, 6: 65.7, 9: 70.1, 12: 74.0, 18: 80.7, 24: 85.7,
          36: 95.1, 48: 102.7, 60: 109.4, 72: 115.1, 96: 126.6, 120: 138.6,
          144: 151.2, 168: 159.7, 192: 162.5, 216: 163.1},
}

CV_PESO = 0.14    # coeficiente de variação aproximado para peso
CV_ALTURA = 0.045  # coeficiente de variação aproximado para altura/estatura


def _interpolar(tabela, sexo, idade_meses):
    pontos = sorted(tabela[sexo].keys())
    idade_meses = max(pontos[0], min(pontos[-1], idade_meses))
    for i in range(len(pontos) - 1):
        a, b = pontos[i], pontos[i + 1]
        if a <= idade_meses <= b:
            va, vb = tabela[sexo][a], tabela[sexo][b]
            if b == a:
                return va
            frac = (idade_meses - a) / (b - a)
            return va + (vb - va) * frac
    return tabela[sexo][pontos[-1]]


def avaliar_peso(sexo, idade_meses, peso_kg):
    p50 = _interpolar(PESO_P50_MESES, sexo, idade_meses)
    return _classificar(peso_kg, p50, CV_PESO)


def avaliar_altura(sexo, idade_meses, altura_cm):
    p50 = _interpolar(ALTURA_P50_MESES, sexo, idade_meses)
    return _classificar(altura_cm, p50, CV_ALTURA)


def _classificar(valor, p50, cv):
    dp = p50 * cv
    p3 = p50 - 1.88 * dp
    p97 = p50 + 1.88 * dp
    if valor < p3:
        status = "Abaixo do esperado (< P3 aprox.)"
    elif valor > p97:
        status = "Acima do esperado (> P97 aprox.)"
    else:
        status = "Dentro da faixa esperada (P3-P97 aprox.)"
    return {"p50": p50, "p3_aprox": p3, "p97_aprox": p97, "status": status}
