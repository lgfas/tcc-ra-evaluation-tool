# Priorização de Wireframes — v0.1

> Este documento define quais telas do MVP devem receber maior atenção durante a criação dos wireframes.
>
> A priorização considera principalmente a importância da tela para demonstrar a proposta da ferramenta, a complexidade de interação e a possibilidade de reutilização de padrões visuais entre diferentes telas.

## Prioridade alta

Estas telas representam os principais conceitos e fluxos da ferramenta e devem possuir wireframes próprios.

### W01 — Login
Baseado em: T01 — Login.

Motivação:
Representa a entrada da aplicação e estabelece o padrão inicial de autenticação.

### W02 — Início
Baseado em: T03 — Início.

Motivação:
Define a navegação geral da aplicação e os principais pontos de acesso às funcionalidades do MVP.

### W03 — Detalhes da Arquitetura de Referência
Baseado em: T07 — Detalhes da Arquitetura de Referência.

Motivação:
É uma das telas centrais da ferramenta, reunindo versões, elementos, avaliações por checklist, instanciações e conformidade.

### W04 — Editor da Checklist
Baseado em:
- T13 — Editor da Checklist;
- T14 — Adicionar/editar questão.

Motivação:
Representa a flexibilidade da ferramenta para trabalhar com diferentes instrumentos de avaliação, tipos de resposta, seções e stakeholders.

### W05 — Configuração da Avaliação por Checklist
Baseado em:
- T16 — Nova Avaliação por Checklist;
- T17 — Configuração da Avaliação.

Motivação:
Demonstra a associação entre versão da RA, checklist, participantes e stakeholders.

### W06 — Responder Avaliação por Checklist
Baseado em: T18 — Responder Avaliação.

Motivação:
Representa a principal interação do avaliador durante uma avaliação por checklist.

### W07 — Acompanhamento e Resultados da Avaliação por Checklist
Baseado em:
- T19 — Acompanhamento da Avaliação;
- T20 — Resultados da Avaliação por Checklist.

Motivação:
Demonstra o acompanhamento dos participantes e a consolidação dos resultados.

### W08 — Detalhes da Arquitetura Concreta
Baseado em: T24 — Detalhes da Arquitetura Concreta.

Motivação:
Funciona como ponto central para elementos concretos, mapeamentos e avaliações de conformidade.

### W09 — Mapeamento entre Arquitetura Concreta e RA
Baseado em: T27 — Mapeamento entre arquitetura concreta e RA.

Motivação:
É uma das interações mais específicas da proposta da ferramenta e representa a correspondência entre os elementos concretos e os elementos da RA.

### W10 — Executar Avaliação de Conformidade
Baseado em:
- T29 — Executar Avaliação de Conformidade;
- T30 — Registrar Evidência;
- T31 — Registrar Violação.

Motivação:
Representa a avaliação manual assistida de conformidade e conecta critérios, elementos da RA, mapeamentos, evidências e violações.

### W11 — Resultados da Avaliação de Conformidade
Baseado em: T32 — Resultados da Avaliação de Conformidade.

Motivação:
Demonstra de forma consolidada os resultados de conformidade e as violações identificadas.

---

## Prioridade média

Estas telas devem ser prototipadas, mas podem reutilizar estruturas e componentes definidos nos wireframes de prioridade alta.

- T02 — Cadastro;
- T04 — Minhas Arquiteturas de Referência;
- T05 — Nova Arquitetura de Referência;
- T06 — Criar versão da RA;
- T08 — Elementos da RA;
- T09 — Adicionar/editar elemento da RA;
- T10 — Minhas Checklists;
- T11 — Nova Checklist;
- T12 — Criar versão da Checklist;
- T15 — Minhas Avaliações;
- T21 — Minhas Arquiteturas Concretas;
- T22 — Nova Arquitetura Concreta;
- T23 — Criar versão da Arquitetura Concreta;
- T25 — Elementos da Arquitetura Concreta;
- T26 — Adicionar/editar elemento concreto;
- T28 — Nova Avaliação de Conformidade;
- T33 — Catálogo Público;
- T34 — Detalhes de RA Pública;
- T35 — Detalhes de Checklist Pública.

---

## Prioridade baixa

Estas telas ou estados podem ser representados inicialmente por componentes, modais ou variações das telas anteriores, sem necessidade de um wireframe completo próprio.

- T30 — Registrar Evidência;
- T31 — Registrar Violação;
- T36 — Criar Derivação de Checklist;
- T37 — Menu/Conta do Usuário;
- estados vazios;
- mensagens de erro;
- confirmações;
- diálogos simples de criação de tipos customizados.

---

## Padrões reutilizáveis

Os seguintes grupos devem compartilhar padrões visuais para reduzir a quantidade de layouts distintos.

### Listagens

Podem compartilhar uma mesma estrutura:

- Minhas RAs;
- Minhas Checklists;
- Minhas Arquiteturas Concretas;
- Minhas Avaliações;
- Catálogo.

### Formulários de criação

Podem compartilhar um mesmo padrão de formulário:

- Nova RA;
- Nova Checklist;
- Nova Arquitetura Concreta;
- criação de versões;
- criação de derivação de checklist.

### Detalhes de artefatos versionados

Podem compartilhar padrões de cabeçalho e seleção de versão:

- Detalhes da RA;
- Detalhes da Checklist;
- Detalhes da Arquitetura Concreta.

### Elementos arquiteturais

RA e arquitetura concreta podem reutilizar os mesmos componentes para:

- listagem de elementos;
- seleção de tipo;
- descrição em Markdown;
- criação de tipo customizado.

### Avaliações

Avaliação por checklist e avaliação de conformidade podem compartilhar padrões para:

- status;
- progresso;
- navegação;
- finalização;
- apresentação de resultados.