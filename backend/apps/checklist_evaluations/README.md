# Avaliações por checklist — AVA-01, AVA-02 e AVA-03

Implementa RF-AVA-01 a RF-AVA-04, seleção de versões próprias/autorizadas ou públicas (RF-CAT-03/04), participantes e papéis por versão, e a transição DRAFT → IN_PROGRESS. AVA-02 acrescenta respostas e progresso individual; AVA-03 acrescenta acompanhamento, finalização e resultados. Não há convites ou notificações. Não existe título persistido adicional nem snapshots dos artefatos.

## Modelos

- `ChecklistEvaluation`: RA versionada, checklist versionada, criador, status e data de criação. FKs obrigatórias com PROTECT; status válido por constraint. DRAFT é o padrão, COMPLETED representa a finalização implementada em AVA-03.
- `EvaluationParticipant`: conta cadastrada associada à avaliação, com unicidade `(checklist_evaluation, user)` no PostgreSQL. O criador não é participante automático.
- `ParticipantRole`: associação explícita com os stakeholders da versão da checklist da avaliação; unicidade do par. Não são papéis de colaboração OWNER/EDITOR.

Migração: `0001_initial.py`. As tabelas e registros anteriores são preservados.

## API

Todas as operações exigem sessão Django; POST/PATCH/DELETE mantêm SessionAuthentication e CSRF. Prefixo: `/api/checklist-evaluations/`.

| Rota relativa | Método | Finalidade |
| --- | --- | --- |
| `/` | GET | Avaliações criadas pelo usuário ou das quais ele participa |
| `/` | POST | Criar DRAFT |
| `/choices/` | GET | Metadados mínimos de RAs/checklists acessíveis e suas versões, para seleção |
| `/{id}/` | GET | Configuração completa para criador; contexto mínimo para participante |
| `/{id}/` | PATCH | Revisar seleção de versões em DRAFT |
| `/{id}/participants/` | GET | Criador vê todos; participante vê somente seu próprio registro |
| `/{id}/participants/` | POST | Adicionar conta por e-mail exato e atribuir papéis |
| `/{id}/participants/{participant_id}/` | PATCH | Substituir papéis do participante em DRAFT |
| `/{id}/participants/{participant_id}/` | DELETE | Remover participante do DRAFT |
| `/{id}/start/` | POST | Iniciar, retornando `{id, status: "IN_PROGRESS"}` |

Não há DELETE de avaliações nem PUT de configuração. O endpoint de finalização é descrito em AVA-03 abaixo. Campos desconhecidos são rejeitados com 400, inclusive `status`, `created_by_user`, título e IDs redundantes dos artefatos.

Criação:

```json
{"ra_version_id": 1, "checklist_version_id": 2}
```

Os IDs são resolvidos pelas FKs reais e pelas permissões dos artefatos. Cada versão identifica inequivocamente seu artefato; não há um segundo ID de artefato aceito no payload que possa contradizer essa relação. IDs inexistentes ou privados não autorizados retornam 404. No início, perda de acesso aos vínculos já selecionados retorna erro de validação.

Participante:

```json
{"email": "participante@exemplo.com", "stakeholder_role_ids": [1, 3]}
```

O e-mail é pesquisado por igualdade, sem distinção de capitalização. Não há diretório nem busca parcial de usuários. Papéis inexistentes, duplicados ou de outra versão são rejeitados; `[]` é válido. PATCH do participante recebe somente `{"stakeholder_role_ids": [...]}` e substitui toda a associação. Associação e papéis são persistidos na mesma transação, inclusive na edição.

PATCH da avaliação aceita um ou ambos os IDs de versão. Se a versão da checklist mudar, todos os papéis anteriormente atribuídos são removidos na mesma transação e os participantes são mantidos. Alterar só a RA ou reenviar a mesma versão da checklist preserva os papéis. Todas as seleções e alterações de papéis revalidam o acesso atual do criador aos artefatos.

