# NutriDesktop 6.2.0 — Atualização simplificada via GitHub

- Atualizador passa a consultar diretamente a última GitHub Release estável.
- Nova versão é apenas avisada; o usuário escolhe se deseja atualizar agora ou depois.
- Download do instalador continua validado por SHA-256 usando `SHA256SUMS.txt` da própria Release.
- Instalação deixa de ser silenciosa e abre o instalador normal do Windows.
- Removida a dependência de `version.json`, chave Ed25519 e `UPDATE_SIGNING_PRIVATE_KEY_B64` para releases futuras.
- Pipeline de release passa a publicar instalador + checksum sem Secrets adicionais.
- Configuração antiga do manifesto padrão é migrada em runtime sem alterar o schema SQLite, que permanece na versão 13.

# NutriDesktop 6.1.0 — Refinamento clínico de UI

- UI Kit canônico em PySide6/QSS com botões primary/secondary/ghost/danger, badges semânticos, toolbar, FormGrid, PatientHeader, Timeline e estados de salvamento.
- Pacientes reorganizado com toolbar compacta, seleção contextual e redução de espaço vazio.
- Agenda com datas em `dd/MM/yyyy`, calendário alinhado ao tema e estados visuais consistentes.
- Prontuário com contexto persistente do paciente, próxima consulta e timeline clínica.
- Receitas reorganizadas em workspace de duas colunas, preservando ingredientes, categorias, tags, porções e modo de preparo.
- Shell compacto com sidebar de 218 px, topbar, busca global e atalho `Ctrl+K`.
- Dashboard operacional priorizando agenda, pendências e retornos antes dos indicadores gerenciais.
- Paleta verde original preservada; schema SQLite permanece na versão 13.
- Pipeline de verificação Windows com `compileall`, 96 testes e smoke runtime PySide6 em modo offscreen.
- Correção de portabilidade do backup ZIP no Windows e guard de compatibilidade para `weight_stature` no `pygrowthstandards 0.1.3` sem substituir cálculos WHO suportados.

# NutriDesktop 3.0.0 — P3

- Atualizador com manifesto Ed25519, SHA-256, health-check e rollback assistido.
- Versionamento separado de aplicativo, schema, conteúdo clínico e engine WHO.
- Pacotes `.nutri` exportáveis/importáveis com checksums e senha opcional.
- Exportações estruturadas JSON, CSV ZIP e XLSX.
- Central de diagnóstico e pacote de suporte sem banco/prontuários.
- Backup automático diário/semanal com retenção diária, semanal e mensal.
- Pipeline de release: testes, compileall, PyInstaller, Inno Setup, SHA256SUMS e manifesto assinado.

## 4.0.0 — Conta e painel de licenças
- Ativação por e-mail + senha criada pelo cliente no primeiro acesso.
- E-mail pré-autorizado não pode ser reivindicado novamente após criação da senha.
- Limite de dispositivos por licença, desvinculação e bloqueio remoto.
- Token exclusivo por dispositivo; a senha do cliente não é armazenada no desktop.
- Renovação silenciosa e autorização offline assinada com Ed25519.
- Minidashboard web separado para clientes, licenças, dispositivos e histórico.
- Migração compatível com licenças assinadas antigas.
## 5.0.0 — UX clínica P0–P2
- Novo design system e navegação agrupada em Trabalho, Conteúdo e Sistema.
- Dashboard clínico com pendência de plano alimentar não enviado.
- Nova consulta guiada em seis etapas e prontuário reorganizado.
- Plano alimentar com seleção explícita de alimentos e resumo nutricional.
- Idade automática, calendários, prefills e métodos de composição corporal.
- WHO e Materno-infantil contextuais ao paciente.
- Agenda com calendário e configurações categorizadas.
- Estados vazios/loading, erros amigáveis e atalhos Ctrl+N/Ctrl+K/Ctrl+P.
- Marca visível padronizada para NutriDesk, preservando identificadores internos por compatibilidade.
- Painel de licenças passa a registrar status de entrega do e-mail de acesso.
- Troca da senha provisória permanece opcional.


## 6.0.0 — Expansão clínica e operacional

- Exames laboratoriais estruturados por painel, marcador, unidade, referência, sinalização e revisão.
- Comparação longitudinal unificando avaliações, exames, consultas, planos e packs clínicos.
- Pendências inteligentes: plano não enviado, retorno não agendado, avaliação desatualizada, exame a revisar, pack sem acompanhamento e ações manuais.
- Saída para WhatsApp com mensagens pré-preenchidas para plano, retorno, exames e acompanhamento.
- Central de importação CSV/XLSX para pacientes, avaliações e exames, com prévia, duplicidades e histórico.
- Packs clínicos contextuais: Materno-infantil, Esportiva, Obesidade/Metabólica, Renal, Bariátrica, Gastrointestinal e SIBO.
- SIBO documenta status, teste externo, tratamento informado, fase dietética, gatilhos, reintroduções e sintomas sem realizar diagnóstico automático.
- Biblioteca visual de templates com estilos e template padrão por tipo.
- Plano alimentar PDF com estilos visuais, refeições, receitas e substituições persistidas.
- Receitas ampliadas com categoria, tags, porções e modo de preparo.
- Schema SQLite 13 e NutriDesk 6.0.0.
