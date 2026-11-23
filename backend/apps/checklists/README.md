# Checklists — Editor e derivação

Esta app implementa checklists, versões, seções, stakeholders e questões configuráveis. As especificações acadêmicas em `docs/` não foram alteradas. A derivação pública foi acrescentada em CAT-02, conforme a seção abaixo. Avaliações e respostas pertencem à app específica; não há exclusão de recursos.

## Executar e validar

Na raiz, com `.env` configurado conforme o README principal:

```bash
docker compose up -d --wait db
source backend/.venv/bin/activate
python backend/manage.py migrate
python backend/manage.py check
python backend/manage.py makemigrations --check --dry-run
python backend/manage.py test
python backend/manage.py runserver 127.0.0.1:8000
```

Em outro terminal:

```bash
cd frontend
npm ci
npm run typecheck
npm run build
npm run dev
```

Acesse `http://127.0.0.1:5173/#/checklists`. O runner de testes descobre as apps de domínio tanto da raiz quanto de `backend/`; rótulos explícitos continuam disponíveis, por exemplo `python backend/manage.py test apps.checklists`.

## API

Todas as rotas exigem sessão autenticada. POST/PATCH exigem CSRF pelo mecanismo existente. A listagem inclui somente checklists do usuário; consultas públicas de conteúdo são feitas por ID; a descoberta usa a app catalog (CAT-01). Somente o proprietário pode modificar qualquer estrutura. A API retorna `can_edit` para o controle visual; a autorização é sempre verificada no servidor.

Prefixo: `/api/checklists/`.

| Rota relativa | Métodos | Operação |
| --- | --- | --- |
| `/` | GET, POST | Listar próprias / criar checklist e primeira versão |
| `/{id}/` | GET, PATCH | Consultar / alterar nome, origem e visibilidade |
| `/{id}/versions/` | GET, POST | Listar / criar versão vazia |
| `/{id}/versions/{version_id}/` | GET | Consultar versão |
| `/{id}/versions/{version_id}/sections/` | GET, POST | Listar / cadastrar seções |
| `/{id}/versions/{version_id}/sections/{item_id}/` | PATCH | Alterar seção |
| `/{id}/versions/{version_id}/sections/reorder/` | POST | Reordenar todas as seções da versão |
| `/{id}/versions/{version_id}/stakeholders/` | GET, POST | Listar / cadastrar papéis configuráveis |
| `/{id}/versions/{version_id}/stakeholders/{item_id}/` | PATCH | Alterar nome e descrição do papel |
| `/{id}/versions/{version_id}/questions/` | GET, POST | Listar / cadastrar questões completas |
| `/{id}/versions/{version_id}/questions/{item_id}/` | GET, PATCH | Consultar / alterar questão, opções e associações |
| `/{id}/versions/{version_id}/questions/reorder/` | POST | Reordenar todas as questões da versão |

Cadastro inicial atômico:

```json
{
  "name": "Instrumento de avaliação",
  "origin": "Fonte bibliográfica ou texto livre opcional",
  "visibility": "PRIVATE",
  "initial_version": {"version": "1.0"}
}
```

`owner_user` é definido pelo servidor. `derived_from_checklist_version` existe no modelo, permanece nulo no cadastro comum e não é atribuível pelo cadastro comum; o endpoint dedicado de CAT-02 o define a partir da versão pública validada. Campos desconhecidos, incluindo IDs de propriedade, versão e derivação, são rejeitados com 400.

Questão de seleção (rótulos livres; nenhuma escala predefinida):

```json
{
  "statement": "Os objetivos estão definidos?",
  "response_type": "SINGLE_CHOICE",
  "comment_mode": "OPTIONAL",
  "section_id": null,
  "stakeholder_ids": [],
  "options": [
    {"label": "Atende ao critério", "order_index": 0},
    {"label": "Necessita revisão", "order_index": 1}
  ]
}
```

`TEXT` deve ter `options: []` ou omitir opções na criação. A seção é opcional. Stakeholders ausentes ou vazios não geram registros artificiais de “Todos”: a ausência de associação significa questão comum a todos os futuros participantes. Vários papéis representam uma condição de qualquer um dos papéis, aplicada pelo módulo de avaliações.

