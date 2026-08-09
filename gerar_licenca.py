"""
gerar_licenca.py - Gerador de chaves de licença do NutriDesktop.

*** ESTE ARQUIVO É SÓ SEU - NÃO ENVIE PARA CLIENTES ***
Ele usa o mesmo SECRET que está em licensing.py para calcular chaves
válidas. Guarde os dois em local seguro.

COMO USAR
---------
Cada venda = um número de série novo (1, 2, 3, 4...). Nunca repita um
número de série já usado, senão duas pessoas ficam com a mesma chave.

Rodar direto pelo terminal, informando o número de série:
    python gerar_licenca.py 1
    python gerar_licenca.py 2

Ou sem argumento, ele pergunta interativamente e sugere o próximo
número automaticamente (guarda um contador em proximo_serial.txt).
"""

import sys
import os
import hmac
import hashlib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import licensing as lic  # usa o mesmo SECRET definido em licensing.py

CONTADOR_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "proximo_serial.txt")


def gerar_chave(numero_serial: int) -> str:
    """Gera uma chave de licença válida a partir de um número de série (1, 2, 3...).
    Só existe aqui, neste arquivo que fica com você - o app do cliente não
    tem essa função, só a de validar."""
    bloco = f"{numero_serial:08d}"
    assinatura = hmac.new(lic.SECRET, bloco.encode(), hashlib.sha256).hexdigest()[:12].upper()
    return f"NUTRI-{bloco[:4]}-{bloco[4:]}-{assinatura[0:4]}-{assinatura[4:8]}-{assinatura[8:12]}"


def _ler_proximo_serial():
    if os.path.exists(CONTADOR_PATH):
        with open(CONTADOR_PATH) as f:
            return int(f.read().strip())
    return 1


def _salvar_proximo_serial(n):
    with open(CONTADOR_PATH, "w") as f:
        f.write(str(n))


def main():
    if len(sys.argv) > 1:
        numero_serial = int(sys.argv[1])
    else:
        sugestao = _ler_proximo_serial()
        entrada = input(f"Número de série (Enter para usar sugestão automática {sugestao}): ").strip()
        numero_serial = int(entrada) if entrada else sugestao

    chave = gerar_chave(numero_serial)

    print()
    print("=" * 50)
    print(f"  Nº de série : {numero_serial}")
    print(f"  Chave       : {chave}")
    print("=" * 50)
    print()
    print("Envie essa chave para o cliente. Ela só ativa em UM computador")
    print("(o primeiro em que for digitada).")

    if numero_serial >= _ler_proximo_serial():
        _salvar_proximo_serial(numero_serial + 1)


if __name__ == "__main__":
    main()
