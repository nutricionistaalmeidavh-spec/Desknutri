# NutriDesktop v2.0 — Implementações 01–28

Este pacote é um **overlay cumulativo** para o repositório `Desknutri/NutriDesktop`. Ele não apaga `data/alimentos_taco.csv`, `content_seed.py`, `icon.ico` nem outros recursos existentes.

## Estado por item

1. **Backup completo** — banco + `pacientes_arquivos` + `fotos_pacientes`.
2. **Documentos gerenciados** — novos anexos são copiados para `%LOCALAPPDATA%\NutriDesktop\pacientes_arquivos`; documentos legados são migrados sem apagar a origem.
3. **Backup transacional** — snapshot SQLite, manifest, SHA-256, validação, staging e rollback; senha opcional com criptografia.
4. **Licença assimétrica** — Ed25519; o app contém somente chave pública. `tools/license_admin.py` gera/assina licenças.
5. **Configuração comercial externa** — `config/commercial.json`, fora da lógica de licença.
6. **Proteção local** — PIN com scrypt, auto-lock, backup criptografado opcional e opção de criptografia transparente da pasta de dados via Windows EFS/NTFS quando disponível.
7. **Crescimento WHO real** — adaptador para `pygrowthstandards 0.1.3`, com dados WHO 2006/2007 empacotados, z-score, percentil e classificações.
8. **Testes clínicos** — fórmulas energéticas/composição, DRI e teste WHO quando a dependência estiver instalada.
9. **Modularização da UI** — `nutridesktop/ui`.
10. **Repositórios de dados** — `nutridesktop/data/repositories.py`.
11. **Migrations versionadas** — `schema_meta`, migrations 1→8, aditivas e idempotentes.
12. **Edição de paciente** — cadastro editável na ficha.
13. **Revisões de avaliações** — snapshots em `avaliacao_revisoes` + audit log.
14. **Validação central** — `core/validation.py`.
15. **Logs técnicos redigidos** — log rotativo sem campos clínicos conhecidos.
16. **Exceção global** — captura/log + mensagem amigável.
17. **Testes de banco/migrations** — SQLite temporário, integridade e fluxos.
18. **Prontuário longitudinal** — timeline de avaliação, anamnese, plano, documento, foto, crescimento e consulta.
19. **Gráficos de evolução** — peso, IMC, % gordura, massa magra, cintura + z-scores de crescimento.
20. **Plano avançado** — metas macro/micro e distribuição de VET por refeição.
21. **Substituições** — equivalência energética com penalidade por diferença proteica.
22. **Versões do plano** — revisão clona itens/metas e preserva anterior como histórico.
23. **Receitas compostas** — nutrientes por porção e inserção direta no plano.
24. **DRI por ciclo de vida** — infância, adolescência, adulto, idoso, gestante e lactante para nutrientes-chave da base atual.
25. **Protocolos versionados** — fonte, população-alvo, versão e conteúdo.
26. **Relatório clínico completo** — cadastro, última avaliação, plano/metas e timeline; anexo gerenciado.
27. **Templates de documentos** — editor, variáveis e geração/anexo em PDF.
28. **Agenda avançada** — retorno, tipo, duração, status, filtros e recorrência materializada até a data definida.

## Recursos anteriores preservados/reintegrados

- Anamnese versionada.
- Fotos de evolução.
- Base TACO e importação CSV.
- Receitas.
- Materno-infantil (ganho gestacional + referências de gestação/lactação).
- Dados em `%LOCALAPPDATA%\NutriDesktop`.
- Conteúdo legado opcional via `content_seed.py` quando presente.

## Requisitos

- Windows 10/11 x64.
- Python 3.11+ para verificar/gerar o build a partir do código-fonte.
- Inno Setup para gerar o instalador final.

## Aplicação segura

No PowerShell, dentro da pasta extraída:

```powershell
.\APLICAR_V2.ps1 -RepoPath "C:\caminho\para\Desknutri"
```

O script cria uma cópia dos arquivos que serão substituídos em `.nutridesktop_v1_backup\<timestamp>` antes de aplicar.

Depois:

```powershell
cd "C:\caminho\para\Desknutri"
.\VERIFICAR_V2.ps1
```

## Licença Ed25519

Uma vez, no computador administrativo:

```powershell
python tools\license_admin.py init
```

Guarde `license_admin\private_key.pem` fora do Git e fora de pacotes enviados a clientes. O arquivo `config\license_public_key.pem` pode ser distribuído com o aplicativo.

Gerar licença:

```powershell
python tools\license_admin.py sign --serial CLIENTE-0001 --machine "*"
```

Para travar na máquina, use o ID exibido pelo suporte/diagnóstico em uma futura rotina administrativa ou o retorno de `machine_id()`.

## Observação clínica importante

O motor WHO foi trocado para dados LMS/referências empacotados pelo projeto `pygrowthstandards`, que declara suporte aos padrões WHO 2006 (0–5) e referência WHO 2007 (5–19). Antes de comercialização clínica, execute o teste WHO em um ambiente com todas as dependências instaladas e valide amostras contra WHO Anthro/AnthroPlus.
