# TCC — Ferramenta de Avaliação de Arquiteturas de Referência

Este repositório contém a especificação e a implementação de uma ferramenta de apoio à avaliação de Arquiteturas de Referência, desenvolvida como TCC de Engenharia de Computação.

A proposta atual combina:

- avaliação conceitual da RA, apoiada por checklists e critérios da literatura;
- avaliação prática por instanciação, registrando evidências e conformidade entre uma RA e arquiteturas concretas derivadas dela.

A documentação acadêmica em `docs/` é a fonte de verdade e permanece preservada. Estão implementados a fundação executável, RF-USR-01/02/03 (cadastro, login e encerramento de sessão) e RA-01 (cadastro transacional de RAs, propriedade, versões e permissões). RA-02 acrescenta elementos arquiteturais por versão e tipos customizados. Checklists, avaliações, imagens e conformidade permanecem para entregas futuras.

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
(cd backend && .venv/bin/python manage.py test --verbosity 2)
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


## RA-01 — Arquiteturas de Referência

O módulo está em `backend/apps/reference_architectures/`: modelos, migração, serviços de criação, permissões, serializers, views, URLs e testes. No frontend, `pages/ArchitecturesPage.tsx` contém T04–T07. A autenticação existente permanece por sessão e CSRF.

### Contrato HTTP

Todos os caminhos abaixo usam o prefixo `/api/reference-architectures/` e exigem autenticação. POST e PATCH exigem o token CSRF obtido em `/api/auth/csrf/` no cabeçalho `X-CSRFToken`, junto ao cookie de sessão.

| Método | Caminho relativo | Resultado |
| --- | --- | --- |
| GET | vazio | Array das RAs em que o usuário é membro |
| POST | vazio | Cria RA, OWNER e primeira versão; 201 |
| GET | `{id}/` | Metadados e versões; 200 |
| PATCH | `{id}/` | Altera nome/visibilidade, apenas OWNER; 200 |
| GET | `{id}/versions/` | Array de versões; 200 |
| POST | `{id}/versions/` | Cria versão, OWNER ou EDITOR; 201 |
| GET | `{id}/versions/{version_id}/` | Consulta versão pelo ID numérico; 200 |

Exemplo de POST para criar a RA:

```json
{
  "name": "RA Exemplo",
  "visibility": "PRIVATE",
  "initial_version": {
    "version": "1.0",
    "description_markdown": "# Descrição da arquitetura"
  }
}
```

Resposta de criação/detalhe (IDs e data ilustrativos):

```json
{
  "id": 1,
  "name": "RA Exemplo",
  "visibility": "PRIVATE",
  "role": "OWNER",
  "version_count": 1,
  "versions": [{
    "id": 1,
    "version": "1.0",
    "description_markdown": "# Descrição da arquitetura",
    "created_at": "2026-11-05T12:00:00-03:00"
  }]
}
```

A listagem omite `versions`, mantendo os demais campos. O papel é `null` na consulta pública por não membro. Nenhum dado pessoal dos membros é retornado. POST de nova versão recebe `{"version":"2.0","description_markdown":"Nova descrição"}` e retorna somente a versão criada. PATCH recebe, por exemplo, `{"visibility":"PUBLIC"}` e retorna o detalhe atualizado. Validação retorna 400; sessão ausente, CSRF inválido e operações não autorizadas em artefato acessível retornam 403. RAs privadas inacessíveis e versões que não pertencem à RA retornam 404, como IDs inexistentes.

### Decisões de implementação

- `transaction.atomic()` cria a RA, a associação OWNER e a primeira versão juntos. Isso refina a persistência intermediária descrita no Fluxo 01/T05 conforme a decisão explícita da tarefa RA-01; a documentação acadêmica não foi alterada.
- Unicidades no banco: membro por RA/usuário, um OWNER por RA (condicional) e identificador de versão por RA. A unicidade do OWNER garante no máximo um; a existência de pelo menos um é garantida pelo serviço transacional, não por essa restrição. Alterações diretas pelo ORM podem remover membros; não existe API de remoção nesta entrega.
- CHECKs restringem visibilidade e papel aos valores enumerados. A FK do membro para usuário usa PROTECT, evitando remoção de usuários associados. As FKs da RA para seus filhos usam CASCADE; não há endpoint de exclusão.
- Nome: até 255 caracteres; identificador de versão: até 100, sem normalização semântica ("1.0" e "1.0.0" são distintos). A API remove espaços externos do identificador e nome. A descrição é obrigatória, preserva seu texto Markdown e é apresentada como texto, sem HTML.
- Versões são ordenadas por data de criação decrescente e ID como desempate; não se infere ordem semântica do identificador. A seleção inicial usa a versão criada mais recentemente. Não há cópia de conteúdo nem endpoints de alteração de versões.
- O conflito de unicidade de versão é tratado a partir da restrição PostgreSQL, inclusive em gravações concorrentes, retornando erro de validação.
- Navegação por hash (`#/reference-architectures`, `#/reference-architectures/new`, `#/reference-architectures/{id}`) mantém links, atualização e histórico nativos sem nova dependência ou configuração de fallback no servidor. O formulário em dois passos mantém os valores em memória ao voltar; recarregar a página descarta um cadastro ainda não confirmado. A sessão continua recuperada via `/api/auth/me/`.

