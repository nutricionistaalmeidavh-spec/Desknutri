# Relatório de verificação — NutriDesktop 3.0.0 / P3

## Escopo verificado
Implementações P3 29–35 sobre a base v2 itens 01–28: updater, versionamento, `.nutri`, exportações estruturadas, diagnóstico/suporte, backup automático e pipeline de release.

## Evidência executada
- `pytest -q`: **31 passed, 1 skipped**.
- Skip: teste WHO dependente de `pygrowthstandards`, ausente neste ambiente; a dependência permanece fixada em `requirements.txt` e é instalada pelo verificador Windows.
- `python -m compileall -q app.py nutridesktop tools`: aprovado.
- XLSX gerado pelo exporter: pacote ZIP/XML íntegro; todos os XMLs parsearam sem erro.
- Pipeline de release em `--skip-build` com chave Ed25519 temporária + instalador fictício: aprovado; gerou `version.json`, assinatura verificável e `SHA256SUMS.txt`.
- Varredura de segredos: nenhuma chave privada foi incluída. O pacote contém apenas ferramenta para gerar a chave fora do repositório.

## Fluxos cobertos por teste
- migrations até schema 10 e idempotência anterior;
- backup automático + registro em `backup_history`;
- pacote `.nutri` criptografado e roundtrip de prontuário;
- `.nutri` carregando documentos e fotos com checksum;
- JSON, CSV ZIP e XLSX estruturados;
- manifesto de atualização Ed25519 e resolução de instalador relativo;
- pacote de suporte sem `.db`, documentos/fotos e com redação de nome/e-mail/telefone;
- testes clínicos, banco, planos, agenda, relatórios e segurança herdados da v2.

## Limitações de ambiente
- PySide6 não está instalado neste runtime, portanto a janela Qt não foi aberta aqui; os módulos de UI passaram na compilação de sintaxe.
- O runtime não é Windows, portanto PyInstaller+Inno Setup não foram executados até o `.exe`/Setup real. O pipeline Windows e os scripts de build estão incluídos para essa verificação final no PC.
- `pygrowthstandards` não está instalado neste runtime, causando o único skip citado acima.

## Estado
**Implementação P3: PASS no código/serviços e PARTIAL no build/runtime Windows**, por limitação do ambiente de execução atual. O pacote não afirma que o instalador Windows foi compilado aqui.
