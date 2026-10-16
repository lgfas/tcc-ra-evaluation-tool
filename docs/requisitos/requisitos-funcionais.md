# Requisitos Funcionais — v0.1

## Arquiteturas de Referência

### RF-RA-01 — Cadastrar Arquitetura de Referência
O sistema deve permitir cadastrar uma Arquitetura de Referência.

### RF-RA-02 — Versionar Arquitetura de Referência
O sistema deve permitir manter diferentes versões de uma Arquitetura de Referência.

### RF-RA-03 — Cadastrar elementos arquiteturais da RA
O sistema deve permitir cadastrar elementos arquiteturais pertencentes a uma versão da RA.

### RF-RA-04 — Classificar elementos arquiteturais da RA
O sistema deve permitir associar um tipo a cada elemento arquitetural cadastrado.

### RF-RA-05 — Descrever elementos arquiteturais
O sistema deve permitir registrar a descrição de um elemento arquitetural utilizando conteúdo textual formatado.

### RF-RA-06 — Definir tipos customizados de elementos
O sistema deve permitir utilizar tipos de elementos arquiteturais além dos tipos previamente disponibilizados pela ferramenta.

### RF-RA-07 — Visualizar avaliações da Arquitetura de Referência
O sistema deve permitir visualizar as avaliações por checklist e as avaliações de conformidade associadas às versões de uma Arquitetura de Referência.

---

## Checklists e critérios

### RF-CHK-01 — Cadastrar checklist
O sistema deve permitir cadastrar checklists de avaliação.

### RF-CHK-02 — Versionar checklist
O sistema deve permitir manter versões distintas de um mesmo checklist.

### RF-CHK-03 — Organizar checklist em seções
O sistema deve permitir organizar as questões de uma versão de checklist em seções ou grupos.

### RF-CHK-04 — Cadastrar questões
O sistema deve permitir cadastrar questões pertencentes a uma versão de checklist.

### RF-CHK-05 — Configurar tipo de resposta
O sistema deve permitir definir o tipo de resposta esperado para uma questão.

### RF-CHK-06 — Configurar opções de resposta
O sistema deve permitir definir as opções disponíveis para questões que utilizem respostas por seleção.

### RF-CHK-07 — Configurar comentários
O sistema deve permitir definir se uma questão aceita ou exige comentários adicionais.

### RF-CHK-08 — Associar questões a stakeholders
O sistema deve permitir associar questões aos papéis/stakeholders responsáveis por respondê-las.

### RF-CHK-09 — Registrar origem da checklist
O sistema deve permitir registrar informações sobre a origem ou fonte de uma checklist.

---

## Avaliações

### RF-AVA-01 — Criar avaliação
O sistema deve permitir criar uma avaliação de uma versão de Arquitetura de Referência.

### RF-AVA-02 — Selecionar checklist da avaliação
O sistema deve permitir associar uma versão de checklist à avaliação.

### RF-AVA-03 — Adicionar participantes
O sistema deve permitir adicionar usuários como participantes de uma avaliação.

### RF-AVA-04 — Atribuir papel ao participante
O sistema deve permitir associar um ou mais stakeholders/papéis a cada participante da avaliação.

### RF-AVA-05 — Responder questão de avaliação
O sistema deve permitir ao avaliador responder às questões atribuídas ao seu papel.

### RF-AVA-06 — Comentar resposta
O sistema deve permitir ao avaliador complementar sua resposta com comentários quando a questão permitir.

### RF-AVA-07 — Visualizar resultados da avaliação
O sistema deve permitir visualizar de forma consolidada as respostas fornecidas pelos avaliadores.

---

## Catálogo e compartilhamento

### RF-CAT-01 — Definir visibilidade da Arquitetura de Referência
O sistema deve permitir definir se uma Arquitetura de Referência cadastrada é privada ou pública.

### RF-CAT-02 — Definir visibilidade da checklist
O sistema deve permitir definir se uma checklist cadastrada é privada ou pública.

### RF-CAT-03 — Reutilizar Arquitetura de Referência
O sistema deve permitir utilizar em uma avaliação uma versão pública de uma Arquitetura de Referência cadastrada por outro usuário.

### RF-CAT-04 — Reutilizar checklist
O sistema deve permitir utilizar em uma avaliação uma versão pública de uma checklist cadastrada por outro usuário.

### RF-CAT-05 — Criar derivação de checklist
O sistema deve permitir criar uma nova checklist a partir de uma versão existente, preservando a referência à checklist de origem.

---

## Instanciações

### RF-INS-01 — Cadastrar arquitetura concreta
O sistema deve permitir cadastrar uma arquitetura concreta derivada de uma Arquitetura de Referência.

### RF-INS-02 — Versionar arquitetura concreta
O sistema deve permitir manter diferentes versões de uma arquitetura concreta.

### RF-INS-03 — Associar versão concreta à versão da RA
O sistema deve permitir associar cada versão de uma arquitetura concreta à versão da Arquitetura de Referência utilizada como sua base.

### RF-INS-04 — Cadastrar elementos da arquitetura concreta
O sistema deve permitir cadastrar elementos arquiteturais pertencentes a uma versão da arquitetura concreta.

### RF-INS-05 — Mapear elementos da arquitetura concreta para elementos da RA
O sistema deve permitir relacionar elementos de uma versão da arquitetura concreta aos elementos da versão da Arquitetura de Referência correspondente.

### RF-INS-06 — Visualizar mapeamentos
O sistema deve permitir visualizar os mapeamentos existentes entre os elementos da arquitetura concreta e os elementos da Arquitetura de Referência.

---

## Conformidade

### RF-CONF-01 — Cadastrar critério de conformidade
O sistema deve permitir cadastrar critérios de conformidade associados a uma versão de Arquitetura de Referência.

### RF-CONF-02 — Associar critério de conformidade a elementos da RA
O sistema deve permitir associar um critério de conformidade a um ou mais elementos arquiteturais da versão da RA.

### RF-CONF-03 — Criar avaliação de conformidade
O sistema deve permitir criar uma avaliação de conformidade entre uma versão de arquitetura concreta e a versão da Arquitetura de Referência utilizada como sua base.

### RF-CONF-04 — Registrar resultado de conformidade
O sistema deve permitir registrar manualmente o resultado da verificação de cada critério de conformidade.

### RF-CONF-05 — Registrar evidências de conformidade
O sistema deve permitir registrar evidências que fundamentem o resultado de uma verificação de conformidade.

### RF-CONF-06 — Registrar violações
O sistema deve permitir registrar violações identificadas durante a avaliação de conformidade, associando-as ao critério de conformidade correspondente.

### RF-CONF-07 — Visualizar resultados de conformidade
O sistema deve permitir visualizar de forma consolidada os resultados e as violações identificadas em uma avaliação de conformidade.