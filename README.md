# Django Commerce API

E-commerce construído com Django, Django REST Framework e PostgreSQL. O projeto oferece um site server-rendered com sessões e CSRF e mantém a API pública autenticada por JWT.

## Autoria e origem

Este fork é mantido e modernizado por **Andrew da Silva**. Ele deriva do projeto `Nizoszz/django-commerce-api`; as alterações deste fork incluem a modernização do domínio, segurança, testes, frontend Django Templates e integração OIDC. O histórico Git preserva a autoria do projeto-base e de cada contribuição posterior.

Pedidos novos armazenam snapshots de quantidade, preço unitário e dados do produto. Na migração de pedidos anteriores a esse recurso, a quantidade assume `1`, pois o modelo legado não guardava a quantidade original; preço e identificação do produto são recuperados do catálogo existente durante a migração.

## Requisitos

- Python 3.12+
- Docker com Docker Compose

## Instalação

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/macOS: source .venv/bin/activate
pip install -r requirements-dev.txt
```

Copie `.env.example` para `.env` e preencha as credenciais usadas em desenvolvimento.

Sem variáveis de banco, o servidor de desenvolvimento usa SQLite automaticamente. Para usar PostgreSQL local, configure `POSTGRESQL_DB_NAME`, `POSTGRESQL_USERNAME`, `POSTGRESQL_PASSWORD`, `POSTGRESQL_DB_HOST` e `POSTGRESQL_DB_PORT`. Produção exige PostgreSQL por `DATABASE_URL` ou por essas variáveis; a suíte de testes continua usando exclusivamente PostgreSQL no Docker.

Prepare o banco e os arquivos estáticos:

```bash
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py runserver
```

Para carregar um catálogo demonstrativo de calçados com imagens, execute:

```bash
python manage.py seed_shoes
```

O comando pode ser executado novamente sem duplicar produtos nem restaurar o estoque de itens existentes. Por padrão, ele cria o vendedor técnico `demo-seller` com senha inutilizável; use `--seller nome-do-vendedor` para atribuir o catálogo a outro vendedor já existente. Para corrigir URLs do catálogo já carregado sem alterar os demais dados, execute `python manage.py seed_shoes --refresh-images`.

## Site

As rotas principais são `/`, `/shop/`, `/login/`, `/register/`, `/account/`, `/cart/`, `/checkout/`, `/orders/`, `/partner/apply/` e `/seller/`. O site usa Django Templates, forms, sessões HttpOnly, CSRF e JavaScript sem dependências apenas para o menu e o carrinho lateral.

Contas locais usam Argon2id. O endereço pode ser completado em `/account/`; carrinho e checkout permanecem bloqueados enquanto rua, número, CEP, cidade e estado não estiverem preenchidos. Solicitações para se tornar parceiro são analisadas no Django Admin e o próprio usuário não pode promover sua conta.

## OpenID Connect

OIDC é opcional e usa Authorization Code, PKCE S256, state e nonce. Configure:

```dotenv
OIDC_SERVER_METADATA_URL=https://provedor/.well-known/openid-configuration
OIDC_CLIENT_ID=commerce-web
OIDC_CLIENT_SECRET=
OIDC_SCOPES=openid email profile
OIDC_PROVIDER_NAME=default
OIDC_REDIRECT_URI=http://127.0.0.1:8000/auth/oidc/callback/
```

### OIDC local pronto para uso

O Compose inclui Keycloak 26.7.0 com o realm e o cliente importados automaticamente:

```bash
docker compose up -d keycloak
python manage.py runserver
```

Acesse `/login/` e escolha **Continuar com Keycloak local**. Conta de demonstração, apenas para desenvolvimento:

```text
usuário: cliente
senha: Cliente123!
```

O Admin do Keycloak fica em `http://127.0.0.1:8080/admin/`, com usuário `keycloak-admin` e senha local `local-admin-password`. Essas credenciais pertencem somente ao ambiente descartável de desenvolvimento e não devem ser utilizadas em produção.

Cadastre no provedor exatamente o callback definido em `OIDC_REDIRECT_URI` — em produção, por exemplo, `https://seu-dominio/auth/oidc/callback/`. Reinicie o servidor depois de alterar o `.env`. O botão fica desabilitado e explica a configuração ausente enquanto metadata ou client ID não estiverem definidos. Apenas e-mails verificados são aceitos. Uma identidade externa nunca é vinculada automaticamente a uma conta local com o mesmo e-mail; o vínculo explícito é iniciado em `/account/` por um usuário já autenticado. Tokens do provedor não são armazenados no navegador nem persistidos após a criação da sessão Django.

## Testes

Os testes usam exclusivamente PostgreSQL. O Compose publica o banco temporário na porta `5433` e mantém os dados somente enquanto o container estiver ativo.

