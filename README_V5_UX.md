# NutriDesk 5.0 — UX clínica P0–P2

Esta entrega reorganiza o NutriDesk em torno do fluxo **Paciente → Consulta → Avaliação → Plano → Evolução → Retorno**, preservando o banco local, o motor clínico, os pacotes `.nutri`, backups, atualizações e o licenciamento online existentes.

## O que mudou

### P0 — experiência principal
- Novo design system desktop com identidade NutriDesk, cards, hierarquia visual, estados vazios e navegação mais enxuta.
- Menu principal agrupado em **Trabalho / Conteúdo / Sistema**.
- Novo fluxo guiado **Nova consulta** em seis etapas: Dados da consulta, Anamnese, Avaliação, Plano alimentar, Orientações e Retorno.
- Prontuário reorganizado em **Resumo, Consulta, Avaliações, Plano alimentar, Evolução e Arquivos**.
- Plano alimentar redesenhado com refeição, busca explícita de alimento, tabela de itens e resumo de energia/macros. O sistema não escolhe mais automaticamente o primeiro alimento encontrado.

### P1 — clínica e contexto
- Dashboard clínico com consultas, pacientes, retornos e pendências, removendo métricas técnicas de backup/versão do fluxo principal.
- Pendência **Plano alimentar não enviado** vinculada à consulta concluída. A nutricionista pode entregar depois e marcar o plano como enviado pelo prontuário.
- Mantidas **Distribuição de objetivos** e **Adesão aos planos**; quando não existem dados reais de adesão, o produto mostra estado sem dados em vez de inventar percentual.
- Idade derivada da data de nascimento; cadastro usa seletor de data e rótulos Feminino/Masculino.
- Avaliação pré-preenche medidas recentes e permite selecionar o método de composição corporal.
- Crescimento WHO e Materno-infantil passam a aparecer no contexto do paciente, em vez de ocupar destinos principais da navegação.
- Configuração do servidor de licenças e detalhes técnicos de atualização deixam de aparecer na UI cotidiana.
- O status da conta/licença fica como card em Configurações.
- Painel online de licenças agora registra **Não enviado / Enviado / Falhou** para o e-mail da senha provisória.
- A senha provisória de 8 dígitos continua podendo ser alterada pelo usuário, **sem troca obrigatória**, conforme decisão desta entrega.

### P2 — acabamento operacional
- Agenda com calendário.
- Configurações separadas em Geral, Consultório, Relatórios, Segurança, Backup, Dados e portabilidade e Avançado.
- Mensagens de erro de rede/banco/permissão mais amigáveis.
- Estados vazios em listas principais e feedback de carregamento na renovação online da conta.
- Atalhos: **Ctrl+N** Nova consulta, **Ctrl+K** buscar paciente e **Ctrl+P** Pacientes.
- Marca visível padronizada para **NutriDesk**. Nomes internos como `NutriDesktop.exe`, pasta de dados e identificadores de licença foram mantidos por compatibilidade.

## Banco de dados

Schema local: **12**.

A migration 12 adiciona a `consultas`:
- `objetivo`
- `abordagem`
- `plano_enviado_em`
- `finalizada_em`

Bancos no schema 11 migram automaticamente para 12.

## Licenciamento online

O fluxo continua:
1. Administrador libera o e-mail.
2. O sistema gera senha provisória numérica de 8 dígitos.
3. Gmail envia a credencial.
4. O painel registra o resultado do envio.
5. O cliente ativa o NutriDesk no computador permitido.
6. O cliente pode trocar a senha em **Conta → Trocar senha**, mas não é obrigado.

## Compatibilidade
- Dados locais continuam no mesmo diretório para não quebrar instalações existentes.
- Executável interno continua `NutriDesktop.exe`.
- Identificadores de licença e formato `.nutri` não foram renomeados.
- Instalador passa a exibir o produto como **NutriDesk 5.0.0**.

## Verificação nesta entrega
- `pytest`: **61 aprovados, 1 ignorado (WHO)**.
- `compileall`: aprovado.
- Migração 11 → 12: testada automaticamente.
- AppDeploy do painel de licenças: pronto, sem erros de frontend/rede no QA automático.
- Supabase `nutridesk-account`: versão 3 ACTIVE.

### Limitação do ambiente de construção
O ambiente desta sessão não possui `PySide6` e não consegue baixá-lo da rede. Por isso, as mudanças de UI foram verificadas por contratos estáticos de fonte/AST + compilação Python, e os testes funcionais de banco/serviços rodaram normalmente. O **smoke test visual Qt real deve ser executado em Windows com PySide6** antes de compilar o instalador final.
