import os
import hmac
from datetime import datetime
from flask import Flask, request, redirect, url_for, session, flash, render_template_string, abort
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import or_

app = Flask(__name__)

database_url = os.getenv("DATABASE_URL", "sqlite:///plataforma.db")
# Compatibilidade com URLs antigas no formato postgres://
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

app.config["SQLALCHEMY_DATABASE_URI"] = database_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret-change-me")

db = SQLAlchemy(app)

class Prestador(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(120), nullable=False)
    cidade = db.Column(db.String(100), nullable=False)
    telefone = db.Column(db.String(40), nullable=False)
    email = db.Column(db.String(160), nullable=True)
    categoria = db.Column(db.String(100), nullable=False)
    descricao = db.Column(db.Text, nullable=False)
    aprovado = db.Column(db.Boolean, default=False, nullable=False)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

class Pedido(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(120), nullable=False)
    cidade = db.Column(db.String(100), nullable=False)
    telefone = db.Column(db.String(40), nullable=False)
    email = db.Column(db.String(160), nullable=True)
    servico = db.Column(db.String(120), nullable=False)
    descricao = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(30), default="Novo", nullable=False)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

with app.app_context():
    db.create_all()

BASE = """
<!doctype html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{{ title }} | Conecta Serviços</title>
  <style>
    :root{--bg:#f5f7fb;--card:#fff;--text:#1e293b;--muted:#64748b;--brand:#2563eb;--brand2:#1d4ed8;--border:#e2e8f0;--ok:#15803d;--danger:#b91c1c}
    *{box-sizing:border-box} body{margin:0;font-family:system-ui,-apple-system,Segoe UI,Roboto,Arial,sans-serif;background:var(--bg);color:var(--text)}
    .wrap{max-width:980px;margin:auto;padding:20px}.nav{background:#0f172a;color:#fff}.nav .wrap{display:flex;gap:16px;align-items:center;justify-content:space-between;padding-top:14px;padding-bottom:14px}
    .brand{font-weight:800;font-size:20px}.nav a{color:#fff;text-decoration:none;margin-left:14px}.hero{padding:48px 0 28px}.hero h1{font-size:clamp(34px,7vw,58px);line-height:1.03;margin:0 0 14px}.hero p{font-size:19px;color:var(--muted);max-width:760px}
    .grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:18px}.card{background:var(--card);border:1px solid var(--border);border-radius:16px;padding:20px;box-shadow:0 6px 20px rgba(15,23,42,.05)}
    .btn{display:inline-block;background:var(--brand);color:#fff!important;text-decoration:none;border:0;border-radius:10px;padding:11px 16px;font-weight:700;cursor:pointer}.btn:hover{background:var(--brand2)}.btn.secondary{background:#334155}.btn.danger{background:var(--danger)}
    label{display:block;font-weight:700;margin:14px 0 6px}input,textarea,select{width:100%;padding:12px;border:1px solid #cbd5e1;border-radius:9px;font:inherit;background:white}textarea{min-height:120px}
    .muted{color:var(--muted)}.flash{padding:12px 14px;border-radius:10px;background:#dcfce7;color:#166534;margin:12px 0}.bad{background:#fee2e2;color:#991b1b}.tag{display:inline-block;padding:4px 9px;border-radius:999px;background:#e0e7ff;color:#3730a3;font-size:13px}
    .item{padding:15px 0;border-bottom:1px solid var(--border)}.item:last-child{border-bottom:0}.actions{display:flex;gap:8px;flex-wrap:wrap;margin-top:10px}.topgap{margin-top:22px}
    footer{padding:38px 0;color:var(--muted);text-align:center}.search{display:flex;gap:8px}.search input{flex:1}@media(max-width:620px){.search{display:block}.search .btn{width:100%;margin-top:8px}.nav .wrap{align-items:flex-start}.navlinks{font-size:14px}}
  </style>
</head>
<body>
<nav class="nav"><div class="wrap"><div class="brand">Conecta Serviços</div><div class="navlinks">
<a href="{{ url_for('home') }}">Início</a><a href="{{ url_for('prestadores') }}">Prestadores</a><a href="{{ url_for('quero_servico') }}">Pedir serviço</a><a href="{{ url_for('sou_prestador') }}">Sou prestador</a>
</div></div></nav>
<main class="wrap">
{% with messages = get_flashed_messages(with_categories=true) %}
  {% for category, message in messages %}<div class="flash {{ 'bad' if category == 'error' else '' }}">{{ message }}</div>{% endfor %}
{% endwith %}
{{ body|safe }}
</main>
<footer><div class="wrap">Conecta Serviços • Plataforma para aproximar clientes e profissionais</div></footer>
</body></html>
"""