A coleção retorna uma lista única com `is_creator`, `is_participant` e `can_configure`. A interface a divide em “Criadas por mim” e “Minhas participações”; quem for criador e participante aparece nos dois grupos. Combinações idênticas de versões podem ser avaliadas deliberadamente várias vezes. Na criação React, botão desabilitado e guarda síncrona por ref impedem submits repetidos do mesmo formulário; não há restrição global de unicidade da combinação.

## Acesso e privacidade

- Somente o criador configura ou inicia. Participantes não ganham esse direito nem por serem membros de um artefato.
- Externos não veem avaliações nem seus participantes; consultas retornam 404 e listagem não os inclui.
- O participante recebe identificação mínima dos artefatos/versões, status, data e seu próprio vínculo/papéis. Não recebe outros participantes, e-mails alheios, catálogo de stakeholders, questões, opções, descrições ou elementos privados.
- Participar não altera as permissões de RA/checklist. Os endpoints originais continuam exigindo propriedade, membership ou visibilidade pública.
- Usar artefatos públicos não cria membership nem transfere propriedade.
- `/choices/` aplica as mesmas regras de acesso existentes e retorna apenas nomes, visibilidade e identificadores de versões. Não é um catálogo público completo e não lista usuários.
- Se o criador perder acesso à checklist, o detalhe não expõe seus stakeholders disponíveis nem contagem de questões. Ele pode revisar a seleção para artefatos acessíveis.

## Início e decisões operacionais

O início exige DRAFT, criador autorizado, ao menos um participante e ao menos uma questão. Todas as questões da versão precisam ter enunciado, tipo/comentários válidos, opções compatíveis e relações com a própria versão. Os papéis dos participantes também são conferidos. O acesso atual às versões é revalidado após obter os bloqueios.

A exigência mínima de participantes e questões é uma **decisão operacional de implementação**, não uma regra presumida como validada pelos orientadores. Não se exige papel de todos os participantes nem seção em todas as questões. Comentário REQUIRED configura uma resposta futura, não um campo a preencher no cadastro.

O congelamento de participantes e papéis após o início é uma **decisão conservadora de implementação** para manter a configuração estável. Não é possível reabrir DRAFT, reiniciar ou trocar versões após IN_PROGRESS. A transição para COMPLETED foi acrescentada em AVA-03, conforme o contrato abaixo.

## Preservação histórica e concorrência

A utilização por **qualquer** avaliação IN_PROGRESS ou COMPLETED impede editar a versão, mesmo se houver avaliações DRAFT usando-a. DRAFT sozinho não congela conteúdo. A verificação deriva dos registros das avaliações, sem campos persistidos `locked` ou `is_used`.

- RA: `reference_architectures.services.writable_version()` sincroniza criação e atualização de elementos.
- Checklist: `checklists.services.writable_version()` sincroniza seções, stakeholders, questões, opções, associações e reordenação.
- `apps.version_protection` faz a consulta de utilização; usa o registro de apps Django para evitar imports circulares.
- Operações de configuração primeiro bloqueiam a linha da avaliação. As que precisam das versões adquirem, em ordem fixa, **avaliação → versão da RA → versão da checklist**. O início mantém esses bloqueios até o commit.
- Escritas de conteúdo bloqueiam sua versão com `select_for_update(of=('self',))`, depois verificam utilização e só então escrevem. Não bloqueiam linhas de avaliação. `of=('self',)` impede adquirir acidentalmente locks dos pais por joins.
- Se a edição obtiver o lock primeiro, o início espera seu commit e valida o conteúdo confirmado. Se o início obtiver primeiro, a edição espera e, após o commit, encontra IN_PROGRESS e é rejeitada. Não existe uma janela entre checar uso e editar sem o lock da versão.
- Os bloqueios são mantidos por `transaction.atomic`. Alterações de configuração são serializadas pela avaliação; duas tentativas simultâneas de início produzem uma única transição. Avaliações distintas podem iniciar utilizando as mesmas versões, na mesma ordem de locks.

As respostas de versões de RA/checklist incluem `is_frozen`, derivado da consulta de uso. A interface usa esse campo para informar o bloqueio e ocultar edição. O servidor continua sendo a autoridade, inclusive para abas antigas abertas antes do início.