### Validação manual de RA-01

1. Inicie o banco, Django e Vite conforme as instruções anteriores. Acesse `http://127.0.0.1:5173`.
2. Cadastre uma conta, entre e abra **Arquiteturas de Referência**. Confirme o estado vazio.
3. Crie uma RA privada: preencha nome/visibilidade, continue, preencha versão/Markdown e volte para verificar a preservação dos valores. Confirme apenas no segundo passo.
4. Nos detalhes, confira OWNER, versão e descrição. Crie outra versão com descrição diferente; alterne as versões e confira o histórico. Repita um identificador e confira o erro.
5. Altere nome e visibilidade; confira que as descrições permanecem iguais. Volte à listagem e confira a quantidade de versões.
6. Recarregue o detalhe; a sessão e a URL devem continuar funcionando. Encerre a sessão pelo Início e entre com outra conta.
7. Com outra conta autenticada, abra pelo URL uma RA pública: a leitura deve funcionar sem ações de edição. Confira que ela não aparece em Minhas Arquiteturas. Tente o URL de uma RA privada: deve exibir erro de recurso não encontrado.
8. Para validar EDITOR, crie a associação via Django shell (não há gerenciamento de colaboradores na interface), usando os IDs reais:

```python
from apps.reference_architectures.models import ReferenceArchitectureMember
ReferenceArchitectureMember.objects.create(reference_architecture_id=RA_ID, user_id=USER_ID, role="EDITOR")
```

Entre com esse usuário: a RA deve aparecer na listagem, permitir nova versão e não oferecer alteração de metadados. A suíte automatizada também verifica essas permissões no backend.


### Verificações desta entrega

Executadas em 05/11/2026: migrações aplicadas ao PostgreSQL 18.6 do Compose; `manage.py check` sem problemas; `makemigrations --check --dry-run` sem mudanças; 29 testes Django aprovados (16 de RAs e 13 de autenticação); `npm run typecheck` e `npm run build` aprovados. Execute a suíte a partir de `backend/`: a descoberta padrão partindo da raiz do repositório encontra zero testes. O frontend não possui suíte de testes configurada. A validação visual no navegador permanece manual.

O ambiente disponível usa Python 3.14.7; as versões fixadas de Django e demais dependências foram mantidas. O `.env` local foi criado com os valores do exemplo para o banco e uma chave Django gerada; ele é ignorado pelo Git. O Compose encontrou seu volume ausente e inicializou um volume novo; o container preexistente `postgres_global` foi preservado. Nenhum banco/volume foi removido, e o Compose não foi alterado.


## RA-02 — Elementos arquiteturais e tipos

Os modelos `ArchitecturalElementType` e `RAElement` foram adicionados à app existente de RAs. Tipos possuem nome (até 255 caracteres) e criador opcional. O criador usa PROTECT: remover um usuário não deve transformar um tipo customizado em predefinido pela conversão do criador para NULL. Elementos possuem nome (até 255 caracteres), descrição Markdown, versão obrigatória (`related_name="elements"`, CASCADE) e tipo obrigatório (`related_name="ra_elements"`, PROTECT). Não há unicidade de nomes de elementos ou tipos.

As migrações `0002_architecturalelementtype_raelement` e `0003_seed_element_types` acrescentam as duas tabelas e os tipos predefinidos **Componente** e **Conector**. São categorias genéricas iniciais, sem pretensão de taxonomia científica ou universal. A migração de dados usa get_or_create com criador NULL, é idempotente e sua reversão não apaga tipos que possam estar em uso. Não altera tabelas da RA-01.

### API de elementos e tipos

| Método | Endpoint | Resultado |
| --- | --- | --- |
| GET | `/api/reference-architectures/{ra_id}/versions/{version_id}/elements/` | Array dos elementos da versão |
| POST | mesmo caminho | Cria elemento; 201 |
| GET | caminho anterior + `{element_id}/` | Consulta elemento; 200 |
| PATCH | caminho anterior + `{element_id}/` | Altera nome, tipo ou descrição; 200 |
| GET | `/api/architectural-element-types/` | Array de tipos predefinidos e próprios |
| GET | `/api/architectural-element-types/?reference_architecture_id={ra_id}` | Inclui tipos já usados na RA, quando o usuário é membro |
| POST | `/api/architectural-element-types/` | Cria tipo com o usuário da sessão; 201 |

