from flask import url_for

import app as legacy

app = legacy.app


@app.get("/privacidade")
def politica_privacidade():
    body = """
    <h1>Política de Privacidade</h1>
    <div class="card">
    <p><strong>Última atualização:</strong> 7 de setembro de 2026.</p>
    <p>O Conecta Serviços aproxima clientes e prestadores de serviços. Esta política explica como tratamos os dados informados na plataforma.</p>
    <h2>Dados coletados</h2>
    <p>Podemos coletar nome, telefone/WhatsApp, e-mail, cidade, estado, categoria profissional, descrição do serviço, logomarca ou cartão de visita e registros de uso necessários ao funcionamento e à segurança da plataforma.</p>
    <h2>Como usamos os dados</h2>
    <p>Usamos os dados para cadastrar perfis, registrar pedidos, localizar profissionais compatíveis, permitir contato entre as partes, enviar alertas de oportunidades pelo WhatsApp quando o prestador tiver autorizado e manter a segurança da plataforma.</p>
    <h2>Compartilhamento</h2>
    <p>Compartilhamos somente os dados necessários para prestar o serviço, inclusive com provedores de hospedagem, banco de dados e a Meta/WhatsApp para o envio dos alertas autorizados. Não vendemos dados pessoais.</p>
    <h2>Armazenamento e segurança</h2>
    <p>Adotamos medidas razoáveis de segurança e mantemos os dados pelo tempo necessário às finalidades descritas ou ao cumprimento de obrigações legais.</p>
    <h2>Seus direitos</h2>
    <p>Você pode solicitar confirmação, acesso, correção, revogação do consentimento ou exclusão de seus dados, observadas as obrigações legais aplicáveis.</p>
    <h2>Alertas pelo WhatsApp</h2>
    <p>Os alertas são opcionais. O prestador pode ativá-los ou desativá-los na Área do prestador. A desativação impede novos alertas automáticos.</p>
    <h2>Contato e exclusão</h2>
    <p>Para exercer seus direitos ou pedir exclusão, acesse as <a href="{{ url_for('exclusao_dados') }}">instruções de exclusão de dados</a>.</p>
    </div>
    """
    return legacy.page("Política de Privacidade", body)


@app.get("/termos")
def termos_servico():
    body = """
    <h1>Termos de Serviço</h1>
    <div class="card">
    <p><strong>Última atualização:</strong> 7 de setembro de 2026.</p>
    <p>O Conecta Serviços funciona como plataforma de aproximação entre clientes e prestadores independentes. A plataforma não executa, garante ou fiscaliza os serviços negociados entre as partes.</p>
    <p>O usuário deve fornecer informações verdadeiras, usar a plataforma de forma lícita e verificar por conta própria qualificações, preços, prazos e condições antes de contratar ou prestar um serviço.</p>
    <p>Cadastros e conteúdos que violem estes termos, a lei ou a segurança da comunidade poderão ser suspensos ou removidos.</p>
    <p>O uso dos alertas do WhatsApp é opcional e pode ser desativado pelo prestador na Área do prestador.</p>
    </div>
    """
    return legacy.page("Termos de Serviço", body)


@app.get("/exclusao-de-dados")
def exclusao_dados():
    body = """
    <h1>Exclusão de dados</h1>
    <div class="card">
    <p>Para solicitar a exclusão dos seus dados, entre na Área do prestador e desative os alertas do WhatsApp. Para a exclusão completa do cadastro, envie uma solicitação pelo canal de contato informado na plataforma, identificando o telefone usado no cadastro.</p>
    <p>Após confirmar a identidade do solicitante, o Conecta Serviços excluirá ou anonimizará os dados que não precisem ser mantidos por obrigação legal, segurança ou exercício regular de direitos.</p>
    <p>O atendimento da solicitação será confirmado pelo canal de contato fornecido pelo usuário.</p>
    </div>
    """
    return legacy.page("Exclusão de dados", body)
