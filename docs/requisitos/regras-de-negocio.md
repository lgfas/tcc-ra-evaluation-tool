# Regras de Negócio — v0.1

> Regras iniciais derivadas dos requisitos funcionais e das decisões tomadas durante a especificação da ferramenta.
> Estas regras ainda devem ser revisadas e validadas com os orientadores.

## Arquiteturas de Referência

### RN-RA-01 — Versionamento da Arquitetura de Referência
Alterações em uma versão de Arquitetura de Referência já utilizada em uma avaliação não devem modificar o conteúdo considerado naquela avaliação.

Quando for necessário alterar a RA, uma nova versão deve ser criada.

### RN-RA-02 — Elementos pertencem a uma versão da RA
Todo elemento arquitetural cadastrado deve estar associado a uma versão específica de uma Arquitetura de Referência.

### RN-RA-03 — Tipos de elementos podem ser predefinidos ou customizados
Um elemento arquitetural pode utilizar um tipo disponibilizado pela ferramenta ou um tipo customizado definido pelo responsável pela RA.

---

## Checklists

### RN-CHK-01 — Checklist é versionada
As questões, seções, tipos de resposta, opções de resposta, configurações de comentários e associações com stakeholders devem pertencer a uma versão específica da checklist.

### RN-CHK-02 — Preservação das versões utilizadas
Alterações em uma checklist não devem modificar retroativamente avaliações realizadas ou iniciadas com versões anteriores.

Quando for necessário alterar uma versão já utilizada, uma nova versão da checklist deve ser criada.

### RN-CHK-03 — Questão pertence a uma única versão de checklist
Toda questão deve estar associada a exatamente uma versão de checklist.

### RN-CHK-04 — Seções são opcionais
Uma checklist pode organizar suas questões em seções ou grupos, mas essa organização não é obrigatória.

### RN-CHK-05 — Opções de resposta dependem do tipo de resposta
Questões configuradas para respostas por seleção devem possuir opções de resposta previamente definidas.

Questões de resposta textual não necessitam de opções de resposta.

### RN-CHK-06 — Comentários são configuráveis
Cada questão deve definir se comentários adicionais são permitidos, obrigatórios ou não utilizados.

### RN-CHK-07 — Questões podem ser associadas a múltiplos stakeholders
Uma questão pode ser destinada a um ou mais papéis/stakeholders.

### RN-CHK-08 — Origem da checklist deve ser preservada
Quando uma checklist for baseada ou adaptada de outra fonte, o sistema deve manter informações que permitam identificar sua origem.

---

## Avaliações

### RN-AVA-01 — Composição da avaliação
Cada avaliação deve estar associada a exatamente:

- uma versão de Arquitetura de Referência; e
- uma versão de checklist.

### RN-AVA-02 — Versões utilizadas pela avaliação são fixas
Após o início de uma avaliação, as versões da Arquitetura de Referência e da checklist associadas a ela não devem ser substituídas.

Caso seja necessário avaliar outra versão da RA ou da checklist, uma nova avaliação deve ser criada.

### RN-AVA-03 — Participante possui papel na avaliação
Todo participante responsável por responder questões deve possuir pelo menos um papel/stakeholder associado no contexto daquela avaliação.

### RN-AVA-04 — Questões são disponibilizadas de acordo com o papel
Um avaliador deve ter acesso às questões associadas aos papéis/stakeholders que exerce naquela avaliação.

### RN-AVA-05 — Questões sem stakeholder são comuns a todos os avaliadores
Quando uma questão não possuir nenhum papel/stakeholder associado, ela deve ser disponibilizada a todos os participantes responsáveis por responder à avaliação.

### RN-AVA-06 — Resposta pertence ao contexto da avaliação
Toda resposta deve estar associada a:

- uma avaliação;
- uma questão da versão de checklist utilizada;
- um participante da avaliação.

### RN-AVA-07 — Uma resposta por avaliador e questão
Um participante deve possuir, no máximo, uma resposta ativa para cada questão em uma mesma avaliação.

### RN-AVA-08 — Comentários respeitam a configuração da questão
O preenchimento de comentários deve respeitar a configuração definida para a questão correspondente.

---

## Catálogo e compartilhamento

### RN-CAT-01 — Artefatos privados possuem acesso restrito
Arquiteturas de Referência e checklists definidas como privadas não devem estar disponíveis para reutilização por outros usuários.

### RN-CAT-02 — Artefatos públicos podem ser reutilizados
Versões públicas de Arquiteturas de Referência e checklists podem ser utilizadas por outros usuários em suas próprias avaliações.

### RN-CAT-03 — Reutilização não concede permissão de edição
Utilizar uma RA ou checklist pública em uma avaliação não concede ao usuário permissão para alterar o artefato original.

### RN-CAT-04 — Derivação de checklist cria um novo artefato
Ao derivar uma checklist existente, deve ser criada uma nova checklist independente da original.

### RN-CAT-05 — Derivação preserva rastreabilidade
Uma checklist derivada deve manter referência à checklist e à versão que lhe deram origem.