# Mapa de Telas — v0.1

> Este documento organiza as principais telas previstas para o MVP da ferramenta a partir dos fluxos de usuário definidos.
>
> O objetivo é servir como ponte entre a especificação funcional e a criação dos wireframes de baixa fidelidade.

## Navegação principal

Após a autenticação, a aplicação deve possuir uma navegação principal com acesso às seguintes áreas:

- Início;
- Arquiteturas de Referência;
- Checklists;
- Avaliações;
- Arquiteturas Concretas;
- Catálogo;
- Conta do usuário.

A navegação exata poderá ser refinada durante a prototipação.

---

## 1. Autenticação

### T01 — Login

Permite ao usuário informar:

- e-mail;
- senha.

Ações principais:

- Entrar;
- Criar conta.

### T02 — Cadastro

Permite informar:

- nome;
- e-mail;
- senha.

Ações principais:

- Criar conta;
- Voltar para login.

---

## 2. Área inicial

### T03 — Início

Tela inicial após autenticação.

Deve oferecer acesso rápido às principais áreas da ferramenta.

Pode apresentar, de maneira simples:

- Arquiteturas de Referência recentes;
- avaliações em andamento;
- checklists recentes;
- atalhos para criação de artefatos.

> O MVP não exige dashboards analíticos complexos nessa tela.

---

## 3. Arquiteturas de Referência

### T04 — Minhas Arquiteturas de Referência

Apresenta as RAs pertencentes ao usuário.

Informações principais:

- nome;
- visibilidade;
- quantidade de versões.

Ações:

- Criar RA;
- Abrir RA.

### T05 — Nova Arquitetura de Referência

Formulário para informar:

- nome;
- visibilidade.

Após o cadastro, o usuário segue para a criação da primeira versão.

### T06 — Criar versão da RA

Formulário para informar:

- identificador da versão;
- descrição geral em Markdown.

### T07 — Detalhes da Arquitetura de Referência

Tela central da RA.

Deve permitir:

- selecionar a versão da RA;
- consultar a descrição da versão;
- navegar pelas áreas relacionadas.

Áreas previstas:

- Visão geral;
- Elementos;
- Avaliações por checklist;
- Instanciações;
- Conformidade.

Ações principais:

- Criar nova versão;
- Criar avaliação por checklist;
- Cadastrar arquitetura concreta.

### T08 — Elementos da RA

Apresenta os elementos da versão selecionada.

Informações:

- nome;
- tipo;
- descrição.

Ações:

- Adicionar elemento;
- Editar elemento, quando permitido.

### T09 — Adicionar/editar elemento da RA

Formulário para:

- nome;
- tipo arquitetural;
- descrição em Markdown.

Permite também criar um tipo arquitetural customizado.

---

## 4. Checklists

### T10 — Minhas Checklists

Apresenta as checklists pertencentes ao usuário.

Informações principais:

- nome;
- origem;
- visibilidade;
- versões existentes.

Ações:

- Criar checklist;
- Abrir checklist.

### T11 — Nova Checklist

Formulário para:

- nome;
- origem;
- visibilidade.

Após o cadastro, o usuário segue para a criação da primeira versão.

### T12 — Criar versão da Checklist

Formulário para informar:

- identificador da versão.

### T13 — Editor da Checklist

Tela principal de edição de uma versão.

Áreas previstas:

- Questões;
- Seções;
- Stakeholders.

A tela deve permitir:

- adicionar questões;
- criar seções;
- cadastrar stakeholders;
- ordenar questões e seções.

### T14 — Adicionar/editar questão

Formulário para:

- enunciado;
- tipo de resposta;
- configuração de comentários;
- seção;
- stakeholders.

Quando `SINGLE_CHOICE`, permite cadastrar e ordenar opções de resposta.

---

## 5. Avaliações por checklist

### T15 — Minhas Avaliações

Apresenta avaliações relacionadas ao usuário.

Pode possuir duas áreas:

- Avaliações por checklist;
- Avaliações de conformidade.

Para avaliações por checklist, deve distinguir:

- avaliações criadas pelo usuário;
- avaliações das quais o usuário participa.

### T16 — Nova Avaliação por Checklist

Permite selecionar:

- versão da RA;
- checklist;
- versão da checklist.

Ao ser criada, a avaliação inicia com status `DRAFT`.

### T17 — Configuração da Avaliação

Permite:

- visualizar RA e checklist escolhidas;
- adicionar participantes;
- associar zero ou mais papéis a cada participante;
- revisar a configuração;
- iniciar a avaliação.

### T18 — Responder Avaliação

Tela utilizada pelo participante.

Deve apresentar:

- nome da avaliação;
- progresso;
- questão atual;
- resposta esperada;
- comentário, quando aplicável.

