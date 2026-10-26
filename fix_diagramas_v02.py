#!/usr/bin/env python3
from pathlib import Path

ROOT = Path.cwd()

def must_replace(text: str, old: str, new: str, label: str) -> str:
    if old not in text:
        raise RuntimeError(f"Trecho não encontrado para {label}. O arquivo pode ter mudado.")
    return text.replace(old, new, 1)

def update(path_str: str, transform):
    path = ROOT / path_str
    text = path.read_text(encoding="utf-8")
    new_text = transform(text)
    path.write_text(new_text, encoding="utf-8")
    print(f"Atualizado: {path_str}")

def fix_class_diagram(s: str) -> str:
    old = """    Violation "0..*" -- "0..*" RAElement : involves
    Violation "0..*" -- "0..*" ConcreteElement : involves

## Observações adicionadas na v0.2"""
    new = """    Violation "0..*" -- "0..*" RAElement : involves
    Violation "0..*" -- "0..*" ConcreteElement : involves
```

## Observações adicionadas na v0.2"""
    return must_replace(s, old, new, "fechamento do bloco Mermaid em diagrama-classes.md")

def fix_readme(s: str) -> str:
    old = """Os arquivos `.mmd` contêm apenas o bloco Mermaid; os `.md` estão prontos para documentação Markdown.

## Regras que o desenho sozinho não garante"""
    new = """Os arquivos `.md` são a fonte oficial dessas visões e contêm diretamente os blocos Mermaid renderizados pelo GitHub.

## Regras que o desenho sozinho não garante"""
    s = must_replace(s, old, new, "referência aos arquivos .mmd")

    old2 = """## Previews

Os arquivos `*-preview.png` são representações equivalentes geradas apenas para inspeção visual da estrutura. Eles não substituem o Mermaid como fonte da documentação.
"""
    new2 = """## Representação visual

As próprias visões Mermaid são a fonte da documentação. Exportações em PNG ou SVG podem ser geradas posteriormente para uso em slides, relatórios ou na monografia, evitando manter imagens duplicadas e potencialmente desatualizadas no repositório.
"""
    return must_replace(s, old2, new2, "seção de previews")

def fix_instantiation_view(s: str) -> str:
    old = """    ConcreteArchitecture "1" *-- "1..*" ConcreteArchitectureVersion : versions
    RAVersion "1" --> "0..*" ConcreteArchitectureVersion : basisFor

    ConcreteArchitectureVersion "1" *-- "0..*" ConcreteElement : elements"""
    new = """    ConcreteArchitecture "1" *-- "1..*" ConcreteArchitectureVersion : versions
    RAVersion "1" --> "0..*" ConcreteArchitectureVersion : basisFor
    RAVersion "1" *-- "0..*" RAElement : elements

    ConcreteArchitectureVersion "1" *-- "0..*" ConcreteElement : elements"""
    return must_replace(s, old, new, "relação RAVersion -> RAElement na visão de instanciação")

def fix_conformance_view(s: str) -> str:
    old = """    RAVersion "1" *-- "0..*" ConformanceCriterion : criteria
    ConformanceCriterion "0..*" -- "0..*" RAElement : appliesTo

    ConcreteArchitectureVersion "1" --> "0..*" ConformanceEvaluation : evaluatedIn
    User "1" --> "0..*" ConformanceEvaluation : creates"""
    new = """    RAVersion "1" *-- "0..*" RAElement : elements
    RAVersion "1" *-- "0..*" ConformanceCriterion : criteria
    ConformanceCriterion "0..*" -- "0..*" RAElement : appliesTo

    ConcreteArchitectureVersion "1" *-- "0..*" ConcreteElement : elements
    ConcreteArchitectureVersion "1" --> "0..*" ConformanceEvaluation : evaluatedIn
    User "1" --> "0..*" ConformanceEvaluation : creates"""
    s = must_replace(s, old, new, "relações de contexto na visão de conformidade")

    old2 = """    ConformanceResult "1" *-- "0..*" ConformanceEvidence : evidence
    ConformanceEvidence "1" *-- "0..*" ImageAttachment : images

    ConformanceResult "1" *-- "0..*" Violation : violations"""
    new2 = """    ConformanceResult "1" *-- "0..*" ConformanceEvidence : evidence
    ConformanceEvidence "1" *-- "0..*" ImageAttachment : images
    User "1" --> "0..*" ImageAttachment : uploads

    ConformanceResult "1" *-- "0..*" Violation : violations"""
    return must_replace(s, old2, new2, "relação User -> ImageAttachment na visão de conformidade")

update("docs/diagramas/diagrama-classes.md", fix_class_diagram)
update("docs/diagramas/visoes/README.md", fix_readme)
update("docs/diagramas/visoes/03-instanciacao-mapeamentos.md", fix_instantiation_view)
update("docs/diagramas/visoes/04-conformidade.md", fix_conformance_view)

print("\nConcluído. Revise com:")
print("  git diff -- docs/diagramas")
