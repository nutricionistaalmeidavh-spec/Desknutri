from __future__ import annotations

import html
import json
import os
import time
from collections import defaultdict, deque
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse

from .core import (
    AdminService, LicenseError, LicenseService, LicenseSigner, LicenseStore, ServerPaths,
    get_or_create_server_secret, make_session, parse_session,
)

paths = ServerPaths.from_env()
store = LicenseStore(paths.db_path)
store.initialize()
signer = LicenseSigner(paths.private_key)
licenses = LicenseService(store, signer)
admins = AdminService(store)
secret = get_or_create_server_secret(paths)
app = FastAPI(title="NutriDesktop License Server", version="1.0")

_ATTEMPTS: dict[str, deque[float]] = defaultdict(deque)

def rate_limit(key: str, limit: int = 12, window: int = 900) -> bool:
    now = time.time(); q = _ATTEMPTS[key]
    while q and q[0] < now-window: q.popleft()
    if len(q) >= limit: return False
    q.append(now); return True


def esc(v: Any) -> str: return html.escape("" if v is None else str(v), quote=True)

def page(title: str, body: str, session: dict | None = None) -> HTMLResponse:
    nav = ""
    if session:
        nav = f'''<header><a class="brand" href="/admin">NutriDesktop <span>Licenças</span></a><div class="user">{esc(session['email'])}<form method="post" action="/admin/logout"><input type="hidden" name="csrf" value="{esc(session['csrf'])}"><button class="link">Sair</button></form></div></header>'''
    css = '''
    :root{--bg:#f6f7f8;--card:#fff;--ink:#17201f;--muted:#66716f;--line:#e3e8e7;--accent:#145c57;--soft:#e4f0ed;--danger:#b42318}
    *{box-sizing:border-box}body{margin:0;font:14px Inter,Segoe UI,Arial,sans-serif;background:var(--bg);color:var(--ink)}
    header{height:64px;background:#fff;border-bottom:1px solid var(--line);display:flex;align-items:center;justify-content:space-between;padding:0 28px;position:sticky;top:0}.brand{font-size:20px;font-weight:800;color:var(--ink);text-decoration:none}.brand span{color:var(--accent)}.user{display:flex;gap:14px;align-items:center;color:var(--muted)}
    main{max-width:1180px;margin:28px auto;padding:0 20px}.grid{display:grid;gap:16px}.stats{grid-template-columns:repeat(5,1fr)}.two{grid-template-columns:1.2fr .8fr}.card{background:var(--card);border:1px solid var(--line);border-radius:16px;padding:20px;box-shadow:0 1px 2px #00000008}.metric b{display:block;font-size:28px;color:var(--accent);margin-top:8px}.muted{color:var(--muted)}
    h1{font-size:28px;margin:0 0 6px}h2{font-size:18px;margin:0 0 14px}table{width:100%;border-collapse:collapse}th,td{text-align:left;border-bottom:1px solid var(--line);padding:12px 10px;vertical-align:top}th{font-size:12px;color:var(--muted)}
    input,select,textarea{width:100%;padding:10px 12px;border:1px solid #ccd5d3;border-radius:10px;background:white;font:inherit}textarea{min-height:82px}.form{display:grid;grid-template-columns:repeat(2,1fr);gap:12px}.full{grid-column:1/-1}.btn,button{border:0;border-radius:10px;padding:10px 14px;background:var(--accent);color:white;font-weight:700;cursor:pointer;text-decoration:none;display:inline-block}.btn.secondary,button.secondary{background:white;color:var(--ink);border:1px solid var(--line)}.btn.danger,button.danger{background:var(--danger)}button.link{background:none;color:var(--accent);padding:0}.pill{padding:5px 9px;border-radius:999px;background:var(--soft);color:var(--accent);font-size:12px;font-weight:700}.pill.blocked{background:#fee4e2;color:var(--danger)}.actions{display:flex;gap:8px;flex-wrap:wrap}.notice{padding:12px 14px;border-radius:10px;background:var(--soft);margin:12px 0}.login{max-width:420px;margin:10vh auto}.login .card{padding:28px}.stack>*+*{margin-top:12px}
    @media(max-width:850px){.stats,.two,.form{grid-template-columns:1fr 1fr}.stats .card:last-child{grid-column:1/-1}table{font-size:12px}}@media(max-width:560px){.stats,.two,.form{grid-template-columns:1fr}header{padding:0 16px}.user{font-size:0}}
    '''
    return HTMLResponse(f"<!doctype html><html lang='pt-BR'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>{esc(title)}</title><style>{css}</style></head><body>{nav}<main>{body}</main></body></html>")

