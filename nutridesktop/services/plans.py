from __future__ import annotations
from collections import defaultdict
from nutridesktop.data.repositories import FoodRepository, RecipeRepository, PlanRepository

NUTRIENTS=("kcal","proteina","lipideos","carboidrato","fibra","calcio","ferro","zinco","magnesio","vitamina_c","sodio","potassio")

def _scaled(row,grams):
    return {n:(float(row[n] or 0)*grams/100) for n in NUTRIENTS}

def recipe_nutrients(recipe_id,repo=None):
    repo=repo or RecipeRepository(); rows=repo.ingredients(recipe_id); total=defaultdict(float)
    for r in rows:
        for n,v in _scaled(r,float(r['quantidade_g'] or 0)).items():total[n]+=v
    with repo.db.connect() as c: rec=c.execute('SELECT porcoes FROM receitas WHERE id=?',(recipe_id,)).fetchone(); servings=max(float(rec['porcoes'] or 1),1) if rec else 1
    return {k:v/servings for k,v in total.items()}

def plan_nutrients(plan_id,plan_repo=None):
    repo=plan_repo or PlanRepository(); total=defaultdict(float); meals=defaultdict(lambda:defaultdict(float))
    for it in repo.items(plan_id):
        if it['alimento_id']:
            vals=_scaled(it,float(it['quantidade_g'] or 0))
        elif it['receita_id']:
            vals={k:v*float(it['quantidade_porcoes'] or 1) for k,v in recipe_nutrients(it['receita_id'], RecipeRepository(repo.db)).items()}
        else:continue
        for k,v in vals.items(): total[k]+=v; meals[it['refeicao'] or 'Sem refeição'][k]+=v
    return dict(total),{m:dict(v) for m,v in meals.items()}

def substitute(food_id,grams,query="",food_repo=None,tolerance=0.15,limit=12):
    repo=food_repo or FoodRepository(); base=repo.get(food_id)
    if not base:raise KeyError(food_id)
    target=float(base['kcal'] or 0)*grams/100
    candidates=repo.search(query or '',200); out=[]
    for c in candidates:
        kcal100=float(c['kcal'] or 0)
        if c['id']==food_id or kcal100<=0:continue
        g=target/kcal100*100
        pbase=float(base['proteina'] or 0)*grams/100; pc=float(c['proteina'] or 0)*g/100
        macro_penalty=abs(pc-pbase)/(max(pbase,5))
        if macro_penalty<=0.8: out.append({'food_id':c['id'],'descricao':c['descricao'],'grams':round(g,1),'kcal':round(target,1),'protein_delta':round(pc-pbase,1),'score':macro_penalty})
    return sorted(out,key=lambda x:x['score'])[:limit]

def target_status(plan_id,plan_repo=None):
    repo=plan_repo or PlanRepository(); totals,_=plan_nutrients(plan_id,repo)
    with repo.db.connect() as c:targets=c.execute('SELECT * FROM plano_metas WHERE plano_id=?',(plan_id,)).fetchall()
    result=[]
    for t in targets:
        actual=totals.get(t['nutriente'],0); target=t['meta'] or 0; pct=(actual/target*100) if target else None
        status='ok'
        if t['limite_min'] is not None and actual<t['limite_min']:status='baixo'
        if t['limite_max'] is not None and actual>t['limite_max']:status='alto'
        result.append({'nutrient':t['nutriente'],'actual':actual,'target':target,'unit':t['unidade'],'pct':pct,'status':status})
    return result

def apply_lifecycle_dri(plan_id,age,sex,pregnant=False,lactating=False,plan_repo=None):
    from nutridesktop.clinical.dri_lifecycle import recommendations
    repo=plan_repo or PlanRepository();refs=recommendations(age,sex,pregnant,lactating)
    column_map={'calcio':'calcio','ferro':'ferro','zinco':'zinco','vitamina_c':'vitamina_c'}
    for nutrient,dri in refs.items():repo.set_target(plan_id,column_map[nutrient],dri.value,dri.unit,0.8*dri.value,None)
    return refs


def meal_distribution_status(plan_id, plan_repo=None):
    repo = plan_repo or PlanRepository()
    totals, meals = plan_nutrients(plan_id, repo)
    with repo.db.connect() as c:
        plan = c.execute("SELECT vet_meta FROM planos WHERE id=?", (plan_id,)).fetchone()
        targets = c.execute("SELECT * FROM refeicao_metas WHERE plano_id=? ORDER BY refeicao", (plan_id,)).fetchall()
    vet = float(plan["vet_meta"] or totals.get("kcal", 0) or 0) if plan else 0
    out = []
    for target in targets:
        meal = target["refeicao"]
        pct = float(target["percentual_vet"] or 0)
        expected = vet * pct / 100 if vet else 0
        actual = float(meals.get(meal, {}).get("kcal", 0))
        delta_pct = ((actual - expected) / expected * 100) if expected else None
        status = "ok" if delta_pct is None or abs(delta_pct) <= 20 else ("alto" if delta_pct > 0 else "baixo")
        out.append({"meal": meal, "pct": pct, "expected_kcal": expected, "actual_kcal": actual, "delta_pct": delta_pct, "status": status})
    return out
