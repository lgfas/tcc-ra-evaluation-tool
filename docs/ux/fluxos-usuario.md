# Fluxos de Usuário — v0.2

> Este documento descreve os principais fluxos de interação previstos para o MVP da ferramenta.
>
> Os fluxos foram derivados dos requisitos funcionais, regras de negócio e decisões de projeto e servirão de base para a definição das telas e dos protótipos da interface.

## Fluxo 01 — Cadastrar e estruturar uma Arquitetura de Referência

### Objetivo

Permitir que um usuário autenticado cadastre uma nova Arquitetura de Referência, gerencie colaboradores, crie sua primeira versão, registre imagens e cadastre os elementos arquiteturais que a compõem.

### Ator principal

Usuário autenticado.

### Pré-condições

- O usuário deve possuir uma conta cadastrada.
- O usuário deve estar autenticado no sistema.

### Fluxo principal

1. O usuário acessa a área de suas Arquiteturas de Referência.
2. O usuário seleciona a opção para criar uma nova Arquitetura de Referência.
3. O sistema solicita as informações gerais da RA:
   - nome;
   - visibilidade (`PUBLIC` ou `PRIVATE`).
4. O usuário informa os dados e confirma o cadastro.
5. O sistema cria a Arquitetura de Referência e registra o usuário criador como membro `OWNER`.
6. O proprietário pode adicionar zero ou mais usuários como colaboradores `EDITOR`.
7. O sistema solicita os dados da primeira versão:
   - identificador da versão;
   - descrição geral da versão em conteúdo textual formatado;
   - imagens anexas, quando aplicável.
8. O usuário informa os dados da versão e confirma.
9. O sistema cria a primeira versão da RA.
10. O usuário acessa a área de elementos arquiteturais da versão.
11. O usuário seleciona a opção para adicionar um elemento arquitetural.
12. O sistema solicita:
    - nome;
    - tipo do elemento;
    - descrição em conteúdo textual formatado;
    - imagens anexas, quando aplicável.
13. O usuário seleciona um tipo arquitetural existente ou cria um tipo customizado.
14. O usuário confirma o cadastro do elemento.
15. O sistema adiciona o elemento e seus anexos à versão da RA.
16. O usuário pode repetir o processo para cadastrar outros elementos.
17. O usuário retorna à visão geral da versão da RA.

### Resultado

A Arquitetura de Referência fica cadastrada com:

- um proprietário e zero ou mais colaboradores;
- uma primeira versão;
- sua descrição geral e imagens associadas, quando existirem;
- zero ou mais elementos arquiteturais, cada um podendo possuir imagens;
- os tipos associados aos elementos cadastrados.

### Fluxos alternativos

#### FA01 — Criar tipo arquitetural customizado

Durante o cadastro de um elemento, caso o tipo desejado não esteja disponível:

1. O usuário seleciona a opção para criar um novo tipo.
2. O usuário informa o nome do tipo.
3. O sistema cadastra o tipo como criado pelo usuário.
4. O novo tipo passa a estar disponível para seleção.
5. O usuário continua o cadastro do elemento.

#### FA02 — Criar nova versão de uma RA existente

1. O usuário acessa uma Arquitetura de Referência já cadastrada.
2. O usuário seleciona a opção para criar uma nova versão.
3. O sistema solicita:
   - identificador da nova versão;
   - descrição geral da nova versão.
4. O usuário informa os dados e confirma.
5. O sistema cria a nova versão.
6. O usuário cadastra os elementos arquiteturais correspondentes à nova versão.

> No MVP, os elementos de uma versão anterior não são transferidos automaticamente para a nova versão.

#### FA03 — Gerenciar colaboradores da RA

1. O usuário `OWNER` acessa a área de colaboradores da Arquitetura de Referência.
2. O usuário seleciona um usuário cadastrado e o adiciona como `EDITOR`.
3. O sistema registra o colaborador.
4. O colaborador passa a poder editar o conteúdo da RA conforme as permissões definidas no MVP.
5. O `OWNER` pode remover posteriormente um colaborador `EDITOR`.

#### FA04 — Anexar imagens à RA ou a seus elementos

1. Durante a edição de uma versão ou de um elemento da RA, o usuário seleciona a opção para adicionar uma imagem.
2. O sistema valida o arquivo enviado.
3. O sistema armazena o arquivo e registra seus metadados.
4. A imagem passa a ser exibida como conteúdo complementar à descrição textual.
5. A imagem permanece associada exclusivamente ao contexto em que foi anexada.

---

## Fluxo 02 — Cadastrar e estruturar uma checklist

### Objetivo

Permitir que um usuário autenticado cadastre uma checklist de avaliação, crie sua primeira versão e configure sua estrutura de questões, seções, opções de resposta e stakeholders.

### Ator principal

Usuário autenticado.

