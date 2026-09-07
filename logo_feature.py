import base64

from flask import abort, flash, redirect, render_template_string, request, url_for
from sqlalchemy import inspect, or_, text

import app as legacy

app = legacy.app
db = legacy.db
Prestador = legacy.Prestador
UFS = legacy.UFS

MAX_IMAGE_BYTES = 1_500_000
ALLOWED_IMAGE_TYPES = {
    "image/jpeg": "jpeg",
    "image/png": "png",
    "image/webp": "webp",
}


# Migração aditiva: preserva todos os cadastros já existentes.
with app.app_context():
    with db.engine.begin() as conexao:
        colunas = {
            coluna["name"]
            for coluna in inspect(conexao).get_columns("prestador")
        }
        if "logo_data" not in colunas:
            conexao.execute(
                text("ALTER TABLE prestador ADD COLUMN logo_data TEXT")
            )

    if not hasattr(Prestador, "logo_data"):
        Prestador.logo_data = db.Column(db.Text, nullable=True)


LOGO_CSS = """
.provider-row{
    display:flex;
    gap:16px;
    align-items:flex-start;
}
.provider-logo{
    width:92px;
    height:92px;
    object-fit:contain;
    border:1px solid var(--border);
    border-radius:12px;
    background:#fff;
    padding:6px;
    flex:0 0 auto;
}
.profile-logo{
    width:min(260px,100%);
    max-height:180px;
    object-fit:contain;
    border:1px solid var(--border);
    border-radius:14px;
    background:#fff;
    padding:8px;
}
.file-help{
    margin-top:6px;
    font-size:13px;
    color:var(--muted);
}
@media(max-width:520px){
    .provider-logo{
        width:76px;
        height:76px;
    }
}
"""

if LOGO_CSS not in legacy.BASE:
    legacy.BASE = legacy.BASE.replace("</style>", LOGO_CSS + "\n</style>")


def imagem_para_data_url(arquivo):
    if not arquivo or not arquivo.filename:
        return None, None

    mime = (arquivo.mimetype or "").lower()
    if mime not in ALLOWED_IMAGE_TYPES:
        return None, "Envie uma imagem JPG, PNG ou WEBP."

    dados = arquivo.read(MAX_IMAGE_BYTES + 1)
    if not dados:
        return None, "A imagem enviada está vazia."

    if len(dados) > MAX_IMAGE_BYTES:
        return None, "A imagem deve ter no máximo 1,5 MB."

    codificado = base64.b64encode(dados).decode("ascii")
    return f"data:{mime};base64,{codificado}", None


def sou_prestador_com_logo():
    if request.method == "POST":
        dados = {
            k: (request.form.get(k) or "").strip()
            for k in [
                "nome",
                "cidade",
                "uf",
                "telefone",
                "email",
                "categoria",
                "descricao",
            ]
        }
        dados["uf"] = dados["uf"].upper()
        obrigatorios = [
            "nome",
            "cidade",
            "uf",
            "telefone",
            "categoria",
            "descricao",
        ]

        logo_data, erro_imagem = imagem_para_data_url(
            request.files.get("logo")
        )

        if any(not dados[k] for k in obrigatorios):
            flash("Preencha todos os campos obrigatórios.", "error")
        elif dados["uf"] not in UFS:
            flash("Selecione um Estado (UF) válido.", "error")
        elif erro_imagem:
            flash(erro_imagem, "error")
        else:
            dados["logo_data"] = logo_data
            db.session.add(Prestador(**dados))
            db.session.commit()
            flash(
                "Cadastro recebido! Ele ficará visível após aprovação."
            )
            return redirect(url_for("sou_prestador"))

    body = """
    <h1>Cadastro de prestador</h1>

    <div class="card">
    <form method="post" enctype="multipart/form-data">

    <label>Nome ou empresa *</label>
    <input name="nome" required>

    <label>Estado (UF) *</label>
    <select name="uf" required>
    <option value="">Selecione</option>
    {% for sigla in ufs %}
    <option value="{{ sigla }}">{{ sigla }}</option>
    {% endfor %}
    </select>

    <label>Cidade *</label>
    <input name="cidade" required>

    <label>Telefone/WhatsApp *</label>
    <input name="telefone" type="tel" inputmode="tel" autocomplete="tel" required>

    <label>E-mail</label>
    <input type="email" name="email" autocomplete="email">

    <label>Categoria *</label>
    <input
        name="categoria"
        placeholder="Ex.: encanador, pintor, jardinagem"
        required
    >

    <label>Apresente seus serviços *</label>
    <textarea name="descricao" required></textarea>

    <label>Logomarca ou cartão de visita</label>
    <input
        type="file"
        name="logo"
        accept="image/jpeg,image/png,image/webp"
    >
    <div class="file-help">
    Opcional. Envie JPG, PNG ou WEBP de até 1,5 MB. A imagem aparecerá no seu perfil e na busca.
    </div>

    <div class="topgap">
    <button class="btn">Cadastrar</button>
    </div>

    </form>
    </div>
    """

    return legacy.page(
        "Sou prestador",
        body,
        ufs=UFS,
    )


