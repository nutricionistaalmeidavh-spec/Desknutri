"""
database.py - Camada de acesso ao banco de dados SQLite do NutriDesktop.
O banco Ã© um Ãºnico arquivo (nutridesktop.db) criado na primeira execuÃ§Ã£o,
na mesma pasta do programa (ou ao lado do .exe, quando empacotado). NÃ£o
precisa instalar nenhum servidor de banco.
"""

import sqlite3
import os
import sys
import csv
import json
import shutil
from datetime import date


def _pasta_dados():
    """Diret?rio grav?vel, independente de onde o programa foi instalado."""
    # NUTRIDESKTOP_DATA_DIR permite testes/suporte sem alterar o local de producao.
    raiz = os.environ.get("NUTRIDESKTOP_DATA_DIR") or os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
    destino = raiz if os.environ.get("NUTRIDESKTOP_DATA_DIR") else os.path.join(raiz, "NutriDesktop")
    os.makedirs(destino, exist_ok=True)
    return destino


def _pasta_recursos():
    """Pasta de recursos embutidos no pacote (ex: base TACO), somente leitura.
    Quando empacotado com --onefile, o PyInstaller extrai esses arquivos numa
    pasta temporÃ¡ria (sys._MEIPASS) a cada execuÃ§Ã£o."""
    if getattr(sys, "frozen", False):
        return getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
    return os.path.dirname(os.path.abspath(__file__))


BASE_DIR = _pasta_dados()
DB_PATH = os.path.join(BASE_DIR, "nutridesktop.db")
TACO_CSV = os.path.join(_pasta_recursos(), "data", "alimentos_taco.csv")


def _pasta_portatil_antiga():
    """Local da vers?o port?til anterior (nunca ? usado para novos dados)."""
    return os.path.dirname(sys.executable) if getattr(sys, "frozen", False) else os.path.dirname(os.path.abspath(__file__))