## Atualizações transacionais

- PATCH é parcial para os campos da questão. Omitir `section_id` ou `stakeholder_ids` preserva os valores; `null` remove a seção e `[]` remove as associações.
- Quando `options` é informado, substitui **a lista inteira** de opções da própria questão. Cada item exige `label` e `order_index`; IDs não são aceitos. Os registros antigos são substituídos e seus IDs não são preservados. Essa substituição só é permitida em versões editáveis; as proteções históricas de AVA-01 bloqueiam versões utilizadas.
- Omitir `options` preserva a lista se a questão continuar `SINGLE_CHOICE`. Alterar para `TEXT` remove as opções na mesma transação; fornecer opções não vazias para `TEXT` resulta em 400. Alterar de `TEXT` para `SINGLE_CHOICE` exige uma lista não vazia válida.
- Falhas de validação ou persistência não deixam atualizações parciais em questão, opções ou associações.
- Comentários NONE, OPTIONAL e REQUIRED são independentes do tipo de resposta. REQUIRED configura uma exigência futura ao responder; não exige conteúdo de comentário no editor.
- Seção e stakeholders devem pertencer à mesma versão da questão. Cada caminho valida checklist, versão e recurso antes do acesso. IDs internos não permitem acessar checklists privadas.

## Ordenação

`order_index` é global à versão para seções e, separadamente, para questões. As posições são contíguas a partir de zero. A ordem das opções é local à questão.

- Na criação, omitir `order_index` acrescenta ao fim; informá-lo insere na posição e desloca os demais itens. PATCH com uma posição move o item, também deslocando os demais. Posições fora da lista são rejeitadas.
- Reordenação recebe `{"ids": [3, 1, 2]}` com uma permutação completa de todos os IDs daquela coleção e versão, sem duplicações. Nenhum ID de outra versão/checklist é aceito. Uma lista vazia só é válida para uma coleção vazia.
- Opções recebidas são ordenadas por `order_index` e renumeradas a partir de zero. Posições negativas e duplicadas são rejeitadas.
- As escritas estruturais bloqueiam a linha da versão com `select_for_update`, e mudanças de ordem são atômicas. Constraints adiáveis do PostgreSQL impedem posições repetidas sem impedir trocas intermediárias dentro da transação.
- Na interface, seções são exibidas na sua ordem; questões são agrupadas por seção e ordenadas pelo índice global dentro de cada grupo. As setas de questões trocam posições com a questão vizinha do mesmo grupo, preservando a posição das demais questões. Trocar de seção é feito no editor. Questões sem seção aparecem em um grupo separado. Opções possuem setas próprias.

## Decisões provisórias e dependências

**Novas versões começam vazias**, sem copiar seções, stakeholders ou questões. Essa é a decisão provisória autorizada para CHK-01; o Fluxo 02 ainda a registra como aberta e não houve validação presumida com orientadores.

**Atualização AVA-01:** versões usadas por avaliações IN_PROGRESS ou COMPLETED agora têm suas escritas estruturais bloqueadas em `services.writable_version`. O início da avaliação e as escritas sincronizam a mesma linha de versão com `select_for_update`; avaliações DRAFT não congelam o conteúdo. Não há campo LOCKED redundante. Metadados gerais e criação de novas versões continuam permitidos. Consulte a estratégia e os testes concorrentes no [README de AVA-01](../checklist_evaluations/README.md).

RF-CAT-02 e consulta pública somente leitura estão implementados. AVA-01 acrescentou a seleção de versões públicas para criar e iniciar avaliações, sem conceder edição ao usuário que as reutiliza. Respostas e resultados são implementados pela app de avaliações; CAT-01 acrescentou o catálogo e CAT-02 acrescenta a derivação descrita abaixo.

## Revisão visual e manual

A implementação reutiliza AppLayout, PageHeader, EditorPanel, EmptyState, Notice e os tokens da UI-01. W04 orienta cabeçalho, origem, versão, abas, agrupamento e formulário lateral. O painel mantém o comportamento modal acessível já adotado na UI-01; o Figma apresenta um painel acoplado. Foram acrescentados controles explícitos de ordenação e de opções. Configurações de metadados ficam em “Alterar dados”, sem uma aba adicional. Não há dados do exemplo FERA preenchidos automaticamente.

