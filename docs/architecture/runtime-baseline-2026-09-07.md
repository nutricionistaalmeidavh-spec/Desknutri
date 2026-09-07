# NutriDesk — baseline de runtime e consolidação

Data: 2026-09-07
Base analisada: `main` em `7733352bbe4fbaed9cc8136addf54ac1a3ba7d2b`

## Objetivo

Registrar o contrato atual antes do refinamento visual e consolidar o caminho de execução sem alterar regras clínicas, persistência ou serviços.

## Runtime antes da consolidação

`app.py` iniciava `V4MainWindow`, cuja cadeia efetiva era:

`V4MainWindow -> P3MainWindow -> MainWindow -> QMainWindow`

A UI base e o design system já estavam concentrados em:

- `nutridesktop/ui/main_window.py`
- `nutridesktop/ui/design_system.py`
- `nutridesktop/ui_kit/theme.py`

## Capacidades exclusivas preservadas

### Camada operacional (antiga P3)

- backup automático no startup/close e política de retenção;
- atualização assinada, canal stable/beta, SHA-256, staging e rollback;
- exportação/importação `.nutri`;
- exportações JSON, CSV ZIP e XLSX;
- diagnóstico e pacote de suporte sem prontuários;
- abertura da pasta local de dados.

### Camada de conta/licença (antiga V4)

- página Conta;
- ativação/troca de conta;
- renovação de licença;
- troca de senha;
- desvinculação do computador;
- status de conta dentro de Configurações.

## Contratos que não podem mudar nesta etapa

- `SCHEMA_VERSION = 13`;
- banco local e migrations existentes;
- repositórios e serviços clínicos;
- TACO e seeds;
- WHO e conteúdo clínico;
- prontuário, avaliações, planos e documentos;
- licenciamento legado assinado e licenciamento por conta;
- backup/restore;
- importação/exportação e pacote `.nutri`;
- healthcheck;
- caminhos de dados do usuário;
- atalhos `Ctrl+N`, `Ctrl+P`, `Ctrl+K`;
- tema verde atual e ThemeManager.

## Telas principais observadas

- Dashboard
- Pacientes
- Agenda
- Biblioteca
- Conta
- Configurações
- Prontuário do paciente
- Consulta guiada
- Alimentos
- Crescimento WHO
- Materno-infantil
- Receitas
- Templates
- Protocolos
- Atualizações
- Exportações e portabilidade
- Suporte e diagnóstico

## Dialogs e fluxos relevantes

- novo paciente;
- PIN de desbloqueio;
- ativação de conta;
- consulta guiada;
- prontuário do paciente;
- importação;
- laboratórios;
- pacotes clínicos;
- seleção de arquivos e destinos de exportação.

## Build e release

Fontes atuais:

- `nutridesktop/version.py` — versão de aplicação, schema, conteúdo clínico e WHO;
- `tools/build_release.py` — testes, compileall, PyInstaller, Inno Setup e manifesto assinado;
- `nutridesktop.spec` — empacotamento PyInstaller;
- `NutriDesktop.iss` — instalador Windows;
- `GERAR_RELEASE.ps1` e `gerar_instalador.bat` — entradas auxiliares de build;
- `.github/workflows/release.yml` — automação de release.

Há documentação histórica e scripts P3/V4 na raiz. Eles permanecem nesta etapa como referência e rollback; não fazem mais parte do caminho canônico de execução após a consolidação.

## Runtime depois da consolidação

`app.py` inicia `nutridesktop.ui.application_window.MainWindow`.

A composição canônica preserva a mesma ordem comportamental anterior:

`AccountFeaturesMixin -> OperationalFeaturesMixin -> ui.main_window.MainWindow`

Os recursos foram movidos para `nutridesktop/ui/window_features.py`, eliminando nomes de versão do runtime sem apagar as implementações históricas.

## Evidência esperada

- teste de MRO/composição da janela canônica;
- teste de presença das capacidades operacionais e de conta;
- teste garantindo que `app.py` não importa `p3_main_window` nem `v4_main_window`;
- suíte existente continua sendo a referência para banco, P3, conta/licença, UX v5 e expansão clínica v6.