def prestadores_com_logo():
    servico = (request.args.get("servico") or "").strip()
    uf = (request.args.get("uf") or "").strip().upper()
    cidade = (request.args.get("cidade") or "").strip()

    query = Prestador.query.filter_by(aprovado=True)

    if servico:
        like_servico = f"%{servico}%"
        query = query.filter(
            or_(
                Prestador.categoria.ilike(like_servico),
                Prestador.descricao.ilike(like_servico),
                Prestador.nome.ilike(like_servico),
            )
        )

    if cidade:
        query = query.filter(Prestador.cidade.ilike(f"%{cidade}%"))

    if uf in UFS:
        query = query.filter(Prestador.uf.ilike(uf))

    itens = query.order_by(Prestador.criado_em.desc()).all()

    body = """
    <h1>Encontre um prestador</h1>
    <p class="muted">
    Pesquise o serviço de que precisa e informe o estado e a cidade onde será realizado.
    </p>

    <form class="search card" method="get">
    <div>
    <label for="servico">Serviço ou categoria</label>
    <input id="servico" name="servico" value="{{ servico }}" placeholder="Ex.: eletricista, pintura">
    </div>

    <div>
    <label for="uf">Estado (UF)</label>
    <select id="uf" name="uf">
    <option value="">Todos os estados</option>
    {% for sigla in ufs %}
    <option value="{{ sigla }}" {% if uf == sigla %}selected{% endif %}>{{ sigla }}</option>
    {% endfor %}
    </select>
    </div>

    <div>
    <label for="cidade">Cidade</label>
    <input id="cidade" name="cidade" value="{{ cidade }}" placeholder="Ex.: Londrina">
    </div>

    <div class="search-actions">
    <button class="btn" type="submit">Buscar</button>
    {% if servico or uf or cidade %}
    <a class="btn secondary" href="{{ url_for('prestadores') }}">Limpar</a>
    {% endif %}
    </div>
    </form>

    {% if servico or uf or cidade %}
    <p class="muted result-summary">
    {{ itens|length }} prestador{% if itens|length != 1 %}es{% endif %} encontrado{% if itens|length != 1 %}s{% endif %}.
    </p>
    {% endif %}

    <div class="card topgap">
    {% if itens %}
    {% for p in itens %}
    <div class="item">
    <div class="provider-row">
    {% if p.logo_data %}
    <img class="provider-logo" src="{{ p.logo_data }}" alt="Logomarca ou cartão de {{ p.nome }}">
    {% endif %}
    <div>
    <h3>{{ p.nome }}</h3>
    <div>
    <span class="tag">{{ p.categoria }}</span>
    <span class="muted">{{ formatar_localizacao(p.cidade, p.uf) }}</span>
    </div>
    <p>{{ p.descricao }}</p>
    <div class="actions">
    <a class="btn secondary" href="{{ url_for('perfil_prestador', pid=p.id) }}">Ver perfil</a>
    {% set wpp = whatsapp_url(p.telefone) %}
    {% if wpp %}
    <a class="btn whatsapp" href="{{ wpp }}" target="_blank" rel="noopener noreferrer">WhatsApp</a>
    {% endif %}
    </div>
    </div>
    </div>
    </div>
    {% endfor %}
    {% else %}
    <p class="muted">
    Nenhum prestador encontrado com esses filtros. Tente outro serviço ou uma cidade próxima.
    </p>
    {% endif %}
    </div>
    """

    return legacy.page(
        "Prestadores",
        body,
        itens=itens,
        servico=servico,
        uf=uf,
        cidade=cidade,
        ufs=UFS,
        whatsapp_url=legacy.whatsapp_url,
    )


def perfil_prestador_com_logo(pid):
    p = db.get_or_404(Prestador, pid)
    if not p.aprovado:
        abort(404)

    body = """
    <div class="card">
    <div class="profile-head">
    <div>
    <span class="tag">{{ p.categoria }}</span>
    <h1>{{ p.nome }}</h1>
    <p class="muted">{{ formatar_localizacao(p.cidade, p.uf) }}</p>
    </div>
    {% if p.logo_data %}
    <img class="profile-logo" src="{{ p.logo_data }}" alt="Logomarca ou cartão de {{ p.nome }}">
    {% endif %}
    </div>

    <h2>Sobre os serviços</h2>
    <p class="profile-description">{{ p.descricao }}</p>

    <h2>Contato</h2>
    <p><strong>Telefone/WhatsApp:</strong> {{ p.telefone }}</p>
    {% if p.email %}
    <p><strong>E-mail:</strong> {{ p.email }}</p>
    {% endif %}

    <div class="actions">
    {% set wpp = whatsapp_url(p.telefone) %}
    {% if wpp %}
    <a class="btn whatsapp" href="{{ wpp }}" target="_blank" rel="noopener noreferrer">Conversar no WhatsApp</a>
    {% endif %}
    <a class="btn secondary" href="{{ url_for('prestadores') }}">Voltar para prestadores</a>
    </div>
    </div>
    """

    return legacy.page(
        p.nome,
        body,
        p=p,
        whatsapp_url=legacy.whatsapp_url,
    )


# Mantém as mesmas URLs/endpoints da plataforma, apenas troca as telas afetadas.
app.view_functions["sou_prestador"] = sou_prestador_com_logo
app.view_functions["prestadores"] = prestadores_com_logo
app.view_functions["perfil_prestador"] = perfil_prestador_com_logo