1. Entre, abra Checklists e crie um instrumento. Volte entre as etapas para confirmar que os valores são preservados.
2. Crie uma questão TEXT sem seção e sem stakeholders; confira a indicação de questão comum.
3. Cadastre duas seções e dois stakeholders. Edite seus nomes e descrições.
4. Adicione SINGLE_CHOICE com rótulos próprios, reordene opções, associe uma seção e múltiplos stakeholders.
5. Edite o tipo para TEXT; confirme a remoção das opções. Retorne para SINGLE_CHOICE fornecendo opções.
6. Reordene seções e questões com as setas. Recarregue para confirmar a persistência.
7. Crie nova versão e confirme que começa vazia. Volte à anterior e confira todo o conteúdo.
8. Tente repetir um identificador de versão: o painel deve mostrar o erro e manter o valor informado.
9. Torne a checklist pública; em outra conta, abra sua URL direta. Deve ser somente leitura e não aparecer em “Minhas Checklists” da outra conta.
10. Torne-a privada; a outra conta deve perder acesso, inclusive por IDs de recursos internos.
11. Confira navegação em desktop/mobile, abas com setas do teclado e Escape/retorno do foco nos painéis.

## CAT-02 — Derivação de checklist pública

RF-CAT-05, RN-CAT-04/05 e T36 são implementados com os modelos e a FK `derived_from_checklist_version` existentes. Não há nova app, tabela, campo ou migração. O serviço `services.derive_checklist()` copia somente o instrumento da versão selecionada; não copia avaliações, participantes, respostas, comentários de avaliação ou resultados.

### Contrato REST

`POST /api/checklists/derive/`, com sessão autenticada e CSRF:

```json
{
  "source_checklist_version_id": 5,
  "name": "Adaptação independente",
  "origin": "Fonte ou adaptação confirmada pelo usuário",
  "visibility": "PRIVATE",
  "initial_version": {"version": "1.0"}
}
```

O identificador da primeira versão independe da origem. `origin` é opcional, podendo ficar vazio; nome, visibilidade e identificador de versão seguem os limites e validadores normais. O serializer estrito rejeita campos desconhecidos, inclusive proprietário, estrutura, IDs de objetos a copiar e campos adicionais da versão inicial. Não se aceita um segundo ID de checklist: a FK da versão identifica inequivocamente sua checklist, evitando pares inconsistentes.

HTTP 201 retorna o detalhe normal da nova checklist, incluindo sua primeira versão, `can_edit: true`, `derived_from_checklist_version` e os metadados de origem descritos abaixo. O proprietário é sempre `request.user`. O cadastro comum e PATCH de metadados continuam rejeitando atribuição de propriedade/proveniência pelo cliente. HTTP 400 indica payload/estrutura inválidos; 403 indica ausência de sessão ou CSRF; 404 indica versão inexistente ou origem não pública, inclusive quando PRIVATE pertence ao próprio solicitante. Uma origem que muda para PRIVATE antes da confirmação é rejeitada na revalidação transacional.

O detalhe GET `/{id}/` acrescenta somente o campo de leitura `derivation_source`:

- `null`: checklist comum, sem derivação.
- `{available: true, checklist_id, name, version_id, version}`: o usuário pode consultar a origem pelas permissões normais de checklist.
- `{available: false}`: existe a referência, mas a origem não está acessível. Não retorna seu nome, identificador de versão textual ou ID da checklist e não gera link na interface.

A FK numérica `derived_from_checklist_version` já existente permanece no contrato para rastreabilidade. Conhecer esse ID não permite consultar o conteúdo privado. Uma origem privada continua consultável por seu proprietário, inclusive na indicação de proveniência de uma derivada pública; outros leitores não recebem seus metadados. O texto livre `origin`, confirmado pelo autor da derivada, é um dado independente e não é apagado nem sincronizado conforme a visibilidade da fonte.

### Cópia e integridade

