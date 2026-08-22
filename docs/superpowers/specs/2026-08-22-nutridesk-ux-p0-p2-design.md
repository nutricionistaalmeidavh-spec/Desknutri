# NutriDesk UX P0-P2 Design

## Objetivo
Elevar a UI/UX do NutriDesk desktop ao nível visual do site institucional, reorganizando o produto em torno do fluxo clínico Paciente → Consulta → Avaliação → Plano → Evolução → Retorno, sem remover o motor clínico existente e sem tornar obrigatória a troca da senha provisória.

## Escopo aprovado

### P0
- Aplicar design system visual consistente com verde petróleo/off-white, cards, chips, estados vazios e cabeçalhos contextuais.
- Reorganizar navegação em Trabalho, Conteúdo e Sistema, reduzindo itens técnicos de primeiro nível.
- Criar fluxo guiado “Nova consulta”.
- Redesenhar prontuário como workspace do paciente com Resumo, Consulta, Avaliações, Plano alimentar, Evolução e Arquivos.
- Redesenhar editor de plano alimentar com seleção explícita do alimento e resumo por refeição.

### P1
- Novo dashboard clínico com consultas de hoje, pacientes, retornos, pendências e atalhos; remover métricas operacionais do produto do dashboard.
- Idade calculada pela data de nascimento; usar QDateEdit em cadastro e consulta; pré-preencher altura/peso com última avaliação quando apropriado.
- Busca real de alimentos/ingredientes com lista de resultados; nunca “melhor resultado” automático.
- Crescimento WHO e Materno-infantil contextuais ao paciente, acessíveis do prontuário.
- Remover servidor de licenças da UI comum e esconder configuração técnica de updates em Configurações → Avançado.
- NÃO forçar troca da senha provisória.
- Dashboard deve destacar “Pacientes com plano alimentar não enviado”, vinculado à última consulta concluída.

### P2
- Agenda com calendário + lista diária/intervalo.
- Configurações agrupadas em Geral, Consultório, Relatórios, Segurança, Backup, Dados/Portabilidade e Avançado.
- Estados vazios e mensagens de erro amigáveis.
- Atalhos/ações rápidas: Ctrl+N nova consulta, Ctrl+K buscar paciente, Ctrl+P abrir pacientes.
- Padronizar marca visual para “NutriDesk”; manter nomes internos de arquivo/banco por compatibilidade.

## Dados
Adicionar migration 12 em `consultas` com campos opcionais: `objetivo`, `abordagem`, `plano_enviado_em`, `finalizada_em`. O plano pendente é a consulta mais recente com status `Realizada`/finalizada e `plano_enviado_em IS NULL`, quando o usuário optar por entregar o plano depois.

## Arquitetura UI
- `ui/design_system.py`: tokens, cards, títulos, chips, empty states e helpers de estilo.
- `ui/view_models.py`: idade, formatação, agrupamento de navegação, resumo de dashboard e erros amigáveis; lógica testável sem Qt.
- `ui/consultation_dialog.py`: wizard de nova consulta.
- `ui/main_window.py`: navegação, dashboard, pacientes e agenda modernizados.
- `ui/patient_dialog.py`: workspace clínico e editor de plano.
- `ui/p3_main_window.py`/`ui/v4_main_window.py`: recursos técnicos movidos para Configurações/Conta simplificada.

## Compatibilidade
- Banco existente migra automaticamente de schema 11 para 12.
- Licenças existentes permanecem válidas.
- Recursos clínicos e exportações existentes continuam acessíveis.
- Senha provisória pode ser alterada pelo cliente, mas a troca não é obrigatória.

## Critérios de aceite
- Suite anterior continua verde.
- Novos testes cobrem schema 12, idade automática, pendência de plano, nav agrupada, UI básica do prontuário e nova consulta.
- Aplicação inicia em modo offscreen sem exceções.