def page(title, body_tpl, **ctx):
    body = render_template_string(body_tpl, **ctx)
    return render_template_string(BASE, title=title, body=body)

@app.get("/")
def home():
    body = """
    <section class="hero">
      <span class="tag">Encontre quem faz</span>
      <h1>Serviços locais, sem complicação.</h1>
      <p>Clientes publicam o que precisam. Profissionais se cadastram para serem encontrados na sua região.</p>
      <div class="actions"><a class="btn" href="{{ url_for('quero_servico') }}">Preciso de um serviço</a><a class="btn secondary" href="{{ url_for('sou_prestador') }}">Quero prestar serviços</a></div>
    </section>
    <section class="grid">
      <div class="card"><h2>Para clientes</h2><p class="muted">Descreva o serviço, informe sua cidade e deixe seus dados para contato.</p></div>
      <div class="card"><h2>Para profissionais</h2><p class="muted">Cadastre sua especialidade e apareça na busca depois da aprovação.</p></div>
      <div class="card"><h2>Administração simples</h2><p class="muted">Painel protegido para aprovar prestadores e acompanhar solicitações.</p></div>
    </section>
    """
    return page("Início", body)

@app.route("/prestadores")
def prestadores():
    q = (request.args.get("q") or "").strip()
    query = Prestador.query.filter_by(aprovado=True)
    if q:
        like = f"%{q}%"
        query = query.filter(or_(Prestador.nome.ilike(like), Prestador.cidade.ilike(like), Prestador.categoria.ilike(like), Prestador.descricao.ilike(like)))
    itens = query.order_by(Prestador.criado_em.desc()).all()
    body = """
    <h1>Prestadores</h1>
    <form class="search" method="get"><input name="q" value="{{ q }}" placeholder="Ex.: pedreiro, eletricista, Londrina"><button class="btn">Buscar</button></form>
    <div class="card topgap">
    {% if itens %}
      {% for p in itens %}<div class="item"><h3>{{ p.nome }}</h3><div><span class="tag">{{ p.categoria }}</span> <span class="muted">{{ p.cidade }}</span></div><p>{{ p.descricao }}</p><strong>Contato:</strong> {{ p.telefone }}{% if p.email %} • {{ p.email }}{% endif %}</div>{% endfor %}
    {% else %}<p class="muted">Nenhum prestador encontrado ainda.</p>{% endif %}
    </div>
    """
    return page("Prestadores", body, itens=itens, q=q)

@app.route("/quero-servico", methods=["GET", "POST"])
def quero_servico():
    if request.method == "POST":
        dados = {k:(request.form.get(k) or "").strip() for k in ["nome","cidade","telefone","email","servico","descricao"]}
        obrig = ["nome","cidade","telefone","servico","descricao"]
        if any(not dados[k] for k in obrig):
            flash("Preencha todos os campos obrigatórios.", "error")
        else:
            db.session.add(Pedido(**dados))
            db.session.commit()
            flash("Pedido enviado com sucesso! Entraremos em contato quando houver um profissional compatível.")
            return redirect(url_for("quero_servico"))
    body = """
    <h1>Preciso de um serviço</h1><div class="card">
    <form method="post">
      <label>Seu nome *</label><input name="nome" required>
      <label>Cidade *</label><input name="cidade" required>
      <label>Telefone/WhatsApp *</label><input name="telefone" required>
      <label>E-mail</label><input type="email" name="email">
      <label>Qual serviço precisa? *</label><input name="servico" placeholder="Ex.: eletricista, jardinagem, pintura" required>
      <label>Descreva o que precisa *</label><textarea name="descricao" required></textarea>
      <div class="topgap"><button class="btn">Enviar pedido</button></div>
    </form></div>
    """
    return page("Pedir serviço", body)

@app.route("/sou-prestador", methods=["GET", "POST"])
def sou_prestador():
    if request.method == "POST":
        dados = {k:(request.form.get(k) or "").strip() for k in ["nome","cidade","telefone","email","categoria","descricao"]}
        obrig = ["nome","cidade","telefone","categoria","descricao"]
        if any(not dados[k] for k in obrig):
            flash("Preencha todos os campos obrigatórios.", "error")
        else:
            db.session.add(Prestador(**dados))
            db.session.commit()
            flash("Cadastro recebido! Ele ficará visível após aprovação.")
            return redirect(url_for("sou_prestador"))
    body = """
    <h1>Cadastro de prestador</h1><div class="card">
    <form method="post">
      <label>Nome ou empresa *</label><input name="nome" required>
      <label>Cidade *</label><input name="cidade" required>
      <label>Telefone/WhatsApp *</label><input name="telefone" required>
      <label>E-mail</label><input type="email" name="email">
      <label>Categoria *</label><input name="categoria" placeholder="Ex.: encanador, pintor, jardinagem" required>
      <label>Apresente seus serviços *</label><textarea name="descricao" required></textarea>
      <div class="topgap"><button class="btn">Cadastrar</button></div>
    </form></div>
    """
    return page("Sou prestador", body)