def migrar_dados_portateis():
    """Copia uma instala??o antiga apenas na primeira abertura da vers?o nova."""
    antigo = _pasta_portatil_antiga()
    if os.path.abspath(antigo) == os.path.abspath(BASE_DIR) or os.path.exists(DB_PATH):
        return False
    origem_db = os.path.join(antigo, "nutridesktop.db")
    if not os.path.exists(origem_db):
        return False
    shutil.copy2(origem_db, DB_PATH)
    for pasta in ("pacientes_arquivos", "fotos_pacientes"):
        origem, destino = os.path.join(antigo, pasta), os.path.join(BASE_DIR, pasta)
        if os.path.isdir(origem) and not os.path.exists(destino):
            shutil.copytree(origem, destino)
    return True


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    migrar_dados_portateis()
    conn = get_conn()
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS pacientes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        sexo TEXT NOT NULL,
        data_nascimento TEXT,
        telefone TEXT,
        email TEXT,
        observacoes TEXT,
        criado_em TEXT DEFAULT CURRENT_TIMESTAMP
    )""")

    c.execute("""
    CREATE TABLE IF NOT EXISTS avaliacoes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        paciente_id INTEGER NOT NULL,
        data TEXT NOT NULL,
        peso REAL, altura_cm REAL, idade REAL, imc REAL,

        dobra_triceps REAL, dobra_biceps REAL, dobra_subescapular REAL,
        dobra_suprailiaca REAL, dobra_abdominal REAL, dobra_coxa REAL,
        dobra_peitoral REAL, dobra_axilar REAL, dobra_panturrilha REAL,

        cintura REAL, quadril REAL, pescoco REAL,
        bia_pg REAL, bia_massa_magra REAL,

        pg_final REAL, origem_pg TEXT, massa_gorda REAL, massa_magra REAL,
        detalhes_pg TEXT,

        formula_tmb TEXT, tmb REAL, atividade TEXT, fator_atividade REAL,
        get_total REAL, ajuste_pct REAL, vet REAL,
        ptn_gkg REAL, ptn_g REAL, lip_pct REAL, lip_g REAL, cho_g REAL,

        observacoes TEXT,
        FOREIGN KEY (paciente_id) REFERENCES pacientes(id) ON DELETE CASCADE
    )""")

    c.execute("""
    CREATE TABLE IF NOT EXISTS alimentos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        categoria TEXT, descricao TEXT NOT NULL,
        kcal REAL, proteina REAL, lipideos REAL, carboidrato REAL, fibra REAL,
        calcio REAL, magnesio REAL, fosforo REAL, ferro REAL, sodio REAL,
        potassio REAL, cobre REAL, zinco REAL, tiamina REAL, riboflavina REAL,
        piridoxina REAL, niacina REAL, vitamina_c REAL, origem TEXT DEFAULT 'TACO'
    )""")

    c.execute("""
    CREATE TABLE IF NOT EXISTS planos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        paciente_id INTEGER NOT NULL,
        nome TEXT, data TEXT, vet_meta REAL, observacoes TEXT,
        FOREIGN KEY (paciente_id) REFERENCES pacientes(id) ON DELETE CASCADE
    )""")

    c.execute("""
    CREATE TABLE IF NOT EXISTS plano_itens (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        plano_id INTEGER NOT NULL,
        refeicao TEXT, alimento_id INTEGER, quantidade_g REAL,
        FOREIGN KEY (plano_id) REFERENCES planos(id) ON DELETE CASCADE,
        FOREIGN KEY (alimento_id) REFERENCES alimentos(id)
    )""")

    c.execute("""
    CREATE TABLE IF NOT EXISTS receitas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL, categoria TEXT, tags TEXT, porcoes REAL DEFAULT 1,
        modo_preparo TEXT
    )""")

    c.execute("""
    CREATE TABLE IF NOT EXISTS receita_ingredientes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        receita_id INTEGER NOT NULL, alimento_id INTEGER, quantidade_g REAL,
        FOREIGN KEY (receita_id) REFERENCES receitas(id) ON DELETE CASCADE,
        FOREIGN KEY (alimento_id) REFERENCES alimentos(id)
    )""")

    c.execute("""
    CREATE TABLE IF NOT EXISTS planos_modelo (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL, categoria TEXT, vet_alvo REAL, descricao TEXT
    )""")

    c.execute("""
    CREATE TABLE IF NOT EXISTS planos_modelo_itens (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        modelo_id INTEGER NOT NULL, refeicao TEXT, alimento_id INTEGER, quantidade_g REAL,
        FOREIGN KEY (modelo_id) REFERENCES planos_modelo(id) ON DELETE CASCADE,
        FOREIGN KEY (alimento_id) REFERENCES alimentos(id)
    )""")

    c.execute("""
    CREATE TABLE IF NOT EXISTS configuracoes (
        chave TEXT PRIMARY KEY,
        valor TEXT
    )""")

    c.execute("""
    CREATE TABLE IF NOT EXISTS diretrizes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL, fonte TEXT, pontos TEXT
    )""")

    c.execute("""
    CREATE TABLE IF NOT EXISTS documentos_paciente (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        paciente_id INTEGER NOT NULL, tipo TEXT, nome_arquivo TEXT,
        caminho TEXT, data TEXT,
        FOREIGN KEY (paciente_id) REFERENCES pacientes(id) ON DELETE CASCADE
    )""")

    c.execute("""
    CREATE TABLE IF NOT EXISTS anamneses_modelo (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL, conteudo TEXT
    )""")

    c.execute("""
    CREATE TABLE IF NOT EXISTS anamneses_paciente (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        paciente_id INTEGER NOT NULL, nome_modelo TEXT, conteudo TEXT, data TEXT,
        tipo TEXT DEFAULT 'Estruturada', dados_json TEXT DEFAULT '{}', versao INTEGER DEFAULT 1,
        FOREIGN KEY (paciente_id) REFERENCES pacientes(id) ON DELETE CASCADE
    )""")

    c.execute("""
    CREATE TABLE IF NOT EXISTS fotos_paciente (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        paciente_id INTEGER NOT NULL, data TEXT NOT NULL, observacao TEXT, caminho TEXT NOT NULL,
        FOREIGN KEY (paciente_id) REFERENCES pacientes(id) ON DELETE CASCADE
    )""")

    c.execute("""
    CREATE TABLE IF NOT EXISTS consultas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        paciente_id INTEGER NOT NULL, data TEXT, hora TEXT,
        status TEXT DEFAULT 'Agendada', observacoes TEXT,
        FOREIGN KEY (paciente_id) REFERENCES pacientes(id) ON DELETE CASCADE
    )""")

    conn.commit()

    # migraÃ§Ã£o leve: garante que colunas novas existam mesmo em bancos criados
    # por uma versÃ£o anterior do programa
    colunas_novas = {
        "dobra_panturrilha": "REAL", "bia_pg": "REAL", "bia_massa_magra": "REAL",
    }
    colunas_existentes = {row["name"] for row in c.execute("PRAGMA table_info(avaliacoes)")}
    for nome, tipo in colunas_novas.items():
        if nome not in colunas_existentes:
            c.execute(f"ALTER TABLE avaliacoes ADD COLUMN {nome} {tipo}")
    conn.commit()

    # popular tabela de alimentos com a TACO, uma Ãºnica vez
    # Evolu??o de esquemas de vers?es anteriores.
    for tabela, colunas in {
        "alimentos": {"origem": "TEXT DEFAULT 'TACO'"},
        "anamneses_paciente": {"tipo": "TEXT DEFAULT 'Estruturada'", "dados_json": "TEXT DEFAULT '{}'", "versao": "INTEGER DEFAULT 1"},
    }.items():
        existentes = {row["name"] for row in c.execute(f"PRAGMA table_info({tabela})")}
        for nome, tipo in colunas.items():
            if nome not in existentes:
                c.execute(f"ALTER TABLE {tabela} ADD COLUMN {nome} {tipo}")
    conn.commit()

    c.execute("SELECT COUNT(*) FROM alimentos")
    if c.fetchone()[0] == 0:
        _importar_taco(conn)

    c.execute("SELECT COUNT(*) FROM receitas")
    if c.fetchone()[0] == 0:
        import content_seed
        content_seed.seed_receitas(conn)

    c.execute("SELECT COUNT(*) FROM planos_modelo")
    if c.fetchone()[0] == 0:
        import content_seed
        content_seed.seed_planos_modelo(conn)

    c.execute("SELECT COUNT(*) FROM diretrizes")
    if c.fetchone()[0] == 0:
        import content_seed
        content_seed.seed_diretrizes(conn)

    c.execute("SELECT COUNT(*) FROM anamneses_modelo")
    if c.fetchone()[0] == 0:
        import content_seed
        content_seed.seed_anamneses(conn)

    # roda sempre (idempotente): completa diretrizes existentes com pontos novos
    # e adiciona diretrizes novas que ainda nÃ£o existem
    import content_seed
    content_seed.atualizar_e_completar_diretrizes(conn)

    conn.close()


def _num(v):
    """Converte string do CSV da TACO em float; NA/vazio vira None."""
    if v is None:
        return None
    v = v.strip()
    if v in ("", "NA", "Tr", "*"):
        return None
    try:
        return float(v)
    except ValueError:
        return None


def _importar_taco(conn):
    if not os.path.exists(TACO_CSV):
        return
    with open(TACO_CSV, encoding="utf-8") as f:
        reader = csv.reader(f)
        next(reader)  # cabeÃ§alho
        linhas = []
        for row in reader:
            if len(row) < 28:
                continue
            linhas.append((
                row[1].strip(), row[2].strip(),          # categoria, descricao
                _num(row[4]), _num(row[6]), _num(row[7]), _num(row[9]), _num(row[10]),  # kcal, ptn, lip, cho, fibra
                _num(row[12]), _num(row[13]), _num(row[15]), _num(row[16]), _num(row[17]),  # ca, mg, p, fe, na
                _num(row[18]), _num(row[19]), _num(row[20]),  # k, cu, zn
                _num(row[24]), _num(row[25]), _num(row[26]), _num(row[27]), _num(row[28] if len(row) > 28 else None),  # tiamina..vitC
            ))
    conn.executemany("""
        INSERT INTO alimentos (categoria, descricao, kcal, proteina, lipideos, carboidrato, fibra,
            calcio, magnesio, fosforo, ferro, sodio, potassio, cobre, zinco,
            tiamina, riboflavina, piridoxina, niacina, vitamina_c)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, linhas)
    conn.commit()


