from __future__ import annotations
import math

FATORES_ATIVIDADE={"Sedentário":1.2,"Levemente ativo":1.375,"Moderadamente ativo":1.55,"Muito ativo":1.725,"Extremamente ativo":1.9}

def siri(d): return (4.95/d-4.50)*100

def brozek(d): return (4.57/d-4.142)*100

def jp7(s,idade,sexo): return (1.112-.00043499*s+.00000055*s*s-.00028826*idade) if sexo=="M" else (1.097-.00046971*s+.00000056*s*s-.00012828*idade)
def jp3(s,idade,sexo): return (1.10938-.0008267*s+.0000016*s*s-.0002574*idade) if sexo=="M" else (1.0994921-.0009929*s+.0000023*s*s-.0001392*idade)
def durnin_womersley(s,idade,sexo):
    table={"M":[(19,1.1620,.0630),(29,1.1631,.0632),(39,1.1422,.0544),(49,1.1620,.0700),(999,1.1715,.0779)],"F":[(19,1.1549,.0678),(29,1.1599,.0717),(39,1.1423,.0632),(49,1.1333,.0612),(999,1.1339,.0645)]}
    if s<=0:return None
    for lim,c,m in table[sexo]:
        if idade<=lim:return c-m*math.log10(s)
def deurenberg(imc,idade,sexo): return 1.20*imc+.23*idade-10.8*(1 if sexo=="M" else 0)-5.4

def petroski4(s,idade,sexo,peso=None,altura_cm=None):
    if sexo=="M": return 1.10726863-.00081201*s+.00000212*s*s-.00041761*idade
    if peso is None or altura_cm is None:return None
    return 1.03465850-.00063129*s*s-.000311*idade-.00048890*peso+.00051345*altura_cm

def tmb_mifflin(peso,altura,idade,sexo): return 10*peso+6.25*altura-5*idade+(5 if sexo=="M" else -161)
def tmb_harris(peso,altura,idade,sexo): return (88.362+13.397*peso+4.799*altura-5.677*idade) if sexo=="M" else (447.593+9.247*peso+3.098*altura-4.330*idade)
def tmb_katch(magra): return 370+21.6*magra
def tmb_cunningham(magra): return 500+22*magra

def calcular_avaliacao_completa(sexo,idade,peso,altura_cm,dobras,formula_tmb="Mifflin-St Jeor",atividade="Sedentário",ajuste_pct=0,ptn_gkg=1.2,lip_pct=30,bia_pg=None):
    imc=peso/(altura_cm/100)**2; r={}
    if all(dobras.get(k) is not None for k in ["peitoral","axilar","triceps","subescapular","abdominal","suprailiaca","coxa"]):
        s=sum(dobras[k] for k in ["peitoral","axilar","triceps","subescapular","abdominal","suprailiaca","coxa"]); r["Jackson & Pollock 7 dobras"]=siri(jp7(s,idade,sexo))
    keys=["peitoral","abdominal","coxa"] if sexo=="M" else ["triceps","suprailiaca","coxa"]
    if all(dobras.get(k) is not None for k in keys):r["Jackson & Pollock 3 dobras"]=siri(jp3(sum(dobras[k] for k in keys),idade,sexo))
    keys=["biceps","triceps","subescapular","suprailiaca"]
    if all(dobras.get(k) is not None for k in keys):
        d=durnin_womersley(sum(dobras[k] for k in keys),idade,sexo)
        if d:r["Durnin & Womersley"]=brozek(d)
    keys=["subescapular","triceps","suprailiaca","panturrilha"] if sexo=="M" else ["axilar","suprailiaca","coxa","panturrilha"]
    if all(dobras.get(k) is not None for k in keys):
        d=petroski4(sum(dobras[k] for k in keys),idade,sexo,peso,altura_cm)
        if d:r["Petroski 4 dobras (BR)"]=siri(d)
    r["Deurenberg (estimativa por IMC)"]=deurenberg(imc,idade,sexo)
    if bia_pg is not None:r["Bioimpedância (informado)"]=bia_pg
    fold=[v for k,v in r.items() if "Deurenberg" not in k and "Bioimpedância" not in k]
    if bia_pg is not None:pg=bia_pg;origem="Bioimpedância"
    elif fold:pg=sum(fold)/len(fold);origem=f"média de {len(fold)} método(s) com dobras"
    else:pg=r["Deurenberg (estimativa por IMC)"];origem="Deurenberg"
    fat=peso*pg/100; lean=peso-fat
    tmb={"Mifflin-St Jeor":lambda:tmb_mifflin(peso,altura_cm,idade,sexo),"Harris-Benedict":lambda:tmb_harris(peso,altura_cm,idade,sexo),"Katch-McArdle":lambda:tmb_katch(lean),"Cunningham":lambda:tmb_cunningham(lean)}.get(formula_tmb,lambda:tmb_mifflin(peso,altura_cm,idade,sexo))()
    factor=FATORES_ATIVIDADE[atividade]; get=tmb*factor; vet=get*(1+ajuste_pct/100); ptn=ptn_gkg*peso; lip=vet*(lip_pct/100)/9; cho=(vet-ptn*4-lip*9)/4
    return {"imc":imc,"resultados_pg":r,"pg_final":pg,"origem_pg":origem,"massa_gorda":fat,"massa_magra":lean,"tmb":tmb,"fator_atividade":factor,"get_total":get,"vet":vet,"ptn_g":ptn,"lip_g":lip,"cho_g":cho}