```bash
docker compose up -d --wait postgres-test
pytest
pytest --cov=addresses --cov=cart --cov=orders --cov=products --cov=storefront --cov=users
docker compose down
```

As credenciais padrão podem ser substituídas pelas variáveis `TEST_POSTGRES_DB`, `TEST_POSTGRES_USER`, `TEST_POSTGRES_PASSWORD`, `TEST_POSTGRES_HOST` e `TEST_POSTGRES_PORT`.

## Qualidade e integração contínua

A pipeline `.github/workflows/quality.yml` é executada em todo `push`, pull request e merge queue. Ela valida lint e formatação com Ruff, auditoria de dependências, checks do Django, migrações, OpenAPI, configurações de implantação e a suíte completa em PostgreSQL 17 com cobertura mínima de 80%.

Execute as mesmas verificações de lint localmente antes de enviar alterações:

```bash
ruff check .
ruff format --check .
python manage.py check
python manage.py makemigrations --check --dry-run
```

## Docker e CD no Render

A imagem roda como usuário sem privilégios, inclui os arquivos estáticos e expõe `/health/` para os health checks:

```bash
docker build -t django-commerce-api .
docker run --rm -p 8000:8000 --env-file .env django-commerce-api
```

Após a pipeline de qualidade passar em `develop`, o workflow `.github/workflows/deploy.yml` chama o Deploy Hook. O próprio Render clona a branch e constrói o `Dockerfile`, portanto não são necessárias credenciais do Docker Hub.

No Render, desative Auto-Deploy para não duplicar implantações e defina o health check como `/health/`. Como o Pre-Deploy Command não está disponível em todos os planos, o container executa `python manage.py migrate --noinput` antes de iniciar o Gunicorn. No environment GitHub `production`, crie o secret `RENDER_DEPLOY_HOOK_URL` com o hook do serviço.

Para popular o PostgreSQL do Render, defina temporariamente `SEED_DEMO_PRODUCTS=true` nas variáveis do Web Service e faça um deploy. A inicialização executará `seed_shoes --refresh-images` depois das migrações e antes do Gunicorn. Após confirmar o catálogo, remova a variável ou altere-a para `false`; reexecuções não duplicam produtos nem restauram estoque existente. Se o plano oferecer Shell, o equivalente é executar uma única vez `python manage.py seed_shoes --refresh-images` diretamente no serviço.

O Render sobe a nova instância ao lado da atual, testa sua saúde e então transfere o tráfego, realizando a troca blue/green sem indisponibilidade. Migrações devem ser retrocompatíveis durante essa janela (expand/migrate/contract). Para rollback, selecione no Render a tag imutável do commit anterior.

### Variáveis de ambiente no Render

Na página **Environment** do Web Service, use **Add from .env** com o modelo `.env.render.example`. As únicas variáveis obrigatórias da aplicação são:

```dotenv
DEBUG=false
SECRET_KEY=<chave longa e aleatória>
DATABASE_URL=<Internal Database URL do Render Postgres>
```

Use a URL interna do PostgreSQL quando banco e serviço estiverem na mesma conta e região. O Render fornece `RENDER_EXTERNAL_HOSTNAME`, `PORT` e `WEB_CONCURRENCY` automaticamente, portanto elas não precisam ser cadastradas. Defina `ALLOWED_HOSTS` apenas para domínios personalizados; o domínio `*.onrender.com` é reconhecido automaticamente. SMTP e OIDC são opcionais e estão documentados no arquivo de exemplo.

## Verificações

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py spectacular --file docs/openapi/schema.yaml --validate
python -m pip_audit -r requirements.txt
```

## Segurança em produção

Defina `DEBUG=false`, uma `SECRET_KEY` longa e aleatória e `ALLOWED_HOSTS` com os domínios reais. HTTPS, HSTS e cookies seguros são ativados automaticamente fora do modo debug. A documentação OpenAPI fica restrita a administradores em produção.

Os tokens de acesso expiram em 15 minutos. Refresh tokens são rotacionados e invalidados após o uso; use `/api/users/token/refresh/` para renovar e `/api/users/logout/` para invalidar uma sessão.

Logins locais, JWT e administrativos são protegidos contra brute force por usuário e endereço IP. Após cinco falhas, o acesso recebe `429 Too Many Requests` por 15 minutos; os contadores ficam no PostgreSQL e são compartilhados entre os workers. Os limites podem ser ajustados por `AXES_FAILURE_LIMIT` e `AXES_COOLOFF_MINUTES`.

A equivalência funcional com o projeto React de referência está documentada em [FRONTEND_REFERENCE_MATRIX.md](FRONTEND_REFERENCE_MATRIX.md).