A proteção abrange as operações de escrita do sistema por seus serviços; não pretende impedir administração SQL direta. AVA-02/03 mantêm a mesma ordem de bloqueios e não introduzir rotas alternativas de escrita retroativa. Metadados gerais (nome, visibilidade e origem) continuam distintos do conteúdo versionado. Novas versões continuam permitidas e editáveis. Opções antigas não são substituídas após o congelamento.

## Interface e W05

Rotas: `#/evaluations`, `#/evaluations/new` e `#/evaluations/{id}`. O atalho da RA usa `#/evaluations/new?ra_version_id=...` para preencher a versão selecionada, inclusive em uma RA pública de terceiro.

Reutiliza AppLayout, PageHeader, EditorPanel, EmptyState, Notice, estilos e o SVG original da navegação. W05 orienta as etapas, cartão de artefatos, participantes com identidade/papéis e resumo lateral de 320 px. Em telas pequenas, as colunas são empilhadas. A inclusão/edição, revisão de versões, remoção e confirmação de início usam os painéis acessíveis existentes.

Diferenças funcionais do protótipo: cada painel salva sua própria operação, portanto “Rascunho salvo” substitui um botão de salvar redundante; as linhas têm ações explícitas de editar/remover; o início pede confirmação do congelamento. O título é derivado da RA e não persistido. Na configuração DRAFT não há dados de exemplo, progresso, resultados, formulários de resposta ou botão de finalização.

## Executar e validar

Na raiz, com o ambiente existente ativado:

```bash
docker compose up -d --wait db
python backend/manage.py makemigrations
python backend/manage.py migrate
python backend/manage.py check
python backend/manage.py makemigrations --check --dry-run
python backend/manage.py test
python backend/manage.py runserver 127.0.0.1:8000
```

Em outro terminal:

```bash
cd frontend
npm run typecheck
npm run build
npm run dev
```

Os testes incluem regressão, privacidade, CSRF, transações e concorrência real no PostgreSQL. Os testes concorrentes usam conexões independentes, observam `pg_stat_activity.wait_event_type = 'Lock'` e coordenam liberação dos locks; não simulam a disputa com mocks.

Roteiro manual:

1. Crie uma checklist com questões válidas e stakeholders. Cadastre uma RA com duas versões e elementos.
2. Na RA, selecione uma versão e use “Criar avaliação por checklist”. Confira o preenchimento, selecione a checklist/versão e crie DRAFT.
3. Adicione contas existentes pelo e-mail exato, com zero e múltiplos papéis. Tente e-mail inexistente e repetido; confira que o formulário mantém os valores.
4. Edite papéis e remova um participante. O criador só participa se for incluído explicitamente.
5. Revise as versões. Ao trocar a checklist, confirme que os papéis são limpos e os participantes mantidos. Reatribua os papéis.
6. Em DRAFT, confirme que os elementos/estrutura ainda podem ser editados. Inicie a avaliação após revisar o resumo.
7. Confira IN_PROGRESS e ausência de ações de configuração. Recarregue e tente mutações antigas via API: devem ser rejeitadas.
8. Nas versões usadas, confira as mensagens de preservação e edição indisponível. Crie novas versões e confira que continuam editáveis. Renomeie metadados gerais para confirmar sua separação.
9. Entre como participante: veja somente seu contexto; tente abrir os artefatos privados originais e outra avaliação não relacionada.
10. Use uma RA e checklist públicas de terceiro; crie e inicie sem ganhar permissão de editar os originais.
11. Confira “Criadas por mim” e “Minhas participações”, navegação mobile, teclado, foco e logout.

A seção anterior registra a configuração da AVA-01. Respostas e progresso individual foram acrescentados pela AVA-02; acompanhamento, finalização e resultados, pela AVA-03.

## AVA-02 — Preenchimento individual

A AVA-02 acrescenta respostas e progresso **individual**. As descrições anteriores de recursos futuros referem-se ao escopo original da AVA-01; agora o participante pode responder em IN_PROGRESS. Acompanhamento consolidado, finalização e resultados são implementados na seção AVA-03 abaixo; participantes continuam sem acesso a respostas alheias.