# ---------------- PACIENTES ----------------

def add_paciente(nome, sexo, data_nascimento="", telefone="", email="", observacoes=""):
    conn = get_conn()
    cur = conn.execute(
        "INSERT INTO pacientes (nome, sexo, data_nascimento, telefone, email, observacoes) VALUES (?,?,?,?,?,?)",
        (nome, sexo, data_nascimento, telefone, email, observacoes))
    conn.commit()
    pid = cur.lastrowid
    conn.close()
    return pid


def update_paciente(pid, nome, sexo, data_nascimento, telefone, email, observacoes):
    conn = get_conn()
    conn.execute(
        "UPDATE pacientes SET nome=?, sexo=?, data_nascimento=?, telefone=?, email=?, observacoes=? WHERE id=?",
        (nome, sexo, data_nascimento, telefone, email, observacoes, pid))
    conn.commit()
    conn.close()


def delete_paciente(pid):
    conn = get_conn()
    conn.execute("DELETE FROM pacientes WHERE id=?", (pid,))
    conn.commit()
    conn.close()


def list_pacientes(busca=""):
    conn = get_conn()
    if busca:
        rows = conn.execute("SELECT * FROM pacientes WHERE nome LIKE ? ORDER BY nome",
                             (f"%{busca}%",)).fetchall()
    else:
        rows = conn.execute("SELECT * FROM pacientes ORDER BY nome").fetchall()
    conn.close()
    return rows