### Pré-condições

- O usuário deve possuir uma conta cadastrada.
- O usuário deve estar autenticado no sistema.

### Fluxo principal

1. O usuário acessa a área de suas checklists.
2. O usuário seleciona a opção para criar uma nova checklist.
3. O sistema solicita as informações gerais da checklist:
   - nome;
   - origem ou fonte;
   - visibilidade (`PUBLIC` ou `PRIVATE`).
4. O usuário informa os dados e confirma o cadastro.
5. O sistema cria a checklist e solicita os dados de sua primeira versão:
   - identificador da versão.
6. O usuário informa os dados e confirma.
7. O sistema cria a primeira versão da checklist.
8. O usuário acessa a área de edição da versão da checklist.
9. O usuário pode cadastrar os stakeholders/papéis utilizados pela checklist.
10. O usuário pode criar seções para organizar as questões.
11. O usuário seleciona a opção para adicionar uma nova questão.
12. O sistema solicita:
    - enunciado da questão;
    - tipo de resposta;
    - configuração de comentários;
    - seção, quando aplicável;
    - stakeholders responsáveis, quando aplicável.
13. O usuário configura a questão.
14. Caso o tipo de resposta seja por seleção, o usuário cadastra as opções disponíveis.
15. O usuário confirma o cadastro da questão.
16. O sistema adiciona a questão à versão da checklist.
17. O usuário pode repetir o processo para cadastrar outras questões.
18. O usuário pode reorganizar as questões e seções de acordo com a ordem desejada.
19. O usuário retorna à visão geral da versão da checklist.

### Resultado

A checklist fica cadastrada com:

- uma primeira versão;
- sua origem ou fonte, quando informada;
- sua visibilidade;
- zero ou mais seções;
- zero ou mais stakeholders;
- zero ou mais questões configuradas.

### Fluxos alternativos

#### FA01 — Checklist sem seções

1. O usuário não cadastra nenhuma seção.
2. O usuário adiciona questões diretamente à versão da checklist.
3. As questões permanecem válidas sem associação a uma seção.

#### FA02 — Questão com resposta por seleção

1. O usuário seleciona `SINGLE_CHOICE` como tipo de resposta.
2. O sistema solicita o cadastro das opções de resposta.
3. O usuário informa as opções disponíveis, por exemplo:
   - Sim;
   - Parcialmente;
   - Não.
4. O usuário define a ordem das opções.
5. O sistema associa as opções à questão.

#### FA03 — Questão com resposta textual

1. O usuário seleciona `TEXT` como tipo de resposta.
2. O sistema não solicita opções de resposta.
3. A questão é configurada para receber conteúdo textual.

#### FA04 — Configurar comentários

Ao cadastrar ou editar uma questão, o usuário seleciona uma das configurações:

- `NONE`: a questão não utiliza comentário;
- `OPTIONAL`: o comentário pode ser preenchido;
- `REQUIRED`: o comentário deve ser preenchido junto à resposta.

#### FA05 — Questão sem stakeholder específico

1. O usuário não associa nenhum stakeholder à questão.
2. O sistema considera a questão comum a todos os participantes da avaliação.

#### FA06 — Questão associada a múltiplos stakeholders

1. O usuário seleciona dois ou mais stakeholders para a questão.
2. O sistema associa a questão a todos os papéis selecionados.
3. Durante uma avaliação, participantes que exerçam qualquer um desses papéis poderão receber a questão.

#### FA07 — Criar nova versão de uma checklist existente

1. O usuário acessa uma checklist já cadastrada.
2. O usuário seleciona a opção para criar uma nova versão.
3. O sistema solicita o identificador da nova versão.
4. O usuário confirma a criação.
5. O sistema cria uma nova versão da checklist.
6. O usuário configura o conteúdo correspondente à nova versão.

> A forma de inicialização de uma nova versão — vazia ou a partir de uma cópia da versão anterior — ainda não foi definida para o MVP e deverá ser decidida antes da prototipação dessa funcionalidade.

---

## Fluxo 03 — Criar e realizar uma avaliação por checklist

### Objetivo

Permitir que um usuário crie uma avaliação de uma versão de Arquitetura de Referência utilizando uma versão de checklist, defina os participantes e seus papéis e acompanhe o preenchimento das respostas até a conclusão da avaliação.

### Ator principal

Usuário autenticado responsável pela criação da avaliação.

### Atores secundários

Participantes da avaliação.

### Pré-condições

- O usuário responsável deve estar autenticado.
- Deve existir uma versão de Arquitetura de Referência a ser avaliada.
- Deve existir uma versão de checklist disponível para utilização.
- Os participantes adicionados à avaliação devem possuir conta cadastrada na ferramenta.

### Fluxo principal