### Modelo e migração

`Answer` referencia `EvaluationParticipant`, `Question` e, opcionalmente, `ResponseOption`. Não armazena um ID redundante de avaliação. Os textos opcionais usam string vazia por padrão, mantendo o padrão Django; a opção usa NULL. Questão e opção usam PROTECT para preservar respostas; o participante usa CASCADE, mas sua remoção pelo sistema já está bloqueada após o início.

A migração `0002_answer.py` cria somente a nova tabela. A constraint `evaluation_unique_answer` garante um registro por participante/questão. `answer_single_value` exige opção com texto vazio ou texto com conteúdo não branco e sem opção. Regras que dependem das relações (tipo configurado, opção da própria questão, versão e comentário) são validadas em `Answer.clean()`, chamado por `save_answer` antes de qualquer gravação. Não há triggers para impedir alterações SQL administrativas diretas.

### Contrato

Ambos os endpoints exigem sessão, participação explícita e IN_PROGRESS. Criador não participante e usuário externo recebem 404, como recursos inexistentes. DRAFT e COMPLETED retornam 400 com mensagem específica. A decisão desta etapa é restringir também GET a IN_PROGRESS; leitura de respostas concluídas fica para o futuro fluxo de resultados, sem alterar respostas já armazenadas.

`GET /api/checklist-evaluations/{id}/my-questions/` retorna:

```json
{
  "evaluation": {
    "id": 1,
    "status": "IN_PROGRESS",
    "ra_version": {"version": "1.0", "architecture_name": "RA Exemplo"},
    "checklist_version": {"version": "1.0", "checklist_name": "Checklist Exemplo"}
  },
  "participant": {"name": "Ana", "stakeholder_roles": [{"id": 3, "name": "Arquiteto"}]},
  "questions": [{
    "id": 10,
    "statement": "Descreva a separação de responsabilidades.",
    "response_type": "TEXT",
    "comment_mode": "OPTIONAL",
    "section": null,
    "order_index": 0,
    "options": [],
    "answer": null
  }],
  "progress": {"answered": 0, "total": 1}
}
```

Seção, quando presente: `{id, name, order_index}`. Opções de seleção: `{id, label, order_index}`. Uma resposta já salva substitui `answer: null` pelo objeto abaixo. Apenas as respostas do próprio vínculo são buscadas. Não se retorna a estrutura completa dos artefatos privados, e-mails ou respostas de outros participantes.

`PUT /api/checklist-evaluations/{id}/my-answers/{question_id}/` cria ou substitui os valores da resposta, retornando 200 em ambos os casos. Seleção:

```json
{"response_option_id": 5, "comment": "Justificativa"}
```

Texto:

```json
{"text_value": "A arquitetura separa interface, serviços e persistência.", "comment": ""}
```

Resposta salva:

```json
{"id": 20, "response_option_id": null, "text_value": "A arquitetura separa interface, serviços e persistência.", "comment": ""}
```

PUT substitui o valor e o comentário; comentários omitidos equivalem a vazio. Não há PATCH de respostas nesta etapa. Payloads com IDs de participante, usuário, questão, avaliação ou outros campos desconhecidos são rejeitados, em vez de ignorados. O participante vem da sessão e a questão vem do caminho autorizado. PUT usa a proteção CSRF já existente. Campos textuais preservam o conteúdo original; a validação considera `.strip()` para detectar texto ou comentário obrigatório somente em branco. NONE rejeita qualquer comentário não vazio, inclusive espaços. OPTIONAL aceita vazio ou preenchido; REQUIRED exige conteúdo tanto em TEXT quanto SINGLE_CHOICE. SINGLE_CHOICE rejeita qualquer texto principal não vazio e exige opção própria; TEXT exige texto e opção nula.

### Seleção, integridade e concorrência

`available_questions` restringe primeiro a versão da checklist da avaliação. Dentro dela, aplica `stakeholders IS NULL OR stakeholder IN papéis_do_participante`, com DISTINCT e ordenação por `order_index, id`. Sem papéis, somente a primeira condição é satisfeita. Papéis são também restritos à mesma versão. A operação de escrita usa esse mesmo queryset; conhecer um ID de questão omitida não permite respondê-la. Perguntas, seção, opções e respostas próprias são carregadas com select_related/prefetch_related; a quantidade de consultas de leitura não cresce por questão.

