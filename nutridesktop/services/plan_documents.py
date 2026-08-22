from __future__ import annotations
from pathlib import Path
from collections import defaultdict
from fpdf import FPDF
from fpdf.enums import XPos,YPos
from nutridesktop.data.repositories import PatientRepository,PlanRepository,TemplateRepository
from nutridesktop.services.templates import STYLE_PRESETS
from nutridesktop.services.plans import plan_nutrients


def _rgb(hexv):
    h=hexv.lstrip('#');return tuple(int(h[i:i+2],16) for i in (0,2,4))

def _txt(v):
    return str(v or '').replace('–','-').replace('—','-').encode('latin-1','replace').decode('latin-1')


def generate_plan_pdf(patient_id,plan_id,destination,template_id=None,database=None):
    pr=PatientRepository(database) if database else PatientRepository();db=pr.db
    patient=pr.get(patient_id);plans=PlanRepository(db);plan=next((p for p in plans.list(patient_id) if p['id']==plan_id),None)
    if not patient or not plan:raise ValueError('Paciente ou plano não encontrado.')
    tr=TemplateRepository(db)
    template=None
    if template_id:template=next((x for x in tr.list('Plano') if x['id']==template_id),None)
    template=template or tr.default('Plano')
    style=STYLE_PRESETS.get(template['style_key'] if template else 'clean_clinical',STYLE_PRESETS['clean_clinical'])
    accent=_rgb(style['accent']);soft=_rgb(style['soft']);text=_rgb(style['text'])
    items=plans.items(plan_id);totals,_=plan_nutrients(plan_id,plans);meals=defaultdict(list)
    for it in items:meals[it['refeicao'] or 'Refeição'].append(it)
    pdf=FPDF();pdf.set_auto_page_break(True,15);pdf.add_page();pdf.set_text_color(*text)
    pdf.set_fill_color(*accent);pdf.rect(0,0,pdf.w,25,'F');pdf.set_xy(12,8);pdf.set_text_color(255,255,255);pdf.set_font('Helvetica','B',18);pdf.cell(0,8,_txt('Plano alimentar'))
    pdf.set_text_color(*text);pdf.set_xy(12,31);pdf.set_font('Helvetica','B',15);pdf.cell(0,8,_txt(patient['nome']),new_x=XPos.LMARGIN,new_y=YPos.NEXT)
    pdf.set_font('Helvetica','',9);pdf.cell(0,6,_txt(f"{plan['nome']} • {plan['data']} • Meta {plan['vet_meta'] or '-'} kcal"),new_x=XPos.LMARGIN,new_y=YPos.NEXT);pdf.ln(3)
    for meal,rows in meals.items():
        pdf.set_fill_color(*soft);pdf.set_font('Helvetica','B',11);pdf.cell(0,8,_txt(meal),fill=True,new_x=XPos.LMARGIN,new_y=YPos.NEXT)
        pdf.set_font('Helvetica','',9)
        substitutions=plans.substitutions(plan_id)
        for it in rows:
            name=it['descricao'] or it['recipe_name'] or 'Item';qty=f"{float(it['quantidade_g'] or 0):g} g" if it['alimento_id'] else f"{float(it['quantidade_porcoes'] or 1):g} porção(ões)"
            pdf.cell(0,6,_txt(f"• {name} — {qty}"),new_x=XPos.LMARGIN,new_y=YPos.NEXT)
            for sub in substitutions:
                if sub['plano_item_id']==it['id']:
                    pdf.set_text_color(95,105,102);pdf.set_font('Helvetica','I',8);pdf.cell(0,5,_txt(f"   ou {sub['alternative_name']} — {float(sub['quantidade_g'] or 0):g} g"),new_x=XPos.LMARGIN,new_y=YPos.NEXT);pdf.set_text_color(*text);pdf.set_font('Helvetica','',9)
        pdf.ln(2)
    pdf.set_fill_color(*soft);pdf.set_font('Helvetica','B',10);pdf.cell(0,8,_txt('Resumo nutricional'),fill=True,new_x=XPos.LMARGIN,new_y=YPos.NEXT)
    pdf.set_font('Helvetica','',9);pdf.multi_cell(0,6,_txt(f"Energia: {totals.get('kcal',0):.0f} kcal | Proteína: {totals.get('proteina',0):.1f} g | Carboidratos: {totals.get('carboidrato',0):.1f} g | Lipídios: {totals.get('lipideos',0):.1f} g"),new_x=XPos.LMARGIN,new_y=YPos.NEXT)
    if plan['observacoes']:
        pdf.ln(2);pdf.set_font('Helvetica','B',10);pdf.cell(0,7,_txt('Orientações'),new_x=XPos.LMARGIN,new_y=YPos.NEXT);pdf.set_font('Helvetica','',9);pdf.multi_cell(0,5,_txt(plan['observacoes']),new_x=XPos.LMARGIN,new_y=YPos.NEXT)
    pdf.set_y(-15);pdf.set_text_color(110,120,117);pdf.set_font('Helvetica','',8);tpl_name=template['nome'] if template else style['label'];pdf.cell(0,6,_txt(f"NutriDesk • {tpl_name}"),align='C')
    out=Path(destination);out.parent.mkdir(parents=True,exist_ok=True);pdf.output(str(out));return out
