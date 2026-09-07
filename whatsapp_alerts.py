import json
import os
from datetime import datetime
from urllib import error as urlerror
from urllib import request as urlrequest

from flask import abort, flash, redirect, request, session, url_for
from sqlalchemy import inspect, text

import app as legacy
import logo_feature

app = legacy.app
db = legacy.db
Prestador = legacy.Prestador
Pedido = legacy.Pedido
UFS = legacy.UFS


class AlertaWhatsApp(db.Model):
    __tablename__ = "alerta_whatsapp"

    id = db.Column(db.Integer, primary_key=True)
    pedido_id = db.Column(db.Integer, db.ForeignKey("pedido.id"), nullable=False)
    prestador_id = db.Column(db.Integer, db.ForeignKey("prestador.id"), nullable=False)
    status = db.Column(db.String(30), nullable=False, default="pendente")
    detalhe = db.Column(db.Text, nullable=True)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        db.UniqueConstraint(
            "pedido_id",
            "prestador_id",
            name="uq_alerta_whatsapp_pedido_prestador",
        ),
    )


with app.app_context():
    with db.engine.begin() as conexao:
        colunas = {
            coluna["name"]
            for coluna in inspect(conexao).get_columns("prestador")
        }
        if "alertas_whatsapp" not in colunas:
            conexao.execute(
                text(
                    "ALTER TABLE prestador "
                    "ADD COLUMN alertas_whatsapp BOOLEAN NOT NULL DEFAULT FALSE"
                )
            )
        if "alcance_alerta" not in colunas:
            conexao.execute(
                text(
                    "ALTER TABLE prestador "
                    "ADD COLUMN alcance_alerta VARCHAR(20) NOT NULL DEFAULT 'cidade'"
                )
            )

    if not hasattr(Prestador, "alertas_whatsapp"):
        Prestador.alertas_whatsapp = db.Column(
            db.Boolean,
            nullable=False,
            default=False,
            server_default=text("FALSE"),
        )
    if not hasattr(Prestador, "alcance_alerta"):
        Prestador.alcance_alerta = db.Column(
            db.String(20),
            nullable=False,
            default="cidade",
            server_default="cidade",
        )

    db.create_all()


ALERT_CSS = """
.alert-box{
    background:#f0fdf4;
    border:1px solid #bbf7d0;
    border-radius:14px;
    padding:16px;
    margin:18px 0;
}
.alert-box h3{margin:0 0 6px}
.check-row{
    display:flex;
    gap:10px;
    align-items:flex-start;
    margin-top:16px;
}
.check-row input{
    width:auto;
    margin-top:4px;
    transform:scale(1.15);
}
.check-row label{
    margin:0;
    font-weight:600;
}
.status-pill{
    display:inline-block;
    padding:5px 10px;
    border-radius:999px;
    background:#e2e8f0;
    font-size:13px;
}
"""

if ALERT_CSS not in legacy.BASE:
    legacy.BASE = legacy.BASE.replace("</style>", ALERT_CSS + "\n</style>")

nav_anchor = """<a href=\"{{ url_for('area_prestador') }}\">\nÁrea do prestador\n</a>"""
nav_alertas = nav_anchor + """\n\n<a href=\"{{ url_for('preferencias_alertas') }}\">\nAlertas WhatsApp\n</a>"""
if "url_for('preferencias_alertas')" not in legacy.BASE:
    legacy.BASE = legacy.BASE.replace(nav_anchor, nav_alertas)


def telefone_meta(telefone):
    numeros = legacy.numeros_telefone(telefone)
    if len(numeros) in (10, 11):
        numeros = "55" + numeros
    return numeros


def whatsapp_configurado():
    obrigatorias = (
        "WHATSAPP_ACCESS_TOKEN",
        "WHATSAPP_PHONE_NUMBER_ID",
        "WHATSAPP_GRAPH_API_VERSION",
        "WHATSAPP_TEMPLATE_NAME",
    )
    return all((os.getenv(chave) or "").strip() for chave in obrigatorias)