`save_answer` verifica participação, inicia uma transação e bloqueia somente a linha da **avaliação**, reconsulta o vínculo e confere IN_PROGRESS. Essa transação curta serializa salvamentos da mesma avaliação e segue a ordem de bloqueios da AVA-01, sem bloquear versões da RA/checklist. Depois resolve a questão disponível, a opção da questão e a resposta do participante. Valida todos os campos antes de inserir ou atualizar. A constraint única permanece como garantia no banco. Dois PUTs simultâneos atualizam o mesmo registro; o último salvamento confirmado prevalece. Não há controle de edição otimista entre abas nesta etapa.

A proteção histórica existente das versões não foi modificada. Nenhum endpoint de finalização foi adicionado; quando esse fluxo existir, deverá coordenar a mudança de status pelo mesmo lock da avaliação. Administração direta por SQL continua fora das garantias dos serviços.

### T18 e W06

`#/evaluations/{id}/respond` reutiliza AppLayout, PageHeader, EmptyState, Notice, estilos e o SVG de navegação existente. O W06 foi consultado no Figma: cabeçalho contextual, progresso, navegador de questões de 272 px e área de resposta. A lista identifica as seções sem alterar a ordem global das questões. Seletores são radios nativos acessíveis, com opções vindas da API; não há escala fixa. TEXT usa textarea e o comentário adicional segue sua configuração. Conteúdo do usuário continua escapado pelo React.

Ações de resposta aparecem na listagem/detalhe apenas para participantes em IN_PROGRESS. A tela oferece anterior, próxima, salvar e salvar/próxima, confirmação de persistência, questões respondidas e progresso derivado de respostas salvas. Uma guarda síncrona impede submissão duplicada. Alterações locais geram confirmação ao trocar de questão, navegar por hash ou sair da sessão, além do aviso nativo em recarregamento/fechamento. Cancelar mantém o rascunho. Não há autosave nem persistência local de respostas não salvas; descartar é uma ação explícita do usuário.

### Roteiro manual AVA-02

1. Prepare uma checklist com TEXT e SINGLE_CHOICE, comentários NONE/OPTIONAL/REQUIRED, questões comuns e questões ligadas a diferentes papéis. Inclua ao menos uma seção e uma questão vinculada a dois papéis.
2. Crie uma avaliação, associe contas com zero, um e múltiplos papéis e inicie conforme o fluxo da AVA-01.
3. Entre como participante e use **Responder avaliação**. Confira a união de suas questões e das comuns, sem duplicação; outro participante pode receber uma lista diferente.
4. Salve uma seleção e uma resposta textual. Tente salvar sem opção, texto vazio e comentário obrigatório em branco. NONE não deve apresentar campo adicional.
5. Troque de questão, retorne, altere e salve a resposta. Confira progresso sem aumentar a contagem na atualização da mesma questão. Digitar sem salvar não aumenta o progresso.
6. Com alterações locais, tente trocar de questão, navegar para outra área, usar voltar do navegador ou sair da sessão. Cancele e confira a preservação; aceite apenas quando quiser descartar. Recarregar mostra o aviso nativo.
7. Após salvar, recarregue e confira sessão, respostas e progresso recuperados da API. Use a tela em desktop e mobile e navegue por teclado.
8. Entre como criador não participante ou usuário externo e tente o URL de resposta: deve negar acesso. Um participante de avaliação com artefatos privados consegue responder, mas continua sem abrir os endpoints privados originais.
9. Abra diretamente a rota de resposta de uma avaliação DRAFT: a mensagem deve informar que ainda não iniciou. Em COMPLETED, o preenchimento é bloqueado; a finalização pelo criador é descrita em AVA-03.
10. Confira o estado vazio de um participante sem questões comuns nem papéis correspondentes, sem respostas artificiais.

### Verificações executadas em 12/11/2026

