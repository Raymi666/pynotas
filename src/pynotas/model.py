"""Contrato serializable entre análisis, selección y render (sin objetos AST)."""
from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class Resource:
    qualified_name: str
    binding: str
    alias: str | None
    purpose: str
    access_name: str = ""


@dataclass(frozen=True)
class Expression:
    code: str
    label: str
    line: int
    end_line: int
    children: tuple["Expression", ...] = ()


@dataclass(frozen=True)
class Section:
    label: str
    blocks: tuple["Block", ...] = ()


@dataclass(frozen=True)
class Block:
    id: str
    kind: str
    title: str
    code: str
    line: int
    end_line: int
    explanation: str
    reads: tuple[str, ...] = ()
    writes: tuple[str, ...] = ()
    body: tuple["Block", ...] = ()
    alternative: tuple["Block", ...] = ()
    expression: Expression | None = None
    summaries: tuple[str, ...] = ()
    resources: tuple[Resource, ...] = ()
    result: str = ""
    topics: tuple[str, ...] = ()
    sections: tuple[Section, ...] = ()
    column: int = 0
    end_column: int = 0


@dataclass(frozen=True)
class ReadingStep:
    """One source instruction (or clause header), in reading order, never a trace."""
    title: str
    code: str
    line: int
    end_line: int
    explanations: tuple[str, ...]
    scope: tuple[str, ...] = ()
    kind: str = "instruction"
    brief: str = ""
    aside: str = ""


@dataclass(frozen=True)
class CaseContext:
    title: str
    idea: str
    facts: tuple[str, ...] = ()
    route: tuple[str, ...] = ()
    sources: tuple[str, ...] = ()


@dataclass(frozen=True)
class TeachingStage:
    title: str
    kind: str
    steps: tuple[ReadingStep, ...]
    details: tuple[str, ...] = ()
    summary: str = ""
    tip: str = ""


@dataclass(frozen=True)
class CapturedFigure:
    """A raster image already published by this cell; never a recomputation."""
    mime: str
    data: str
    width: int
    height: int


@dataclass(frozen=True)
class PedagogicalModel:
    source: str
    blocks: tuple[Block, ...]
    objective: str
    level: str
    notes: tuple[str, ...] = ()
    schema_version: str = "0.11"
    context: str = "auto"
    theories: tuple = ()
    steps: tuple[ReadingStep, ...] = ()
    case: CaseContext | None = None
    stages: tuple[TeachingStage, ...] = ()
    figures: tuple[CapturedFigure, ...] = ()
    capture_notes: tuple[str, ...] = ()

    def to_dict(self):
        return asdict(self)


@dataclass(frozen=True)
class Representation:
    format: str
    title: str
    reason: str
    learn: str
    practice: str
    apply: str
    check: str = ""
    lesson_key: str = ""


def is_preparation(model):
    """Only pure preparation cells receive a grouped, non-sequential view."""
    return (bool(model.blocks)
            and all(b.kind in {"import", "setup"} for b in model.blocks)
            and 0 < sum(len(b.resources) for b in model.blocks) <= 12
            and sum(b.kind == "setup" for b in model.blocks) <= 3)
