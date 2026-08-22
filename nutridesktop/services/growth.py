from __future__ import annotations
from datetime import date,datetime
from nutridesktop.clinical.growth import assess
from nutridesktop.data.database import Database,db
class GrowthService:
    def __init__(self,database:Database=db):self.db=database
    def assess_and_save(self,pid,sex,birth_date,measurement_date,weight=None,height=None):
        b=date.fromisoformat(birth_date);m=date.fromisoformat(measurement_date);age=(m-b).days
        res=assess(sex,age,weight,height); bmi=(weight/(height/100)**2) if weight and height else None
        def z(key): return res.get(key).zscore if res.get(key) else None
        with self.db.transaction() as c:
            cur=c.execute("INSERT INTO growth_measurements(paciente_id,data,idade_dias,peso,altura_cm,imc,waz,haz,bmiz,wfhz,source) VALUES(?,?,?,?,?,?,?,?,?,?,?)",(pid,measurement_date,age,weight,height,bmi,z('weight_age'),z('height_age'),z('bmi_age'),z('weight_height'),'WHO 2006/2007'))
            gid=cur.lastrowid;c.execute("INSERT INTO timeline_events(paciente_id,event_type,event_date,title,entity_id) VALUES(?,?,?,?,?)",(pid,'crescimento',measurement_date,'Avaliação de crescimento WHO',gid))
        return res
    def list(self,pid):
        with self.db.connect() as c:return c.execute("SELECT * FROM growth_measurements WHERE paciente_id=? ORDER BY data",(pid,)).fetchall()