def get_paciente(pid):
    conn = get_conn()
    row = conn.execute("SELECT * FROM pacientes WHERE id=?", (pid,)).fetchone()
    conn.close()
    return row


# ---------------- AVALIAÃ‡Ã•ES ----------------

def add_avaliacao(dados: dict):
    conn = get_conn()
    campos = ", ".join(dados.keys())
    interrogacoes = ", ".join("?" * len(dados))
    cur = conn.execute(f"INSERT INTO avaliacoes ({campos}) VALUES ({interrogacoes})", tuple(dados.values()))
    conn.commit()
    aid = cur.lastrowid
    conn.close()
    return aid


def list_avaliacoes(paciente_id):
    conn = get_conn()
    rows = conn.execute("SELECT * FROM avaliacoes WHERE paciente_id=? ORDER BY data",
                         (paciente_id,)).fetchall()
    conn.close()
    return rows


def delete_avaliacao(aid):
    conn = get_conn()
    conn.execute("DELETE FROM avaliacoes WHERE id=?", (aid,))
    conn.commit()
    conn.close()


# ---------------- ALIMENTOS ----------------

def buscar_alimentos(termo, limite=30):
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM alimentos WHERE descricao LIKE ? ORDER BY descricao LIMIT ?",
        (f"%{termo}%", limite)).fetchall()
    conn.close()
    return rows


def list_alimentos(busca="", limite=500):
    conn = get_conn()
    rows = conn.execute("SELECT * FROM alimentos WHERE descricao LIKE ? OR categoria LIKE ? ORDER BY descricao LIMIT ?", (f"%{busca}%", f"%{busca}%", limite)).fetchall()
    conn.close()
    return rows


def salvar_alimento(dados, alimento_id=None):
    campos = ("categoria", "descricao", "kcal", "proteina", "lipideos", "carboidrato", "fibra")
    valores = [dados.get(c) if dados.get(c) not in ("", None) else None for c in campos]
    if not str(dados.get("descricao", "")).strip():
        raise ValueError("Descri??o do alimento ? obrigat?ria.")
    conn = get_conn()
    if alimento_id:
        conn.execute("UPDATE alimentos SET categoria=?, descricao=?, kcal=?, proteina=?, lipideos=?, carboidrato=?, fibra=? WHERE id=?", (*valores, alimento_id))
        resultado = alimento_id
    else:
        cur = conn.execute("INSERT INTO alimentos (categoria, descricao, kcal, proteina, lipideos, carboidrato, fibra, origem) VALUES (?,?,?,?,?,?,?,?)", (*valores, "Manual"))
        resultado = cur.lastrowid
    conn.commit(); conn.close()
    return resultado


def excluir_alimento(alimento_id):
    conn = get_conn()
    vinculos = conn.execute("SELECT COUNT(*) FROM plano_itens WHERE alimento_id=?", (alimento_id,)).fetchone()[0]
    if vinculos:
        conn.close(); raise ValueError("Este alimento est? em um plano alimentar e n?o pode ser exclu?do.")
    conn.execute("DELETE FROM alimentos WHERE id=?", (alimento_id,))
    conn.commit(); conn.close()


def importar_alimentos_csv(caminho):
    """Importa CSV ; ou , com colunas descricao, categoria e macros. Retorna relat?rio."""
    erros, inseridos = [], 0
    with open(caminho, encoding="utf-8-sig", newline="") as arquivo:
        amostra = arquivo.read(2048); arquivo.seek(0)
        dialeto = csv.Sniffer().sniff(amostra, delimiters=";,")
        leitor = csv.DictReader(arquivo, dialect=dialeto)
        nomes = {n.strip().lower(): n for n in (leitor.fieldnames or [])}
        if "descricao" not in nomes:
            return {"inseridos": 0, "erros": ["Cabe?alho obrigat?rio ausente: descricao."]}
        for linha_no, linha in enumerate(leitor, 2):
            try:
                descricao = (linha.get(nomes["descricao"]) or "").strip()
                if not descricao: raise ValueError("descri??o vazia")
                dados = {"descricao": descricao, "categoria": (linha.get(nomes.get("categoria", "")) or "").strip()}
                for campo in ("kcal", "proteina", "lipideos", "carboidrato", "fibra"):
                    bruto = (linha.get(nomes.get(campo, "")) or "").strip().replace(",", ".")
                    dados[campo] = float(bruto) if bruto else None
                salvar_alimento(dados); inseridos += 1
            except (ValueError, TypeError) as exc:
                erros.append(f"Linha {linha_no}: {exc}")
    return {"inseridos": inseridos, "erros": erros}


