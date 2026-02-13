"""Pydantic models for 1C:Enterprise 7.7 configuration metadata."""

from __future__ import annotations

from pydantic import BaseModel, Field


class Attribute(BaseModel):
    """A field/attribute of a metadata object."""

    id: str = ""
    name: str = ""
    synonym: str = ""
    comment: str = ""
    type: str = ""  # B=Reference, S=String, N=Number, D=Date, E=Enum, O=Document
    length: int = 0
    precision: int = 0
    ref_type_id: str = ""  # ID of referenced type (for B/E/O types)
    periodic: bool = False
    group: bool = False


class EnumValue(BaseModel):
    """A value in an enumeration."""

    id: str = ""
    name: str = ""
    synonym: str = ""
    comment: str = ""
    order: str = ""


class TabularSection(BaseModel):
    """A tabular section (table part) of a document."""

    attributes: list[Attribute] = Field(default_factory=list)


class FormInfo(BaseModel):
    """Form reference info."""

    id: str = ""
    name: str = ""
    synonym: str = ""
    comment: str = ""


class Constant(BaseModel):
    """A configuration constant."""

    id: str = ""
    name: str = ""
    synonym: str = ""
    comment: str = ""
    type: str = ""
    length: int = 0
    precision: int = 0
    ref_type_id: str = ""


class Catalog(BaseModel):
    """A catalog (справочник) metadata object."""

    id: str = ""
    name: str = ""
    synonym: str = ""
    comment: str = ""
    code_length: str = ""
    code_type: str = ""
    has_owner: bool = False
    owner_id: str = ""
    attributes: list[Attribute] = Field(default_factory=list)
    forms: list[FormInfo] = Field(default_factory=list)


class Document(BaseModel):
    """A document metadata object."""

    id: str = ""
    name: str = ""
    synonym: str = ""
    comment: str = ""
    number_length: str = ""
    head_attributes: list[Attribute] = Field(default_factory=list)
    table_attributes: list[Attribute] = Field(default_factory=list)
    forms: list[FormInfo] = Field(default_factory=list)
    journal_id: str = ""


class Register(BaseModel):
    """A register (регистр) metadata object."""

    id: str = ""
    name: str = ""
    synonym: str = ""
    comment: str = ""
    dimensions: list[Attribute] = Field(default_factory=list)  # Props
    resources: list[Attribute] = Field(default_factory=list)  # Figures
    attributes: list[Attribute] = Field(default_factory=list)  # Flds


class Enum(BaseModel):
    """An enumeration (перечисление) metadata object."""

    id: str = ""
    name: str = ""
    synonym: str = ""
    comment: str = ""
    values: list[EnumValue] = Field(default_factory=list)


class Report(BaseModel):
    """A report or data processor."""

    id: str = ""
    name: str = ""
    synonym: str = ""
    comment: str = ""


class DocumentJournal(BaseModel):
    """A document journal (журнал документов)."""

    id: str = ""
    name: str = ""
    synonym: str = ""
    comment: str = ""
    forms: list[FormInfo] = Field(default_factory=list)


class ChartOfAccounts(BaseModel):
    """Chart of accounts (план счетов) configuration."""

    id: str = ""
    forms: list[FormInfo] = Field(default_factory=list)


class CalcVar(BaseModel):
    """A calculation variable (внешний отчет/обработка)."""

    id: str = ""
    name: str = ""
    synonym: str = ""
    comment: str = ""


class Configuration(BaseModel):
    """Root configuration object representing a parsed 1Cv7.MD file."""

    name: str = ""
    version: str = ""
    file_path: str = ""
    constants: list[Constant] = Field(default_factory=list)
    catalogs: list[Catalog] = Field(default_factory=list)
    documents: list[Document] = Field(default_factory=list)
    registers: list[Register] = Field(default_factory=list)
    enums: list[Enum] = Field(default_factory=list)
    reports: list[Report] = Field(default_factory=list)
    journals: list[DocumentJournal] = Field(default_factory=list)
    chart_of_accounts: ChartOfAccounts | None = None
    calc_vars: list[CalcVar] = Field(default_factory=list)

    def summary(self) -> str:
        """Return a human-readable summary of the configuration."""
        lines = [
            f"Конфигурация: {self.name}",
            f"Версия: {self.version}",
            f"Файл: {self.file_path}",
            "",
            f"Константы: {len(self.constants)}",
            f"Справочники: {len(self.catalogs)}",
            f"Документы: {len(self.documents)}",
            f"Регистры: {len(self.registers)}",
            f"Перечисления: {len(self.enums)}",
            f"Отчёты/Обработки: {len(self.reports)}",
            f"Журналы: {len(self.journals)}",
            f"Виды расчётов: {len(self.calc_vars)}",
        ]
        return "\n".join(lines)
