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

---

## D07 — Avaliação por checklist e avaliação de conformidade são processos distintos

### Decisão
A ferramenta possuirá dois tipos distintos de avaliação:

1. avaliação por checklist, aplicada a uma versão de Arquitetura de Referência; e
2. avaliação de conformidade, aplicada entre uma versão de Arquitetura de Referência e uma versão de arquitetura concreta derivada dela.

Os resultados dos dois tipos de avaliação poderão ser consultados a partir da Arquitetura de Referência.

### Motivação
Os dois processos possuem objetivos e informações diferentes.

A avaliação por checklist concentra-se principalmente na análise da Arquitetura de Referência segundo critérios respondidos por stakeholders.

A avaliação de conformidade concentra-se na relação entre a RA e uma arquitetura concreta derivada dela.

Mantê-los separados evita acoplamento desnecessário e permite utilizar uma abordagem independentemente da outra.

---

## D08 — Cada versão concreta referencia uma versão da RA

### Decisão
A associação com a Arquitetura de Referência será realizada no nível da versão da arquitetura concreta.

Cada versão concreta deve indicar qual versão da RA foi utilizada como sua base.

### Motivação
Uma arquitetura concreta pode evoluir ao longo do tempo e passar a utilizar versões diferentes de uma mesma RA.

A associação por versão preserva o histórico e permite identificar exatamente qual especificação da RA foi considerada durante uma avaliação de conformidade.

---

## D09 — Mapeamento entre elementos será muitos-para-muitos

### Decisão
A ferramenta não limitará o mapeamento entre elementos da RA e da arquitetura concreta a relações um-para-um.

### Motivação
Um elemento concreto pode realizar responsabilidades de mais de um elemento da RA, assim como diferentes elementos concretos podem conjuntamente representar um único elemento da RA.

Essa decisão também é compatível com o modelo de correspondência apresentado pelo MORE.

---

## D10 — A avaliação de conformidade será assistida e manual no MVP

### Decisão
A primeira versão da ferramenta não realizará análise automática de modelos, diagramas ou código-fonte para determinar conformidade.

O responsável pela avaliação realizará a verificação e utilizará a ferramenta para registrar:

- o critério avaliado;
- o resultado;
- as evidências;
- e as violações identificadas.

### Motivação
Abordagens de conformidade automática, como o MORE, envolvem técnicas de Model-Driven Engineering, metamodelagem, transformação de modelos, weaving e scripts de validação.

A implementação dessas técnicas aumentaria significativamente a complexidade do projeto e não é necessária para demonstrar a proposta central do TCC.

A automação de verificações poderá ser explorada como evolução futura.

---

## D11 — Elementos obrigatórios não serão modelados explicitamente no MVP

### Decisão
A primeira versão não terá uma propriedade estrutural específica para classificar elementos da RA como obrigatórios ou opcionais.

Requisitos desse tipo poderão ser expressos por meio de critérios de conformidade.

### Motivação
Embora abordagens como MORE representem componentes obrigatórios e realizem verificações automáticas sobre sua presença, essa estrutura não é necessária para a avaliação manual inicialmente proposta.

Caso a automação de conformidade seja incorporada futuramente, a classificação de elementos obrigatórios e opcionais poderá ser adicionada ao modelo.