async def form_data(request: Request) -> dict[str,str]:
    form = await request.form(); return {str(k):str(v) for k,v in form.items()}

def admin_session(request: Request): return parse_session(secret, request.cookies.get("nd_admin"))
def require_csrf(session: dict | None, data: dict[str,str]) -> bool: return bool(session and data.get("csrf") == session.get("csrf"))

@app.get("/health")
def health():
    return {"ok": True, "product": "NutriDesktop", "keys_configured": paths.private_key.exists() and paths.public_key.exists()}

@app.post("/api/v1/activate")
async def api_activate(request: Request):
    data = await request.json(); ip = request.client.host if request.client else "unknown"; email = str(data.get("email","")).lower()
    if not rate_limit(f"activate:{ip}:{email}", 10, 900): return JSONResponse({"code":"rate_limited","message":"Muitas tentativas. Tente novamente mais tarde."},429)
    try:
        return licenses.activate(email,str(data.get("password","")),str(data.get("machine_id","")),str(data.get("device_name","")),str(data.get("app_version","")))
    except LicenseError as e: return JSONResponse({"code":e.code,"message":e.message},e.status)
    except RuntimeError as e: return JSONResponse({"code":"server_not_configured","message":str(e)},503)

@app.post("/api/v1/refresh")
async def api_refresh(request: Request):
    data=await request.json()
    try:return licenses.refresh(str(data.get("device_token","")),str(data.get("machine_id","")),str(data.get("app_version","")))
    except LicenseError as e:return JSONResponse({"code":e.code,"message":e.message},e.status)
    except RuntimeError as e:return JSONResponse({"code":"server_not_configured","message":str(e)},503)

@app.post("/api/v1/unlink")
async def api_unlink(request: Request):
    data=await request.json()
    try:licenses.unlink(str(data.get("device_token","")),str(data.get("machine_id","")));return {"ok":True}
    except LicenseError as e:return JSONResponse({"code":e.code,"message":e.message},e.status)

@app.post("/api/v1/change-password")
async def api_change_password(request: Request):
    data=await request.json();ip=request.client.host if request.client else "unknown"
    if not rate_limit(f"password:{ip}:{str(data.get('email','')).lower()}",8,900): return JSONResponse({"code":"rate_limited","message":"Muitas tentativas."},429)
    try:licenses.change_password(str(data.get("email","")),str(data.get("current_password","")),str(data.get("new_password","")));return {"ok":True}
    except LicenseError as e:return JSONResponse({"code":e.code,"message":e.message},e.status)

@app.get("/admin/login")
def login_get():
    return page("Entrar",'''<div class="login"><div class="card"><h1>Painel de Licenças</h1><p class="muted">Acesso administrativo do NutriDesktop.</p><form class="stack" method="post"><input name="email" type="email" placeholder="E-mail administrativo" required><input name="password" type="password" placeholder="Senha" required><button>Entrar</button></form></div></div>''')

@app.post("/admin/login")
async def login_post(request: Request):
    data=await form_data(request);ip=request.client.host if request.client else "unknown"
    if not rate_limit(f"admin:{ip}",10,900):return page("Entrar","<div class='login'><div class='card'><h2>Muitas tentativas</h2><p>Tente novamente mais tarde.</p></div></div>")
    row=admins.verify_admin(data.get("email",""),data.get("password",""))
    if not row:return page("Entrar","<div class='login'><div class='card'><h2>Credenciais inválidas</h2><a class='btn secondary' href='/admin/login'>Voltar</a></div></div>")
    token,_=make_session(secret,row["id"],row["email"]);resp=RedirectResponse("/admin",303);resp.set_cookie("nd_admin",token,httponly=True,samesite="strict",secure=os.environ.get("NUTRIDESK_COOKIE_SECURE","1")!="0",max_age=8*3600);return resp

@app.post("/admin/logout")
async def logout(request:Request):
    s=admin_session(request);data=await form_data(request)
    if not require_csrf(s,data):return RedirectResponse("/admin/login",303)
    resp=RedirectResponse("/admin/login",303);resp.delete_cookie("nd_admin");return resp

