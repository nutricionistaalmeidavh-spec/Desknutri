"""
content_seed.py - Popula o banco com receitas e planos alimentares modelo
prontos, usando alimentos reais da base TACO. Roda uma única vez (na primeira
inicialização) a partir de database.init_db().
"""


def _achar_alimento(conn, termo_exato):
    """Busca um alimento pela descrição (aceita prefixo/trecho único)."""
    row = conn.execute("SELECT id FROM alimentos WHERE descricao = ?", (termo_exato,)).fetchone()
    if row:
        return row["id"]
    row = conn.execute("SELECT id FROM alimentos WHERE descricao LIKE ? LIMIT 1", (f"%{termo_exato}%",)).fetchone()
    return row["id"] if row else None


RECEITAS = [
    {
        "nome": "Omelete de claras com espinafre",
        "categoria": "Café da manhã",
        "tags": "low carb, hiperproteico",
        "porcoes": 1,
        "modo_preparo": ("Refogue o espinafre rapidamente numa frigideira antiaderente com o azeite. "
                          "Bata as claras levemente com sal a gosto, despeje sobre o espinafre e "
                          "cozinhe em fogo baixo até firmar. Dobre ao meio e sirva."),
        "ingredientes": [("Ovo, de galinha, clara, cozida/10minutos", 100),
                          ("Espinafre, Nova Zelândia, refogado", 50),
                          ("Azeite, de oliva, extra virgem", 5)],
    },
    {
        "nome": "Frango grelhado com batata-doce e brócolis",
        "categoria": "Almoço/Jantar",
        "tags": "hipertrofia, low carb moderado",
        "porcoes": 1,
        "modo_preparo": ("Tempere o peito de frango e grelhe até dourar dos dois lados. "
                          "Cozinhe a batata-doce em cubos até ficar macia. Cozinhe o brócolis "
                          "no vapor por 5 minutos. Monte o prato e finalize com fio de azeite."),
        "ingredientes": [("Frango, peito, sem pele, cozido", 120),
                          ("Batata, doce, cozida", 150),
                          ("Brócolis, cozido", 100),
                          ("Azeite, de oliva, extra virgem", 5)],
    },
    {
        "nome": "Salada de grão-de-bico com legumes",
        "categoria": "Almoço",
        "tags": "vegetariano, fibras, diabetes",
        "porcoes": 1,
        "modo_preparo": ("Deixe o grão-de-bico de molho na véspera e cozinhe até ficar macio. "
                          "Misture com o tomate picado e a alface. Tempere com azeite, limão e sal."),
        "ingredientes": [("Grão-de-bico, cru", 60),
                          ("Tomate, salada", 80),
                          ("Alface, crespa, crua", 30),
                          ("Azeite, de oliva, extra virgem", 5)],
    },
    {
        "nome": "Panqueca de banana com aveia",
        "categoria": "Café da manhã",
        "tags": "pré-treino, fibras",
        "porcoes": 1,
        "modo_preparo": ("Amasse a banana, misture com o ovo e a aveia até formar uma massa homogênea. "
                          "Despeje em frigideira antiaderente quente e doure dos dois lados."),
        "ingredientes": [("Banana, nanica, crua", 100),
                          ("Aveia, flocos, crua", 30),
                          ("Ovo, de galinha, inteiro, cru", 50)],
    },
    {
        "nome": "Sopa de legumes com lentilha",
        "categoria": "Jantar",
        "tags": "baixo sódio, fibras, digestão leve",
        "porcoes": 1,
        "modo_preparo": ("Cozinhe a lentilha até ficar macia. Adicione a cenoura, a abobrinha e o "
                          "tomate picados, e cozinhe por mais 10 minutos. Tempere com ervas a gosto "
                          "(evite excesso de sal)."),
        "ingredientes": [("Lentilha, cozida", 100),
                          ("Cenoura, cozida", 50),
                          ("Abobrinha, italiana, cozida", 50),
                          ("Tomate, salada", 50)],
    },
    {
        "nome": "Bowl de iogurte com aveia e banana",
        "categoria": "Lanche",
        "tags": "rápido, cálcio, fibras",
        "porcoes": 1,
        "modo_preparo": "Misture o iogurte com a aveia e finalize com a banana fatiada por cima.",
        "ingredientes": [("Iogurte, natural, desnatado", 150),
                          ("Aveia, flocos, crua", 20),
                          ("Banana, nanica, crua", 80)],
    },
]

