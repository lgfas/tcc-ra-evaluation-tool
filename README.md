# TCC — Ferramenta de Avaliação de Arquiteturas de Referência

Este repositório contém a especificação e a implementação de uma ferramenta de apoio à avaliação de Arquiteturas de Referência, desenvolvida como TCC de Engenharia de Computação.

A proposta atual combina:

- avaliação conceitual da RA, apoiada por checklists e critérios da literatura;
- avaliação prática por instanciação, registrando evidências e conformidade entre uma RA e arquiteturas concretas derivadas dela.

A documentação acadêmica em `docs/` é a fonte de verdade e permanece preservada. Nesta etapa (SETUP-01 + AUTH-01), estão implementadas somente a fundação executável e RF-USR-01/02/03: cadastro, login e encerramento de sessão. RAs, checklists, avaliações e conformidade ainda não estão implementados.

## Pré-requisitos e versões

- Linux, Python **3.13**, com `venv` e `pip`.
- Node.js **24 LTS** recomendado (Vite requer Node >=22.12 ou >=20.19), npm e Docker com Compose v2 ou superior.
- Django **5.2.19 LTS**, Django REST Framework **3.18.3**, Psycopg **3.3.8**.
- PostgreSQL **18.6**, imagem oficial com tag explícita.
- React 19, TypeScript 5.9 e Vite 7; versões exatas resolvidas em `frontend/package-lock.json`.

`python-dotenv` carrega o `.env` da raiz independentemente do diretório de execução. Psycopg binary evita exigir compilador/libpq local. As demais dependências do frontend são as necessárias para React, TypeScript e Vite; não há biblioteca de rotas, estado global ou componentes.

## Estrutura

```text
backend/
  manage.py
  requirements.txt
  config/                 # settings, URLs, WSGI e healthcheck
  apps/users/             # modelo, admin, serializers, views, URLs e testes
    migrations/0001_initial.py
frontend/
  src/
    components/           # mensagens reutilizáveis
    pages/                # login/cadastro e início autenticado
    services/api.ts       # Fetch, cookies, CSRF e erros
    App.tsx
    styles.css
  package.json
  package-lock.json
  vite.config.ts
compose.yaml
.env.example
docs/                     # especificação acadêmica
```

## Configuração

Na raiz do repositório:

```bash
cp .env.example .env
chmod 600 .env
python3 -c 'import secrets; print(secrets.token_urlsafe(48))'
```

Edite `.env`: use a saída como `DJANGO_SECRET_KEY` e defina uma senha local própria em `POSTGRES_PASSWORD`. Não versione esse arquivo. As variáveis exportadas no shell têm precedência sobre o arquivo.

| Variável | Finalidade / padrão do exemplo |
| --- | --- |
| `DJANGO_SECRET_KEY` | Segredo obrigatório do Django |
| `DJANGO_DEBUG` | `true` somente no desenvolvimento |
| `DJANGO_ALLOWED_HOSTS` | `127.0.0.1,localhost` |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | Origens Vite `http://127.0.0.1:5173,http://localhost:5173` |
| `DJANGO_SECURE_COOKIES` | `false` no HTTP local; cookies Secure requerem HTTPS |
| `POSTGRES_DB` | `tcc_ra` |
| `POSTGRES_USER` | `tcc_ra` |
| `POSTGRES_PASSWORD` | Senha obrigatória, compartilhada entre Compose e Django |
| `POSTGRES_HOST` | `127.0.0.1`, pois Django executa no host |
| `POSTGRES_PORT` | `5433`, porta publicada fixa do Compose |

## Iniciar PostgreSQL

```bash
docker compose up -d --wait db
docker compose ps
```

O serviço `db` publica somente `127.0.0.1:5433:5432`, possui healthcheck e persiste dados no volume nomeado `postgres_data` (prefixado pelo nome do projeto). Não interfere com PostgreSQL na porta 5432 do host. As credenciais de inicialização do PostgreSQL só se aplicam quando o volume está vazio; editar `.env` não altera usuários/senhas de um banco já inicializado.

## Backend

Na raiz, em um terminal:

```bash
python3.13 -m venv backend/.venv
source backend/.venv/bin/activate
python -m pip install -r backend/requirements.txt
python backend/manage.py migrate
python backend/manage.py check
python backend/manage.py runserver 127.0.0.1:8000
```

Healthcheck: `curl http://127.0.0.1:8000/api/health/` → `{"status":"ok"}`. É uma verificação de funcionamento HTTP; não verifica disponibilidade do banco.

Opcionalmente, para usar o Django Admin:

