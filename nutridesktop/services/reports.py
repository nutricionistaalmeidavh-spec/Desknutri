from __future__ import annotations
from pathlib import Path

from fpdf import FPDF
from fpdf.enums import XPos, YPos

from nutridesktop.services.plans import plan_nutrients, target_status, meal_distribution_status
from nutridesktop.data.repositories import (
    PatientRepository,
    AssessmentRepository,
    PlanRepository,
    TimelineRepository,
    AnamnesisRepository,
    LabRepository,
    ClinicalPackRepository,
)
from nutridesktop.clinical.packs import PACK_DEFINITIONS


def _pdf_text(value) -> str:
    """Keep core-font PDFs robust while preserving Portuguese Latin-1 text."""
    text = str(value or "-").replace("–", "-").replace("—", "-").replace("…", "...")
    return text.encode("latin-1", "replace").decode("latin-1")


class ClinicalPDF(FPDF):
    report_title = "NutriDesk"
    identity_lines: list[str] = []

    def header(self):
        self.set_font("Helvetica", "B", 14)
        self.cell(0, 8, _pdf_text(self.report_title), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        if self.identity_lines:
            self.set_font("Helvetica", "", 8)
            for line in self.identity_lines[:3]:
                if line:
                    self.cell(0, 4, _pdf_text(line), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.set_draw_color(20, 92, 87)
        self.line(self.l_margin, self.get_y() + 2, self.w - self.r_margin, self.get_y() + 2)
        self.ln(5)

    def footer(self):
        self.set_y(-12)
        self.set_font("Helvetica", "", 8)
        self.cell(0, 8, _pdf_text(f"Página {self.page_no()}"), align="C")


def _txt(pdf: FPDF, title, text):
    pdf.set_x(pdf.l_margin)
    pdf.set_font("Helvetica", "B", 11)
    pdf.multi_cell(0, 7, _pdf_text(title), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Helvetica", "", 9)
    pdf.multi_cell(0, 5, _pdf_text(text), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(2)


def _identity(database) -> list[str]:
    keys = (
        "clinica_nome",
        "profissional_nome",
        "profissional_crn",
        "profissional_telefone",
        "profissional_email",
    )
    with database.connect() as c:
        rows = c.execute(
            "SELECT chave,valor FROM configuracoes WHERE chave IN (%s)" % ",".join("?" * len(keys)),
            keys,
        ).fetchall()
    cfg = {r["chave"]: r["valor"] for r in rows}
    clinic = cfg.get("clinica_nome", "")
    professional = " - ".join(x for x in (cfg.get("profissional_nome", ""), cfg.get("profissional_crn", "")) if x)
    contact = " | ".join(x for x in (cfg.get("profissional_telefone", ""), cfg.get("profissional_email", "")) if x)
    return [clinic, professional, contact]


def generate_complete_report(pid, destination, sections=None, database=None):
    sections = set(sections or {"patient", "anamnesis", "assessment", "evolution", "plan", "labs", "packs", "timeline"})
    pr = PatientRepository(database) if database else PatientRepository()
    ar = AssessmentRepository(pr.db)
    pl = PlanRepository(pr.db)
    tr = TimelineRepository(pr.db)
    an = AnamnesisRepository(pr.db)
    patient = pr.get(pid)
    if not patient:
        raise ValueError("Paciente não encontrado.")
    assessments = ar.list(pid)
    plans = pl.list(pid)
    timeline = tr.list(pid)
    anamneses = an.list(pid)
    labs = LabRepository(pr.db).list_results(pid)
    pack_repo = ClinicalPackRepository(pr.db)
    active_packs = pack_repo.active(pid)

    pdf = ClinicalPDF()
    pdf.report_title = "Relatório Clínico Nutricional"
    pdf.identity_lines = _identity(pr.db)
    pdf.set_auto_page_break(True, 15)
    pdf.add_page()

    if "patient" in sections:
        patient_text = (
            f"{patient['nome']} | Sexo: {patient['sexo']} | Nascimento: {patient['data_nascimento'] or '-'}\n"
            f"Telefone: {patient['telefone'] or '-'} | E-mail: {patient['email'] or '-'}"
        )
        if patient["observacoes"]:
            patient_text += f"\nObservações: {patient['observacoes']}"
        _txt(pdf, "Paciente", patient_text)

    if "anamnesis" in sections and anamneses:
        latest = anamneses[0]
        data = an.data(latest)
        ordered = [f"{k}: {v}" for k, v in data.items() if str(v).strip()]
        _txt(pdf, f"Anamnese - versão {latest['versao'] or '-'}", "\n".join(ordered) or latest["conteudo"] or "-")

    if "assessment" in sections and assessments:
        a = assessments[-1]
        _txt(
            pdf,
            "Última avaliação",
            f"Data: {a['data']} | Peso: {a['peso']} kg | Altura: {a['altura_cm']} cm | "
            f"IMC: {a['imc']} | Gordura: {a['pg_final']}% | Massa magra: {a['massa_magra']} kg | VET: {a['vet']} kcal",
        )

    if "evolution" in sections and assessments:
        lines = []
        for a in assessments[-8:]:
            lines.append(
                f"{a['data']}: peso {a['peso'] or '-'} kg | IMC {a['imc'] or '-'} | "
                f"gordura {a['pg_final'] or '-'}% | cintura {a['cintura'] or '-'} cm"
            )
        _txt(pdf, "Evolução antropométrica", "\n".join(lines))

    if "plan" in sections and plans:
        p = next((x for x in plans if x["status"] == "Ativo"), plans[0])
        totals, meals = plan_nutrients(p["id"], pl)
        meal_lines = [f"{meal}: {vals.get('kcal', 0):.0f} kcal" for meal, vals in meals.items()]
        _txt(
            pdf,
            f"Plano alimentar v{p['version_no'] or 1}",
            f"{p['nome']} | Meta: {p['vet_meta']} kcal | Calculado: {totals.get('kcal', 0):.0f} kcal\n"
            f"Proteína {totals.get('proteina', 0):.1f} g | Carboidrato {totals.get('carboidrato', 0):.1f} g | "
            f"Lipídios {totals.get('lipideos', 0):.1f} g\n" + "\n".join(meal_lines),
        )
        statuses = target_status(p["id"], pl)
        if statuses:
            _txt(
                pdf,
                "Metas nutricionais",
                "\n".join(
                    f"{s['nutrient']}: {s['actual']:.1f}/{s['target']} {s['unit']} ({s['status']})"
                    for s in statuses
                ),
            )
        meal_status = meal_distribution_status(p["id"], pl)
        if meal_status:
            _txt(
                pdf,
                "Distribuição por refeição",
                "\n".join(
                    f"{m['meal']}: {m['actual_kcal']:.0f} kcal / {m['expected_kcal']:.0f} kcal esperadas "
                    f"({m['pct']:.0f}% VET; {m['status']})"
                    for m in meal_status
                ),
            )

    if "labs" in sections and labs:
        lab_lines=[]
        for r in labs[:30]:
            value=r['value_numeric'] if r['value_numeric'] is not None else r['value_text']
            marker=f"{r['marker_name']}: {value} {r['unit'] or ''}".strip()
            if r['flag']:marker+=f" ({r['flag']})"
            lab_lines.append(f"{r['data_coleta']} - {marker}")
        _txt(pdf,"Exames laboratoriais","\n".join(lab_lines))

    if "packs" in sections and active_packs:
        pack_lines=[]
        for active in active_packs:
            latest=pack_repo.latest_record(pid,active['pack_slug']);label=PACK_DEFINITIONS.get(active['pack_slug'],{}).get('label',active['pack_slug'])
            if latest:
                data=latest['data_json'];summary=', '.join(f"{k}: {v}" for k,v in list(data.items())[:8] if v not in ('',None,[],False))
                pack_lines.append(f"{label} ({latest['record_date']}): {summary or 'acompanhamento registrado'}")
            else:pack_lines.append(f"{label}: ativo, sem acompanhamento registrado")
        _txt(pdf,"Packs clínicos","\n".join(pack_lines))

    if "timeline" in sections:
        _txt(
            pdf,
            "Linha do tempo",
            "\n".join(f"{e.get('event_date', '')} - {e.get('title', '')}" for e in timeline[:30]) or "Sem eventos",
        )

    path = Path(destination)
    path.parent.mkdir(parents=True, exist_ok=True)
    pdf.output(str(path))
    return path


def generate_from_template(pid, destination, rendered_text, title="Documento"):
    pdf = ClinicalPDF()
    pdf.report_title = title
    pdf.set_auto_page_break(True, 15)
    pdf.add_page()
    pdf.set_font("Helvetica", "", 10)
    pdf.multi_cell(0, 6, _pdf_text(rendered_text), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    path = Path(destination)
    path.parent.mkdir(parents=True, exist_ok=True)
    pdf.output(str(path))
    return path