def get_alimento(aid):
    conn = get_conn()
    row = conn.execute("SELECT * FROM alimentos WHERE id=?", (aid,)).fetchone()
    conn.close()
    return row


# ---------------- PLANOS ALIMENTARES ----------------

def add_plano(paciente_id, nome, data, vet_meta, observacoes=""):
    conn = get_conn()
    cur = conn.execute(
        "INSERT INTO planos (paciente_id, nome, data, vet_meta, observacoes) VALUES (?,?,?,?,?)",
        (paciente_id, nome, data, vet_meta, observacoes))
    conn.commit()
    pid = cur.lastrowid
    conn.close()
    return pid


def list_planos(paciente_id):
    conn = get_conn()
    rows = conn.execute("SELECT * FROM planos WHERE paciente_id=? ORDER BY data DESC",
                         (paciente_id,)).fetchall()
    conn.close()
    return rows


def add_item_plano(plano_id, refeicao, alimento_id, quantidade_g):
    conn = get_conn()
    conn.execute(
        "INSERT INTO plano_itens (plano_id, refeicao, alimento_id, quantidade_g) VALUES (?,?,?,?)",
        (plano_id, refeicao, alimento_id, quantidade_g))
    conn.commit()
    conn.close()


def remove_item_plano(item_id):
    conn = get_conn()
    conn.execute("DELETE FROM plano_itens WHERE id=?", (item_id,))
    conn.commit()
    conn.close()


def list_itens_plano(plano_id):
    conn = get_conn()
    rows = conn.execute("""
        SELECT pi.id, pi.refeicao, pi.quantidade_g, a.*
        FROM plano_itens pi JOIN alimentos a ON a.id = pi.alimento_id
        WHERE pi.plano_id = ?
        ORDER BY pi.refeicao, a.descricao
    """, (plano_id,)).fetchall()
    conn.close()
    return rows


def delete_plano(plano_id):
    conn = get_conn()
    conn.execute("DELETE FROM planos WHERE id=?", (plano_id,))
    conn.commit()
    conn.close()


# ---------------- RECEITAS ----------------

def add_receita(nome, categoria, tags, porcoes, modo_preparo, ingredientes):
    """ingredientes: lista de (alimento_id, quantidade_g)"""
    conn = get_conn()
    cur = conn.execute(
        "INSERT INTO receitas (nome, categoria, tags, porcoes, modo_preparo) VALUES (?,?,?,?,?)",
        (nome, categoria, tags, porcoes, modo_preparo))
    rid = cur.lastrowid
    for alimento_id, qtd in ingredientes:
        conn.execute("INSERT INTO receita_ingredientes (receita_id, alimento_id, quantidade_g) VALUES (?,?,?)",
                     (rid, alimento_id, qtd))
    conn.commit()
    conn.close()
    return rid


def list_receitas(categoria=None, busca=""):
    conn = get_conn()
    q = "SELECT * FROM receitas WHERE 1=1"
    params = []
    if categoria and categoria != "Todas":
        q += " AND categoria = ?"
        params.append(categoria)
    if busca:
        q += " AND nome LIKE ?"
        params.append(f"%{busca}%")
    q += " ORDER BY nome"
    rows = conn.execute(q, params).fetchall()
    conn.close()
    return rows


def get_receita(receita_id):
    conn = get_conn()
    receita = conn.execute("SELECT * FROM receitas WHERE id=?", (receita_id,)).fetchone()
    ingredientes = conn.execute("""
        SELECT ri.quantidade_g, a.* FROM receita_ingredientes ri
        JOIN alimentos a ON a.id = ri.alimento_id WHERE ri.receita_id=?
    """, (receita_id,)).fetchall()
    conn.close()
    return receita, ingredientes


def list_categorias_receitas():
    conn = get_conn()
    rows = conn.execute("SELECT DISTINCT categoria FROM receitas ORDER BY categoria").fetchall()
    conn.close()
    return [r["categoria"] for r in rows]


# ---------------- PLANOS-MODELO ----------------

