# NutriDesk para macOS

Distribuição do mesmo NutriDesk/PySide6, com SQLite local, sem Electron nem serviço pago obrigatório.

## Baixar e instalar

Na [última Release](https://github.com/nutricionistaalmeidavh-spec/Desknutri/releases/latest),
escolha o DMG macos-arm64 para Apple Silicon ou o DMG macos-x86_64 para Intel.

1. Abra o DMG baixado.
2. Arraste NutriDesk.app para Aplicativos.
3. Ejete a imagem de disco e abra NutriDesk pelos Aplicativos.
4. Para atualizar, feche o NutriDesk antes de substituir o aplicativo em Aplicativos.

**Gatekeeper:** esta edição não está notarizada pela Apple. No primeiro uso,
o macOS pode impedir a abertura. Confirme a procedência da GitHub Release e,
caso necessário, use Ajustes do Sistema → Privacidade e Segurança →
Abrir Mesmo Assim. Não desabilite o Gatekeeper globalmente. Assinatura
Developer ID e notarização são opcionais, não dependências do build R$0.

## Dados e atualização

O SQLite e os prontuários permanecem fora do app, em
~/Library/Application Support/NutriDesktop/.
Uma instalação antiga que possua banco em ~/.local/share/NutriDesktop/
continua usando o diretório legado, sem migração destrutiva.
A variável NUTRIDESKTOP_DATA_DIR tem prioridade se configurada.

O programa identifica a arquitetura, consulta a GitHub Release estável e
valida o SHA-256 antes de abrir o DMG. O fluxo cria backup SQLite
consistente, abre o DMG no Finder e o usuário decide copiar/substituir.
Ao abrir a nova versão, a integridade do SQLite é verificada.
No macOS não há atualização silenciosa nem substituição do .app em execução.

## Build gratuito e self-hosted

Requisitos: macOS, Python 3.12, Xcode Command Line Tools e hdiutil.

Comandos:

    python3 -m pip install -r requirements-dev.txt
    python3 -m pip install -r license_server/requirements.txt
    python3 -m pip install httpx2
    python3 -m pytest -q
    python3 tools/build_macos.py --arch "$(uname -m)"

O DMG aparece no diretório release/.
O GitHub Actions usa os runners macos-15 (arm64) e
macos-15-intel (x86_64), gratuitos para repositórios públicos.

A CI verifica testes clínicos, compilação, PyInstaller, plist,
assinatura ad hoc, executável empacotado (--healthcheck),
imagem DMG e SHA-256 sem sobrescrever o checksum do Windows.
