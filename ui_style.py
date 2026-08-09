"""
ui_style.py - Paleta, tipografia e componentes visuais reutilizáveis do NutriDesktop.
Paleta sincronizada com o Design System criado no Figma (azul-claro / branco / cinza
neutro). Usa o tema sv_ttk (Sun Valley) como base moderna, com estilos próprios
por cima para reproduzir os componentes do Figma (sidebar com hover/active, cards,
botões primário/secundário).
"""

import tkinter as tk
from tkinter import ttk

FONT_FAMILY = "Segoe UI"  # fallback local para "Inter" do Figma (Inter raramente vem instalada no Windows)

F_TITULO = (FONT_FAMILY, 18, "bold")
F_SUBTITULO = (FONT_FAMILY, 12, "bold")
F_SECAO = (FONT_FAMILY, 11, "bold")
F_TEXTO = (FONT_FAMILY, 10)
F_TEXTO_PEQUENO = (FONT_FAMILY, 9)
F_NUMERO_GRANDE = (FONT_FAMILY, 22, "bold")
F_MONO = ("Consolas", 9)

# ---- Paleta (mesmos valores das variáveis "Colors" do arquivo Figma) ----
COR_PRIMARIA = "#145C57"        # primary/500
COR_PRIMARIA_HOVER = "#0B4945"  # primary/600
COR_PRIMARIA_FUNDO = "#D8E9E4"  # primary/100 - fundo do item ativo da sidebar
COR_PRIMARIA_FUNDO_LEVE = "#EDF6F3"  # primary/50 - fundo do hover

COR_TEXTO = "#1B2129"       # neutral/900
COR_TEXTO_SEC = "#646D79"   # neutral/600
COR_BORDA = "#D3D8DE"       # neutral/300
COR_FUNDO_PAGINA = "#F4F7F5"  # neutral/100
COR_BRANCO = "#FFFFFF"

COR_OK = "#2F7D62"        # success/500
COR_ALERTA = "#DC2626"    # danger/500
COR_ATENCAO = "#D97706"   # warning/500
COR_INFO = COR_PRIMARIA   # alias - mantém compatibilidade com o código já existente

PAD = 12
PAD_S = 6


def aplicar_tema(root, modo="light"):
    """Aplica o tema sv_ttk se disponível; cai para o tema padrão sem quebrar."""
    try:
        import sv_ttk
        sv_ttk.set_theme(modo)
        return True
    except ImportError:
        return False


def alternar_tema(root):
    try:
        import sv_ttk
        atual = sv_ttk.get_theme()
        sv_ttk.set_theme("dark" if atual == "light" else "light")
    except ImportError:
        pass


def titulo_pagina(parent, texto, subtitulo=None):
    frame = ttk.Frame(parent)
    ttk.Label(frame, text=texto, font=F_TITULO).pack(anchor="w")
    if subtitulo:
        ttk.Label(frame, text=subtitulo, font=F_TEXTO, foreground=COR_TEXTO_SEC).pack(anchor="w")
    return frame


def secao(parent, texto):
    """Um LabelFrame padronizado para agrupar campos de formulário."""
    return ttk.LabelFrame(parent, text=f"  {texto}  ", padding=PAD)


def card_metrica(parent, rotulo, valor, cor=None, unidade=""):
    """Um 'cartão' com número grande + rótulo, para destacar resultados-chave."""
    frame = ttk.Frame(parent, padding=PAD, style="Card.TFrame")
    ttk.Label(frame, text=rotulo, font=F_TEXTO_PEQUENO, foreground=COR_TEXTO_SEC,
              style="Card.TLabel").pack(anchor="w")
    lbl_valor = ttk.Label(frame, text=f"{valor}{unidade}", font=F_NUMERO_GRANDE,
                           style="Card.TLabel")
    if cor:
        lbl_valor.configure(foreground=cor)
    lbl_valor.pack(anchor="w")
    return frame


def configurar_estilos(style: ttk.Style):
    style.configure("Card.TFrame", relief="groove", borderwidth=1)
    style.configure("Treeview", rowheight=26, font=F_TEXTO)
    style.configure("Treeview.Heading", font=F_SUBTITULO)

    # Botão primário (equivalente ao "Variant=Primary" do Figma) - com hover
    style.configure("Accent.TButton", font=F_TEXTO)

    # Itens de menu da sidebar - replica os estados Default/Hover/Active do Figma
    style.configure("Sidebar.TButton", font=F_TEXTO, anchor="w", padding=(14, 10),
                     foreground=COR_TEXTO_SEC, background=COR_BRANCO, borderwidth=0,
                     focuscolor=COR_BRANCO)
    style.map("Sidebar.TButton",
              background=[("active", COR_PRIMARIA_FUNDO_LEVE)],
              foreground=[("active", COR_PRIMARIA_HOVER)])

    style.configure("SidebarActive.TButton", font=(FONT_FAMILY, 10, "bold"), anchor="w",
                     padding=(14, 10), foreground=COR_PRIMARIA_HOVER,
                     background=COR_PRIMARIA_FUNDO, borderwidth=0, focuscolor=COR_PRIMARIA_FUNDO)
    style.map("SidebarActive.TButton",
              background=[("active", COR_PRIMARIA_FUNDO)],
              foreground=[("active", COR_PRIMARIA_HOVER)])