def add_plano_modelo(nome, categoria, vet_alvo, descricao, itens):
    """itens: lista de (refeicao, alimento_id, quantidade_g)"""
    conn = get_conn()
    cur = conn.execute("INSERT INTO planos_modelo (nome, categoria, vet_alvo, descricao) VALUES (?,?,?,?)",
                        (nome, categoria, vet_alvo, descricao))
    mid = cur.lastrowid
    for refeicao, alimento_id, qtd in itens:
        conn.execute("INSERT INTO planos_modelo_itens (modelo_id, refeicao, alimento_id, quantidade_g) VALUES (?,?,?,?)",
                     (mid, refeicao, alimento_id, qtd))
    conn.commit()
    conn.close()
    return mid


def list_planos_modelo():
    conn = get_conn()
    rows = conn.execute("SELECT * FROM planos_modelo ORDER BY categoria, nome").fetchall()
    conn.close()
    return rows


def get_plano_modelo_itens(modelo_id):
    conn = get_conn()
    rows = conn.execute("""
        SELECT pmi.refeicao, pmi.quantidade_g, a.* FROM planos_modelo_itens pmi
        JOIN alimentos a ON a.id = pmi.alimento_id WHERE pmi.modelo_id=?
        ORDER BY pmi.refeicao
    """, (modelo_id,)).fetchall()
    conn.close()
    return rows


def aplicar_modelo_a_paciente(modelo_id, paciente_id, nome_plano, vet_meta):
    """Cria um novo plano real para o paciente a partir de um modelo, copiando os itens."""
    conn = get_conn()
    from datetime import date
    hoje = date.today().strftime("%d/%m/%Y")
    cur = conn.execute("INSERT INTO planos (paciente_id, nome, data, vet_meta, observacoes) VALUES (?,?,?,?,?)",
                        (paciente_id, nome_plano, hoje, vet_meta, "Criado a partir de modelo"))
    novo_id = cur.lastrowid
    itens = conn.execute("SELECT refeicao, alimento_id, quantidade_g FROM planos_modelo_itens WHERE modelo_id=?",
                          (modelo_id,)).fetchall()
    for it in itens:
        conn.execute("INSERT INTO plano_itens (plano_id, refeicao, alimento_id, quantidade_g) VALUES (?,?,?,?)",
                     (novo_id, it["refeicao"], it["alimento_id"], it["quantidade_g"]))
    conn.commit()
    conn.close()
    return novo_id


# ---------------- CONFIGURAÃ‡Ã•ES ----------------

def get_config(chave, padrao=None):
    conn = get_conn()
    row = conn.execute("SELECT valor FROM configuracoes WHERE chave=?", (chave,)).fetchone()
    conn.close()
    return row["valor"] if row else padrao


def set_config(chave, valor):
    conn = get_conn()
    conn.execute("INSERT INTO configuracoes (chave, valor) VALUES (?,?) "
                 "ON CONFLICT(chave) DO UPDATE SET valor=excluded.valor", (chave, valor))
    conn.commit()
    conn.close()


# ---------------- DIRETRIZES ----------------

def add_diretriz(nome, fonte, pontos_lista):
    conn = get_conn()
    cur = conn.execute("INSERT INTO diretrizes (nome, fonte, pontos) VALUES (?,?,?)",
                        (nome, fonte, "\n".join(pontos_lista)))
    conn.commit()
    did = cur.lastrowid
    conn.close()
    return did


def list_diretrizes():
    conn = get_conn()
    rows = conn.execute("SELECT * FROM diretrizes ORDER BY nome").fetchall()
    conn.close()
    return rows


def get_diretriz(diretriz_id):
    conn = get_conn()
    row = conn.execute("SELECT * FROM diretrizes WHERE id=?", (diretriz_id,)).fetchone()
    conn.close()
    return row


def delete_diretriz(diretriz_id):
    conn = get_conn()
    conn.execute("DELETE FROM diretrizes WHERE id=?", (diretriz_id,))
    conn.commit()
    conn.close()


# ---------------- DOCUMENTOS DO PACIENTE ----------------

def add_documento_paciente(paciente_id, tipo, nome_arquivo, caminho):
    from datetime import date
    conn = get_conn()
    cur = conn.execute(
        "INSERT INTO documentos_paciente (paciente_id, tipo, nome_arquivo, caminho, data) VALUES (?,?,?,?,?)",
        (paciente_id, tipo, nome_arquivo, caminho, date.today().strftime("%d/%m/%Y")))
    conn.commit()
    did = cur.lastrowid
    conn.close()
    return did


def list_documentos_paciente(paciente_id):
    conn = get_conn()
    rows = conn.execute("SELECT * FROM documentos_paciente WHERE paciente_id=? ORDER BY id DESC",
                         (paciente_id,)).fetchall()
    conn.close()
    return rows