Exemplo de criação de elemento:

```json
{"name":"API Backend","element_type_id":1,"description_markdown":"## Responsabilidade\nDisponibilizar serviços."}
```

Resposta (IDs ilustrativos):

```json
{"id":1,"name":"API Backend","description_markdown":"## Responsabilidade\nDisponibilizar serviços.","element_type":{"id":1,"name":"Componente"}}
```

PATCH aceita qualquer subconjunto dos três campos de entrada. `ra_version` e `ra_version_id` são rejeitados; a associação vem exclusivamente da URL na criação e permanece fixa na edição. O elemento é sempre buscado dentro da versão, que é buscada dentro da RA acessível. IDs incompatíveis e RAs privadas inacessíveis retornam 404. Usuários externos em RAs públicas podem ler, mas suas escritas retornam 403. Todas as operações exigem sessão; escritas exigem CSRF. A listagem de elementos usa select_related para obter os tipos sem consultas por elemento.

Para criar tipo, envie `{"name":"Serviço"}`. A resposta contém apenas `id` e `name`; o backend fixa o criador na sessão, ignorando tentativas de informar criador arbitrário, inclusive NULL. Não há endpoints de exclusão ou renomeação global.

### Política provisória dos tipos

Esta é uma decisão de implementação, não uma regra da literatura: cada usuário pode selecionar tipos predefinidos e próprios. Membros de uma RA também podem selecionar tipos já associados a elementos de qualquer versão daquela RA. Esse acesso contextual não libera a seleção em outras RAs nem expõe o catálogo privado do criador. A consulta pública dos elementos mostra ID e nome de seu tipo, sem dados pessoais do criador; ela não amplia a lista de tipos selecionáveis do visitante. O filtro contextual verifica primeiro o acesso à RA.

### Interface e integridade histórica

T08 está integrada à versão selecionada nos detalhes da RA. T09 permite adicionar/editar elementos e criar um tipo sem sair do formulário; nome e descrição preenchidos são mantidos, e o novo tipo é selecionado automaticamente. A troca de versão remonta a seção e descarta o formulário ainda não salvo. Respostas de carregamentos anteriores são ignoradas após desmontagem para evitar mistura entre versões. Markdown continua exibido como texto, sem interpretar HTML. A navegação por hash e as dependências do frontend foram preservadas.

Criação e edição são centralizadas em `create_element` e `update_element` nos serviços, com transação e verificação do papel. **O bloqueio de versões utilizadas em avaliações ainda não está implementado nem pode ser validado de ponta a ponta**: as entidades de avaliação não existem. Essas operações são os pontos para integrar a futura proteção, sem uma verificação artificial de editabilidade. No estado atual, membros podem editar elementos de versões existentes. Criar uma versão continua sem copiar elementos.

### Validação manual da RA-02

1. Inicie o backend e o frontend conforme as instruções anteriores, entre e abra uma RA.
2. Selecione uma versão e confira o estado vazio em **Elementos**. Adicione um elemento usando **Componente**, nome e descrição Markdown; confira o resultado.
3. Edite nome, tipo e descrição. Inclua texto com `<script>`: ele deve aparecer como texto, sem execução.
4. Abra outro cadastro, preencha nome/descrição e use **Criar novo tipo**. Salve o tipo e confira a seleção automática e a preservação dos demais campos. Salve o elemento. Teste cancelar e erros de validação.
5. Crie uma nova versão: sua lista deve estar vazia. Adicione um elemento nela; volte à primeira versão e confira que seu conteúdo permanece intacto.
6. Com um EDITOR associado conforme o roteiro da RA-01, confira criação/edição e reutilização dos tipos já usados pelo proprietário na RA.
7. Torne a RA pública e consulte seu URL com outra conta: nomes dos tipos e descrições devem aparecer, sem botões de adicionar/editar. A mesma conta não pode abrir uma RA privada.
8. Recarregue a página e confira a sessão, navegação por hash e funcionalidades anteriores.

### Verificações da RA-02

Executadas em 05/11/2026: as duas migrações foram aplicadas ao PostgreSQL existente sem remover registros; `check` sem problemas; `makemigrations --check --dry-run` sem mudanças. A suíte completa, executada em `backend/` com `.venv/bin/python manage.py test`, aprovou **52 testes**: 23 de elementos/tipos, 16 de RA-01 e 13 de autenticação. Inclui permissões, CSRF, IDs incompatíveis, disponibilidade contextual, seed idempotente, preservação de Markdown e isolamento entre versões. `npm run typecheck`, `npm run build` e `git diff --check` passaram. Não há suíte frontend configurada e não foi realizada validação visual no navegador.