1. O usuário acessa uma Arquitetura de Referência.
2. O usuário seleciona a versão da RA que deseja avaliar.
3. O usuário seleciona a opção para criar uma nova avaliação por checklist.
4. O sistema solicita a seleção da checklist que será utilizada.
5. O usuário seleciona:
   - uma checklist própria ou pública;
   - a versão da checklist desejada.
6. O usuário confirma a criação da avaliação.
7. O sistema cria a avaliação com status `DRAFT`.
8. O usuário acessa a configuração de participantes.
9. O usuário adiciona os usuários que participarão da avaliação.
10. Para cada participante, o usuário pode associar zero ou mais stakeholders/papéis definidos pela versão da checklist.
11. O sistema apresenta um resumo contendo:
    - versão da RA;
    - checklist e versão selecionadas;
    - participantes;
    - papéis atribuídos.
12. O usuário inicia a avaliação.
13. O sistema altera o status da avaliação para `IN_PROGRESS`.
14. As versões da RA e da checklist utilizadas pela avaliação passam a permanecer fixas para aquela avaliação.
15. Cada participante acessa a avaliação.
16. O sistema determina quais questões devem ser apresentadas ao participante com base em seus papéis.
17. O participante responde às questões disponibilizadas.
18. Para cada questão, o sistema apresenta o mecanismo de resposta correspondente à configuração da checklist.
19. Quando aplicável, o participante adiciona comentários à resposta.
20. O sistema registra as respostas fornecidas.
21. O participante pode continuar respondendo às demais questões disponíveis.
22. O responsável acompanha o andamento da avaliação.
23. Quando a avaliação estiver pronta para encerramento, o responsável seleciona a opção para finalizá-la.
24. O sistema altera o status da avaliação para `COMPLETED`.
25. O sistema disponibiliza a visualização consolidada dos resultados.
26. A avaliação passa a aparecer entre os resultados associados à versão da Arquitetura de Referência.

### Resultado

A avaliação fica registrada com:

- a versão da RA avaliada;
- a versão da checklist utilizada;
- os participantes;
- os papéis atribuídos a cada participante;
- as respostas fornecidas;
- os comentários associados às respostas;
- o status final da avaliação;
- os resultados consolidados.

### Fluxos alternativos

#### FA01 — Participante com múltiplos papéis

1. O responsável associa dois ou mais stakeholders/papéis ao participante.
2. O sistema reúne as questões associadas a todos os papéis atribuídos.
3. Questões repetidas entre diferentes papéis devem ser apresentadas apenas uma vez ao participante.
4. As questões sem stakeholder específico também são apresentadas ao participante.

#### FA02 — Participante sem papel específico

1. O responsável adiciona o participante sem atribuir nenhum stakeholder/papel.
2. O sistema apresenta ao participante apenas as questões que não possuem stakeholder específico associado.

#### FA03 — Questão comum a todos os participantes

1. A questão não possui stakeholder associado.
2. O sistema apresenta a questão a todos os participantes da avaliação, independentemente dos papéis atribuídos.

#### FA04 — Questão de seleção

1. O sistema apresenta as opções configuradas para a questão.
2. O participante seleciona uma das opções.
3. Caso o comentário seja `OPTIONAL`, o participante pode adicionar um comentário.
4. Caso o comentário seja `REQUIRED`, o sistema exige o preenchimento do comentário para registrar a resposta.
5. Caso o comentário seja `NONE`, o campo de comentário não é apresentado.

#### FA05 — Questão textual

1. O sistema apresenta um campo textual para resposta.
2. O participante informa o conteúdo da resposta.
3. O comentário adicional segue a configuração definida para a questão.

#### FA06 — Alterar configuração antes do início

Enquanto a avaliação estiver em `DRAFT`, o responsável pode revisar a configuração da avaliação antes de iniciá-la.

Após o início, as versões da RA e da checklist utilizadas não podem ser substituídas.

#### FA07 — Consultar avaliação em andamento

1. O responsável acessa uma avaliação com status `IN_PROGRESS`.
2. O sistema apresenta o andamento do preenchimento pelos participantes.
3. O responsável pode consultar quais participantes já forneceram respostas e quais ainda possuem questões pendentes.

> O MVP não utiliza prazos ou deadlines para respostas.

---

## Fluxo 04 — Cadastrar uma arquitetura concreta e mapear seus elementos para a RA

### Objetivo

Permitir que um usuário cadastre colaborativamente uma arquitetura concreta derivada de uma versão de Arquitetura de Referência, descreva sua versão e seus elementos com conteúdo textual e imagens e estabeleça manualmente os mapeamentos entre os elementos concretos e os elementos da RA.

### Ator principal

Usuário autenticado responsável pela arquitetura concreta.

### Pré-condições

- O usuário deve estar autenticado.
- Deve existir uma versão de Arquitetura de Referência que será utilizada como base da arquitetura concreta.