PLANOS_MODELO = [
    {
        "nome": "Emagrecimento - déficit moderado",
        "categoria": "Emagrecimento",
        "vet_alvo": 1500,
        "descricao": "Ponto de partida para pacientes em déficit calórico moderado. Ajuste porções conforme o VET calculado na avaliação.",
        "itens": [
            ("Café da manhã", "Ovo, de galinha, clara, cozida/10minutos", 100),
            ("Café da manhã", "Pão, trigo, forma, integral", 50),
            ("Lanche da manhã", "Maçã, Fuji, com casca, crua", 130),
            ("Almoço", "Frango, peito, sem pele, cozido", 120),
            ("Almoço", "Arroz, integral, cozido", 100),
            ("Almoço", "Brócolis, cozido", 100),
            ("Almoço", "Alface, crespa, crua", 30),
            ("Lanche da tarde", "Iogurte, natural, desnatado", 170),
            ("Jantar", "Frango, peito, sem pele, cozido", 100),
            ("Jantar", "Batata, doce, cozida", 100),
            ("Jantar", "Abobrinha, italiana, cozida", 80),
        ],
    },
    {
        "nome": "Manutenção de peso",
        "categoria": "Manutenção",
        "vet_alvo": 2000,
        "descricao": "Distribuição equilibrada para pacientes eutróficos sem objetivo de perda/ganho.",
        "itens": [
            ("Café da manhã", "Ovo, de galinha, inteiro, cozido/10minutos", 100),
            ("Café da manhã", "Pão, trigo, forma, integral", 60),
            ("Lanche da manhã", "Banana, nanica, crua", 100),
            ("Almoço", "Frango, peito, sem pele, cozido", 130),
            ("Almoço", "Arroz, integral, cozido", 150),
            ("Almoço", "Feijão, carioca, cozido", 100),
            ("Almoço", "Alface, crespa, crua", 40),
            ("Lanche da tarde", "Iogurte, natural", 170),
            ("Lanche da tarde", "Aveia, flocos, crua", 20),
            ("Jantar", "Carne, bovina, peito, sem gordura, cozido", 120),
            ("Jantar", "Batata, doce, cozida", 130),
            ("Jantar", "Cenoura, cozida", 60),
        ],
    },
    {
        "nome": "Hipertrofia - superávit calórico",
        "categoria": "Hipertrofia",
        "vet_alvo": 2800,
        "descricao": "Base para pacientes em treino de força buscando ganho de massa magra, com proteína elevada.",
        "itens": [
            ("Café da manhã", "Ovo, de galinha, inteiro, cozido/10minutos", 150),
            ("Café da manhã", "Pão, trigo, forma, integral", 80),
            ("Café da manhã", "Aveia, flocos, crua", 40),
            ("Lanche da manhã", "Banana, nanica, crua", 120),
            ("Lanche da manhã", "Castanha-do-Brasil, crua", 20),
            ("Almoço", "Frango, peito, sem pele, cozido", 180),
            ("Almoço", "Arroz, integral, cozido", 200),
            ("Almoço", "Feijão, carioca, cozido", 130),
            ("Lanche da tarde", "Iogurte, natural", 200),
            ("Lanche da tarde", "Aveia, flocos, crua", 30),
            ("Jantar", "Carne, bovina, peito, sem gordura, cozido", 180),
            ("Jantar", "Batata, doce, cozida", 200),
            ("Jantar", "Brócolis, cozido", 100),
        ],
    },
    {
        "nome": "Hipertensão - baixo sódio",
        "categoria": "Doenças crônicas",
        "vet_alvo": 1800,
        "descricao": ("Baseado nos princípios da dieta DASH: rica em potássio/magnésio/cálcio "
                      "(vegetais, frutas, laticínios magros), sódio controlado. Evitar itens "
                      "industrializados/embutidos ao montar o plano real do paciente."),
        "itens": [
            ("Café da manhã", "Ovo, de galinha, inteiro, cozido/10minutos", 100),
            ("Café da manhã", "Pão, trigo, forma, integral", 50),
            ("Lanche da manhã", "Banana, nanica, crua", 100),
            ("Almoço", "Frango, peito, sem pele, cozido", 120),
            ("Almoço", "Arroz, integral, cozido", 120),
            ("Almoço", "Feijão, carioca, cozido", 100),
            ("Almoço", "Cenoura, crua", 50),
            ("Lanche da tarde", "Iogurte, natural, desnatado", 170),
            ("Jantar", "Frango, peito, sem pele, cozido", 100),
            ("Jantar", "Batata, doce, cozida", 130),
            ("Jantar", "Abobrinha, italiana, cozida", 80),
        ],
    },
    {
        "nome": "Diabetes - baixo índice glicêmico",
        "categoria": "Doenças crônicas",
        "vet_alvo": 1800,
        "descricao": ("Prioriza carboidratos integrais e fibrosos, distribuídos ao longo do dia. "
                      "Referência: SBD recomenda mínimo de 14g de fibra a cada 1000kcal e "
                      "priorização de carboidratos de baixo índice glicêmico."),
        "itens": [
            ("Café da manhã", "Ovo, de galinha, inteiro, cozido/10minutos", 100),
            ("Café da manhã", "Aveia, flocos, crua", 30),
            ("Lanche da manhã", "Maçã, Fuji, com casca, crua", 130),
            ("Almoço", "Frango, peito, sem pele, cozido", 120),
            ("Almoço", "Arroz, integral, cozido", 100),
            ("Almoço", "Feijão, carioca, cozido", 100),
            ("Almoço", "Brócolis, cozido", 100),
            ("Lanche da tarde", "Iogurte, natural, desnatado", 170),
            ("Jantar", "Lentilha, cozida", 100),
            ("Jantar", "Abobrinha, italiana, cozida", 80),
            ("Jantar", "Cenoura, cozida", 60),
        ],
    },
]