@app.get("/admin")
def dashboard(request:Request):
    s=admin_session(request)
    if not s:return RedirectResponse("/admin/login",303)
    stats=admins.stats();rows=admins.list_accounts();cards=''.join(f"<div class='card metric'><span class='muted'>{label}</span><b>{stats[key]}</b></div>" for key,label in [('accounts','Clientes'),('active','Contas ativas'),('pending','Aguardando 1º acesso'),('blocked','Bloqueadas'),('devices','Dispositivos')])
    trs=''.join(f"<tr><td><b>{esc(r['display_name'] or '—')}</b><br><span class='muted'>{esc(r['email'])}</span></td><td><span class='pill{' blocked' if r['status']=='blocked' else ''}'>{esc(r['status'])}</span></td><td>{esc(r['plan'])}</td><td>{r['device_count']}/{r['max_devices']}</td><td>{esc(r['expires_at'] or 'Vitalício')}</td><td><a class='btn secondary' href='/admin/accounts/{r['id']}'>Gerenciar</a></td></tr>" for r in rows)
    body=f'''<h1>Licenças</h1><p class="muted">Libere e-mails, acompanhe contas e controle computadores autorizados.</p><div class="grid stats">{cards}</div><div class="grid two" style="margin-top:16px"><div class="card"><h2>Clientes</h2><div style="overflow:auto"><table><thead><tr><th>Cliente</th><th>Conta</th><th>Plano</th><th>PCs</th><th>Validade</th><th></th></tr></thead><tbody>{trs or '<tr><td colspan=6>Nenhum cliente cadastrado.</td></tr>'}</tbody></table></div></div><div class="card"><h2>Liberar novo e-mail</h2><form class="form" method="post" action="/admin/accounts"><input type="hidden" name="csrf" value="{esc(s['csrf'])}"><div class="full"><input name="display_name" placeholder="Nome do cliente"></div><div class="full"><input name="email" type="email" placeholder="E-mail autorizado" required></div><div><input name="plan" value="Vitalício" placeholder="Plano"></div><div><input name="max_devices" type="number" min="1" value="1" placeholder="PCs"></div><div><input name="offline_days" type="number" min="1" max="365" value="30" placeholder="Dias offline"></div><div><input name="expires_at" type="date" placeholder="Validade"></div><div class="full"><textarea name="notes" placeholder="Observações internas"></textarea></div><div class="full"><button>Liberar acesso</button></div></form><div class="notice">No primeiro uso, o cliente informa este e-mail e cria a própria senha. Depois disso, o e-mail só ativa outro computador com a senha já cadastrada.</div></div></div>'''
    return page("Licenças",body,s)

@app.post("/admin/accounts")
async def create_account(request:Request):
    s=admin_session(request);data=await form_data(request)
    if not require_csrf(s,data):return RedirectResponse("/admin/login",303)
    try:aid=admins.authorize_email(data.get("email",""),data.get("display_name",""),data.get("plan","Vitalício"),int(data.get("max_devices","1")),int(data.get("offline_days","30")),data.get("expires_at") or None,data.get("notes",""));return RedirectResponse(f"/admin/accounts/{aid}",303)
    except Exception as e:return page("Erro",f"<div class='card'><h2>Não foi possível cadastrar</h2><p>{esc(e)}</p><a class='btn secondary' href='/admin'>Voltar</a></div>",s)

