"""
guidelines.py - Resumos de diretrizes nutricionais para as principais doenças
crônicas atendidas em consultório. São sínteses educacionais para consulta
rápida, elaboradas a partir de diretrizes brasileiras e internacionais.
NÃO substituem a leitura das diretrizes originais nem o julgamento clínico
individualizado - use como ponto de partida, não como prescrição pronta.
"""

DOENCAS = [
    {
        "nome": "Diabetes Mellitus Tipo 2",
        "fonte": "Diretriz da Sociedade Brasileira de Diabetes (SBD), ed. 2023-2025",
        "pontos": [
            "Priorizar carboidratos de baixo índice glicêmico, integrais e minimamente processados; reduzir refinados e açúcares adicionados.",
            "Fibras: mínimo de 14g a cada 1000 kcal ingeridas (mesmo parâmetro adotado pela ADA). No pré-diabetes, a SBD recomenda 25-30g de fibra/dia.",
            "Redução de carboidratos totais pode ser considerada para melhora do controle glicêmico, de forma individualizada (não é consenso obrigatório).",
            "Distribuir carboidratos ao longo do dia evita picos glicêmicos; associar sempre a fontes de fibra, proteína ou gordura na mesma refeição.",
            "Monitorar necessidade de ajuste com a equipe médica ao alterar padrão de carboidratos, por risco de hipoglicemia em pacientes em uso de insulina/secretagogos.",
        ],
    },
    {
        "nome": "Hipertensão Arterial Sistêmica",
        "fonte": "Diretrizes Brasileiras de Hipertensão Arterial - 2020 (Sociedade Brasileira de Cardiologia)",
        "pontos": [
            "Sódio: limitar a aproximadamente 2g/dia (equivalente a ~5g de sal de cozinha/dia).",
            "Padrão alimentar DASH (rico em frutas, vegetais, grãos integrais, laticínios magros; pobre em gordura saturada) reduz PA sistólica e diastólica de forma consistente.",
            "Potássio, magnésio e cálcio da dieta (não de suplemento isolado) têm papel protetor - hortaliças, leguminosas e frutas são as principais fontes.",
            "Cerca de 80% do sódio consumido pelo brasileiro vem de alimentos processados/industrializados, não do sal adicionado à mesa - orientar leitura de rótulos.",
            "Controle de peso e redução do consumo de álcool são medidas não farmacológicas de grau de recomendação I.",
        ],
    },
    {
        "nome": "Dislipidemia",
        "fonte": "Princípios gerais de terapia nutricional (Diretriz Brasileira de Dislipidemias/SBC e literatura consolidada)",
        "pontos": [
            "Gordura saturada: manter abaixo de 7% do VET; eliminar/minimizar gordura trans (industrializados, frituras de repetição).",
            "Priorizar gorduras insaturadas: azeite, oleaginosas, peixes de água fria (ômega-3).",
            "Fibras solúveis (aveia, leguminosas, frutas cítricas): 25-30g/dia, ajudam a reduzir LDL.",
            "Fitosteróis/estanois vegetais podem ser considerados como estratégia adjuvante.",
            "Perda de peso moderada (5-10%) já melhora o perfil lipídico em pacientes com sobrepeso/obesidade.",
        ],
    },
    {
        "nome": "Doença Renal Crônica (não dialítica)",
        "fonte": "Princípios gerais KDOQI / Diretrizes SBN - individualizar sempre com o nefrologista",
        "pontos": [
            "Proteína: geralmente restrita a 0,6-0,8 g/kg/dia em estágios avançados não dialíticos, para reduzir sobrecarga renal - decisão conjunta com nefrologista, nunca isolada.",
            "Sódio: tipicamente limitado a 1,5-2g/dia para controle de PA e edema.",
            "Potássio e fósforo: restrição depende do estágio e dos exames laboratoriais - não restringir empiricamente sem dado laboratorial.",
            "Atenção a aditivos fosfatados em alimentos ultraprocessados (fósforo de alta biodisponibilidade).",
            "Adequação calórica é prioridade para evitar catabolismo proteico - déficit calórico agressivo é contraindicado nesse grupo.",
        ],
    },
    {
        "nome": "Obesidade",
        "fonte": "Princípios gerais consolidados de terapia nutricional para perda de peso",
        "pontos": [
            "Déficit calórico individualizado (geralmente 15-25% abaixo do GET) é mais sustentável que déficits agressivos.",
            "Proteína elevada (1,6-2,2 g/kg peso ou meta ajustada) ajuda a preservar massa magra durante o déficit.",
            "Priorizar alimentos com maior saciedade por caloria: fibras, proteína magra, volume de vegetais.",
            "Mudança de comportamento alimentar e atividade física são complementares à dieta, não substitutas.",
            "Evitar restrições extremas sem acompanhamento - risco de efeito rebote e relação disfuncional com comida.",
        ],
    },
    {
        "nome": "Guia Alimentar para a População Brasileira",
        "fonte": "Ministério da Saúde, 2ª edição, 2014 - referência oficial brasileira de alimentação saudável",
        "pontos": [
            "Classifica os alimentos por grau de processamento (in natura/minimamente processados, ingredientes culinários, processados e ultraprocessados) - essa classificação é a base de todo o restante do guia.",
            "Regra central: tornar os alimentos in natura ou minimamente processados a base da alimentação, usando óleos/gorduras/sal/açúcar em pequena quantidade para temperar e cozinhar.",
            "Limitar o uso de alimentos processados (conservas, queijos, pães simples) e evitar ultraprocessados (refrigerantes, embutidos, macarrão instantâneo, salgadinhos, biscoitos recheados).",
            "Comer com regularidade e atenção, em ambientes apropriados, preferencialmente em companhia - a dimensão social e cultural da alimentação é tratada como parte da saúde, não só o nutriente isolado.",
            "Desenvolver e praticar habilidades culinárias, planejar o tempo para preparar refeições, e ao comer fora escolher locais que sirvam refeições feitas na hora em vez de redes de fast-food.",
            "É a referência de escolha para orientação de população geral e prevenção primária, complementar (não substituto) às diretrizes específicas por condição clínica.",
        ],
    },
    {
        "nome": "SIBO (Supercrescimento Bacteriano do Intestino Delgado)",
        "fonte": "Síntese de literatura clínica atual sobre manejo nutricional do SIBO/IMO - American College of Gastroenterology e British Society of Gastroenterology endorsam a Low FODMAP para SII/sintomas sobrepostos",
        "pontos": [
            "A dieta Low FODMAP não trata a causa do SIBO (supercrescimento bacteriano) - ela reduz o substrato fermentável disponível, aliviando sintomas como distensão, gases e dor abdominal enquanto a causa de base é investigada e tratada.",
            "Estrutura em 3 fases: restrição temporária dos FODMAPs (oligo/di/monossacarídeos fermentáveis e polióis), reintrodução gradual para identificar gatilhos individuais, e personalização/manutenção restringindo só o que realmente causa sintoma.",
            "Restrição prolongada sem reintrodução tem risco real: menor diversidade de microbiota e ingestão inadequada de fibras - a fase de restrição deve ser tempo-limitada, não virar padrão permanente.",
            "Monitorar/investigar deficiências associadas ao SIBO crônico, principalmente vitamina B12, vitaminas lipossolúveis, ferro e zinco.",
            "No IMO (supercrescimento metanogênico, predomínio de constipação), cuidado com restrição excessiva de fibras, que pode piorar o trânsito intestinal já lentificado - a abordagem de fibra precisa ser diferente da variante diarreica.",
            "Dieta é medida complementar, não isolada: acompanhamento nutricional especializado é indispensável para equilibrar alívio de sintoma com adequação nutricional.",
        ],
    },
    {
        "nome": "Uso de Análogos de GLP-1 (semaglutida, tirzepatida etc.)",
        "fonte": "Consenso multissocietário \"Prioridades Nutricionais para Apoiar a Terapia com GLP-1 para Obesidade\" (maio/2025); diretriz global da OMS sobre uso de GLP-1 no tratamento da obesidade (dez/2025)",
        "pontos": [
            "Proteína: 1,2-1,6 g/kg de peso corporal ideal/dia - bem acima da recomendação padrão (0,8g/kg), para reduzir o risco de perda de massa magra associada à queda acentuada de apetite e ingestão.",
            "Priorizar refeições menores e mais frequentes, nutricionalmente densas: como o volume alimentar tolerado cai bastante, cada refeição precisa concentrar mais proteína e micronutrientes por caloria.",
            "Perda de peso muito rápida (acima de 1 a 1,5 kg/semana) está associada a maior perda de massa magra - nesses casos, considerar individualizar a meta ou a velocidade de escalonamento da dose junto à equipe médica.",
            "Efeitos colaterais gastrointestinais (náusea, saciedade precoce, esvaziamento gástrico lento) são o principal fator limitando a ingestão - ajustar consistência, volume e fracionamento das refeições ajuda na adesão.",
            "Treinamento resistido associado preserva massa magra de forma consistente nos estudos - reforçar com o paciente que exercício não é opcional nesse contexto, é parte da eficácia do tratamento.",
            "Avaliar risco de ingestão calórica excessivamente baixa (relatos de pacientes caindo abaixo de 800kcal/dia sem orientação) - isso acelera perda muscular e pode indicar necessidade de ajuste de conduta com a equipe médica.",
            "O nutricionista não prescreve o medicamento, mas tem papel central na segurança nutricional do tratamento - abordagem multidisciplinar (endocrinologista/nutricionista/educador físico) é o padrão recomendado.",
        ],
    },
]


def listar_nomes():
    return [d["nome"] for d in DOENCAS]


def get_doenca(nome):
    return next((d for d in DOENCAS if d["nome"] == nome), None)
