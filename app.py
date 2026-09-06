
1000494095.jpg

1000494096.jpg

1000494098.jpg

1000494100.jpg

1000494101.jpg

1000494102.jpg

1000494103.jpg

1000494104.jpg

1000494108.jpg

1000494110.jpg

1000494111.jpg

1000494112.jpg

Ótimo! ✅ Então essa etapa está concluída.

Agora o Conecta Serviços já tem:

busca por serviço + UF + cidade;

perfil individual de cada prestador;

botão direto para WhatsApp;

dados existentes preservados;

painel administrativo funcionando.

A próxima melhoria que eu faria é permitir que o prestador coloque foto ou logotipo no perfil, deixando a plataforma bem mais profissional. Depois podemos implementar avaliações por estrelas.

Se quiser, seguimos com a foto do prestador agora.


1000494113.jpg

Vi o problema. A funcionalidade entrou, mas os acentos ficaram corrompidos na nova versão.

Por exemplo:

“Início” virou “InÃ­cio”

“Serviços” virou “ServiÃ§os”

“complicação” virou “complicaÃ§Ã£o”

Isso é um problema de codificação UTF-8 ocorrido na cópia pelo celular, não do Render nem do banco de dados.

Não precisamos desfazer as novas funções. Vou corrigir somente os textos/accentuação, mantendo perfil, WhatsApp, UF, cidade e busca funcionando. Depois substituímos o app.py corrigido e fazemos mais um deploy.


Ok

Pronto. Preparei uma nova cópia do arquivo, explicitamente em UTF-8, e validei a sintaxe.

Baixar o app.py corrigido

Agora faça como anteriormente: copie todo o conteúdo desse arquivo. Depois abra o app.py no GitHub → Editar arquivo, apague todo o conteúdo atual e cole este novo.

Antes de confirmar, o começo deverá aparecer assim:

# -*- coding: utf-8 -*-
import os
import hmac
Depois toque em Confirmar alterações. Se pedir mensagem, coloque:

Corrigir acentuação UTF-8

Depois fazemos o deploy no Render novamente. 


app_corrigido_utf8.py
Código


Nenhum arquivo escolhido
Biblioteca
/
app_corrigido_utf8.py


1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
20
21
22
23
24
# -*- coding: utf-8 -*-
import os
import hmac
from datetime import datetime
from flask import Flask, request, redirect, url_for, session, flash, render_template_string, abort
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import inspect, or_, text

app = Flask(__name__)

database_url = os.getenv("DATABASE_URL", "sqlite:///plataforma.db")
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

app.config["SQLALCHEMY_DATABASE_URI"] = database_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret-change-me")

db = SQLAlchemy(app)

UFS = (
    "AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO", "MA",
    "MT", "MS", "MG", "PA", "PB", "PR", "PE", "PI", "RJ", "RN",
    "RS", "RO", "RR", "SC", "SP", "SE", "TO"
