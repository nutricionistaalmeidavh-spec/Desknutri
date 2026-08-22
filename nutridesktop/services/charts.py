from __future__ import annotations
from datetime import datetime
LABELS={'peso':'Peso (kg)','imc':'IMC','pg_final':'Gordura (%)','massa_magra':'Massa magra (kg)','cintura':'Cintura (cm)'}
def _dates(rows):
    out=[]
    for r in rows:
        raw=r['data']
        try:out.append(datetime.fromisoformat(raw))
        except ValueError:out.append(datetime.strptime(raw,'%d/%m/%Y'))
    return out
def patient_metric_figure(assessments,metric='peso'):
    import matplotlib.figure
    rows=[r for r in assessments if r[metric] is not None];fig=matplotlib.figure.Figure(figsize=(7,4),tight_layout=True);ax=fig.add_subplot(111)
    if rows:ax.plot(_dates(rows),[r[metric] for r in rows],marker='o');ax.set_ylabel(LABELS.get(metric,metric))
    ax.set_title(f"Evolução — {LABELS.get(metric,metric)}");ax.grid(True,alpha=.2);return fig
def patient_evolution_figure(assessments):return patient_metric_figure(assessments,'peso')
def growth_z_figure(measurements):
    import matplotlib.figure
    fig=matplotlib.figure.Figure(figsize=(7,4),tight_layout=True);ax=fig.add_subplot(111);x=_dates(measurements)
    for key,label in [('waz','Peso/idade'),('haz','Estatura/idade'),('bmiz','IMC/idade')]:
        ys=[r[key] for r in measurements]
        if any(v is not None for v in ys):ax.plot(x,ys,marker='o',label=label)
    for z in (-3,-2,0,1,2,3):ax.axhline(z,linewidth=.6,alpha=.25)
    ax.set_ylabel('Z-score WHO');ax.set_ylim(-4,4);ax.legend();ax.grid(True,alpha=.2);return fig