def link_area_prestador():
    base = (os.getenv("PUBLIC_BASE_URL") or "").strip().rstrip("/")
    if base:
        return base + "/area-prestador"
    return "/area-prestador"


def enviar_template_whatsapp(prestador, pedido):
    if not whatsapp_configurado():
        return False, "configuracao_whatsapp_pendente"

    destino = telefone_meta(prestador.telefone)
    if len(destino) < 12:
        return False, "telefone_invalido"

    versao = os.getenv("WHATSAPP_GRAPH_API_VERSION").strip()
    phone_id = os.getenv("WHATSAPP_PHONE_NUMBER_ID").strip()
    token = os.getenv("WHATSAPP_ACCESS_TOKEN").strip()
    template = os.getenv("WHATSAPP_TEMPLATE_NAME").strip()
    idioma = (os.getenv("WHATSAPP_TEMPLATE_LANGUAGE") or "pt_BR").strip()

    endpoint = f"https://graph.facebook.com/{versao}/{phone_id}/messages"
    local = legacy.formatar_localizacao(pedido.cidade, pedido.uf)

    payload = {
        "messaging_product": "whatsapp",
        "to": destino,
        "type": "template",
        "template": {
            "name": template,
            "language": {"code": idioma},
            "components": [
                {
                    "type": "body",
                    "parameters": [
                        {"type": "text", "text": prestador.nome[:120]},
                        {"type": "text", "text": pedido.servico[:120]},
                        {"type": "text", "text": local[:120]},
                        {"type": "text", "text": link_area_prestador()[:500]},
                    ],
                }
            ],
        },
    }

    requisicao = urlrequest.Request(
        endpoint,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urlrequest.urlopen(requisicao, timeout=8) as resposta:
            conteudo = resposta.read().decode("utf-8", errors="replace")
            return 200 <= resposta.status < 300, conteudo[:1500]
    except urlerror.HTTPError as exc:
        detalhe = exc.read().decode("utf-8", errors="replace")
        return False, f"http_{exc.code}: {detalhe[:1200]}"
    except Exception as exc:
        return False, f"erro_envio: {type(exc).__name__}: {str(exc)[:700]}"


def prestador_deve_receber(prestador, pedido):
    if not prestador.aprovado or not bool(prestador.alertas_whatsapp):
        return False
    if not legacy.categoria_compativel(pedido.servico, prestador.categoria):
        return False
    if legacy.uf_valida(prestador.uf) != legacy.uf_valida(pedido.uf):
        return False

    mesma_cidade = (
        legacy.normalizar_texto(prestador.cidade)
        == legacy.normalizar_texto(pedido.cidade)
    )
    alcance = (prestador.alcance_alerta or "cidade").strip().lower()
    return mesma_cidade or alcance == "estado"


def disparar_alertas_para_pedido(pedido):
    prestadores = Prestador.query.filter_by(aprovado=True).all()
    enviados = 0

    for prestador in prestadores:
        if not prestador_deve_receber(prestador, pedido):
            continue

        existente = AlertaWhatsApp.query.filter_by(
            pedido_id=pedido.id,
            prestador_id=prestador.id,
        ).first()
        if existente:
            continue

        registro = AlertaWhatsApp(
            pedido_id=pedido.id,
            prestador_id=prestador.id,
            status="processando",
        )
        db.session.add(registro)
        db.session.commit()

        ok, detalhe = enviar_template_whatsapp(prestador, pedido)
        registro.status = "enviado" if ok else "nao_enviado"
        registro.detalhe = detalhe
        db.session.commit()
        if ok:
            enviados += 1

    return enviados


def quero_servico_com_alertas():
    if request.method == "POST":
        dados = {
            k: (request.form.get(k) or "").strip()
            for k in ["nome", "cidade", "uf", "telefone", "email", "descricao"]
        }
        dados["servico"] = (
            request.form.get("categoria")
            or request.form.get("servico")
            or ""
        ).strip()
        dados["uf"] = dados["uf"].upper()
        obrig = ["nome", "cidade", "uf", "telefone", "servico", "descricao"]

        if any(not dados[k] for k in obrig):
            flash("Preencha todos os campos obrigatórios.", "error")
        elif dados["uf"] not in UFS:
            flash("Selecione um Estado (UF) válido.", "error")
        else:
            pedido = Pedido(**dados)
            db.session.add(pedido)
            db.session.commit()
            disparar_alertas_para_pedido(pedido)
            flash(
                "Pedido enviado com sucesso! Profissionais compatíveis que optaram por alertas serão avisados."
            )
            return redirect(url_for("quero_servico"))

    body = """
    <h1>Preciso de um serviço</h1>
    <p class="muted">Conte o que precisa. O Conecta procura profissionais compatíveis na sua região.</p>
    <div class="card">
    <form method="post">
    <label>Seu nome *</label><input autocomplete="name" name="nome" required>
    <label>Estado (UF) *</label>
    <select name="uf" required><option value="">Selecione</option>
    {% for sigla in ufs %}<option value="{{ sigla }}">{{ sigla }}</option>{% endfor %}</select>
    <label>Cidade *</label><input autocomplete="address-level2" name="cidade" required>
    <label>Telefone/WhatsApp *</label><input autocomplete="tel" inputmode="tel" name="telefone" required>
    <label>E-mail</label><input autocomplete="email" type="email" name="email">
    <label>Categoria do serviço *</label><input name="categoria" placeholder="Ex.: eletricista, jardinagem, pintura" required>
    <label>Descreva o que precisa *</label><textarea name="descricao" required></textarea>
    <div class="topgap"><button class="btn">Enviar pedido</button></div>
    </form></div>
    """
    return legacy.page("Pedir serviço", body, ufs=UFS)


def sou_prestador_com_alertas():
    if request.method == "POST":
        dados = {
            k: (request.form.get(k) or "").strip()
            for k in ["nome", "cidade", "uf", "telefone", "email", "categoria", "descricao"]
        }
        dados["uf"] = dados["uf"].upper()
        obrigatorios = ["nome", "cidade", "uf", "telefone", "categoria", "descricao"]
        logo_data, erro_imagem = logo_feature.imagem_para_data_url(request.files.get("logo"))

        receber_alertas = request.form.get("alertas_whatsapp") == "sim"
        alcance = (request.form.get("alcance_alerta") or "cidade").strip().lower()
        if alcance not in ("cidade", "estado"):
            alcance = "cidade"

        if any(not dados[k] for k in obrigatorios):
            flash("Preencha todos os campos obrigatórios.", "error")
        elif dados["uf"] not in UFS:
            flash("Selecione um Estado (UF) válido.", "error")
        elif erro_imagem:
            flash(erro_imagem, "error")
        else:
            dados["logo_data"] = logo_data
            dados["alertas_whatsapp"] = receber_alertas
            dados["alcance_alerta"] = alcance
            db.session.add(Prestador(**dados))
            db.session.commit()
            flash("Cadastro recebido! Ele ficará visível após aprovação.")
            return redirect(url_for("sou_prestador"))

    body = """
    <h1>Cadastro de prestador</h1>
    <p class="muted form-intro">Crie seu perfil profissional para ser encontrado e receber oportunidades da sua região.</p>
    <div class="free-banner"><strong>Cadastro gratuito nesta fase</strong>
    Não há cobrança para criar seu perfil e divulgar seus serviços na plataforma.</div>
    <div class="card"><form method="post" enctype="multipart/form-data">
    <label>Nome ou empresa *</label><input name="nome" placeholder="Ex.: João Silva ou JS Elétrica" required>
    <label>Estado (UF) *</label><select name="uf" required><option value="">Selecione</option>
    {% for sigla in ufs %}<option value="{{ sigla }}">{{ sigla }}</option>{% endfor %}</select>
    <label>Cidade *</label><input name="cidade" placeholder="Ex.: Londrina" required>
    <label>Telefone/WhatsApp *</label><input name="telefone" type="tel" inputmode="tel" autocomplete="tel" placeholder="(43) 99999-9999" required>
    <label>E-mail</label><input type="email" name="email" autocomplete="email" placeholder="seuemail@exemplo.com">
    <label>Serviço principal / categoria *</label><input name="categoria" placeholder="Ex.: eletricista, pintor, jardinagem" required>
    <label>Apresente seus serviços *</label><textarea name="descricao" placeholder="Conte o que você faz, sua experiência, tipos de serviço e regiões que atende." required></textarea>
    <label>Logomarca ou cartão de visita</label><input type="file" name="logo" accept="image/jpeg,image/png,image/webp">
    <div class="file-help">Opcional. JPG, PNG ou WEBP de até 1,5 MB.</div>
    <div class="alert-box">
    <h3>🔔 Alertas de novas oportunidades</h3>
    <div class="check-row"><input id="alertas_whatsapp" type="checkbox" name="alertas_whatsapp" value="sim">
    <label for="alertas_whatsapp">Quero receber pelo WhatsApp avisos de clientes procurando meu tipo de serviço.</label></div>
    <label for="alcance_alerta">Onde quero receber oportunidades</label>
    <select id="alcance_alerta" name="alcance_alerta">
    <option value="cidade">Somente na minha cidade</option>
    <option value="estado">Minha cidade e outras cidades do meu estado</option></select>
    <p class="file-help">Você poderá alterar essa preferência depois. O WhatsApp será usado apenas para alertas do Conecta Serviços.</p>
    </div>
    <div class="topgap"><button class="btn">Criar perfil gratuito</button></div>
    </form></div>
    """
    return legacy.page("Sou prestador", body, ufs=UFS)


@app.route("/area-prestador/alertas", methods=["GET", "POST"])
def preferencias_alertas():
    prestador_id = session.get("prestador_id")
    if not prestador_id:
        flash("Entre na Área do prestador para configurar os alertas.", "error")
        return redirect(url_for("area_prestador"))

    prestador = db.session.get(Prestador, prestador_id)
    if not prestador or not prestador.aprovado:
        session.pop("prestador_id", None)
        abort(403)

    if request.method == "POST":
        prestador.alertas_whatsapp = request.form.get("alertas_whatsapp") == "sim"
        alcance = (request.form.get("alcance_alerta") or "cidade").strip().lower()
        prestador.alcance_alerta = alcance if alcance in ("cidade", "estado") else "cidade"
        db.session.commit()
        flash("Preferências de alertas atualizadas.")
        return redirect(url_for("preferencias_alertas"))

    body = """
    <h1>Alertas pelo WhatsApp</h1>
    <p class="muted">Escolha se quer receber novas oportunidades compatíveis com seu serviço.</p>
    <div class="card">
    <p><strong>{{ prestador.nome }}</strong></p>
    <p class="muted">{{ prestador.categoria }} — {{ formatar_localizacao(prestador.cidade, prestador.uf) }}</p>
    <form method="post">
    <div class="check-row"><input id="alertas_whatsapp" type="checkbox" name="alertas_whatsapp" value="sim" {% if prestador.alertas_whatsapp %}checked{% endif %}>
    <label for="alertas_whatsapp">Receber alertas de oportunidades no meu WhatsApp</label></div>
    <label for="alcance_alerta">Área dos alertas</label>
    <select id="alcance_alerta" name="alcance_alerta">
    <option value="cidade" {% if prestador.alcance_alerta == 'cidade' %}selected{% endif %}>Somente minha cidade</option>
    <option value="estado" {% if prestador.alcance_alerta == 'estado' %}selected{% endif %}>Minha cidade e outras cidades do meu estado</option></select>
    <p class="file-help">Status técnico do envio: {% if whatsapp_ativo %}<span class="status-pill">Integração configurada</span>{% else %}<span class="status-pill">Integração aguardando credenciais da Meta</span>{% endif %}</p>
    <div class="topgap"><button class="btn">Salvar preferências</button></div>
    </form></div>
    """
    return legacy.page("Alertas WhatsApp", body, prestador=prestador, whatsapp_ativo=whatsapp_configurado())


app.view_functions["quero_servico"] = quero_servico_com_alertas
app.view_functions["sou_prestador"] = sou_prestador_com_alertas
