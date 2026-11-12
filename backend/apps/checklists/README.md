# CHK-01 — Editor de instrumentos de avaliação

Esta app implementa checklists, versões, seções, stakeholders e questões configuráveis. As especificações acadêmicas em `docs/` não foram alteradas. Não há avaliações, respostas de participantes, exclusão de recursos ou derivação nesta entrega.

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

Todas as rotas exigem sessão autenticada. POST/PATCH exigem CSRF pelo mecanismo existente. A listagem inclui somente checklists do usuário; consultas públicas são feitas por ID, sem catálogo. Somente o proprietário pode modificar qualquer estrutura. A API retorna `can_edit` para o controle visual; a autorização é sempre verificada no servidor.

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

`owner_user` é definido pelo servidor. `derived_from_checklist_version` existe no modelo, permanece nulo no cadastro comum e não é atribuível pela API. Campos desconhecidos, incluindo IDs de propriedade, versão e derivação, são rejeitados com 400.

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

`TEXT` deve ter `options: []` ou omitir opções na criação. A seção é opcional. Stakeholders ausentes ou vazios não geram registros artificiais de “Todos”: a ausência de associação significa questão comum a todos os futuros participantes. Vários papéis representam uma condição de qualquer um dos papéis, a ser aplicada quando existirem avaliações.

## Atualizações transacionais

- PATCH é parcial para os campos da questão. Omitir `section_id` ou `stakeholder_ids` preserva os valores; `null` remove a seção e `[]` remove as associações.
- Quando `options` é informado, substitui **a lista inteira** de opções da própria questão. Cada item exige `label` e `order_index`; IDs não são aceitos. Os registros antigos são substituídos e seus IDs não são preservados. Isso é apropriado para esta etapa sem respostas de participantes.
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

RF-CAT-02 e consulta pública somente leitura estão implementados. AVA-01 acrescentou a seleção de versões públicas para criar e iniciar avaliações, sem conceder edição ao usuário que as reutiliza. Respostas, derivação e catálogo continuam fora de escopo.

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
