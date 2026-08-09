"""PDFs profissionais do NutriDesktop, todos gerados localmente com fpdf2."""
from datetime import datetime
from fpdf import FPDF

DEFAULT_IDENTITY = {
    "clinica_nome": "", "profissional_nome": "", "crn": "", "telefone": "", "email": "",
    "logo_path": "", "cor_primaria": "#145C57", "cor_secundaria": "#DDEBE7",
}


def _rgb(hex_value):
    value = (hex_value or "#145C57").lstrip("#")
    if len(value) != 6:
        value = "145C57"
    return tuple(int(value[i:i + 2], 16) for i in (0, 2, 4))


def _identity(clinica_nome=None, logo_path=None, identidade=None):
    result = DEFAULT_IDENTITY.copy()
    result.update(identidade or {})
    if clinica_nome is not None: result["clinica_nome"] = clinica_nome
    if logo_path is not None: result["logo_path"] = logo_path
    return result


class RelatorioPDF(FPDF):
    def __init__(self, titulo, identidade=None):
        super().__init__(orientation="P", unit="mm", format="A4")
        self.titulo = titulo
        self.identidade = _identity(identidade=identidade)
        self.primary = _rgb(self.identidade["cor_primaria"])
        self.soft = _rgb(self.identidade["cor_secundaria"])
        self.set_auto_page_break(auto=True, margin=20)
        self.set_margins(15, 28, 15)

    def header(self):
        if self.identidade.get("logo_path"):
            try: self.image(self.identidade["logo_path"], x=15, y=8, h=13)
            except Exception: pass
        self.set_text_color(*self.primary); self.set_font("Helvetica", "B", 15)
        self.set_xy(15, 9); self.cell(0, 6, self.titulo, align="R")
        subtitulo = self.identidade.get("clinica_nome") or self.identidade.get("profissional_nome")
        if subtitulo:
            self.set_font("Helvetica", "", 8); self.set_xy(15, 16); self.cell(0, 4, subtitulo, align="R")
        self.set_draw_color(*self.primary); self.line(15, 24, 195, 24)
        self.set_text_color(35, 47, 46)

    def footer(self):
        self.set_y(-14); self.set_draw_color(*self.primary); self.line(15, self.get_y(), 195, self.get_y())
        contato = " | ".join(filter(None, (self.identidade.get("profissional_nome"), self.identidade.get("crn"), self.identidade.get("telefone"), self.identidade.get("email"))))
        self.set_font("Helvetica", "", 7); self.set_text_color(100, 110, 108)
        self.cell(145, 5, contato[:115]); self.cell(35, 5, f"Pagina {self.page_no()}/{{nb}}", align="R")
        self.set_text_color(35, 47, 46)

    def section(self, title):
        self.ln(2); self.set_fill_color(*self.primary); self.set_text_color(255, 255, 255)
        self.set_font("Helvetica", "B", 10); self.cell(0, 7, "  " + title, fill=True, ln=1)
        self.set_text_color(35, 47, 46); self.ln(2)

    def text(self, value, size=9):
        self.set_font("Helvetica", "", size); self.multi_cell(0, 5.2, str(value) if value else "-")

    def metric_cards(self, values):
        usable, gap = 180, 3; width = (usable - gap * (len(values) - 1)) / len(values)
        x, y = self.get_x(), self.get_y()
        for label, value in values:
            self.set_fill_color(*self.soft); self.set_draw_color(215, 225, 221)
            self.rect(x, y, width, 18, style="DF")
            self.set_xy(x + 3, y + 3); self.set_font("Helvetica", "", 7); self.set_text_color(79, 97, 93); self.cell(width - 6, 4, label)
            self.set_xy(x + 3, y + 8); self.set_font("Helvetica", "B", 12); self.set_text_color(*self.primary); self.cell(width - 6, 6, value)
            x += width + gap
        self.set_text_color(35, 47, 46); self.set_y(y + 22)

    def table(self, headers, rows, widths):
        self.set_font("Helvetica", "B", 8); self.set_fill_color(*self.soft)
        for h, w in zip(headers, widths): self.cell(w, 6, str(h), border=0, fill=True)
        self.ln()
        self.set_font("Helvetica", "", 8)
        for row in rows:
            y = self.get_y()
            heights = [self.font_size * 1.8 * max(1, len(str(v)) // max(1, int(w * 2.2)) + 1) for v, w in zip(row, widths)]
            height = max(5.5, min(20, max(heights)))
            if y + height > 275: self.add_page(); y = self.get_y()
            x = self.l_margin
            for value, w in zip(row, widths):
                self.rect(x, y, w, height); self.set_xy(x + 1.5, y + 1); self.multi_cell(w - 3, 3.5, str(value or "-"), border=0)
                x += w
            self.set_xy(self.l_margin, y + height)

    def chart(self, evolucao):
        values = [e for e in evolucao if e.get("peso") is not None]
        if len(values) < 2: return
        x, y, w, h = self.l_margin + 5, self.get_y() + 4, 165, 35
        pesos = [float(e["peso"]) for e in values]; lo, hi = min(pesos), max(pesos)
        if lo == hi: lo -= .5; hi += .5
        self.set_draw_color(205, 217, 213); self.rect(x, y, w, h)
        points = []
        for i, value in enumerate(pesos):
            px = x + 5 + i * (w - 10) / (len(pesos) - 1); py = y + h - 5 - (value - lo) / (hi - lo) * (h - 10); points.append((px, py))
        self.set_draw_color(*self.primary); self.set_line_width(.8)
        for a, b in zip(points, points[1:]): self.line(a[0], a[1], b[0], b[1])
        self.set_fill_color(*self.primary)
        for px, py in points: self.ellipse(px - 1, py - 1, 2, 2, style="F")
        self.set_font("Helvetica", "", 7); self.set_text_color(80, 95, 91); self.set_xy(x, y + h + 1); self.cell(w, 4, f"Evolucao de peso: {pesos[0]:.1f} kg -> {pesos[-1]:.1f} kg", align="C")
        self.set_text_color(35, 47, 46); self.set_y(y + h + 8)

    def photos(self, fotos):
        valid = [f for f in fotos if f.get("caminho")]
        if not valid: return
        self.section("Registro fotografico")
        x, y = self.l_margin, self.get_y(); shown = 0
        for foto in valid[-2:]:
            try:
                self.image(foto["caminho"], x=x, y=y, w=82, h=58, keep_aspect_ratio=True)
                self.set_xy(x, y + 59); self.set_font("Helvetica", "", 7); self.cell(82, 4, f"{foto.get('data','')} - {foto.get('observacao','')}"[:52], align="C")
                x += 92; shown += 1
            except Exception: continue
        if shown: self.set_y(y + 66)


def _new(title, clinica_nome=None, logo_path=None, identidade=None):
    pdf = RelatorioPDF(title, _identity(clinica_nome, logo_path, identidade)); pdf.alias_nb_pages(); pdf.add_page(); pdf.set_y(27); return pdf


def exportar_avaliacao(caminho, paciente, avaliacao, resultados, clinica_nome=None, logo_path=None, identidade=None):
    pdf = _new("Relatorio de avaliacao nutricional", clinica_nome, logo_path, identidade)
    pdf.section("Paciente")
    pdf.text(f"Nome: {paciente['nome']}   |   Data: {avaliacao['data']}   |   Sexo: {'Masculino' if paciente['sexo'] == 'M' else 'Feminino'}")
    pdf.section("Metricas principais")
    pdf.metric_cards([("Peso", f"{avaliacao['peso']:.1f} kg"), ("IMC", f"{resultados['imc']:.1f}"), ("Gordura", f"{resultados['pg_final']:.1f}%"), ("Meta energetica", f"{resultados['vet']:.0f} kcal")])
    pdf.section("Composicao corporal")
    pdf.table(["Indicador", "Resultado"], [("Origem % gordura", resultados['origem_pg']), ("Massa gorda", f"{resultados['massa_gorda']:.1f} kg"), ("Massa magra", f"{resultados['massa_magra']:.1f} kg")], [65, 115])
    pdf.section("Gasto e distribuicao")
    pdf.table(["Indicador", "Valor"], [("Formula", avaliacao['formula_tmb']), ("TMB", f"{resultados['tmb']:.0f} kcal/dia"), ("GET", f"{resultados['get_total']:.0f} kcal/dia"), ("Proteina", f"{resultados['ptn_g']:.0f} g/dia"), ("Lipideos", f"{resultados['lip_g']:.0f} g/dia"), ("Carboidratos", f"{resultados['cho_g']:.0f} g/dia")], [65, 115])
    pdf.output(caminho)


def exportar_relatorio_completo(caminho, paciente, anamnese=None, avaliacao=None, resultados=None, plano_info=None, clinica_nome=None, logo_path=None, identidade=None, evolucao=None, fotos=None):
    pdf = _new("Relatorio clinico", clinica_nome, logo_path, identidade)
    pdf.section("Paciente"); pdf.text(f"Nome: {paciente['nome']}   |   Sexo: {'Masculino' if paciente['sexo'] == 'M' else 'Feminino'}")
    if avaliacao and resultados:
        pdf.section("Resumo da avaliacao")
        pdf.metric_cards([("Peso", f"{avaliacao['peso']:.1f} kg"), ("IMC", f"{resultados['imc']:.1f}"), ("Gordura", f"{resultados['pg_final']:.1f}%"), ("VET", f"{resultados['vet']:.0f} kcal")])
    if evolucao:
        pdf.section("Evolucao"); pdf.chart(evolucao)
    if plano_info:
        pdf.section("Plano alimentar vigente"); pdf.text(f"{plano_info['nome']} - Meta: {plano_info['vet_meta']:.0f} kcal | Calculado: {plano_info['kcal_total']:.0f} kcal")
    if anamnese:
        pdf.section(f"Anamnese - {anamnese.get('data','')}"); pdf.text(anamnese.get("conteudo", ""), 8.5)
    pdf.photos(fotos or [])
    pdf.output(caminho)


def exportar_anamnese(caminho, paciente, nome_modelo, conteudo, clinica_nome=None, logo_path=None, identidade=None):
    pdf = _new("Anamnese nutricional", clinica_nome, logo_path, identidade)
    pdf.section("Paciente"); pdf.text(f"Nome: {paciente['nome']}   |   Tipo: {nome_modelo}")
    pdf.section("Respostas registradas"); pdf.text(conteudo, 9)
    pdf.output(caminho)


def exportar_diretriz(caminho, paciente, diretriz_nome, diretriz_fonte, pontos, orientacoes="", resumo_plano=None, clinica_nome=None, logo_path=None, identidade=None):
    pdf = _new(diretriz_nome, clinica_nome, logo_path, identidade)
    pdf.section("Paciente"); pdf.text(f"Nome: {paciente['nome']}")
    if resumo_plano: pdf.section("Plano vigente"); pdf.text(f"{resumo_plano['nome']} - Meta: {resumo_plano['vet_meta']:.0f} kcal")
    if orientacoes.strip(): pdf.section("Orientacoes do profissional"); pdf.text(orientacoes.strip())
    pdf.section("Pontos-chave"); pdf.table(["Orientacao"], [(p,) for p in pontos], [180])
    pdf.output(caminho)


def exportar_plano(caminho, paciente, plano, itens_por_refeicao, totais, comparacao_dri=None, clinica_nome=None, logo_path=None, identidade=None):
    pdf = _new("Plano alimentar", clinica_nome, logo_path, identidade)
    pdf.section("Paciente"); pdf.text(f"{paciente['nome']} | Plano: {plano['nome']} | Data: {plano['data']}")
    pdf.metric_cards([("Energia", f"{totais['kcal']:.0f} kcal"), ("Meta", f"{plano['vet_meta']:.0f} kcal"), ("Proteina", f"{totais['proteina']:.0f} g"), ("Carboidratos", f"{totais['carboidrato']:.0f} g")])
    for refeicao, itens in itens_por_refeicao.items():
        pdf.section(refeicao)
        pdf.table(["Alimento", "Qtd.", "Kcal", "P", "L", "C"], [(d, f"{q:.0f} g", f"{k:.0f}", f"{p:.1f}", f"{l:.1f}", f"{c:.1f}") for d, q, k, p, l, c in itens], [75, 18, 20, 20, 20, 20])
    if comparacao_dri:
        pdf.section("Micronutrientes vs DRI")
        pdf.table(["Nutriente", "Atual", "Meta", "%"], [(n, f"{v:.1f}", f"{m:.1f}", f"{pct:.0f}%") for n, v, m, pct, _ in comparacao_dri], [65, 38, 38, 39])
    pdf.output(caminho)
