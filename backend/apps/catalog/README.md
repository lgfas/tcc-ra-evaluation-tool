# CAT-01 — Catálogo público

Consulta autenticada de RAs e checklists públicas, usando os modelos existentes. Implementa a descoberta de artefatos de RF-CAT-01 a RF-CAT-04 e T33–T35; não implementa derivação (CAT-02/T36/RF-CAT-05).

## API

`GET /api/catalog/?type=ra&q=sistemas`

`GET /api/catalog/?type=checklist&q=arquitetura`

- `type`: obrigatório; valores `ra` e `checklist`, em minúsculas.
- `q`: opcional, até 255 caracteres; remove espaços nas extremidades. Vazio ou omitido lista todos os públicos daquele tipo.
- Busca parcial somente no nome, com `icontains`, sem distinção de capitalização. `%` e `_` são tratados como texto, não como curingas fornecidos pelo cliente. Não há busca sem acentos, ranking, paginação ou filtros avançados.
- Parâmetros desconhecidos, repetidos, tipo inválido/ausente ou busca acima do limite retornam HTTP 400 com mensagem de validação.
- HTTP 200 retorna uma lista, inclusive `[]` quando não houver resultados. HTTP 403 para usuários sem sessão. Não aceita operações de escrita.

RA: `[{id, name, visibility: "PUBLIC", version_count}]`.

Checklist: `[{id, name, origin, visibility: "PUBLIC", version_count}]`.

A ordenação é `Lower(name), name, id`. A listagem faz uma única consulta de metadados, com contagem de versões via `Count`; não carrega conteúdo das versões, membros, proprietários, participantes nem respostas. Não há modelos, tabelas ou migrações de catálogo. As consultas aplicam `visibility='PUBLIC'` em cada requisição, incluindo artefatos públicos próprios e alheios. RAs privadas compartilhadas e artefatos privados próprios continuam fora do catálogo.

## Detalhes e reutilização

Os detalhes e a estrutura utilizam exclusivamente as APIs existentes:

- `/api/reference-architectures/{id}/`, suas versões e elementos.
- `/api/checklists/{id}/`, suas versões, seções, stakeholders e questões com opções.
- `/api/checklist-evaluations/choices/` e POST `/api/checklist-evaluations/` para seleção e criação de avaliação.

As permissões existentes permanecem intactas: público autoriza consulta/reutilização, mas não concede propriedade, membership ou edição. Os endpoints pessoais continuam retornando somente as RAs do usuário/membership e as checklists próprias. Alterar PUBLIC para PRIVATE remove o item na consulta seguinte e bloqueia detalhes para terceiros; o proprietário e colaboradores autorizados mantêm seus acessos. A criação da avaliação revalida acesso, inclusive quando a página ou URL foi aberta enquanto o artefato ainda era público.

## Interface

`#/catalog` reutiliza AppLayout, PageHeader, EmptyState, Notice, navegação e cartões existentes. Há alternância entre RAs/checklists, busca por formulário (botão Buscar ou Enter), contagem de resultados, carregamento, erro com nova tentativa e estado vazio com ação de limpar busca. Respostas de consultas antigas são ignoradas quando o usuário altera tipo/busca ou sai da página.

Ver detalhes abre as telas existentes, sem duplicação. Artefatos públicos têm um link de retorno ao catálogo. Controles de edição continuam condicionados a `role`/`can_edit`; proprietários e colaboradores autorizados preservam suas ações legítimas.

A ação da RA preserva `#/evaluations/new?ra_version_id=...`. A checklist acrescenta `#/evaluations/new?checklist_version_id=...`, usando a versão atualmente selecionada. Ambos os parâmetros podem ser utilizados juntos. O seletor já existente resolve apenas versões retornadas pela API de artefatos acessíveis; IDs privados/inexistentes não são preenchidos e o backend continua sendo a autoridade. Não há cópia de artefatos nem persistência da avaliação antes da confirmação do formulário.

Não existe frame específico de catálogo no Figma. A organização segue T33–T35 e os padrões visuais atuais, sem alegação de reprodução de wireframe inexistente. A consulta usa busca explícita por formulário; a busca não é persistida na URL e volta ao estado inicial ao reabrir a página. Atualizar a consulta também reaplica a visibilidade atual dos artefatos.

## Validação

```bash
python backend/manage.py check
python backend/manage.py makemigrations --check --dry-run
python backend/manage.py test
npm --prefix frontend run typecheck
npm --prefix frontend run build
```

Os testes do catálogo cobrem autenticação, separação PUBLIC/PRIVATE, artefatos próprios, busca parcial/capitalização/espaços/caracteres especiais, parâmetros inválidos, ordem/contagem/consulta em lote, mudança de visibilidade, acesso direto e indireto, manutenção das listagens pessoais, reutilização sem cópia/edição e ausência de dados privados de avaliações.

Roteiro com duas contas:

1. Como conta A, crie uma RA pública e uma privada; faça o mesmo com checklists. Cadastre duas versões com conteúdos diferentes. Na RA pública, inclua elementos com tipos; na checklist pública, seções, papéis e questões com opções/comentários configuráveis.
2. Como conta B, abra Catálogo. Confira somente os públicos, alterne os tipos e pesquise por parte do nome em outra capitalização. Teste busca sem resultados e Limpar busca.
3. Abra a RA pública, troque a versão e consulte descrição/elementos. Não devem aparecer ações de edição. Use Criar avaliação por checklist: a versão deve estar preenchida. Escolha uma checklist acessível e confirme o rascunho.
4. Retorne ao catálogo, abra a checklist pública, alterne versões e consulte Questões/Seções/Stakeholders, inclusive opções e modos de comentário. Use Utilizar em avaliação; confira o preenchimento e escolha uma RA acessível. Criar o rascunho não deve alterar os originais.
5. Como A, torne os artefatos privados. Como B, consulte novamente o catálogo, recarregue os detalhes e tente reutilizar a versão antiga: o conteúdo deve ser inacessível. Como A, confira que o acesso privado próprio permanece.
6. Confira Minhas Arquiteturas/Minhas Checklists: os artefatos públicos da conta A não devem surgir nas listas da conta B. Pela API, tentativas de editar originais públicos de A devem ser rejeitadas.
7. Repita em desktop/mobile e navegue por teclado, incluindo busca por Enter, alternância de tipos, detalhes e retorno ao catálogo.

Derivação, convites, escala numérica, uploads e busca avançada permanecem fora desta entrega.

## Verificações executadas em 23/11/2026

- `manage.py check`: nenhum problema; `makemigrations --check --dry-run`: nenhuma alteração.
- Suíte completa no PostgreSQL: **192 testes aprovados** — 173 anteriores e 19 novos do catálogo. Nenhum teste anterior foi alterado.
- TypeScript, build Vite e `git diff --check`: aprovados.
- Chromium em 1440 e 390 px, com duas contas em banco temporário: navegação, públicos próprios/alheios, busca parcial por Enter/capitalização, vazio/limpar, erro com nova tentativa, seleção e leitura de versões/conteúdos, atalhos RA/checklist e ambos juntos, criação real de dois rascunhos, ausência de edição, mudança PUBLIC → PRIVATE, URLs antigas rejeitadas e bloqueio anônimo. Sem erros JavaScript ou overflow horizontal nos cenários verificados.
- Os scripts e a instalação do Playwright ficaram em `/tmp`; nenhuma dependência foi acrescentada ao projeto. O Python temporário referenciado pelo ambiente virtual foi restaurado para executar as validações.
- Nenhum modelo, migração, contrato REST anterior ou arquivo acadêmico em `docs/` foi modificado. Não houve commit ou push.