### Fluxo principal

1. O usuário acessa uma Arquitetura de Referência.
2. O usuário seleciona a versão da RA utilizada como base pela arquitetura concreta.
3. O usuário acessa a área de instanciações da RA.
4. O usuário seleciona a opção para cadastrar uma nova arquitetura concreta.
5. O sistema solicita o nome da arquitetura concreta.
6. O usuário informa o nome e confirma o cadastro.
7. O sistema cria a arquitetura concreta, registra o usuário criador como `OWNER` e mantém a versão da RA selecionada como referência para a primeira versão concreta.
8. O proprietário pode adicionar zero ou mais usuários como colaboradores `EDITOR`.
9. O sistema solicita os dados da primeira versão:
   - identificador da versão;
   - descrição geral em conteúdo textual formatado;
   - imagens anexas, quando aplicável.
10. A versão da RA selecionada anteriormente é definida como base da versão concreta.
11. O usuário confirma a criação da versão concreta.
12. O sistema cria a primeira versão da arquitetura concreta.
13. O usuário acessa a área de elementos da versão concreta.
14. O usuário seleciona a opção para adicionar um elemento arquitetural.
15. O sistema solicita:
    - nome;
    - tipo arquitetural;
    - descrição em conteúdo textual formatado;
    - imagens anexas, quando aplicável.
16. O usuário seleciona um tipo existente ou cria um tipo customizado.
17. O usuário confirma o cadastro do elemento.
18. O sistema adiciona o elemento e seus anexos à versão concreta.
19. O usuário repete o processo para os demais elementos da arquitetura concreta.
20. O usuário acessa a área de mapeamento entre a arquitetura concreta e a RA.
21. O sistema apresenta:
    - os elementos da versão concreta;
    - os elementos da versão da RA utilizada como base.
22. O usuário seleciona um elemento concreto.
23. O usuário seleciona um ou mais elementos da RA aos quais aquele elemento concreto corresponde.
24. O usuário confirma o mapeamento.
25. O sistema registra as correspondências.
26. O usuário pode repetir o processo para os demais elementos.
27. O sistema disponibiliza uma visualização consolidada dos mapeamentos existentes.

### Resultado

A arquitetura concreta fica registrada com:

- um proprietário e zero ou mais colaboradores;
- uma primeira versão;
- a versão da RA utilizada como base;
- sua descrição geral e imagens associadas, quando existirem;
- seus elementos arquiteturais, cada um podendo possuir imagens;
- os tipos associados aos elementos;
- os mapeamentos estabelecidos entre os elementos concretos e os elementos da RA.

### Fluxos alternativos

#### FA01 — Criar tipo arquitetural customizado

Durante o cadastro de um elemento concreto, caso o tipo desejado não esteja disponível:

1. O usuário seleciona a opção para criar um novo tipo arquitetural.
2. O usuário informa o nome do tipo.
3. O sistema cadastra o novo tipo.
4. O tipo passa a estar disponível para utilização.
5. O usuário continua o cadastro do elemento concreto.

#### FA02 — Elemento concreto relacionado a múltiplos elementos da RA

1. O usuário seleciona um elemento concreto.
2. O usuário associa dois ou mais elementos da RA ao elemento concreto.
3. O sistema registra cada correspondência como um mapeamento independente.

#### FA03 — Múltiplos elementos concretos relacionados ao mesmo elemento da RA

1. O usuário mapeia um elemento concreto para determinado elemento da RA.
2. Posteriormente, o usuário mapeia outro elemento concreto para o mesmo elemento da RA.
3. O sistema mantém ambos os mapeamentos.

#### FA04 — Elemento ainda não mapeado

1. O usuário cadastra um elemento concreto sem estabelecer imediatamente um mapeamento.
2. O elemento permanece disponível na arquitetura concreta.
3. O usuário pode realizar o mapeamento posteriormente.

#### FA05 — Criar nova versão da arquitetura concreta

1. O usuário acessa uma arquitetura concreta existente.
2. O usuário seleciona a opção para criar uma nova versão.
3. O sistema solicita:
   - identificador da nova versão;
   - versão da RA utilizada como base;
   - descrição geral da nova versão.
4. O usuário informa os dados e confirma.
5. O sistema cria a nova versão concreta.
6. O usuário cadastra os elementos correspondentes à nova versão.
7. O usuário realiza os mapeamentos entre os elementos dessa versão concreta e os elementos da versão da RA selecionada.

> No MVP, os elementos e mapeamentos de versões anteriores não são transferidos automaticamente para a nova versão concreta.

#### FA06 — Gerenciar colaboradores da arquitetura concreta