- Migração `0002_answer` aplicada ao PostgreSQL local; `makemigrations --check --dry-run` sem mudanças; `manage.py check` sem problemas.
- Suíte completa: **148 testes aprovados** (124 anteriores e 24 novos). O teste de concorrência executa dois PUTs com sessões/CSRF e conexões PostgreSQL independentes; ambos retornam o mesmo ID e deixam uma única resposta.
- `npm run typecheck`, `npm run build` e `git diff --check` aprovados, sem dependências novas.
- Chromium headless: login pela interface; leitura de quatro questões disponíveis; salvamento de SINGLE_CHOICE e TEXT; campos NONE/OPTIONAL/REQUIRED; progresso sem contar rascunhos; cancelamento de troca de questão e navegação por hash; respostas e sessão recuperadas após reload. Sem exceções JavaScript no fluxo verificado.
- Capturas desktop de 1440 px e mobile de 390 px foram inspecionadas; não houve overflow horizontal. As rotinas usaram um banco PostgreSQL de testes separado e scripts temporários fora do repositório, preservando os dados de desenvolvimento.
- Nenhum documento acadêmico em `docs/` foi alterado. Não foram executados commit ou push.

## AVA-03 — Acompanhamento, finalização e resultados

Implementa RF-AVA-07, T19/T20 e o encerramento IN_PROGRESS → COMPLETED. Não acrescenta modelos, campos, migrações, snapshots nem dependências. `Answer` e os contratos de preenchimento da AVA-02 são mantidos.

### Contratos adicionais

Prefixo `/api/checklist-evaluations/`. Todos exigem sessão autenticada; POST exige CSRF. Somente o criador tem acesso. Participantes sem autoria recebem 403; externos recebem 404; não autenticados recebem 403. Estado incompatível e dados inválidos retornam 400.

| Método e rota | Estado | Resposta |
| --- | --- | --- |
| GET `/{id}/progress/` | IN_PROGRESS ou COMPLETED | `{id, status, totals, participants}` |
| POST `/{id}/complete/` | IN_PROGRESS | `{id, status: "COMPLETED"}` |
| GET `/{id}/results/` | COMPLETED | contexto das versões, totais, participantes e questões com respostas/distribuição |

`totals` contém:

```typescript
{
  participants: number;
  expected: number; // soma das questões atribuídas a cada participante
  answered: number;
  pending: number;
  percentage: number | null; // duas casas decimais; null se expected = 0
  participants_with_pending: number;
}
```

Cada item de `participants` em progress/results contém `{id, user: {id, name}, stakeholder_roles: [{id, name}], total, answered, pending, percentage, pending_questions: [{id, statement}]}`. `id` identifica a participação, não a conta. Não são enviados e-mails nem valores de respostas no resumo de acompanhamento. O responsável continua podendo consultar as informações cadastrais pelo contrato de configuração já existente.

`complete` aceita exclusivamente `{"confirm_incomplete": boolean}`, opcional e falso por padrão. `{}` é suficiente sem pendências. Havendo pendências sem confirmação, retorna 400 com `detail`, `pending` e `participants_with_pending` (os totais são serializados como strings pela ValidationError do DRF). Nenhum status é alterado nessa rejeição. Uma confirmação aceita retorna 200; nova tentativa após COMPLETED retorna 400. Não há transição de retorno nem registro artificial de respostas ausentes.

`results` contém os mesmos campos de acompanhamento, mais:

```typescript
{
  ra_version: {id, version, architecture_name};
  checklist_version: {id, version, checklist_name};
  questions: [{
    id, statement, response_type, comment_mode, order_index,
    section: {id, name} | null,
    stakeholder_roles: [{id, name}], // [] significa questão comum
    expected, answered, pending,
    distribution: [{id, label, count, percentage}], // [] para TEXT
    responses: [{participant_id, answer: {
      id, response_option_id, text_value, comment
    } | null}]
  }];
}
```

