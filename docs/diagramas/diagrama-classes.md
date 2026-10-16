# Diagrama de Classes — v0.1

> Diagrama de classes inicial derivado do MER, dos requisitos e das regras de negócio.
>
> O objetivo deste modelo é representar as principais entidades de domínio, seus relacionamentos e tipos enumerados, sem definir ainda detalhes específicos de framework ou persistência.

```mermaid
classDiagram

    class User {
        +Id id
        +String name
        +String email
        -String passwordHash
    }

    class ReferenceArchitecture {
        +Id id
        +String name
        +Visibility visibility
    }

    class RAVersion {
        +Id id
        +String version
        +String descriptionMarkdown
        +DateTime createdAt
    }

    class ArchitecturalElementType {
        +Id id
        +String name
    }

    class RAElement {
        +Id id
        +String name
        +String descriptionMarkdown
    }

    class Checklist {
        +Id id
        +String name
        +String origin
        +Visibility visibility
    }

    class ChecklistVersion {
        +Id id
        +String version
        +DateTime createdAt
    }

    class ChecklistSection {
        +Id id
        +String name
        +Integer orderIndex
    }

    class Question {
        +Id id
        +String statement
        +ResponseType responseType
        +CommentMode commentMode
        +Integer orderIndex
    }

    class ResponseOption {
        +Id id
        +String label
        +Integer orderIndex
    }

    class StakeholderRole {
        +Id id
        +String name
        +String description
    }

    class ChecklistEvaluation {
        +Id id
        +EvaluationStatus status
        +DateTime createdAt
    }

    class EvaluationParticipant {
        +Id id
    }

    class Answer {
        +Id id
        +String textValue
        +String comment
    }

    class ConcreteArchitecture {
        +Id id
        +String name
    }

    class ConcreteArchitectureVersion {
        +Id id
        +String version
        +String descriptionMarkdown
        +DateTime createdAt
    }

    class ConcreteElement {
        +Id id
        +String name
        +String descriptionMarkdown
    }

    class ElementMapping {
        +Id id
    }

    class ConformanceCriterion {
        +Id id
        +String name
        +String description
    }

    class ConformanceEvaluation {
        +Id id
        +EvaluationStatus status
        +DateTime createdAt
    }

    class ConformanceResult {
        +Id id
        +ConformanceResultStatus status
        +String notes
    }

    class ConformanceEvidence {
        +Id id
        +String description
        +String externalUrl
    }

    class Violation {
        +Id id
        +String description
    }

    class Visibility {
        <<enumeration>>
        PRIVATE
        PUBLIC
    }

    class ResponseType {
        <<enumeration>>
        SINGLE_CHOICE
        TEXT
    }

    class CommentMode {
        <<enumeration>>
        NONE
        OPTIONAL
        REQUIRED
    }

    class EvaluationStatus {
        <<enumeration>>
        DRAFT
        IN_PROGRESS
        COMPLETED
    }

    class ConformanceResultStatus {
        <<enumeration>>
        CONFORMING
        NON_CONFORMING
        NOT_APPLICABLE
    }


    User "1" --> "0..*" ReferenceArchitecture : owns
    User "1" --> "0..*" Checklist : owns
    User "1" --> "0..*" ConcreteArchitecture : owns

    User "0..1" --> "0..*" ArchitecturalElementType : creates

    ReferenceArchitecture "1" *-- "1..*" RAVersion : versions
    RAVersion "1" *-- "0..*" RAElement : elements
    ArchitecturalElementType "1" --> "0..*" RAElement : classifies

    Checklist "1" *-- "1..*" ChecklistVersion : versions
    ChecklistVersion "0..1" --> "0..*" Checklist : originOf
    ChecklistVersion "1" *-- "0..*" ChecklistSection : sections
    ChecklistVersion "1" *-- "0..*" Question : questions
    ChecklistSection "0..1" --> "0..*" Question : groups

    Question "1" *-- "0..*" ResponseOption : options
    ChecklistVersion "1" *-- "0..*" StakeholderRole : roles
    Question "0..*" -- "0..*" StakeholderRole : targets

    RAVersion "1" --> "0..*" ChecklistEvaluation : evaluatedIn
    ChecklistVersion "1" --> "0..*" ChecklistEvaluation : usedIn
    User "1" --> "0..*" ChecklistEvaluation : creates

    ChecklistEvaluation "1" *-- "0..*" EvaluationParticipant : participants
    User "1" --> "0..*" EvaluationParticipant : participates
    EvaluationParticipant "0..*" -- "0..*" StakeholderRole : assumes
    EvaluationParticipant "1" *-- "0..*" Answer : answers
    Question "1" --> "0..*" Answer : answeredBy
    ResponseOption "0..1" --> "0..*" Answer : selectedIn

    ConcreteArchitecture "1" *-- "1..*" ConcreteArchitectureVersion : versions
    RAVersion "1" --> "0..*" ConcreteArchitectureVersion : basisFor
    ConcreteArchitectureVersion "1" *-- "0..*" ConcreteElement : elements
    ArchitecturalElementType "1" --> "0..*" ConcreteElement : classifies

    ConcreteElement "1" --> "0..*" ElementMapping : source
    RAElement "1" --> "0..*" ElementMapping : target

    RAVersion "1" *-- "0..*" ConformanceCriterion : criteria
    ConformanceCriterion "0..*" -- "0..*" RAElement : appliesTo

    ConcreteArchitectureVersion "1" --> "0..*" ConformanceEvaluation : evaluatedIn
    User "1" --> "0..*" ConformanceEvaluation : creates

    ConformanceEvaluation "1" *-- "0..*" ConformanceResult : results
    ConformanceCriterion "1" --> "0..*" ConformanceResult : criterion

    ConformanceResult "1" *-- "0..*" ConformanceEvidence : evidence
    ConformanceResult "1" *-- "0..*" Violation : violations

    Violation "0..*" -- "0..*" RAElement : involves
    Violation "0..*" -- "0..*" ConcreteElement : involves