1. O usuário `OWNER` acessa a área de colaboradores da arquitetura concreta.
2. O usuário adiciona um usuário cadastrado como `EDITOR`.
3. O sistema registra o colaborador.
4. O colaborador passa a poder editar versões, elementos, imagens e mapeamentos conforme as permissões do MVP.
5. O `OWNER` pode remover posteriormente um colaborador `EDITOR`.

#### FA07 — Anexar imagens à arquitetura concreta ou a seus elementos

1. Durante a edição de uma versão concreta ou de um elemento concreto, o usuário seleciona a opção para adicionar uma imagem.
2. O sistema valida o arquivo enviado.
3. O sistema armazena o arquivo e registra seus metadados.
4. A imagem passa a complementar a descrição textual do contexto correspondente.
5. A imagem permanece associada exclusivamente ao contexto em que foi anexada.

---

## Fluxo 05 — Criar e realizar uma avaliação de conformidade

### Objetivo

Permitir que um usuário avalie manualmente a conformidade de uma versão de arquitetura concreta em relação à versão da Arquitetura de Referência utilizada como sua base, registrando resultados, evidências e eventuais violações para os critérios de conformidade definidos na RA.

### Ator principal

Usuário autenticado responsável pela avaliação de conformidade.

### Pré-condições

- O usuário deve estar autenticado.
- Deve existir uma versão de arquitetura concreta.
- A versão concreta deve estar associada a uma versão de Arquitetura de Referência.
- A versão da RA deve possuir ao menos um critério de conformidade cadastrado.

### Fluxo principal

1. O usuário acessa uma versão de arquitetura concreta.
2. O usuário seleciona a opção para iniciar uma nova avaliação de conformidade.
3. O sistema identifica automaticamente a versão da Arquitetura de Referência utilizada como base pela versão concreta.
4. O sistema apresenta um resumo contendo:
   - arquitetura concreta e sua versão;
   - Arquitetura de Referência e sua versão;
   - quantidade de elementos concretos;
   - quantidade de elementos da RA;
   - mapeamentos existentes;
   - critérios de conformidade disponíveis.
5. O usuário confirma a criação da avaliação.
6. O sistema cria a avaliação com status `DRAFT`.
7. O usuário pode revisar os elementos, mapeamentos e critérios antes de iniciar a avaliação.
8. O usuário inicia a avaliação.
9. O sistema altera o status da avaliação para `IN_PROGRESS`.
10. O sistema apresenta os critérios de conformidade pertencentes à versão da RA.
11. Para cada critério, o sistema apresenta:
    - nome;
    - descrição;
    - elementos da RA associados ao critério, quando existirem;
    - elementos concretos mapeados aos elementos da RA relacionados, quando existirem.
12. O usuário analisa o critério e registra um resultado:
    - `CONFORMING`;
    - `NON_CONFORMING`;
    - `NOT_APPLICABLE`.
13. O usuário pode registrar observações sobre o resultado.
14. O usuário pode adicionar uma ou mais evidências que fundamentem a avaliação, podendo registrar descrição, URL externa opcional e imagens.
15. Caso o resultado seja `NON_CONFORMING`, o usuário pode registrar uma ou mais violações, podendo anexar imagens.
16. Quando aplicável, o usuário associa a violação:
    - aos elementos da RA envolvidos;
    - aos elementos da arquitetura concreta envolvidos.
17. O sistema registra o resultado do critério.
18. O usuário repete o processo para os demais critérios.
19. O usuário acessa o resumo da avaliação.
20. O sistema apresenta os resultados consolidados dos critérios avaliados.
21. O usuário seleciona a opção para finalizar a avaliação.
22. O sistema altera o status da avaliação para `COMPLETED`.
23. O sistema disponibiliza a visualização consolidada dos resultados e das violações.
24. A avaliação passa a aparecer entre os resultados associados à versão da Arquitetura de Referência e à versão da arquitetura concreta.

### Resultado

A avaliação de conformidade fica registrada com:

- a versão concreta avaliada;
- a versão da RA utilizada como base;
- os critérios considerados;
- o resultado de cada critério;
- as observações registradas;
- as evidências;
- as violações identificadas;
- os elementos envolvidos nas violações, quando aplicável;
- o status final da avaliação.

### Fluxos alternativos

#### FA01 — Critério associado a elementos da RA

1. O sistema identifica os elementos da RA relacionados ao critério.
2. O sistema apresenta esses elementos ao avaliador.
3. Quando existirem mapeamentos, o sistema também apresenta os elementos concretos correspondentes.
4. O avaliador utiliza essas informações como apoio para determinar manualmente o resultado.

#### FA02 — Critério aplicável à RA como um todo

1. O critério não possui elementos específicos da RA associados.
2. O sistema apresenta o critério como aplicável à versão da RA de maneira geral.
3. O avaliador analisa a arquitetura concreta considerando o critério globalmente.

#### FA03 — Resultado conforme