A ordem das questões e opções segue `order_index, id`. Todos os participantes e seus papéis constam no contexto; cada `responses` inclui somente os participantes que receberam aquela questão. `answer: null` significa **Não respondida**, sem inserir nada no banco. Uma questão sem destinatários possui `responses: []`, `expected: 0` e `pending: 0`. A distribuição inclui todas as alternativas configuradas, inclusive as não escolhidas. Seu percentual usa exclusivamente `answered` daquela questão; é `null` quando não há respostas, sem divisão por zero. Textos e comentários permanecem campos independentes. Não são enviados descrições da RA, elementos privados ou dados de outras avaliações.

### Cálculo e consultas

`permissions.available_questions()` continua sendo a entrada de seleção da AVA-02 e aceita candidatos e relações pré-carregados para relatórios em lote. A atribuição reúne questões comuns e a união dos papéis, sem duplicação por múltiplos papéis. Testes comparam o caminho em lote com a seleção SQL existente.

Uma resposta só conta se houver um `Answer` persistido para o par participante/questão atribuída. Editar esse registro não aumenta a contagem. Pendências individuais são o conjunto atribuído menos os pares respondidos. O denominador geral é a soma das atribuições, nunca o número de questões da checklist. Participantes sem questões têm percentual `null`, nenhuma pendência e não aumentam o denominador. Se o denominador geral for zero, seu percentual também é `null`.

`reporting.py` carrega questões/seções/opções/papéis, participantes/contas/papéis e respostas em consultas em lote; não executa consultas por participante ou questão. Progress busca somente as chaves das respostas, sem textos/comentários. Resultados busca seus valores; as agregações e percentuais são calculados no backend. Há teste de estabilidade da quantidade de consultas ao acrescentar participantes. Os relatórios são calculados sob o lock da avaliação para não combinar status e contagens de instantes incompatíveis.

### Finalização e concorrência

`complete_evaluation()` usa `transaction.atomic` e `select_for_update(of=('self',))` na mesma linha de avaliação usada por `save_answer()`. Depois do lock, revalida autoria/status e recalcula as pendências. Não exige novos locks de versão nem inverte a ordem avaliação → RA → checklist da AVA-01.

- Se a resposta obtiver o lock primeiro, a finalização espera seu commit e inclui a resposta nos totais recalculados.
- Se a finalização obtiver primeiro, salvamentos concorrentes esperam e depois encontram COMPLETED, sendo rejeitados sem inserir/editar respostas.
- Duas finalizações são serializadas; somente uma efetua a transição.
- As proteções existentes continuam congelando versões em IN_PROGRESS e COMPLETED. Participantes, papéis e versões continuam imutáveis; não há reabertura.

Os testes concorrentes usam conexões PostgreSQL independentes e verificam efetivamente a espera por lock em `pg_stat_activity`, tanto para criação quanto para edição de resposta concorrente.

### Decisões de projeto provisórias

- **Encerramento incompleto:** permitido ao criador mediante confirmação explícita validada pelo backend. É uma decisão operacional provisória do MVP, não uma regra já validada pelos orientadores.
- **Privacidade:** acompanhamento completo e resultados consolidados ficam restritos ao criador. Participar não concede acesso às respostas de terceiros nem aos artefatos privados originais.
- **Atualização:** botão Atualizar dados e carregamento ao abrir a tela; não há polling ou notificações. A confirmação abre com um resumo atualizado, mas o servidor é a autoridade no instante de finalizar.
- **Zero atribuições:** progresso não aplicável, sem pendências; o criador pode finalizar com confirmação normal.

### Interface e diferenças do W07

O detalhe existente mantém a configuração em DRAFT. Para o criador, IN_PROGRESS/COMPLETED utilizam `EvaluationMonitoring`, dentro de AppLayout, com PageHeader, abas, StatCard e EditorPanel existentes. Acompanhamento exibe indicadores, progresso por participante e listas recolhíveis de questões pendentes. Finalizar abre confirmação e exige checkbox adicional com pendências. Após sucesso, a aba Resultados mostra questões, alternativas e barras, respostas individuais, comentários e ausências; Acompanhamento permanece consultável.

