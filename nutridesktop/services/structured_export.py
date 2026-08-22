from __future__ import annotations
import csv,io,json,zipfile
from datetime import datetime,date
from pathlib import Path
from xml.sax.saxutils import escape
from nutridesktop.data.database import Database,db
from nutridesktop.version import VERSION_INFO

TABLES={
 'Pacientes':("SELECT * FROM pacientes ORDER BY id",()),
 'Avaliacoes':("SELECT * FROM avaliacoes ORDER BY paciente_id,data,id",()),
 'Anamneses':("SELECT * FROM anamneses_paciente ORDER BY paciente_id,versao,id",()),
 'Consultas':("SELECT * FROM consultas ORDER BY data,hora,id",()),
 'Planos':("SELECT * FROM planos ORDER BY paciente_id,id",()),
 'PlanoItens':("SELECT * FROM plano_itens ORDER BY plano_id,id",()),
 'MetasPlano':("SELECT * FROM plano_metas ORDER BY plano_id,id",()),
 'MetasRefeicao':("SELECT * FROM refeicao_metas ORDER BY plano_id,id",()),
 'Crescimento':("SELECT * FROM growth_measurements ORDER BY paciente_id,data,id",()),
 'Timeline':("SELECT * FROM timeline_events ORDER BY paciente_id,event_date,id",()),
 'Documentos':("SELECT id,paciente_id,tipo,nome_arquivo,data,managed,sha256 FROM documentos_paciente ORDER BY paciente_id,id",()),
 'Fotos':("SELECT id,paciente_id,data,observacao FROM fotos_paciente ORDER BY paciente_id,id",()),
 'RevisoesAvaliacoes':("SELECT ar.* FROM avaliacao_revisoes ar JOIN avaliacoes a ON a.id=ar.avaliacao_id ORDER BY ar.avaliacao_id,ar.versao",()),
 'VersoesPlanos':("SELECT pv.* FROM plano_versoes pv JOIN planos p ON p.id=pv.plano_id ORDER BY pv.plano_id,pv.versao",()),
}

def _rows(database:Database,sql,args=()):
    with database.connect() as c:return [dict(r) for r in c.execute(sql,args).fetchall()]

def practice_data(database:Database=db):return {name:_rows(database,sql,args) for name,(sql,args) in TABLES.items()}

def export_json(path,database:Database=db):
    data={'exported_at':datetime.now().isoformat(),'versions':VERSION_INFO.as_dict(),'tables':practice_data(database)}
    Path(path).write_text(json.dumps(data,ensure_ascii=False,indent=2,default=str),encoding='utf-8');return Path(path)

def export_csv_zip(path,database:Database=db):
    path=Path(path);data=practice_data(database)
    with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED) as z:
        for name,rows in data.items():
            out=io.StringIO();fields=list(rows[0].keys()) if rows else ['sem_dados'];w=csv.DictWriter(out,fieldnames=fields,delimiter=';',extrasaction='ignore');w.writeheader()
            for row in rows:w.writerow({k:'' if v is None else v for k,v in row.items()})
            z.writestr(f'{name}.csv',out.getvalue().encode('utf-8-sig'))
        z.writestr('metadata.json',json.dumps({'exported_at':datetime.now().isoformat(),'versions':VERSION_INFO.as_dict()},ensure_ascii=False,indent=2))
    return path

def _col(n):
    s=''
    while n:
        n,r=divmod(n-1,26);s=chr(65+r)+s
    return s

def _cell(ref,value):
    if value is None:return f'<c r="{ref}" t="inlineStr"><is><t></t></is></c>'
    if isinstance(value,bool):return f'<c r="{ref}" t="b"><v>{1 if value else 0}</v></c>'
    if isinstance(value,(int,float)) and not isinstance(value,bool):return f'<c r="{ref}"><v>{value}</v></c>'
    txt=escape(str(value))
    return f'<c r="{ref}" t="inlineStr"><is><t xml:space="preserve">{txt}</t></is></c>'

def _sheet_xml(rows):
    fields=list(rows[0].keys()) if rows else ['sem_dados'];allrows=[dict(zip(fields,fields))]+rows
    xml=['<?xml version="1.0" encoding="UTF-8" standalone="yes"?>','<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData>']
    for ri,row in enumerate(allrows,1):
        xml.append(f'<row r="{ri}">')
        for ci,k in enumerate(fields,1):xml.append(_cell(f'{_col(ci)}{ri}',row.get(k,'')))
        xml.append('</row>')
    xml.append('</sheetData></worksheet>');return ''.join(xml)

def export_xlsx(path,database:Database=db):
    """Dependency-free XLSX export using inline strings; keeps desktop runtime small."""
    path=Path(path);data=practice_data(database);names=list(data)
    content_types=['<?xml version="1.0" encoding="UTF-8" standalone="yes"?>','<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">','<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>','<Default Extension="xml" ContentType="application/xml"/>','<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>','<Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>']
    for i in range(1,len(names)+1):content_types.append(f'<Override PartName="/xl/worksheets/sheet{i}.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>')
    content_types.append('</Types>')
    workbook=['<?xml version="1.0" encoding="UTF-8" standalone="yes"?>','<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets>']
    rels=['<?xml version="1.0" encoding="UTF-8" standalone="yes"?>','<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">']
    for i,name in enumerate(names,1):
        workbook.append(f'<sheet name="{escape(name[:31])}" sheetId="{i}" r:id="rId{i}"/>');rels.append(f'<Relationship Id="rId{i}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet{i}.xml"/>')
    rels.append(f'<Relationship Id="rId{len(names)+1}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>');rels.append('</Relationships>');workbook.append('</sheets></workbook>')
    rootrels='<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/></Relationships>'
    styles='<?xml version="1.0" encoding="UTF-8" standalone="yes"?><styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><fonts count="1"><font><sz val="11"/><name val="Calibri"/></font></fonts><fills count="1"><fill><patternFill patternType="none"/></fill></fills><borders count="1"><border/></borders><cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs><cellXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/></cellXfs></styleSheet>'
    with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED) as z:
        z.writestr('[Content_Types].xml',''.join(content_types));z.writestr('_rels/.rels',rootrels);z.writestr('xl/workbook.xml',''.join(workbook));z.writestr('xl/_rels/workbook.xml.rels',''.join(rels));z.writestr('xl/styles.xml',styles)
        for i,name in enumerate(names,1):z.writestr(f'xl/worksheets/sheet{i}.xml',_sheet_xml(data[name]))
    return path
