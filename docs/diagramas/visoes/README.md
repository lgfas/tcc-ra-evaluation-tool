# Diagramas de classes — visões menores (v0.2)

Esta pasta separa o diagrama de classes do TCC em quatro visões para facilitar leitura e validação:

1. `01-ra-colaboracao.md` — usuários, colaboração, RA, versões, elementos, tipos e imagens.
2. `02-checklist-avaliacao.md` — checklist, questões, stakeholders, participantes, respostas e avaliação por checklist.
3. `03-instanciacao-mapeamentos.md` — arquitetura concreta, colaboração, versões, elementos, RA base, imagens e mapeamentos.
4. `04-conformidade.md` — critérios, avaliação de conformidade, resultados, evidências, violações e imagens.

Os arquivos `.md` são a fonte oficial dessas visões e contêm diretamente os blocos Mermaid renderizados pelo GitHub.

## Regras que o desenho sozinho não garante

- Cada `ReferenceArchitecture` e `ConcreteArchitecture` possui exatamente um membro `OWNER`; demais colaboradores são `EDITOR`. Essa restrição é garantida pelas regras de negócio/aplicação.
- `ImageAttachment` pode aparecer associado a diferentes tipos de contexto nos diagramas, mas cada imagem individual pertence a apenas um contexto, conforme `RN-IMG-01`.
- Os mapeamentos entre `ConcreteElement` e `RAElement` são muitos-para-muitos por meio de `ElementMapping`.
- A ausência de mapeamento não determina não conformidade automaticamente.

## Representação visual

As próprias visões Mermaid são a fonte da documentação. Exportações em PNG ou SVG podem ser geradas posteriormente para uso em slides, relatórios ou na monografia, evitando manter imagens duplicadas e potencialmente desatualizadas no repositório.
