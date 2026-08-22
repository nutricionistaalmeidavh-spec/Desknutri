# NutriDesk 6.0 — Expansão clínica

A v6 amplia o NutriDesk sem transformar o menu principal em uma lista de especialidades. Os recursos especializados vivem dentro do prontuário e podem ser combinados para o mesmo paciente.

## Novos fluxos

### Exames laboratoriais
- painéis por data de coleta e laboratório;
- marcadores numéricos ou textuais;
- unidade e faixa de referência opcional;
- sinalização simples baixo/normal/alto quando houver limites numéricos;
- fila de exames aguardando revisão;
- histórico por marcador para comparação longitudinal.

A sinalização não substitui interpretação clínica e não produz diagnóstico.

### Comparação longitudinal
Reúne em uma mesma visão:
- antropometria/composição corporal;
- exames laboratoriais;
- objetivos de consultas;
- versões de plano;
- acompanhamentos dos packs clínicos.

### Pendências inteligentes
O Dashboard passa a identificar:
- última consulta com plano ainda não enviado;
- paciente sem retorno futuro após consulta realizada;
- avaliação antropométrica desatualizada;
- exame marcado para revisão;
- pack ativo ainda sem checkpoint;
- pendências manuais.

### WhatsApp
O NutriDesk apenas abre o WhatsApp com texto pré-preenchido. Não lê conversas nem afirma que a mensagem foi entregue.

Mensagens disponíveis:
- plano alimentar;
- lembrete de retorno;
- solicitação de exames;
- acompanhamento geral.

### Central de importação
Importa CSV/XLSX com pré-visualização antes da gravação:
- pacientes;
- avaliações;
- exames.

Possui aliases comuns de colunas, detecção de duplicidade de paciente e histórico de importações.

## Packs clínicos

### Materno-infantil
Gestação, DPP, idade gestacional, peso pré-gestacional, acompanhamento do ganho de peso, lactação, introdução alimentar e vínculo mãe/bebê.

### Esportiva
Modalidade, frequência/volume de treino, horários, pré/intra/pós-treino, hidratação e objetivos de performance.

### Obesidade / Metabólica
Condições registradas pelo profissional, metas de peso/cintura, pressão arterial, barreiras e metas comportamentais.

### Renal
Condição/estágio registrados, metas de proteína, sódio, potássio, fósforo e líquidos, com exames estruturados no mesmo prontuário.

### Bariátrica
Pré/pós-operatório, data/tipo de cirurgia, fase de consistência, suplementação, intolerâncias e sintomas.

### Gastrointestinal
Bristol, frequência evacuatória, refluxo, constipação, diarreia, intolerâncias, fase FODMAP e correlação alimento-sintoma.

### SIBO
Registro de acompanhamento com estados:
- suspeito registrado;
- encaminhado;
- confirmado por registro externo;
- resolvido.

Também registra subtipo documentado, teste externo, tratamento informado, fase dietética, gatilhos, reintroduções e score de sintomas. O NutriDesk não diagnostica SIBO automaticamente.

## Receitas, substituições e planos
- receitas agora aceitam categoria, tags e modo de preparo;
- substituições podem ser salvas no plano e são preservadas ao criar nova versão;
- PDF do plano pode usar templates visuais diferentes;
- estilos iniciais: Clínico clean, Minimal, Moderno teal e Materno-infantil;
- o nutricionista pode escolher um template padrão para Plano, Relatório, Orientação e Receita.

## Migração
- APP_VERSION: `6.0.0`
- SCHEMA_VERSION: `13`
- migração testada de schema 12 para schema 13;
- dados anteriores permanecem compatíveis.

## Limitação de teste desta sessão
O runtime atual não possui PySide6, portanto não foi possível abrir janelas Qt visualmente. A UI foi verificada por contratos estáticos e compilação Python. A conferência visual final deve ser feita no Windows antes de gerar o instalador comercial definitivo.