ANAMNESES = [
    {
        "nome": "Anamnese - Adulto",
        "conteudo": """FICHA DE ANAMNESE - ADULTO

1. Identificação do paciente
Nome: _______________________________________  Data de Nascimento: ___/___/___
Nome social: _________________________________  Idade: _____  Sexo: F ( ) M ( )
Estado civil: _______________________________  Data da primeira consulta: ___/___/___
Objetivo da consulta nutricional: ___________________________________________________
_____________________________________________________________________________

2. Dados Socioeconômicos
Renda: ____________  Nº de pessoas na casa: ____________
Cidade/Estado: _______________________  Bairro: _______________________
Zona: Urbana ( )  Rural ( )
Moradia: ( ) Alugada ( ) Própria ( ) Casa ( ) Apartamento
Profissão / horário de trabalho: _____________________________________________________
Eletrodomésticos/cozinha: ( )Filtro ( )Fogão ( )Geladeira ( )Microondas ( )Liquidificador
Possui água potável? Sim ( ) Não ( )   Possui esgoto? Sim ( ) Não ( )   Coleta de lixo? Sim ( ) Não ( )

3. Histórico de doenças
Diagnóstico médico de alguma doença: _______________________________________________
Possui alguma doença crônica? Qual/is: _______________________________________________
Faz uso de medicamentos: Sim ( ) Não ( )  Qual: ________________________________________
Interação fármaco-nutriente? _______________________________________________________
Faz uso de suplemento alimentar: Sim ( ) Não ( )  Qual: __________________________________
Fez cirurgia bariátrica? Sim ( ) Não ( )
Histórico de doenças familiares: HAS ( ) Obesidade ( ) DM ( ) Dislipidemias ( ) Neuropatias ( )
Outras: ______________________________________________________________________
Possui alguma alergia alimentar? Sim ( ) Não ( )  Qual: __________________________________
Possui alguma intolerância alimentar? Sim ( ) Não ( )  Qual: ______________________________
Você se considera inquieta(o)? Sim ( ) Não ( )

4. Dados Antropométricos
Peso: __________  Ganho/perda de peso recente (g/%): __________  Altura: __________
IMC: __________
Circunferência da cintura: __________  Circunferência do quadril: __________
Dobra cutânea tricipital: __________  Dobra cutânea bicipital: __________
Dobra cutânea subescapular: __________  Dobra cutânea suprailíaca: __________
Dobra cutânea abdominal: __________  Dobra cutânea da coxa: __________
Dobra cutânea da panturrilha: __________

5. Exame Físico
( ) Anasarca  ( ) Presença de cárie/manchas esbranquiçadas no dente  ( ) Mucosa do olho descorada
( ) Glossite  ( ) Ascite  ( ) Desidratação  ( ) Palidez cutânea
Cabelo: ___________________________  Unhas: ___________________________
Edema: ( )+/4 ( )++/4 ( )+++/4 ( )++++/4
Ganho ou perda de peso foi intencional? Sim ( ) Não ( )

6. Sintomas Gastrointestinais
( ) Vômitos ( ) Náusea ( ) Anorexia ( ) Diarreia (>3 evacuações líquidas/dia)
( ) Constipação ( ) Azia/queimação ( ) Disfagia
Análise da função intestinal - Escala de Bristol (tipo 1 a 7): Qual tipo? __________
Escala de coloração de urina (hidratado / desidratação leve / moderada / grave): Qual coloração? __________
Urina possui odor? Sim ( ) Não ( )

7. Escala de Silhueta (Stunkard et al., 1983)
(A) Silhueta que mais se parece com seu corpo: ____
(B) Silhueta que gostaria de ter: ____
(C) Silhueta que considera um corpo saudável: ____

8. Hábitos de vida
Praticante de atividade física: Sim ( ) Não ( )  Qual: __________  Duração/frequência: __________
Tabagista: Sim ( ) Não ( )  Nº cigarros/dia: ______  Há quanto tempo? __________
Consome bebida alcoólica? Sim ( ) Não ( )  Tipo: __________  Quantidade/frequência: __________
Uso de drogas ilícitas: Sim ( ) Não ( )  Qual/is: __________  Frequência: __________
Dificuldade para dormir: Sim ( ) Não ( )  Horas de sono/dia: ______
Acorda a noite: Sim ( ) Não ( )   Acorda a noite para comer? Sim ( ) Não ( )

9. Hábitos Alimentares
Ingestão hídrica: _______________________________________________________________
Já fez algum tipo de dieta anteriormente? Por quê e foi com acompanhamento profissional? ________
_____________________________________________________________________________
Qual sua relação com a comida e seu corpo? ___________________________________________
Horário que mais come/tem mais fome: ( )manhã ( )tarde ( )noite ( )madrugada
Tempo disponível para as refeições: __________________________________________________
Locais onde costuma fazer as refeições: _______________________________________________
Quem costuma cozinhar: ______________  Quem faz as compras: ______________
Costuma fazer as refeições sozinho(a)? ________________________________________________
Alimentos que mais gosta: _________________________________________________________
Alimentos que não gosta: _________________________________________________________
Humor/sentimentos interferem na alimentação? Sim ( ) Não ( )  Como? ______________________
Gosta de cozinhar? Sim ( ) Não ( )   Tem o hábito de cozinhar? Sim ( ) Não ( )

10. Questionário de Frequência Alimentar
(Registrar quantidade habitual e frequência - mais de 3x/dia, 2-3x/dia, 1x/dia, 5-6x/semana,
2-4x/semana, 1x/semana, 1-3x/mês, nunca ou quase nunca - para os grupos: cereais/farináceos,
leguminosas, hortaliças, frutas, laticínios, carnes/ovos/peixes, doces/frituras/embutidos, bebidas)
Observações: __________________________________________________________________

11. Recordatório Alimentar (24h)
Hora | Refeição | Local da refeição | Alimento/Preparação | Medida caseira
_____________________________________________________________________________
_____________________________________________________________________________
_____________________________________________________________________________

12. Diagnóstico Nutricional
_____________________________________________________________________________
_____________________________________________________________________________

13. Conduta Nutricional
_____________________________________________________________________________
_____________________________________________________________________________

14. Evolução
_____________________________________________________________________________
_____________________________________________________________________________

Referências: STUNKARD, A. J.; SORENSEN, T.; SCHULSINGER, F. Use of the Danish Adoption
Register for the study of obesity and thinness, 1983. ZASLAVSKY, C.; GUERRA, T. C. Escala
Bristol de forma fecal no diagnóstico clínico da constipação, Rev. AMRIGS, 2016. Questionário
de frequência alimentar, Rosely Sichieri.""",
    },
    {
        "nome": "Anamnese - Adolescente",
        "conteudo": """FICHA DE ANAMNESE - ADOLESCENTE

01. Dados de Identificação
Nome/Nome Social: ______________________________________________________________
Idade: __________  Data de nascimento: ___/___/___
Sexo: __________  Naturalidade: __________  Cidade atual: __________
Número/E-mail: ________________________________________________________________
Escolaridade: __________  Religião: __________
Endereço: _____________________________________________________________________
Data da primeira consulta: ___/___/___

02. Avaliação Socioeconômica
Acesso a saneamento básico: ( )Água encanada ( )Água potável ( )Esgoto ( )Coleta de lixo
Frequência de compras: ( )diária ( )semanal ( )mensal
Reside com: ( )pais ( )pais e irmão(s) ( )avós ( )amigos ( )sozinho
Quantidade de pessoas na casa: __________
Eletrodomésticos: ( )Liquidificador ( )Filtro ( )Fogão/Forno ( )Cafeteira ( )Máquina de lavar
( )Sanduicheira/Torradeira ( )Televisão ( )Computador ( )Microondas ( )Telefone/Celular
( )Geladeira ( )Lava-louças ( )Freezer ( )Processador
Renda per capita: ( )<1 salário mínimo ( )1-2 salários ( )2-3 salários ( )>4 salários

03. Histórico familiar (doença / grau de parentesco)
Obesidade: __________  Diabetes: __________  Hipertensão Arterial Sistêmica: __________
Dislipidemias: __________  Câncer: __________  Osteoporose: __________
Disfunção tireoidiana: __________  Constipação Intestinal: __________
Doença Celíaca: __________  Alergia a proteína do leite: __________  Alzheimer: __________

04. Motivo da Consulta / Queixas Principais
_____________________________________________________________________________
Expectativas da consulta: _________________________________________________________

05. Hábitos de vida
Sono: ( )regular ( )irregular  Dorme (horas/dia): __________
Ingestão hídrica: ( )<1 litro/dia ( )1-2 litros/dia ( )>2 litros/dia
Se considera uma pessoa ansiosa: Sim ( ) Não ( )
Bebidas alcoólicas: ( )nunca ( )eventualmente ( )diariamente ( )fins de semana
Fuma: ( )nunca ( )fumante  Média/dia: __________
Uso de drogas ilícitas: Sim ( ) Não ( )
Costume de acordar à noite para se alimentar: Sim ( ) Não ( )

06. História Alimentar
Parte 6.1 - Anamnese
Refeições que realiza: ( )Café da manhã ( )Lanche da manhã ( )Almoço ( )Lanche da tarde
( )Jantar ( )Ceia
Já fez algum tipo de dieta? Sim ( ) Não ( )  Como foi a experiência: __________________
Foi com acompanhamento profissional? Sim ( ) Não ( )
Consome alimento integral? Sim ( ) Não ( )   Gosta de cozinhar? Sim ( ) Não ( )
Usa suplemento esportivo? Sim ( ) Não ( )  Quais: __________________________________
Toma suplemento de vitaminas/minerais? Sim ( ) Não ( )  Qual/is: ___________________
Indicação de: ( )profissional de saúde ( )conta própria
Local onde realiza refeições: __________________________________________________
Preferências alimentares: ___________________________________________________
Aversões alimentares: _____________________________________________________
Intolerâncias alimentares: Sim ( ) Não ( )  Quais: __________________________________
Alergias: Sim ( ) Não ( )  Quais: __________________________________________________
Quem prepara as refeições: __________  Horário de maior apetite: __________
Consome líquido junto com as refeições? Sim ( ) Não ( )  Quais: ______________________

Parte 6.2 - Recordatório 24 horas
Refeição/horário | Alimento | Medida caseira | Local da refeição
_____________________________________________________________________________
_____________________________________________________________________________

Parte 6.3 - Questionário de frequência alimentar (checklist)
(Aplicar questionário de frequência de consumo de alimentos para adolescentes - CNPq/Prato
Virtual - cobrindo tipo de leite, forma de adoçar, uso de azeite/margarina/manteiga, consumo de
frituras, gordura visível das carnes, pele do frango, local das refeições, lanches fora de horário,
uso de vitaminas, e frequência nos últimos 3 meses dos principais grupos alimentares.)

Parte 6.4 - Registro alimentar (a ser entregue ao paciente)
Dia 1 (dia de semana) | Dia 2, não consecutivo (dia de semana) | Dia 3 (fim de semana)
Refeição/horário | Alimento | Medida caseira | Local da refeição

07. Avaliação Antropométrica
Peso atual: __________  Estatura: __________  IMC: __________
Circunferência do braço: __________  Circunferência da cintura: __________
Circunferência do quadril: __________
Dobra cutânea subescapular: __________
Dobras cutâneas tricipital e subescapular (usar equação de Slaughter et al., 1988): __________

08. Avaliação Clínica / Semiologia Nutricional
Ganho de peso recente: Sim ( ) Não ( )  Se sim, foi intencional? Sim ( ) Não ( )
Perda de peso recente: Sim ( ) Não ( )  Se sim, foi intencional? Sim ( ) Não ( )
Diabetes: Sim ( ) Não ( )  Se sim, tipo 1 ( ) tipo 2 ( )  Uso de insulina: __________
Hipertensão: Sim ( ) Não ( )  Há quanto tempo: __________
Utiliza medicamentos: __________

Trato Gastrointestinal
Frequência de evacuações: __________  Gases: Sim ( ) Não ( )
Consistência das fezes - Escala de Bristol (tipo 1 a 7): Qual tipo? __________

Trato Urinário
Frequência urinária: __________
Coloração da urina: amarelo claro ( ) amarelo ( ) âmbar ( ) marrom ( ) vermelho ( )
Odor da urina: forte ( )  ausência de odor ( )

Escala de silhueta (adolescentes)
Número que se identifica: __________  Número que gostaria de apresentar: __________

Exame físico
Hidratação da pele: ( )Desidratada ( )Hidratada   Presença de ferimentos: Sim ( ) Não ( )
Cabelos: ( )Quebradiços ( )Despigmentado ( )Queda
Unhas: ( )Quebradiças ( )Manchadas
Mucosa do olho: ( )Corada ( )Pálida   Palma da mão: ( )Corada ( )Pálida
Edema: Sim ( ) Não ( )  Local: __________
Saúde bucal: ( )Adequada ( )Perda dentária ( )Presença de cáries

Autoavaliação da maturação sexual (Critérios de Tanner, 1962)
Estágio de pelos pubianos e desenvolvimento mamário/genital (registrar estágio 1 a 5 conforme
tabela de referência): __________
Classificação: Pré-púbere / Púbere / Pós-púbere: __________

09. Avaliação do nível de atividade física
Modalidade | Horário | Frequência | Duração | Intensidade
_____________________________________________________________________________

10. Diagnóstico
_____________________________________________________________________________
_____________________________________________________________________________

11. Conduta e evolução
_____________________________________________________________________________
_____________________________________________________________________________

Referências Bibliográficas: MUSSOI, T. D.; BLÜMKE, A. C.; BENEDETTI, F. J. Avaliação
nutricional na prática clínica: da gestação ao envelhecimento. Grupo Gen-Guanabara Koogan,
2000. Duke, P. M. et al. Adolescents' self-assessment of sexual maturation. Pediatrics, 66:918-20,
1980. Tanner, J. M. Growth at Adolescence. 2nd ed. Oxford: Blackwell Scientific Publications,
1962. Dias, M. C. G. et al. Triagem e Avaliação do Estado Nutricional. Projeto Diretrizes. SBNPE,
2011. Araújo MC, Veiga GV, Sichieri R, Pereira RA. Elaboração de questionário de frequência
alimentar semiquantitativo para adolescentes. Rev Nutr 2010;23(2):179-189.""",
    },
]


