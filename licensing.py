"""
licensing.py - Sistema de ativação por chave de licença, com vínculo à máquina.

Como funciona:
- Cada chave é gerada a partir de um número de série + uma assinatura HMAC
  calculada com uma chave secreta (SECRET) que só existe no seu computador
  (no script gerar_licenca.py) e embutida aqui para permitir validação local.
- Na primeira execução, o app pede a chave, valida a assinatura e grava,
  junto com uma "impressão digital" do computador (machine id), no banco.
- Nas execuções seguintes, o app confere se a chave + o machine id batem
  com o que foi gravado. Se o cliente copiar o programa pra outro PC, o
  machine id não bate mais e pede ativação de novo.

IMPORTANTE - LIMITAÇÃO HONESTA: como a validação roda no computador do
cliente, um usuário com conhecimento técnico avançado pode eventualmente
extrair a lógica do .exe. Isso não é "inquebrável" - é uma trava que
impede cópia/revenda casual, que é o cenário mais comum. Para uma proteção
mais forte (chave que só pode ser usada uma única vez em qualquer PC do
mundo, com bloqueio remoto etc.), seria necessário um servidor de validação
online - posso ajudar a montar isso depois, se fizer sentido para o negócio.

*** TROQUE O VALOR DE SECRET ABAIXO ANTES DE VENDER O PRODUTO ***
Edite só aqui - o gerar_licenca.py importa esse valor automaticamente,
não precisa copiar em outro lugar. Guarde em segredo: é ele que garante
que só você consegue gerar chaves válidas.

Este arquivo (licensing.py) SÓ TEM A PARTE DE VALIDAÇÃO - ele vai junto
com o app que o cliente recebe. A função que GERA chaves novas fica
separada, em gerar_licenca.py, que fica só com você.
"""

import hmac
import hashlib
import uuid
import platform

SECRET = b"troque-este-valor-por-um-segredo-longo-e-unico-antes-de-vender-2026"

# ---- Configurações comerciais - edite com seus dados reais ----
LINK_COMPRA = "https://seu-link-de-pagamento-aqui.com"
CONTATO_WHATSAPP = "5534900000000"  # DDI+DDD+número, só números
MENSAGEM_WHATSAPP = "Olá! Comprei o NutriDesktop e preciso da minha chave de ativação."


def _formato_valido(chave: str):
    """Confere a assinatura da chave. Devolve o número de série se for válida, senão None."""
    chave = chave.strip().upper()
    if not chave.startswith("NUTRI-"):
        return None
    partes = chave[6:].split("-")
    if len(partes) != 5:
        return None
    bloco = partes[0] + partes[1]
    assinatura_informada = "".join(partes[2:])
    if len(bloco) != 8 or len(assinatura_informada) != 12:
        return None
    assinatura_esperada = hmac.new(SECRET, bloco.encode(), hashlib.sha256).hexdigest()[:12].upper()
    if not hmac.compare_digest(assinatura_informada, assinatura_esperada):
        return None
    try:
        return int(bloco)
    except ValueError:
        return None


def obter_machine_id() -> str:
    """'Impressão digital' aproximada deste computador (nome + endereço de rede)."""
    bruto = f"{platform.node()}-{uuid.getnode()}"
    return hashlib.sha256(bruto.encode()).hexdigest()[:16]


def esta_ativado(db) -> bool:
    chave_salva = db.get_config("licenca_chave")
    machine_salvo = db.get_config("licenca_machine_id")
    if not chave_salva or not machine_salvo:
        return False
    if _formato_valido(chave_salva) is None:
        return False
    return machine_salvo == obter_machine_id()


def ativar(db, chave: str):
    """Tenta ativar com a chave informada. Devolve (sucesso: bool, mensagem: str)."""
    numero_serial = _formato_valido(chave)
    if numero_serial is None:
        return False, "Chave inválida. Confira se digitou certinho (com os traços)."

    machine_atual = obter_machine_id()
    chave_salva = db.get_config("licenca_chave")
    machine_salvo = db.get_config("licenca_machine_id")

    if chave_salva and machine_salvo and chave_salva.strip().upper() != chave.strip().upper():
        return False, ("Este computador já tem outra licença ativada.\n"
                        "Entre em contato com o suporte se precisar trocar a licença.")

    db.set_config("licenca_chave", chave.strip().upper())
    db.set_config("licenca_machine_id", machine_atual)
    return True, "Licença ativada com sucesso!"