A operação aloca nova Checklist e ChecklistVersion e preserva o identificador informado para a primeira versão. Mapas internos ligam cada seção/papel original à nova instância. Para cada questão original, cria uma nova questão, remapeia sua seção e cria opções e associações com os novos papéis. Os mapas existem apenas durante a operação.

São copiados os nomes, descrições de papéis, enunciados, tipos TEXT/SINGLE_CHOICE, modos NONE/OPTIONAL/REQUIRED e índices de ordem, sem escala fixa. Questões sem seção permanecem sem seção; sem papéis permanecem comuns; múltiplos papéis preservam todas as associações. IDs são novos para todos os registros estruturais. Seções vazias e papéis sem questões também são copiados. Apenas a versão selecionada é lida, nunca outras versões.

Antes da criação, valida-se que seções e papéis referenciados pertencem à origem e que opções/tipos/comentários são compatíveis. Estruturas inconsistentes, inclusive referências cruzadas gravadas fora dos serviços, são rejeitadas sem copiar dados de outra versão. A cópia conserva exatamente os índices de origem, inclusive eventuais lacunas; não reordena nem renumera o instrumento.

A derivada obedece às regras comuns de propriedade e proteção histórica. Não concede edição sobre a original nem concede ao autor original direitos de edição sobre a derivada. A primeira versão derivada é editável enquanto não for utilizada em avaliação iniciada/concluída. A ação normal + Nova versão continua criando uma versão vazia; a cópia ocorre exclusivamente na derivação explícita.

### Atomicidade e concorrência

`transaction.atomic` abrange validação, leitura e todos os inserts. Qualquer falha provoca rollback da checklist, primeira versão e registros estruturais; não há cópias parciais ou órfãs.

A aquisição dos locks é **versão de origem → checklist de origem**, usando `select_for_update(of=('self',))`:

1. O lock da versão sincroniza com `writable_version()`, usado por todas as escritas estruturais de checklist. A leitura de seções, questões, opções e papéis ocorre somente depois desse lock.
2. O lock da checklist sincroniza com `update_checklist()`. Após obtê-lo, a visibilidade PUBLIC é conferida novamente, antes de copiar.
3. Se a edição estrutural obtiver primeiro, a derivação espera e copia o conteúdo confirmado completo. Se a derivação obtiver primeiro, copia o conteúdo anterior completo; a edição espera e permanece permitida após o commit se a versão não estiver congelada.
4. Se a mudança para PRIVATE obtiver o lock primeiro, a derivação espera e é rejeitada. Se a derivação obtiver primeiro, a mudança espera; a cópia já criada continua independente.

Os serviços atuais de metadados e criação de versão bloqueiam somente a checklist; não tentam bloquear uma versão já existente depois dela. A derivação não bloqueia avaliações nem RAs, não altera a ordem avaliação → RA → checklist-version da AVA-01 e não espera por um lock anterior dessa ordem. O início da avaliação disputa somente o mesmo lock de versão, sem ciclo com o lock de metadados da derivação. Os registros de destino são novos e ainda não estão visíveis para outras transações.

Não se usa `writable_version()` para ler a fonte: isso impediria indevidamente derivar versões de terceiros ou congeladas. O congelamento continua derivado exclusivamente de avaliações IN_PROGRESS/COMPLETED. Não há campo ou estado novo de congelamento. A garantia abrange operações pelos serviços do sistema, não edição SQL administrativa que ignore esses locks.

### Interface e decisões de implementação

O detalhe existente de checklist PUBLIC oferece Criar derivação para a versão selecionada, inclusive para seu proprietário e para versões congeladas. PRIVATE não oferece a ação. O formulário reutiliza EditorPanel e MetadataFields, sem reorganizar o layout ou acrescentar rotas.

Sugestões editáveis: nome com sufixo “— Adaptação” (limitado a 255 caracteres), visibilidade PRIVATE, origem textual atual e versão inicial “1.0”. O painel identifica a fonte/versão e explica o que será copiado. Cancelar não grava dados; erros mantêm os campos; ref síncrona e botão desabilitado impedem submissão duplicada. Após 201, navega ao novo detalhe, seleciona sua primeira versão, mostra confirmação e permite edição normal. A confirmação de criação é transitória no estado React, sem novos parâmetros de URL ou armazenamento persistido.