DIRETRIZES_COMPLEMENTOS = {
    "Diabetes Mellitus Tipo 2": [
        "Fracionar em cerca de 6 refeições/dia (café, colação, almoço, lanche, jantar, ceia), com intervalos de ~3h e volumes menores por refeição.",
        "Regra prática para reduzir carga glicêmica: não combinar duas ou mais fontes de amido na mesma refeição (ex: arroz + pão + macarrão + mandioca/batata/inhame + farinha de milho).",
        "3 porções de fruta/dia é uma meta prática comum; 1-2 colheres de sopa de farelo de aveia/chia/linhaça por dia ajudam a reduzir a absorção de açúcar e colesterol.",
        "Adoçantes permitidos na prática clínica: sucralose, stévia, xilitol, eritritol - evitar excesso mesmo assim.",
        "Cuidado com pé diabético: hidratar bem a pele (inclusive mãos e pés) com hidratante à base de ureia, e secar bem os pés após o banho, inclusive entre os dedos - é orientação nutricional-educativa relevante para esse público.",
    ],
    "Hipertensão Arterial Sistêmica": [
        "Regra prática de fracionamento: ~6 refeições/dia a cada 3h, volumes menores, evitando jejum prolongado (mais de 3h sem se alimentar).",
        "Preferir carnes magras específicas (peito de frango, patinho, maminha, lagarto, coxão mole/duro) e preparações cozidas/refogadas/assadas com pouco óleo.",
        "Café em excesso e outros estimulantes (refrigerante de cola, chá mate, guaraná) podem elevar a pressão arterial - orientar redução, não necessariamente eliminação total.",
        "Reforçar leitura de rótulos (sódio e açúcar) e manutenção do peso adequado como medidas de suporte contínuo, além da dieta em si.",
    ],
    "Doença Renal Crônica (não dialítica)": [
        "Sal: cozinhar sem sal e acrescentar apenas na hora de servir - 1 colher de chá rasa no almoço e 1 no jantar (equivalente a ~1g cada) é uma orientação prática comum.",
        "Técnica de remolho do feijão reduz potássio e facilita digestão: deixar de molho na geladeira por 12h trocando a água 3 vezes, descartando grãos que boiarem.",
        "Vegetais em geral: deixar de molho em água filtrada por ~30min antes de cozinhar, descartar essa água, ferver por ~15min e descartar a água do cozimento novamente - reduz a carga de potássio.",
        "Evitar sempre carambola (nefrotoxicidade específica documentada, independente do estágio da doença).",
        "Quando há diabetes associado: não substituir refeições principais por lanches, e após almoço/jantar preferir 1 fruta rica em vitamina C evitando consumir café/chá/leite logo em seguida (interação com absorção de ferro/minerais).",
    ],
}