Ações:

- Salvar resposta;
- Ir para próxima questão;
- Navegar entre questões disponíveis.

### T19 — Acompanhamento da Avaliação

Tela utilizada pelo responsável pela avaliação.

Apresenta:

- participantes;
- papéis;
- progresso de cada participante;
- questões respondidas e pendentes;
- status geral da avaliação.

Ações:

- consultar progresso;
- finalizar avaliação, quando permitido.

### T20 — Resultados da Avaliação por Checklist

Apresenta os resultados consolidados.

Deve permitir consultar:

- questões;
- respostas dos participantes;
- comentários;
- distribuição das opções de resposta, quando aplicável.

---

## 6. Arquiteturas Concretas

### T21 — Minhas Arquiteturas Concretas

Apresenta as arquiteturas concretas pertencentes ao usuário.

Informações:

- nome;
- versões existentes;
- RA relacionada.

Ações:

- abrir arquitetura concreta;
- acessar versão.

### T22 — Nova Arquitetura Concreta

Pode ser iniciada a partir de uma versão de RA.

Solicita:

- nome da arquitetura concreta.

### T23 — Criar versão da Arquitetura Concreta

Formulário para:

- versão;
- versão da RA utilizada como base;
- descrição em Markdown.

### T24 — Detalhes da Arquitetura Concreta

Apresenta:

- nome;
- versão selecionada;
- RA base;
- descrição.

Áreas previstas:

- Visão geral;
- Elementos;
- Mapeamentos;
- Avaliações de conformidade.

### T25 — Elementos da Arquitetura Concreta

Apresenta:

- nome;
- tipo;
- descrição dos elementos concretos.

Ações:

- adicionar elemento;
- editar elemento, quando permitido.

### T26 — Adicionar/editar elemento concreto

Formulário para:

- nome;
- tipo arquitetural;
- descrição em Markdown.

### T27 — Mapeamento entre arquitetura concreta e RA

Tela de apoio ao mapeamento manual.

Deve apresentar:

- elementos da arquitetura concreta;
- elementos da RA base;
- mapeamentos existentes.

Permite:

- selecionar um elemento concreto;
- associar um ou mais elementos da RA;
- remover mapeamentos;
- consultar os mapeamentos consolidados.

---

## 7. Avaliação de Conformidade

### T28 — Nova Avaliação de Conformidade

Apresenta um resumo de:

- arquitetura concreta;
- versão concreta;
- RA base;
- versão da RA;
- elementos;
- mapeamentos;
- critérios disponíveis.

Ações:

- criar avaliação;
- revisar informações antes de iniciar.

### T29 — Executar Avaliação de Conformidade

Apresenta um critério por vez ou uma lista navegável de critérios.

Para cada critério, deve apresentar:

- nome;
- descrição;
- elementos da RA relacionados;
- elementos concretos mapeados, quando existentes.

Permite registrar:

- `CONFORMING`;
- `NON_CONFORMING`;
- `NOT_APPLICABLE`;
- observações;
- evidências;
- violações.

### T30 — Registrar Evidência

Permite informar:

- descrição;
- URL externa opcional.

### T31 — Registrar Violação

Permite informar:

- descrição;
- elementos da RA envolvidos;
- elementos concretos envolvidos.

Disponível apenas para resultados `NON_CONFORMING`.

### T32 — Resultados da Avaliação de Conformidade

Apresenta:

- quantidade de critérios conformes;
- quantidade de critérios não conformes;
- quantidade de critérios não aplicáveis;
- violações identificadas.

Permite acessar:

- detalhe dos critérios;
- evidências;
- violações.

---

## 8. Catálogo

### T33 — Catálogo Público

Permite alternar entre:

- Arquiteturas de Referência;
- Checklists.

Deve permitir uma busca simples por nome.

### T34 — Detalhes de RA Pública

Apresenta:

- nome;
- versões;
- descrição;
- elementos arquiteturais.

O usuário não proprietário não pode editar o artefato.

Pode permitir:

- utilizar uma versão da RA em uma avaliação.

### T35 — Detalhes de Checklist Pública

Apresenta:

- nome;
- origem;
- versões;
- seções;
- questões;
- stakeholders;
- tipos e opções de resposta.

Pode permitir:

- utilizar em avaliação;
- criar derivação.

### T36 — Criar Derivação de Checklist

Permite informar:

- nome da nova checklist;
- visibilidade;
- informações de origem, quando aplicável.

A nova checklist mantém referência à versão de origem.

---

## 9. Conta

### T37 — Menu/Conta do Usuário

Disponibiliza:

- identificação do usuário;
- opção para encerrar sessão.

Funcionalidades avançadas de perfil não fazem parte do MVP.