1. O usuário seleciona `CONFORMING`.
2. O sistema permite o registro de observações e evidências, incluindo imagens quando aplicável.
3. Nenhuma violação é registrada para o resultado.

#### FA04 — Resultado não conforme

1. O usuário seleciona `NON_CONFORMING`.
2. O usuário pode registrar observações e evidências, incluindo imagens quando aplicável.
3. O usuário pode registrar uma ou mais violações identificadas e anexar imagens a cada violação.
4. Para cada violação, quando aplicável, o usuário identifica os elementos da RA e da arquitetura concreta envolvidos.

#### FA05 — Critério não aplicável

1. O usuário seleciona `NOT_APPLICABLE`.
2. O usuário pode registrar uma observação explicando por que o critério não se aplica.
3. Nenhuma violação é registrada.

#### FA06 — Critério sem mapeamento correspondente

1. O critério está associado a um ou mais elementos da RA.
2. O sistema não encontra elementos concretos mapeados para algum desses elementos.
3. O sistema informa ao avaliador que não há mapeamento correspondente.
4. O avaliador decide manualmente o resultado do critério.

> A ausência de mapeamento não determina automaticamente uma não conformidade no MVP.

#### FA07 — Consultar avaliação em andamento

1. O usuário acessa uma avaliação com status `IN_PROGRESS`.
2. O sistema apresenta:
   - critérios já avaliados;
   - critérios ainda pendentes;
   - resultados registrados;
   - violações já identificadas.
3. O usuário continua a avaliação a partir dos critérios pendentes.

#### FA08 — Consultar avaliação concluída

1. O usuário acessa uma avaliação com status `COMPLETED`.
2. O sistema apresenta os resultados consolidados.
3. O usuário pode consultar individualmente os critérios, evidências e violações registrados.

---

## Fluxo 06 — Consultar uma Arquitetura de Referência e seus resultados consolidados

### Objetivo

Permitir que um usuário consulte uma Arquitetura de Referência, navegue entre suas versões e visualize, em um único ponto, seus elementos arquiteturais, avaliações por checklist, arquiteturas concretas derivadas e avaliações de conformidade.

### Ator principal

Usuário autenticado com acesso à Arquitetura de Referência.

### Pré-condições

- O usuário deve estar autenticado.
- A Arquitetura de Referência deve existir.
- O usuário deve possuir acesso à RA como `OWNER`, `EDITOR` ou por meio de sua visibilidade pública.

### Fluxo principal

1. O usuário acessa uma Arquitetura de Referência.
2. O sistema apresenta a visão geral da RA contendo:
   - nome;
   - visibilidade;
   - versões existentes;
   - versão atualmente selecionada.
3. O usuário seleciona a versão da RA que deseja consultar.
4. O sistema apresenta a descrição geral e as imagens da versão selecionada, quando existirem.
5. O sistema disponibiliza as áreas relacionadas àquela versão:
   - elementos arquiteturais;
   - avaliações por checklist;
   - arquiteturas concretas derivadas;
   - avaliações de conformidade.
6. O usuário pode acessar a área de elementos arquiteturais.
7. O sistema apresenta os elementos cadastrados para a versão, incluindo:
   - nome;
   - tipo;
   - descrição;
   - imagens associadas, quando existirem.
8. O usuário pode acessar a área de avaliações por checklist.
9. O sistema apresenta as avaliações associadas à versão da RA, indicando:
   - checklist utilizada;
   - versão da checklist;
   - status da avaliação;
   - quantidade de participantes;
   - progresso ou resultado, quando disponível.
10. O usuário pode selecionar uma avaliação para visualizar seus resultados detalhados.
11. O usuário pode acessar a área de arquiteturas concretas.
12. O sistema apresenta as versões de arquiteturas concretas baseadas na versão da RA selecionada.
13. Para cada versão concreta, o sistema pode apresentar:
   - arquitetura concreta;
   - versão;
   - quantidade de elementos;
   - quantidade de mapeamentos;
   - avaliações de conformidade associadas.
14. O usuário pode selecionar uma arquitetura concreta para consultar seus elementos e mapeamentos.
15. O usuário pode acessar a área de avaliações de conformidade.
16. O sistema apresenta as avaliações de conformidade relacionadas à versão da RA, indicando:
   - arquitetura concreta avaliada;
   - versão concreta;
   - status da avaliação;
   - resultados consolidados, quando disponíveis;
   - quantidade de violações identificadas.
17. O usuário pode selecionar uma avaliação de conformidade para visualizar seus critérios, resultados, evidências e violações.
18. O usuário pode retornar à visão geral da RA a qualquer momento.

### Resultado

O usuário obtém uma visão integrada da versão da Arquitetura de Referência, incluindo:

- sua descrição;
- seus elementos arquiteturais;
- suas avaliações por checklist;
- suas arquiteturas concretas derivadas;
- seus mapeamentos;
- suas avaliações de conformidade;
- os resultados e violações registrados.