def delete_documento_paciente(doc_id):
    conn = get_conn()
    conn.execute("DELETE FROM documentos_paciente WHERE id=?", (doc_id,))
    conn.commit()
    conn.close()


# ---------------- ANAMNESES ----------------

def list_anamneses_modelo():
    conn = get_conn()
    rows = conn.execute("SELECT * FROM anamneses_modelo ORDER BY nome").fetchall()
    conn.close()
    return rows


def get_anamnese_modelo(anamnese_id):
    conn = get_conn()
    row = conn.execute("SELECT * FROM anamneses_modelo WHERE id=?", (anamnese_id,)).fetchone()
    conn.close()
    return row


# ---------------- SALVAR PLANO REAL COMO MODELO ----------------

def salvar_plano_como_modelo(plano_id, nome_modelo, categoria, descricao):
    conn = get_conn()
    plano = conn.execute("SELECT * FROM planos WHERE id=?", (plano_id,)).fetchone()
    cur = conn.execute("INSERT INTO planos_modelo (nome, categoria, vet_alvo, descricao) VALUES (?,?,?,?)",
                        (nome_modelo, categoria, plano["vet_meta"], descricao))
    mid = cur.lastrowid
    itens = conn.execute("SELECT refeicao, alimento_id, quantidade_g FROM plano_itens WHERE plano_id=?",
                          (plano_id,)).fetchall()
    for it in itens:
        conn.execute("INSERT INTO planos_modelo_itens (modelo_id, refeicao, alimento_id, quantidade_g) VALUES (?,?,?,?)",
                     (mid, it["refeicao"], it["alimento_id"], it["quantidade_g"]))
    conn.commit()
    conn.close()
    return mid


# ---------------- ANAMNESES DO PACIENTE (conteÃºdo preenchido, nÃ£o sÃ³ o PDF) ----------------

def add_anamnese_paciente(paciente_id, nome_modelo, conteudo):
    from datetime import date
    conn = get_conn()
    cur = conn.execute(
        "INSERT INTO anamneses_paciente (paciente_id, nome_modelo, conteudo, data) VALUES (?,?,?,?)",
        (paciente_id, nome_modelo, conteudo, date.today().strftime("%d/%m/%Y")))
    conn.commit()
    aid = cur.lastrowid
    conn.close()
    return aid


def list_anamneses_paciente(paciente_id):
    conn = get_conn()
    rows = conn.execute("SELECT * FROM anamneses_paciente WHERE paciente_id=? ORDER BY id DESC",
                         (paciente_id,)).fetchall()
    conn.close()
    return rows


# ---------------- ANAMNESE E FOTOS ----------------

def salvar_anamnese_estruturada(paciente_id, dados, tipo="Consulta nutricional"):
    """Salva um snapshot imutavel, mantendo o historico de versoes."""
    conn = get_conn()
    ultima = conn.execute("SELECT COALESCE(MAX(versao), 0) FROM anamneses_paciente WHERE paciente_id=?", (paciente_id,)).fetchone()[0]
    conteudo = "\n".join(f"{chave}: {valor}" for chave, valor in dados.items() if str(valor).strip())
    cur = conn.execute("INSERT INTO anamneses_paciente (paciente_id, nome_modelo, conteudo, data, tipo, dados_json, versao) VALUES (?,?,?,?,?,?,?)",
        (paciente_id, tipo, conteudo, date.today().strftime("%d/%m/%Y"), tipo, json.dumps(dados, ensure_ascii=False), ultima + 1))
    conn.commit(); aid = cur.lastrowid; conn.close()
    return aid


def dados_anamnese(anamnese):
    try:
        return json.loads(anamnese["dados_json"] or "{}")
    except (json.JSONDecodeError, TypeError):
        return {}


def caminho_fotos_paciente(paciente_id):
    pasta = os.path.join(BASE_DIR, "fotos_pacientes", str(paciente_id))
    os.makedirs(pasta, exist_ok=True)
    return pasta


def add_foto_paciente(paciente_id, origem, data_foto, observacao=""):
    extensao = os.path.splitext(origem)[1].lower() or ".jpg"
    destino = os.path.join(caminho_fotos_paciente(paciente_id), f"{date.today().strftime('%Y%m%d')}_{os.urandom(4).hex()}{extensao}")
    shutil.copy2(origem, destino)
    conn = get_conn()
    cur = conn.execute("INSERT INTO fotos_paciente (paciente_id, data, observacao, caminho) VALUES (?,?,?,?)", (paciente_id, data_foto, observacao, destino))
    conn.commit(); resultado = cur.lastrowid; conn.close()
    return resultado


