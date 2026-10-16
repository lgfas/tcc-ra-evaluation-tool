# Decisões de Projeto — v0.1

Este documento registra decisões tomadas durante a especificação da ferramenta, especialmente aquelas relacionadas a escopo e modelagem.

---

## D01 — Workspaces ficam fora do escopo inicial

### Decisão
A ferramenta poderá futuramente organizar usuários, Arquiteturas de Referência, checklists e avaliações em espaços de trabalho compartilhados, permitindo representar empresas, universidades, laboratórios ou equipes.

A funcionalidade não faz parte do escopo inicial.

### Motivação
A inclusão de Workspaces exigiria regras adicionais de membros, permissões, propriedade e compartilhamento, aumentando a complexidade da primeira versão.

---

## D02 — Uma avaliação utiliza uma versão de RA e uma versão de checklist

### Decisão
Cada avaliação será realizada utilizando exatamente:

- uma versão de Arquitetura de Referência; e
- uma versão de checklist.

### Motivação
Essa decisão simplifica o processo de avaliação, a rastreabilidade dos resultados e a modelagem dos dados.

Caso seja necessário avaliar a mesma RA utilizando outro instrumento, uma nova avaliação deverá ser criada.

---

## D03 — Checklists não terão escala de resposta fixa

### Decisão
A ferramenta não ficará limitada à escala Sim / Não / Parcialmente utilizada em aplicações do FERA.

Cada questão poderá definir seu tipo e, quando aplicável, suas próprias opções de resposta.

### Motivação
A ferramenta pretende permitir o uso de diferentes checklists de avaliação, e não apenas do FERA.

---

## D04 — Comentários são independentes do tipo de resposta

### Decisão
Comentários serão configurados separadamente do tipo principal de resposta de uma questão.

Uma questão poderá permitir, exigir ou não utilizar comentários adicionais.

### Motivação
O comentário funciona como justificativa ou complemento da resposta e não necessariamente como a resposta principal.

---

## D05 — Questões sem stakeholder são respondidas por todos

### Decisão
Quando uma questão não possuir nenhum stakeholder/papel associado, ela será considerada comum a todos os avaliadores.

### Motivação
Essa decisão permite cadastrar checklists que não utilizam divisão de perguntas por papéis, mantendo a compatibilidade com instrumentos mais simples.

---

## D06 — Controle de prazos não faz parte do MVP

### Decisão
A primeira versão da ferramenta não incluirá deadlines para avaliações ou respostas.

### Motivação
Embora essa funcionalidade tenha sido proposta pelo FERA-ES, ela é predominantemente operacional e não é essencial para o objetivo inicial de apoiar a avaliação de Arquiteturas de Referência.

Poderá ser incorporada em uma evolução futura.