### Fluxos alternativos

#### FA01 — Consultar outra versão da RA

1. O usuário seleciona outra versão disponível.
2. O sistema atualiza a visualização para refletir exclusivamente os dados associados à versão escolhida.
3. Elementos, avaliações, arquiteturas concretas e critérios passam a corresponder à nova versão selecionada.

#### FA02 — Versão sem avaliações por checklist

1. A versão da RA não possui avaliações por checklist.
2. O sistema apresenta um estado vazio informando que nenhuma avaliação foi realizada.
3. Caso o usuário seja o responsável pela RA, o sistema pode disponibilizar a opção para iniciar uma nova avaliação por checklist.

#### FA03 — Versão sem arquiteturas concretas

1. Nenhuma arquitetura concreta foi cadastrada com base na versão da RA.
2. O sistema informa que não existem instanciações cadastradas.
3. Caso o usuário seja o responsável pela RA, o sistema pode disponibilizar a opção para cadastrar uma arquitetura concreta.

#### FA04 — Versão sem avaliações de conformidade

1. Não existem avaliações de conformidade para as arquiteturas concretas relacionadas à versão.
2. O sistema apresenta um estado vazio.
3. O usuário pode acessar uma arquitetura concreta existente para iniciar uma avaliação de conformidade.

#### FA05 — Usuário não proprietário consultando RA pública

1. O usuário acessa uma Arquitetura de Referência pública criada por outro usuário.
2. O sistema permite consultar o conteúdo público da RA e suas versões.
3. O usuário não pode alterar a RA original.
4. Quando aplicável, o usuário pode utilizar uma versão pública da RA em uma nova avaliação ou como referência para as funcionalidades permitidas pela ferramenta.

#### FA06 — Consultar resultados de avaliação por checklist

1. O usuário seleciona uma avaliação por checklist concluída.
2. O sistema apresenta os resultados consolidados.
3. O usuário pode consultar:
   - questões;
   - respostas dos participantes;
   - comentários;
   - distribuição das respostas por questão, quando aplicável.

#### FA07 — Consultar resultados de conformidade

1. O usuário seleciona uma avaliação de conformidade concluída.
2. O sistema apresenta:
   - quantidade de critérios `CONFORMING`;
   - quantidade de critérios `NON_CONFORMING`;
   - quantidade de critérios `NOT_APPLICABLE`;
   - quantidade de violações identificadas.
3. O usuário pode acessar o detalhamento de cada critério.
4. O usuário pode consultar as evidências e violações associadas.

> Os resultados apresentados na visão geral da RA são derivados das avaliações, respostas, resultados de conformidade e violações armazenados. O MVP não mantém uma entidade separada de resultado consolidado.

---

## Fluxo 07 — Consultar e reutilizar artefatos públicos

### Objetivo

Permitir que um usuário autenticado consulte Arquiteturas de Referência e checklists públicos cadastrados por outros usuários e reutilize esses artefatos de acordo com as permissões definidas pela ferramenta.

### Ator principal

Usuário autenticado.

### Pré-condições

- O usuário deve estar autenticado.
- Deve existir ao menos um artefato público disponível no catálogo.

### Fluxo principal

1. O usuário acessa o catálogo de artefatos públicos.
2. O sistema permite consultar:
   - Arquiteturas de Referência públicas;
   - checklists públicas.
3. O usuário escolhe o tipo de artefato que deseja consultar.
4. O sistema apresenta os artefatos públicos disponíveis.
5. O usuário seleciona um artefato.
6. O sistema apresenta seus detalhes e versões disponíveis.
7. O usuário pode consultar o conteúdo permitido do artefato.
8. O sistema não permite que o usuário altere diretamente o artefato pertencente a outro usuário.
9. O usuário seleciona uma das ações de reutilização disponíveis para o tipo de artefato.

### Resultado

O usuário consegue consultar e reutilizar artefatos públicos sem modificar seus conteúdos originais.

### Fluxos alternativos

#### FA01 — Utilizar uma RA pública em uma avaliação por checklist

1. O usuário acessa uma Arquitetura de Referência pública.
2. O usuário seleciona a versão da RA que deseja utilizar.
3. O usuário seleciona a opção para criar uma avaliação por checklist.
4. O sistema inicia o fluxo de criação da avaliação utilizando a versão pública da RA selecionada.
5. O artefato original permanece inalterado.

#### FA02 — Utilizar uma checklist pública em uma avaliação

1. Durante a criação de uma avaliação por checklist, o usuário acessa as checklists disponíveis.
2. O sistema apresenta checklists próprias e públicas.
3. O usuário seleciona uma checklist pública.
4. O usuário seleciona a versão desejada.
5. A avaliação passa a utilizar aquela versão da checklist.
6. A checklist original permanece inalterada.