O W07 foi consultado no Figma (frame `13:137`). Mantêm-se a hierarquia, cartões, espaçamentos e painel contextual de 340 px. Adaptações funcionais: os quatro indicadores mostram participantes, respostas registradas, respostas esperadas e percentual geral; não introduzem status de participação. Diferentemente da prévia de resultados do wireframe em IN_PROGRESS, resultados ficam restritos a COMPLETED. São apresentados na aba própria com cartões por questão, permitindo mostrar todos os textos/comentários sem limitar o conteúdo ao painel lateral. A navegação usa o mesmo SVG local `nav-dot.svg` já existente. As colunas empilham em telas menores.

O participante vê a mensagem de encerramento no detalhe ou ao abrir a rota de respostas após COMPLETED. Se sua aba já estiver aberta, uma tentativa de salvar rejeitada consulta o status e remove o formulário quando a avaliação foi concluída. Não há perda retroativa das respostas persistidas nem habilitação de consulta consolidada para participantes.

### Validação manual

1. Crie uma avaliação em DRAFT, configure contas e papéis e inicie: o fluxo anterior permanece disponível.
2. Use questões comuns, questões por papéis e uma compartilhada por dois papéis. Compare os totais individuais; a compartilhada deve contar uma única vez por participante.
3. Responda como participante, edite uma resposta e use Atualizar dados como criador. Contadores devem refletir somente salvamentos; editar não deve aumentar `answered`.
4. Abra Questões pendentes de cada participante. Sem atribuições, confira Nenhuma questão atribuída/Não aplicável e ausência de pendências artificiais.
5. Abra Finalizar avaliação e cancele; o estado deve continuar IN_PROGRESS. Com pendências, confira totais, aviso de bloqueio e checkbox obrigatório. Pela API, tente finalizar sem confirmação: deve retornar 400.
6. Confirme. Confira COMPLETED, ausência de ações de resposta/configuração e abertura dos resultados. Verifique alternativas não escolhidas com zero, percentuais apenas entre válidas, textos, comentários separados e Não respondida.
7. Retorne ao acompanhamento e recarregue. As respostas e contagens devem permanecer iguais. Outra tentativa de finalizar deve ser rejeitada.
8. Como participante, tente progress/results e PUT após encerramento: devem ser bloqueados. Uma aba antiga de respostas também deve informar conclusão após a tentativa rejeitada. Usuários externos não veem a avaliação.
9. Confira desktop 1440 px, mobile 390 px, teclado, foco e cancelamento/fechamento do painel. Novas versões de RA/checklist continuam possíveis; as versões usadas permanecem congeladas.

Comandos de verificação: `python backend/manage.py makemigrations --check --dry-run`, `python backend/manage.py migrate`, `python backend/manage.py check`, `python backend/manage.py test`, `npm --prefix frontend run typecheck` e `npm --prefix frontend run build`.

### Verificações executadas em 14/11/2026

- `makemigrations --check --dry-run`: nenhuma alteração; `migrate`: nenhuma migração pendente; `check`: nenhum problema.
- Suíte completa PostgreSQL: **173 testes aprovados**, incluindo 25 novos de progresso, finalização, resultados, acesso e concorrência. Quatro novos testes observam bloqueios reais de transações independentes: última resposta antes da finalização, edição após finalização, criação após finalização e duas finalizações simultâneas.
- Um teste antigo da AVA-01 foi atualizado de “endpoint complete inexistente” para “finalização de DRAFT rejeitada”, pois o endpoint é o objetivo explícito desta etapa. A verificação de exclusão proibida permanece.
- `npm run typecheck`, `npm run build` e `git diff --check` aprovados.
- Chromium em 1440 e 390 px: configuração/início anteriores, totais individuais diferentes, progresso agregado 2/3, comentários obrigatórios em português, cancelamento de finalização, confirmação explícita de pendências, resultados/textos/comentários, alternativas zeradas, privacidade, bloqueio de aba antiga de participante e recarregamento, além de avaliação sem nenhuma atribuição. Sem exceções JavaScript ou overflow horizontal nos cenários verificados.
- A validação visual utilizou um banco PostgreSQL temporário separado; contas e artefatos de exemplo não foram inseridos no banco de desenvolvimento. Não há dependências adicionais de navegador no repositório.