NOVAS_DIRETRIZES = [
    {
        "nome": "Encefalopatia Hepática e Cirrose",
        "fonte": "Protocolo de orientação nutricional ambulatorial (Hospital de Clínicas - UFTM)",
        "pontos": [
            "Fracionar as refeições a cada 3h, mastigando bem, sem pular nenhuma refeição principal - inclui lanche noturno antes de dormir (mingau de aveia sem açúcar, leite ou iogurte desnatado) para reduzir o catabolismo proteico noturno.",
            "Sódio bastante restrito: cerca de 2g/dia (aprox. 2 tampinhas de caneta bic), com uso generoso de temperos naturais (alho, cebola, cheiro-verde, orégano) para compensar a redução de sal.",
            "Diminuir proteína animal e priorizar proteína vegetal e de laticínios (feijão, soja, leite e derivados desnatados, lentilha, grão-de-bico) - ajuda a reduzir a produção de amônia sem comprometer o aporte proteico total.",
            "Consumir fonte de soja diariamente (leite, farinha, grão, carne de soja) e 1 colher de sopa de azeite de oliva extra virgem por dia no almoço e jantar.",
            "Evitar rigorosamente açúcar e alimentos industrializados/embutidos ricos em sódio (mesma lista de restrição da hipertensão/DRC): frios, embutidos, enlatados, conservas, sopas prontas, molhos industrializados.",
            "Manter boa hidratação (~1 litro/dia) e frutas ricas em vitamina C após as refeições principais, evitando cafeína logo em seguida.",
        ],
    },
    {
        "nome": "Pancreatite Crônica",
        "fonte": "Protocolo de orientação nutricional ambulatorial (Hospital de Clínicas - UFTM)",
        "pontos": [
            "Proibida a ingestão de bebidas alcoólicas - é a orientação mais crítica nessa condição.",
            "5 a 6 pequenas refeições por dia, evitando grandes volumes alimentares de uma vez (reduz a demanda de secreção pancreática por refeição).",
            "Priorizar preparações cozidas, grelhadas ou assadas; evitar frituras e preparações gordurosas (feijoada, moqueca, churrasco, sarapatel).",
            "Incluir fontes de triglicerídeos de cadeia média quando indicado (ex: óleo de coco), que exigem menos enzima pancreática para digestão.",
            "Atenção à vitamina B12: incluir fontes (fígado, leite, ovos, peixe, queijo, carnes) - má digestão de gorduras nessa condição pode comprometer a absorção de vitaminas lipossolúveis e B12.",
            "Preferir farináceos de tapioca, fubá de milho ou aveia no lugar de farinha de mandioca/maisena/creme de arroz.",
        ],
    },
    {
        "nome": "Úlcera Péptica / Gástrica",
        "fonte": "Protocolo de orientação nutricional ambulatorial (Hospital de Clínicas - UFTM)",
        "pontos": [
            "Fracionar em 6 a 7 refeições/dia, volumes reduzidos, mastigando bem e comendo com tranquilidade - reduz distensão e estímulo ácido por refeição.",
            "Evitar condimentos picantes/irritantes (pimenta, cominho, mostarda, caldos industrializados tipo knorr/sazon) e alimentos muito gelados ou muito quentes.",
            "Evitar cafeína (café, chocolate, chá mate, chá preto), bebidas alcoólicas e bebidas gasosas - todos estimulam secreção ácida ou irritam a mucosa.",
            "Última refeição pelo menos 1h antes de deitar; evitar líquidos em excesso durante as principais refeições (dilui enzimas digestivas e aumenta distensão).",
            "Individualizar a tolerância a frutas ácidas - orientar reduzir apenas as que efetivamente causam desconforto ao paciente, não uma restrição genérica.",
            "Evitar alimentos que notoriamente causam gases (repolho, milho, cebola) e jejum prolongado, que pode aumentar a acidez gástrica.",
        ],
    },
]


