# Requisitos Não Funcionais — v0.2

> Requisitos não funcionais iniciais da ferramenta.
> Quando não indicado o contrário, estes requisitos representam decisões de projeto e deverão ser refinados e validados durante o desenvolvimento.

## Usabilidade

### RNF-01 — Facilidade de uso
A interface deve permitir que usuários com diferentes níveis de conhecimento técnico consigam cadastrar artefatos, participar de avaliações e consultar resultados sem necessidade de treinamento específico sobre a implementação da ferramenta.

### RNF-02 — Clareza das avaliações
A interface deve apresentar de forma clara ao avaliador quais questões ou critérios precisam ser avaliados e quais informações já foram preenchidas.

---

## Flexibilidade e extensibilidade

### RNF-03 — Configurabilidade dos checklists
A ferramenta deve permitir a utilização de diferentes estruturas de checklist sem exigir alterações no código-fonte para cada novo instrumento cadastrado.

### RNF-04 — Extensibilidade dos elementos arquiteturais
A ferramenta deve permitir a inclusão de novos tipos de elementos arquiteturais sem exigir alteração da estrutura principal do sistema.

### RNF-05 — Evolução dos mecanismos de avaliação
A arquitetura da ferramenta deve permitir que novos mecanismos de avaliação ou verificação de conformidade sejam incorporados futuramente sem exigir reestruturação significativa das funcionalidades existentes.

---

## Rastreabilidade e integridade

### RNF-06 — Rastreabilidade
O sistema deve preservar as relações entre:

- Arquiteturas de Referência e suas versões;
- arquiteturas concretas e suas versões;
- checklists e suas versões;
- questões, respostas e avaliações;
- elementos arquiteturais e seus mapeamentos;
- critérios de conformidade, resultados, evidências e violações.

### RNF-07 — Integridade histórica
Alterações realizadas em novas versões de Arquiteturas de Referência, arquiteturas concretas ou checklists não devem modificar os dados considerados em avaliações anteriores.

### RNF-08 — Integridade referencial
O sistema deve impedir associações inconsistentes entre entidades, como o mapeamento de um elemento concreto para um elemento pertencente a uma versão da RA diferente daquela utilizada como base pela arquitetura concreta.

---

## Segurança e acesso

### RNF-09 — Controle de acesso
O sistema deve restringir operações de criação, edição, colaboração e participação em avaliações de acordo com as permissões e responsabilidades do usuário.

No caso de Arquiteturas de Referência e arquiteturas concretas colaborativas, as permissões devem distinguir ao menos os papéis `OWNER` e `EDITOR`.

### RNF-10 — Proteção de artefatos privados
Arquiteturas de Referência e checklists definidos como privados, arquiteturas concretas e demais conteúdos protegidos não devem ser acessíveis a usuários não autorizados.

Imagens anexadas devem herdar as restrições de acesso do conteúdo ao qual pertencem.

---

## Plataforma

### RNF-11 — Aplicação Web
A ferramenta deve ser disponibilizada como uma aplicação Web acessível por navegadores modernos.

### RNF-12 — Interface responsiva
A interface deve se adaptar a diferentes tamanhos de tela, mantendo as principais funcionalidades utilizáveis em computadores e dispositivos móveis.

---

## Manutenibilidade

### RNF-13 — Separação de responsabilidades
A implementação deve manter separação entre regras de negócio, persistência de dados, serviços da aplicação e interface com o usuário.

### RNF-14 — Manutenibilidade
O código deve ser organizado de forma modular, permitindo que funcionalidades sejam alteradas ou adicionadas com impacto limitado sobre os demais módulos do sistema.

### RNF-15 — Proteção das credenciais
As senhas dos usuários não devem ser armazenadas em texto puro.

O sistema deve armazenar apenas representações protegidas das senhas utilizando mecanismo apropriado de hashing de senhas.

---

## Arquivos e imagens

### RNF-16 — Validação de imagens enviadas
O sistema deve validar arquivos enviados como imagem antes de associá-los aos artefatos da aplicação, aceitando somente formatos de imagem suportados pela implementação.

### RNF-17 — Armazenamento e referência de imagens
A implementação deve preservar metadados suficientes para identificar e recuperar as imagens anexadas sem acoplar as regras de negócio a um provedor específico de armazenamento.