def admin_ok():
    return session.get("admin") is True

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        senha = request.form.get("senha", "")
        correta = os.getenv("ADMIN_PASSWORD", "")
        if correta and hmac.compare_digest(senha, correta):
            session["admin"] = True
            return redirect(url_for("admin"))
        flash("Senha inválida.", "error")
    body = """
    <h1>Administração</h1><div class="card"><form method="post">
    <label>Senha administrativa</label><input type="password" name="senha" required>
    <div class="topgap"><button class="btn">Entrar</button></div></form></div>
    """
    return page("Login", body)

@app.get("/admin/logout")
def admin_logout():
    session.clear()
    return redirect(url_for("home"))

@app.get("/admin")
def admin():
    if not admin_ok():
        return redirect(url_for("admin_login"))
    prest = Prestador.query.order_by(Prestador.criado_em.desc()).all()
    ped = Pedido.query.order_by(Pedido.criado_em.desc()).all()
    body = """
    <div class="actions" style="justify-content:space-between;align-items:center"><h1>Painel administrativo</h1><a class="btn secondary" href="{{ url_for('admin_logout') }}">Sair</a></div>
    <h2>Prestadores</h2><div class="card">
    {% for p in prest %}<div class="item"><strong>{{ p.nome }}</strong> — {{ p.categoria }} — {{ p.cidade }}<br><span class="muted">{{ p.telefone }}{% if p.email %} • {{ p.email }}{% endif %}</span><p>{{ p.descricao }}</p>
      <div class="actions">{% if not p.aprovado %}<form method="post" action="{{ url_for('aprovar_prestador', pid=p.id) }}"><button class="btn">Aprovar</button></form>{% else %}<span class="tag">Aprovado</span>{% endif %}<form method="post" action="{{ url_for('excluir_prestador', pid=p.id) }}"><button class="btn danger">Excluir</button></form></div>
    </div>{% else %}<p class="muted">Nenhum cadastro.</p>{% endfor %}</div>
    <h2 class="topgap">Pedidos de serviço</h2><div class="card">
    {% for x in ped %}<div class="item"><strong>{{ x.servico }}</strong> — {{ x.nome }} — {{ x.cidade }}<br><span class="muted">{{ x.telefone }}{% if x.email %} • {{ x.email }}{% endif %} • {{ x.status }}</span><p>{{ x.descricao }}</p>
      <div class="actions"><form method="post" action="{{ url_for('concluir_pedido', pid=x.id) }}"><button class="btn secondary">Marcar concluído</button></form><form method="post" action="{{ url_for('excluir_pedido', pid=x.id) }}"><button class="btn danger">Excluir</button></form></div>
    </div>{% else %}<p class="muted">Nenhum pedido.</p>{% endfor %}</div>
    """
    return page("Admin", body, prest=prest, ped=ped)

@app.post("/admin/prestador/<int:pid>/aprovar")
def aprovar_prestador(pid):
    if not admin_ok(): abort(403)
    p = db.get_or_404(Prestador, pid)
    p.aprovado = True
    db.session.commit()
    return redirect(url_for("admin"))

@app.post("/admin/prestador/<int:pid>/excluir")
def excluir_prestador(pid):
    if not admin_ok(): abort(403)
    p = db.get_or_404(Prestador, pid)
    db.session.delete(p)
    db.session.commit()
    return redirect(url_for("admin"))

@app.post("/admin/pedido/<int:pid>/concluir")
def concluir_pedido(pid):
    if not admin_ok(): abort(403)
    x = db.get_or_404(Pedido, pid)
    x.status = "Concluído"
    db.session.commit()
    return redirect(url_for("admin"))

@app.post("/admin/pedido/<int:pid>/excluir")
def excluir_pedido(pid):
    if not admin_ok(): abort(403)
    x = db.get_or_404(Pedido, pid)
    db.session.delete(x)
    db.session.commit()
    return redirect(url_for("admin"))

@app.get("/health")
def health():
    return {"status":"ok"}

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")), debug=True)