def seed_anamneses(conn):
    for a in ANAMNESES:
        conn.execute("INSERT INTO anamneses_modelo (nome, conteudo) VALUES (?,?)",
                     (a["nome"], a["conteudo"]))
    conn.commit()


def atualizar_e_completar_diretrizes(conn):
    """Idempotente: completa diretrizes existentes com pontos que ainda não constam,
    e insere as diretrizes novas (Encefalopatia/Cirrose, Pancreatite, Úlcera) se não existirem."""
    for nome, novos_pontos in DIRETRIZES_COMPLEMENTOS.items():
        row = conn.execute("SELECT id, pontos FROM diretrizes WHERE nome=?", (nome,)).fetchone()
        if not row:
            continue
        pontos_atuais = row[1].split("\n") if row[1] else []
        adicionados = False
        for p in novos_pontos:
            if p not in pontos_atuais:
                pontos_atuais.append(p)
                adicionados = True
        if adicionados:
            conn.execute("UPDATE diretrizes SET pontos=? WHERE id=?", ("\n".join(pontos_atuais), row[0]))

    for d in NOVAS_DIRETRIZES:
        existe = conn.execute("SELECT id FROM diretrizes WHERE nome=?", (d["nome"],)).fetchone()
        if not existe:
            conn.execute("INSERT INTO diretrizes (nome, fonte, pontos) VALUES (?,?,?)",
                         (d["nome"], d["fonte"], "\n".join(d["pontos"])))
    conn.commit()


