# AVA-01 — Criação, configuração e início de avaliações por checklist

Implementa RF-AVA-01 a RF-AVA-04, seleção de versões próprias/autorizadas ou públicas (RF-CAT-03/04), participantes e papéis por versão, e a transição DRAFT → IN_PROGRESS. Não há respostas, progresso, finalização, resultados, convites ou notificações. Não existe título persistido adicional nem snapshots dos artefatos.

## Modelos

- `ChecklistEvaluation`: RA versionada, checklist versionada, criador, status e data de criação. FKs obrigatórias com PROTECT; status válido por constraint. DRAFT é o padrão, COMPLETED existe somente para o ciclo futuro.
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

Não há DELETE de avaliações, PUT de configuração, nem endpoint de finalização. Campos desconhecidos são rejeitados com 400, inclusive `status`, `created_by_user`, título e IDs redundantes dos artefatos.

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

O congelamento de participantes e papéis após o início é uma **decisão conservadora de implementação** para manter a configuração estável. Não é possível reabrir DRAFT, reiniciar ou trocar versões após IN_PROGRESS. COMPLETED está no modelo, mas não tem transição exposta nesta entrega.

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

A proteção abrange as operações de escrita do sistema por seus serviços; não pretende impedir administração SQL direta. AVA-02/03 deverão manter a mesma ordem de bloqueios e não introduzir rotas alternativas de escrita retroativa. Metadados gerais (nome, visibilidade e origem) continuam distintos do conteúdo versionado. Novas versões continuam permitidas e editáveis. Opções antigas não são substituídas após o congelamento.

## Interface e W05

Rotas: `#/evaluations`, `#/evaluations/new` e `#/evaluations/{id}`. O atalho da RA usa `#/evaluations/new?ra_version_id=...` para preencher a versão selecionada, inclusive em uma RA pública de terceiro.

Reutiliza AppLayout, PageHeader, EditorPanel, EmptyState, Notice, estilos e o SVG original da navegação. W05 orienta as etapas, cartão de artefatos, participantes com identidade/papéis e resumo lateral de 320 px. Em telas pequenas, as colunas são empilhadas. A inclusão/edição, revisão de versões, remoção e confirmação de início usam os painéis acessíveis existentes.

Diferenças funcionais do protótipo: cada painel salva sua própria operação, portanto “Rascunho salvo” substitui um botão de salvar redundante; as linhas têm ações explícitas de editar/remover; o início pede confirmação do congelamento. O título é derivado da RA e não persistido. Não há dados de exemplo, progresso, resultados, formulários de resposta ou botão de finalização.

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

Respostas, comentários de respostas, progresso, finalização e resultados ficam para AVA-02/03. Nenhum desses recursos foi antecipado.