#### FA03 — Criar uma derivação de checklist pública

1. O usuário acessa uma checklist pública.
2. O usuário seleciona uma versão da checklist.
3. O usuário seleciona a opção para criar uma derivação.
4. O sistema informa que será criada uma nova checklist independente da original.
5. O usuário informa:
   - nome da nova checklist;
   - visibilidade;
   - informações complementares de origem, quando necessário.
6. O sistema cria uma nova checklist pertencente ao usuário.
7. A nova checklist mantém referência à versão que lhe deu origem.
8. O usuário pode editar e versionar a nova checklist sem alterar a checklist original.

#### FA04 — Consultar versões de uma RA pública

1. O usuário acessa uma RA pública.
2. O sistema apresenta suas versões disponíveis.
3. O usuário seleciona uma versão.
4. O sistema apresenta:
   - descrição geral;
   - elementos arquiteturais;
   - tipos dos elementos;
   - demais informações públicas disponíveis.
5. O usuário pode alternar entre as versões para consultar suas diferenças de conteúdo.

#### FA05 — Consultar versões de uma checklist pública

1. O usuário acessa uma checklist pública.
2. O sistema apresenta suas versões disponíveis.
3. O usuário seleciona uma versão.
4. O sistema apresenta:
   - seções;
   - questões;
   - tipos de resposta;
   - opções de resposta;
   - stakeholders;
   - origem da checklist.
5. O usuário pode utilizar a versão em uma avaliação ou criar uma derivação.

#### FA06 — Catálogo sem resultados

1. O usuário realiza uma consulta no catálogo.
2. Nenhum artefato público corresponde à consulta.
3. O sistema apresenta um estado vazio.
4. O usuário pode alterar sua consulta ou retornar à listagem geral.

---

## Fluxo 08 — Cadastro, autenticação e encerramento de sessão

### Objetivo

Permitir que uma pessoa crie uma conta na ferramenta, autentique-se utilizando e-mail e senha e encerre sua sessão quando desejar.

### Ator principal

Usuário.

### Pré-condições

Para cadastro:

- a pessoa não deve possuir uma conta cadastrada com o mesmo endereço de e-mail.

Para autenticação:

- o usuário deve possuir uma conta cadastrada.

### Fluxo principal — Cadastro

1. A pessoa acessa a página de cadastro.
2. O sistema solicita:
   - nome;
   - e-mail;
   - senha.
3. A pessoa informa os dados solicitados.
4. O sistema valida as informações fornecidas.
5. O sistema verifica se o endereço de e-mail já está associado a outra conta.
6. O sistema protege a senha utilizando mecanismo apropriado de hashing.
7. O sistema cria a conta do usuário.
8. O usuário é direcionado para a autenticação ou entra diretamente na aplicação, de acordo com a estratégia definida na implementação.

### Resultado do cadastro

Uma nova conta de usuário fica registrada no sistema.

### Fluxo principal — Autenticação

1. O usuário acessa a página de autenticação.
2. O sistema solicita:
   - e-mail;
   - senha.
3. O usuário informa suas credenciais.
4. O sistema verifica se as credenciais correspondem a uma conta cadastrada.
5. Quando as credenciais forem válidas, o sistema autentica o usuário.
6. O usuário é direcionado para a área principal da aplicação.

### Resultado da autenticação

O usuário passa a possuir uma sessão autenticada e pode acessar as funcionalidades permitidas pela ferramenta.

### Fluxo principal — Encerramento de sessão

1. O usuário autenticado seleciona a opção para encerrar sua sessão.
2. O sistema invalida a sessão ou credencial de autenticação utilizada.
3. O usuário é direcionado para a página pública ou para a página de autenticação.

### Resultado do encerramento

O usuário deixa de possuir acesso autenticado às funcionalidades protegidas.

### Fluxos alternativos

#### FA01 — E-mail já cadastrado

1. Durante o cadastro, o sistema identifica que o e-mail informado já pertence a uma conta.
2. O sistema não cria uma nova conta.
3. O sistema informa que o endereço já está cadastrado.
4. A pessoa pode retornar à autenticação ou informar outro endereço de e-mail.

#### FA02 — Credenciais inválidas

1. O usuário informa e-mail ou senha incorretos.
2. O sistema rejeita a autenticação.
3. O sistema apresenta uma mensagem indicando que as credenciais são inválidas.
4. O usuário pode tentar novamente.

#### FA03 — Acesso a funcionalidade protegida sem autenticação

1. Uma pessoa não autenticada tenta acessar uma funcionalidade restrita.
2. O sistema impede o acesso.
3. O sistema direciona a pessoa para a página de autenticação.

> Recuperação de senha, autenticação social, autenticação multifator e confirmação de e-mail não fazem parte do MVP.