@app.get("/admin/accounts/{account_id}")
def account_detail(account_id:int,request:Request):
    s=admin_session(request)
    if not s:return RedirectResponse("/admin/login",303)
    a,devices,events=admins.get_account(account_id)
    if not a:return page("Não encontrado","<div class='card'>Conta não encontrada.</div>",s)
    drows=''.join(f"<tr><td><b>{esc(d['device_name'] or 'Computador')}</b><br><span class='muted'>{esc(d['machine_id'])}</span></td><td>{esc(d['app_version'] or '—')}</td><td>{esc(d['activated_at'])}</td><td>{esc(d['last_seen'] or '—')}</td><td>{'<span class="pill blocked">Revogado</span>' if d['revoked_at'] else f'<form method="post" action="/admin/devices/{d["id"]}/revoke"><input type="hidden" name="csrf" value="{esc(s["csrf"])}"><button class="danger">Desvincular</button></form>'}</td></tr>" for d in devices)
    erows=''.join(f"<tr><td>{esc(e['created_at'])}</td><td>{esc(e['event_type'])}</td><td class='muted'>{esc(e['details_json'])}</td></tr>" for e in events)
    body=f'''<div class="actions"><a class="btn secondary" href="/admin">← Clientes</a></div><div style="height:12px"></div><div class="grid two"><div class="card"><h1>{esc(a['display_name'] or a['email'])}</h1><p>{esc(a['email'])}</p><p><span class="pill{' blocked' if a['status']=='blocked' else ''}">{esc(a['status'])}</span></p><div class="actions"><form method="post" action="/admin/accounts/{a['id']}/block"><input type="hidden" name="csrf" value="{esc(s['csrf'])}"><input type="hidden" name="blocked" value="{'0' if a['status']=='blocked' else '1'}"><button class="{'secondary' if a['status']=='blocked' else 'danger'}">{'Desbloquear' if a['status']=='blocked' else 'Bloquear conta'}</button></form><form method="post" action="/admin/accounts/{a['id']}/reset-password"><input type="hidden" name="csrf" value="{esc(s['csrf'])}"><button class="secondary">Permitir nova senha</button></form></div></div><div class="card"><h2>Licença</h2><form class="form" method="post" action="/admin/accounts/{a['id']}/license"><input type="hidden" name="csrf" value="{esc(s['csrf'])}"><div><label>Plano</label><input name="plan" value="{esc(a['plan'])}"></div><div><label>Status</label><select name="status"><option value="active" {'selected' if a['license_status']=='active' else ''}>Ativa</option><option value="blocked" {'selected' if a['license_status']=='blocked' else ''}>Bloqueada</option></select></div><div><label>Máx. dispositivos</label><input type="number" min="1" name="max_devices" value="{a['max_devices']}"></div><div><label>Dias offline</label><input type="number" min="1" max="365" name="offline_days" value="{a['offline_days']}"></div><div class="full"><label>Validade (vazio = vitalício)</label><input type="date" name="expires_at" value="{esc(a['expires_at'] or '')}"></div><div class="full"><label>Observações</label><textarea name="notes">{esc(a['notes'] or '')}</textarea></div><div class="full"><button>Salvar licença</button></div></form></div></div><div class="card" style="margin-top:16px"><h2>Dispositivos</h2><div style="overflow:auto"><table><thead><tr><th>Computador</th><th>Versão</th><th>Ativado</th><th>Último acesso</th><th></th></tr></thead><tbody>{drows or '<tr><td colspan=5>Nenhum dispositivo ativado.</td></tr>'}</tbody></table></div></div><div class="card" style="margin-top:16px"><h2>Histórico</h2><div style="overflow:auto"><table><thead><tr><th>Data</th><th>Evento</th><th>Detalhes</th></tr></thead><tbody>{erows}</tbody></table></div></div>'''
    return page("Cliente",body,s)

@app.post("/admin/accounts/{account_id}/block")
async def block(account_id:int,request:Request):
    s=admin_session(request);d=await form_data(request)
    if not require_csrf(s,d):return RedirectResponse("/admin/login",303)
    admins.set_account_blocked(account_id,d.get("blocked")=='1');return RedirectResponse(f"/admin/accounts/{account_id}",303)

@app.post("/admin/accounts/{account_id}/reset-password")
async def reset_password(account_id:int,request:Request):
    s=admin_session(request);d=await form_data(request)
    if not require_csrf(s,d):return RedirectResponse("/admin/login",303)
    admins.reset_password(account_id);return RedirectResponse(f"/admin/accounts/{account_id}",303)

@app.post("/admin/accounts/{account_id}/license")
async def update_license(account_id:int,request:Request):
    s=admin_session(request);d=await form_data(request)
    if not require_csrf(s,d):return RedirectResponse("/admin/login",303)
    admins.update_license(account_id,d.get("plan","Vitalício"),int(d.get("max_devices","1")),int(d.get("offline_days","30")),d.get("expires_at") or None,d.get("status","active"),d.get("notes",""));return RedirectResponse(f"/admin/accounts/{account_id}",303)

@app.post("/admin/devices/{device_id}/revoke")
async def revoke_device(device_id:int,request:Request):
    s=admin_session(request);d=await form_data(request)
    if not require_csrf(s,d):return RedirectResponse("/admin/login",303)
    with store.connect() as c:r=c.execute("SELECT l.account_id FROM devices d JOIN licenses l ON l.id=d.license_id WHERE d.id=?",(device_id,)).fetchone()
    admins.revoke_device(device_id);return RedirectResponse(f"/admin/accounts/{r['account_id']}" if r else "/admin",303)
