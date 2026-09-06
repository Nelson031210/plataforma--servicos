# Conecta Serviços

Plataforma simples para conectar clientes e prestadores de serviços.

## Recursos
- Cadastro de prestadores
- Aprovação de prestadores pelo administrador
- Busca por nome, cidade, categoria ou descrição
- Pedidos de serviço por clientes
- Painel administrativo
- PostgreSQL no Render
- Blueprint `render.yaml`

## Publicação no Render
1. Coloque todos os arquivos deste projeto na raiz de um repositório GitHub.
2. No Render, escolha **New > Blueprint**.
3. Conecte o repositório.
4. O Render lerá o arquivo `render.yaml`.
5. Quando solicitado, defina uma senha forte para `ADMIN_PASSWORD`.
6. Aguarde a criação do serviço web e do PostgreSQL.

## Administração
Depois de publicar, acesse:
`https://SEU-ENDERECO.onrender.com/admin/login`

Use a senha configurada em `ADMIN_PASSWORD`.

## Observação
O plano gratuito do PostgreSQL no Render é adequado para teste e demonstração, mas expira após o período definido pelo Render. Para uso real/produção, migre o banco para um plano persistente.