A indicação Derivada de usa o contexto de leitura autorizado pelo backend. Se a origem se tornar inacessível, mostra apenas “Checklist derivada · A origem não está disponível para consulta.” sem link. As listas pessoais e o catálogo continuam usando as regras normais de proprietário e visibilidade da nova checklist.

Decisões não especificadas em detalhe nos documentos:

- Uma versão pública vazia também pode ser derivada; não há exigência de possuir questões para copiar. Seções/papéis eventualmente existentes são preservados.
- Uma estrutura inconsistente é rejeitada integralmente, sem tentativa de corrigir ou descartar partes na cópia.
- A proveniência do detalhe é contexto autorizado em cada consulta, sem snapshot adicional de nome da origem.

**Limitação de rastreabilidade:** a cópia representa o conteúdo no instante da derivação. A FK identifica a versão de origem, mas não congela essa versão apenas por existir uma derivação. Se a fonte ainda for editável, poderá mudar depois; essas mudanças não se propagam. Não há sincronização automática nem snapshot redundante da fonte. O nome mostrado na indicação é o nome atual acessível, não um nome histórico persistido.

### Roteiro manual com duas contas

1. Como A, publique uma checklist com duas versões distintas, seções, questões com/sem seção, TEXT/SINGLE_CHOICE, comentários e múltiplos papéis.
2. Como B, encontre-a no catálogo, escolha a versão e abra Criar derivação. Confira fonte, padrões sugeridos e aviso de independência. Cancele e confirme que nada aparece em Minhas Checklists.
3. Reabra, altere nome/origem/visibilidade e identificador inicial. Confirme: confira mensagem, primeira versão selecionada, proveniência e estrutura copiada. A derivada deve aparecer somente na lista de B (ou de A também, se for a mesma conta).
4. Edite questões, alternativas, seção e papéis da derivada. Como A, confira que a original não mudou. Crie nova versão na derivada e confirme que começa vazia.
5. Teste uma derivada PUBLIC no catálogo. O autor original pode consultá-la, mas não editá-la; B também não pode editar a original.
6. Abra o painel como B e, antes de confirmar, torne a fonte PRIVATE como A. A criação deve ser rejeitada, mantendo o formulário sem persistência parcial.
7. Reabra uma derivada já criada depois da mudança: continua independente/editável; a indicação da origem deve ficar indisponível para B. Não deve expor nomes privados atualizados nem links acessíveis indevidamente.
8. Repita a derivação de uma versão pública preservada por uma avaliação IN_PROGRESS/COMPLETED. Compare avaliações/respostas originais e confirme que a nova versão não está congelada.
9. Confira desktop/mobile, teclado, Escape/cancelamento e retorno do foco ao botão de origem.

### Verificações executadas — CAT-02

- `manage.py check`: nenhum problema; `makemigrations --check --dry-run`: nenhuma alteração; `migrate`: nenhuma migração pendente.
- Suíte PostgreSQL completa: **218 testes aprovados**, incluindo os 192 anteriores e 26 novos de derivação. Nenhum teste anterior foi alterado.
- Cinco testes concorrentes com conexões independentes e espera real observada em `pg_stat_activity`: edição antes/depois da cópia, visibilidade antes/depois da cópia e início de avaliação disputando a mesma versão. Rollback também foi exercitado com falhas nas etapas de seções, stakeholders, questões, opções e associações.
- `npm run typecheck`, `npm run build` e `git diff --check`: aprovados.
- Chromium em 1440 e 390 px com duas contas e banco temporário: catálogo/versão/painel, sugestões, cancelamento sem persistência, validação mantendo campos, guarda contra submissão duplicada, criação com confirmação e primeira versão selecionada, edição de questão/opções/papel sem modificar a fonte, nova versão vazia, propriedade, rejeição após tornar a fonte PRIVATE e indicação de proveniência indisponível. Sem erros JavaScript ou overflow horizontal nos cenários verificados.
- Scripts de navegador e dados de exemplo ficaram fora do banco de desenvolvimento e do repositório. Não foram adicionadas dependências. Nenhum documento acadêmico, modelo ou migração foi alterado; não houve commit ou push.