def seed_receitas(conn):
    for r in RECEITAS:
        cur = conn.execute(
            "INSERT INTO receitas (nome, categoria, tags, porcoes, modo_preparo) VALUES (?,?,?,?,?)",
            (r["nome"], r["categoria"], r["tags"], r["porcoes"], r["modo_preparo"]))
        rid = cur.lastrowid
        for termo, qtd in r["ingredientes"]:
            aid = _achar_alimento(conn, termo)
            if aid:
                conn.execute("INSERT INTO receita_ingredientes (receita_id, alimento_id, quantidade_g) VALUES (?,?,?)",
                             (rid, aid, qtd))
    conn.commit()


def seed_planos_modelo(conn):
    for p in PLANOS_MODELO:
        cur = conn.execute("INSERT INTO planos_modelo (nome, categoria, vet_alvo, descricao) VALUES (?,?,?,?)",
                            (p["nome"], p["categoria"], p["vet_alvo"], p["descricao"]))
        mid = cur.lastrowid
        for refeicao, termo, qtd in p["itens"]:
            aid = _achar_alimento(conn, termo)
            if aid:
                conn.execute("INSERT INTO planos_modelo_itens (modelo_id, refeicao, alimento_id, quantidade_g) VALUES (?,?,?,?)",
                             (mid, refeicao, aid, qtd))
    conn.commit()


def seed_diretrizes(conn):
    import guidelines
    for d in guidelines.DOENCAS:
        conn.execute("INSERT INTO diretrizes (nome, fonte, pontos) VALUES (?,?,?)",
                     (d["nome"], d["fonte"], "\n".join(d["pontos"])))
    conn.commit()