def list_fotos_paciente(paciente_id):
    conn = get_conn(); rows = conn.execute("SELECT * FROM fotos_paciente WHERE paciente_id=? ORDER BY data, id", (paciente_id,)).fetchall(); conn.close()
    return rows


def delete_foto_paciente(foto_id):
    conn = get_conn(); foto = conn.execute("SELECT caminho FROM fotos_paciente WHERE id=?", (foto_id,)).fetchone()
    conn.execute("DELETE FROM fotos_paciente WHERE id=?", (foto_id,)); conn.commit(); conn.close()
    if foto and os.path.isfile(foto["caminho"]): os.remove(foto["caminho"])


# ---------------- AVALIAÃ‡Ã•ES: editar/excluir ----------------

def update_avaliacao(avaliacao_id, dados: dict):
    conn = get_conn()
    campos = ", ".join(f"{k}=?" for k in dados.keys())
    conn.execute(f"UPDATE avaliacoes SET {campos} WHERE id=?", (*dados.values(), avaliacao_id))
    conn.commit()
    conn.close()


def get_avaliacao(avaliacao_id):
    conn = get_conn()
    row = conn.execute("SELECT * FROM avaliacoes WHERE id=?", (avaliacao_id,)).fetchone()
    conn.close()
    return row


# ---------------- CONSULTAS (AGENDA) ----------------

def add_consulta(paciente_id, data, hora, observacoes=""):
    conn = get_conn()
    cur = conn.execute(
        "INSERT INTO consultas (paciente_id, data, hora, status, observacoes) VALUES (?,?,?,?,?)",
        (paciente_id, data, hora, "Agendada", observacoes))
    conn.commit()
    cid = cur.lastrowid
    conn.close()
    return cid


def list_consultas(paciente_id=None):
    conn = get_conn()
    if paciente_id:
        rows = conn.execute("""
            SELECT c.*, p.nome AS paciente_nome FROM consultas c
            JOIN pacientes p ON p.id = c.paciente_id
            WHERE c.paciente_id=? ORDER BY c.data, c.hora
        """, (paciente_id,)).fetchall()
    else:
        rows = conn.execute("""
            SELECT c.*, p.nome AS paciente_nome FROM consultas c
            JOIN pacientes p ON p.id = c.paciente_id
            ORDER BY c.data, c.hora
        """).fetchall()
    conn.close()
    return rows


def update_consulta_status(consulta_id, status):
    conn = get_conn()
    conn.execute("UPDATE consultas SET status=? WHERE id=?", (status, consulta_id))
    conn.commit()
    conn.close()


def delete_consulta(consulta_id):
    conn = get_conn()
    conn.execute("DELETE FROM consultas WHERE id=?", (consulta_id,))
    conn.commit()
    conn.close()


# ---------------- BACKUP / RESTORE ----------------

def caminho_pacientes_arquivos():
    return os.path.join(BASE_DIR, "pacientes_arquivos")


def exportar_backup(caminho_zip):
    import zipfile
    with zipfile.ZipFile(caminho_zip, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(DB_PATH, arcname="nutridesktop.db")
        pasta = caminho_pacientes_arquivos()
        if os.path.isdir(pasta):
            for raiz, _, arquivos in os.walk(pasta):
                for nome in arquivos:
                    caminho_completo = os.path.join(raiz, nome)
                    arcname = os.path.join("pacientes_arquivos", os.path.relpath(caminho_completo, pasta))
                    zf.write(caminho_completo, arcname=arcname)


def restaurar_backup(caminho_zip):
    import zipfile, shutil
    with zipfile.ZipFile(caminho_zip, "r") as zf:
        zf.extractall(BASE_DIR)
    # o zip jÃ¡ extrai nutridesktop.db e pacientes_arquivos/ direto na pasta do programa


# ---------------- EXPORTAR LISTA DE PACIENTES ----------------

def exportar_pacientes_csv(caminho_csv):
    conn = get_conn()
    pacientes = conn.execute("SELECT * FROM pacientes ORDER BY nome").fetchall()
    conn.close()
    with open(caminho_csv, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerow(["Nome", "Sexo", "Data Nascimento", "Telefone", "Email", "Cadastrado em"])
        for p in pacientes:
            writer.writerow([p["nome"], p["sexo"], p["data_nascimento"] or "",
                              p["telefone"] or "", p["email"] or "", p["criado_em"] or ""])

