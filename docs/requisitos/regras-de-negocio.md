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

### RN-CHK-09 — Seção da questão pertence à mesma versão
Quando uma questão estiver associada a uma seção, a seção deve pertencer à mesma versão de checklist da questão.

### RN-CHK-10 — Stakeholders da questão pertencem à mesma versão
Os papéis/stakeholders associados a uma questão devem pertencer à mesma versão de checklist da questão.

---

## Avaliações por checklist

### RN-AVA-01 — Composição da avaliação por checklist
Cada avaliação por checklist deve estar associada a exatamente:

- uma versão de Arquitetura de Referência; e
- uma versão de checklist.

### RN-AVA-02 — Versões utilizadas pela avaliação são fixas
Após o início de uma avaliação, as versões da Arquitetura de Referência e da checklist associadas a ela não devem ser substituídas.

Caso seja necessário avaliar outra versão da RA ou da checklist, uma nova avaliação deve ser criada.

### RN-AVA-03 — Papéis do participante são opcionais
Um participante de uma avaliação pode possuir zero ou mais papéis/stakeholders associados.

Quando possuir papéis, o participante deve receber as questões associadas a esses papéis, além das questões sem stakeholder específico.

Quando não possuir nenhum papel, o participante deve receber somente as questões sem stakeholder específico.

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

### RN-AVA-09 — Papel do participante deve pertencer à checklist da avaliação
Os papéis atribuídos a um participante devem pertencer à versão de checklist utilizada pela avaliação da qual ele participa.

### RN-AVA-10 — Resposta deve utilizar questão da checklist da avaliação
Uma resposta somente pode referenciar uma questão pertencente à versão de checklist utilizada pela avaliação.

Quando a questão utilizar resposta por seleção, a opção selecionada deve pertencer à própria questão respondida.

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

---

## Instanciações

### RN-INS-01 — Arquitetura concreta é versionada
Uma arquitetura concreta pode possuir diferentes versões.

Alterações realizadas em uma versão já utilizada em uma avaliação de conformidade não devem modificar retroativamente os dados considerados naquela avaliação.

Quando necessário preservar o estado anterior da arquitetura concreta, uma nova versão deve ser criada.

### RN-INS-02 — Versão concreta possui uma versão da RA como base
Cada versão de uma arquitetura concreta deve estar associada a exatamente uma versão da Arquitetura de Referência utilizada como sua base.

Uma mesma arquitetura concreta pode possuir versões baseadas em diferentes versões da RA ao longo de sua evolução.

### RN-INS-03 — Elementos pertencem a uma versão concreta
Todo elemento arquitetural de uma arquitetura concreta deve estar associado a uma versão específica dessa arquitetura.

### RN-INS-04 — Mapeamentos respeitam as versões relacionadas
Um elemento de uma arquitetura concreta somente pode ser mapeado para elementos da versão da Arquitetura de Referência utilizada como base daquela versão concreta.

### RN-INS-05 — Mapeamentos não são limitados a relações um-para-um
Um elemento de uma versão da arquitetura concreta pode estar relacionado a um ou mais elementos da versão da RA.

Da mesma forma, um elemento da versão da RA pode estar relacionado a um ou mais elementos da arquitetura concreta.

### RN-INS-06 — Mapeamentos são específicos da versão
Os mapeamentos realizados entre uma versão concreta e uma versão da RA pertencem àquela combinação específica de versões.

A criação de uma nova versão da arquitetura concreta ou da RA não deve transferir automaticamente os mapeamentos existentes.

---

## Conformidade

### RN-CONF-01 — Composição da avaliação de conformidade
Cada avaliação de conformidade deve estar associada a exatamente:

- uma versão de arquitetura concreta; e
- a versão da Arquitetura de Referência utilizada como base por essa arquitetura concreta.

### RN-CONF-02 — Critérios de conformidade pertencem a uma versão da RA
Todo critério de conformidade deve estar associado a uma versão específica de uma Arquitetura de Referência.

### RN-CONF-03 — Associação do critério a elementos da RA é opcional
Um critério de conformidade pode se aplicar à versão da RA como um todo ou estar associado a um ou mais elementos arquiteturais específicos.

### RN-CONF-04 — Verificação de conformidade é manual no MVP
Na versão inicial da ferramenta, o resultado de cada critério de conformidade deve ser informado pelo responsável pela avaliação.

A ferramenta deve apoiar o registro e a organização da avaliação, mas não deve inferir automaticamente a conformidade da arquitetura concreta.

### RN-CONF-05 — Resultado pertence a um critério da avaliação
Todo resultado de conformidade deve estar associado a:

- uma avaliação de conformidade; e
- um critério de conformidade considerado nessa avaliação.

### RN-CONF-06 — Evidências fundamentam resultados
Uma verificação de conformidade pode possuir evidências que fundamentem o resultado registrado.

### RN-CONF-07 — Violação identifica uma não conformidade
Toda violação registrada deve estar associada à avaliação de conformidade e ao critério de conformidade que não foi atendido.

Quando aplicável, a violação também pode indicar os elementos da RA e da arquitetura concreta envolvidos.

### RN-CONF-08 — Um critério pode originar múltiplas violações
Um mesmo critério de conformidade pode resultar em mais de uma violação dentro da mesma avaliação.

### RN-CONF-09 — Um resultado por critério em cada avaliação
Cada critério de conformidade deve possuir, no máximo, um resultado registrado em uma mesma avaliação de conformidade.

---

## Usuários e autenticação

### RN-USR-01 — E-mail do usuário é único
Cada endereço de e-mail pode estar associado a apenas uma conta de usuário.