```bash
python backend/manage.py createsuperuser
```

Acesse `http://127.0.0.1:8000/admin/`. O comando solicita e-mail, nome e senha.

## Frontend

Em outro terminal, na raiz:

```bash
cd frontend
npm ci
npm run dev
```

Acesse **http://127.0.0.1:5173**. Cadastre uma conta e entre com e-mail e senha. Atualizar a página recupera a sessão via `/api/auth/me/`. Encerre a sessão pelo botão na área inicial.

O Vite mantém a porta 5173 fixa e encaminha `/api` ao Django em `http://127.0.0.1:8000`. Use o mesmo hostname durante a sessão, pois cookies de `localhost` e `127.0.0.1` são distintos. Não é necessário CORS no desenvolvimento: o navegador acessa a API pela mesma origem do Vite. O proxy é de desenvolvimento; este projeto ainda não contém infraestrutura de publicação.

## API e segurança

| Método | Endpoint | Acesso / resposta |
| --- | --- | --- |
| GET | `/api/health/` | Público, 200 |
| GET | `/api/auth/csrf/` | Público, cookie e `csrfToken` |
| POST | `/api/auth/register/` | Público com CSRF, `name`, `email`, `password`; 201 |
| POST | `/api/auth/login/` | Público com CSRF, `email`, `password`; 200 |
| GET | `/api/auth/me/` | Autenticado; 200 |
| POST | `/api/auth/logout/` | Autenticado com CSRF; 204 |

Usuários são representados somente por `id`, `name` e `email`. Cadastro não autentica automaticamente. Validação e credenciais inválidas retornam 400; ausência de sessão e falhas CSRF retornam 403 (comportamento de SessionAuthentication). O frontend apresenta mensagens de erro e permite repetir operações após falhas de rede.

D12 e fluxo 08 orientam autenticação simples; RN-USR-01 orienta a unicidade. O modelo personalizado existe desde a primeira migração, normaliza e-mail para minúsculas e tem restrição funcional `Lower(email)` no PostgreSQL, inclusive contra gravações concorrentes. Senhas usam hashing e validadores nativos do Django (RNF-15).

A API é privada por padrão. Cadastro e login recebem `csrf_protect` explícito, inclusive para usuários anônimos. O cliente obtém token antes de cada escrita e usa cookies com `credentials: same-origin`; isso também considera a rotação do token no login. A sessão fica no banco; o cookie de sessão é HttpOnly e SameSite=Lax. Senhas e credenciais de sessão não são armazenadas em localStorage. Logout remove a sessão no servidor. Não há JWT nem serviços externos.

As responsabilidades estão separadas em modelo/ORM, serializers de validação, views HTTP e frontend (RNF-13/14). Nenhuma camada Repository ou serviço sem necessidade foi criada. Os campos técnicos de permissões, datas e sessão do Django preservam a integração com Admin.

## Testes e verificações

Com o banco iniciado e o ambiente Python ativado, na raiz:

```bash
python backend/manage.py test apps.users --verbosity 2
python backend/manage.py makemigrations --check --dry-run
python backend/manage.py check
cd frontend
npm run typecheck
npm run build
```

Os testes usam PostgreSQL real e criam/removem `test_tcc_ra`, separado do banco de desenvolvimento. O usuário inicial do container possui permissão para criar esse banco. Não aponte essa configuração para bancos compartilhados ou de produção.

A suíte cobre cadastro, validação, duplicidade exata e por capitalização, restrição no banco, hashing, login válido/inválido/inativo, consulta e persistência da sessão, acesso anônimo, logout e invalidação do cookie antigo, CSRF ausente/inválido/rotacionado e origem não confiável, healthcheck e formulários Admin.

## DBeaver

Crie uma conexão **PostgreSQL** com:

- Host: `127.0.0.1`
- Porta: `5433`
- Database: `tcc_ra`
- Usuário: `tcc_ra`
- Senha: valor de `POSTGRES_PASSWORD` no seu `.env`
- SSL: desabilitado para esta instância local de desenvolvimento.

Use “Testar conexão”; o DBeaver poderá solicitar o download do driver PostgreSQL. A porta interna do container continua sendo 5432.

## Encerrar

Pare Django e Vite com `Ctrl+C` nos respectivos terminais. Na raiz:

```bash
docker compose stop db
# Ou remova container/rede mantendo o volume:
docker compose down
```

Não use `docker compose down -v` se quiser preservar os dados. Esta configuração destina-se a desenvolvimento local; publicação requer configuração própria de HTTPS, segredos, hosts e execução do backend.
