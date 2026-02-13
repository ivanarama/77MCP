"""High-level metadata parser for 1C:Enterprise 7.7 configuration files.

Parses the Main MetaData Stream from 1Cv7.MD and builds a Configuration model.
"""

from __future__ import annotations

from pathlib import Path

import olefile

from . import ole_reader
from .bracket_parser import BracketNode, parse
from .models import (
    Attribute,
    CalcVar,
    Catalog,
    ChartOfAccounts,
    Configuration,
    Constant,
    Document,
    DocumentJournal,
    Enum,
    EnumValue,
    FormInfo,
    Register,
    Report,
)

# Type code to human-readable type name mapping
TYPE_CODES = {
    "S": "Строка",
    "N": "Число",
    "D": "Дата",
    "B": "Справочник",
    "E": "Перечисление",
    "O": "Документ",
    "P": "ПланСчетов",
    "U": "Неопределенный",
    "L": "Логический",
}

# Object type name mapping (Russian to English for API)
OBJECT_TYPE_MAP = {
    "Справочник": "catalogs",
    "Документ": "documents",
    "Регистр": "registers",
    "Перечисление": "enums",
    "Отчёт": "reports",
    "Обработка": "reports",
    "Журнал": "journals",
    "Константа": "constants",
    "ВидРасчёта": "calc_vars",
}


class ConfigurationLoader:
    """Loads and caches a 1C 7.7 configuration from a 1Cv7.MD file."""

    def __init__(self) -> None:
        self._config: Configuration | None = None
        self._ole: olefile.OleFileIO | None = None
        self._file_path: str = ""

    @property
    def config(self) -> Configuration | None:
        return self._config

    @property
    def is_loaded(self) -> bool:
        return self._config is not None

    def load(self, path: str) -> Configuration:
        """Load configuration from file."""
        self.close()
        self._file_path = str(Path(path).resolve())
        self._ole = ole_reader.open_md_file(path)
        metadata_text = ole_reader.get_main_metadata_stream(self._ole)
        root = parse(metadata_text)
        self._config = _parse_configuration(root, self._file_path)
        return self._config

    def close(self) -> None:
        """Close the OLE file if open."""
        if self._ole is not None:
            self._ole.close()
            self._ole = None
        self._config = None

    def get_module(self, obj_type: str, obj_name: str) -> str | None:
        """Get the module text for an object."""
        if self._ole is None or self._config is None:
            return None

        obj_id = self._find_object_id(obj_type, obj_name)
        if obj_id is None:
            return None

        container = _type_to_container(obj_type)
        if container is None:
            return None

        streams = ole_reader.get_object_streams(self._ole, container, obj_id)
        if "module" not in streams:
            return None

        try:
            return ole_reader.read_module_text(self._ole, streams["module"])
        except Exception:
            return None

    def get_form(self, obj_type: str, obj_name: str) -> str | None:
        """Get the form definition (Dialog Stream) for an object."""
        if self._ole is None or self._config is None:
            return None

        obj_id = self._find_object_id(obj_type, obj_name)
        if obj_id is None:
            return None

        container = _type_to_container(obj_type)
        if container is None:
            return None

        streams = ole_reader.get_object_streams(self._ole, container, obj_id)
        if "dialog" not in streams:
            return None

        try:
            return ole_reader.read_stream_text(self._ole, streams["dialog"])
        except Exception:
            return None

    def _find_object_id(self, obj_type: str, obj_name: str) -> str | None:
        """Find object ID by type and name."""
        if self._config is None:
            return None

        objects = self._get_objects_by_type(obj_type)
        for obj in objects:
            if obj.name == obj_name:
                return obj.id
        return None

    def _get_objects_by_type(self, obj_type: str) -> list:
        """Get list of objects by type name."""
        if self._config is None:
            return []

        type_lower = obj_type.lower()
        type_map = {
            "справочник": self._config.catalogs,
            "документ": self._config.documents,
            "регистр": self._config.registers,
            "перечисление": self._config.enums,
            "отчёт": self._config.reports,
            "отчет": self._config.reports,
            "обработка": self._config.reports,
            "журнал": self._config.journals,
            "константа": self._config.constants,
            "видрасчёта": self._config.calc_vars,
            "видрасчета": self._config.calc_vars,
            "catalog": self._config.catalogs,
            "document": self._config.documents,
            "register": self._config.registers,
            "enum": self._config.enums,
            "report": self._config.reports,
            "journal": self._config.journals,
            "constant": self._config.constants,
            "calcvar": self._config.calc_vars,
        }
        return type_map.get(type_lower, [])


def load_configuration(path: str) -> Configuration:
    """Load and parse a 1Cv7.MD configuration file.

    This is a convenience function that creates a temporary loader.
    For repeated access (modules, forms), use ConfigurationLoader directly.
    """
    loader = ConfigurationLoader()
    config = loader.load(path)
    loader.close()
    return config


def _parse_configuration(root: BracketNode, file_path: str) -> Configuration:
    """Parse the root bracket tree into a Configuration model."""
    config = Configuration(file_path=file_path)

    # Parse TaskItem for config name and version
    task_item = root.child_by_first_value("TaskItem")
    if task_item and task_item.children:
        info = task_item.children[0]
        config.name = info.value_at(1)
        config.version = info.value_at(2)

    # Parse Constants
    consts_node = root.child_by_first_value("Consts")
    if consts_node:
        config.constants = _parse_constants(consts_node)

    # Parse Catalogs (SbCnts)
    sbcnts_node = root.child_by_first_value("SbCnts")
    if sbcnts_node:
        config.catalogs = _parse_catalogs(sbcnts_node)

    # Parse Documents
    docs_node = root.child_by_first_value("Documents")
    if docs_node:
        config.documents = _parse_documents(docs_node)

    # Parse Registers
    regs_node = root.child_by_first_value("Registers")
    if regs_node:
        config.registers = _parse_registers(regs_node)

    # Parse Enums
    enums_node = root.child_by_first_value("EnumList")
    if enums_node:
        config.enums = _parse_enums(enums_node)

    # Parse Reports
    reports_node = root.child_by_first_value("ReportList")
    if reports_node:
        config.reports = _parse_reports(reports_node)

    # Parse Document Journals
    journals_node = root.child_by_first_value("Journalisters")
    if journals_node:
        config.journals = _parse_journals(journals_node)

    # Parse CalcVars
    calcvars_node = root.child_by_first_value("CalcVars")
    if calcvars_node:
        config.calc_vars = _parse_calcvars(calcvars_node)

    # Parse Chart of Accounts (Buh)
    buh_node = root.child_by_first_value("Buh")
    if buh_node:
        config.chart_of_accounts = _parse_chart_of_accounts(buh_node)

    return config


def _parse_constants(node: BracketNode) -> list[Constant]:
    """Parse the Consts section."""
    constants = []
    for child in node.children:
        if len(child.values) >= 7:
            constants.append(Constant(
                id=child.value_at(0),
                name=child.value_at(1),
                synonym=child.value_at(2),
                comment=child.value_at(3),
                type=TYPE_CODES.get(child.value_at(4), child.value_at(4)),
                length=_safe_int(child.value_at(5)),
                precision=_safe_int(child.value_at(6)),
                ref_type_id=child.value_at(7),
            ))
    return constants


def _parse_catalogs(node: BracketNode) -> list[Catalog]:
    """Parse the SbCnts (catalogs/subconto) section."""
    catalogs = []
    for child in node.children:
        if len(child.values) < 3:
            continue
        catalog = Catalog(
            id=child.value_at(0),
            name=child.value_at(1),
            synonym=child.value_at(2),
            comment=child.value_at(3),
            code_length=child.value_at(4),
        )

        # Parse Params (attributes)
        params_node = child.child_by_first_value("Params")
        if params_node:
            catalog.attributes = _parse_catalog_attributes(params_node)

        # Parse Form references
        form_node = child.child_by_first_value("Form")
        if form_node:
            catalog.forms = _parse_forms(form_node)

        catalogs.append(catalog)
    return catalogs


def _parse_catalog_attributes(node: BracketNode) -> list[Attribute]:
    """Parse catalog attributes from a Params node."""
    attrs = []
    for child in node.children:
        if len(child.values) >= 7:
            attrs.append(Attribute(
                id=child.value_at(0),
                name=child.value_at(1),
                synonym=child.value_at(2),
                comment=child.value_at(3),
                type=TYPE_CODES.get(child.value_at(4), child.value_at(4)),
                length=_safe_int(child.value_at(5)),
                precision=_safe_int(child.value_at(6)),
                ref_type_id=child.value_at(7),
                periodic=child.value_at(8) == "1" if len(child.values) > 8 else False,
            ))
    return attrs


def _parse_documents(node: BracketNode) -> list[Document]:
    """Parse the Documents section."""
    documents = []
    for child in node.children:
        if len(child.values) < 3:
            continue
        doc = Document(
            id=child.value_at(0),
            name=child.value_at(1),
            synonym=child.value_at(2),
            comment=child.value_at(3),
            number_length=child.value_at(4),
            journal_id=child.value_at(8),
        )

        # Parse Head Fields
        head_node = child.child_by_first_value("Head Fields")
        if head_node:
            doc.head_attributes = _parse_document_attributes(head_node)

        # Parse Table Fields
        table_node = child.child_by_first_value("Table Fields")
        if table_node:
            doc.table_attributes = _parse_document_attributes(table_node)

        documents.append(doc)
    return documents


def _parse_document_attributes(node: BracketNode) -> list[Attribute]:
    """Parse document attributes from a Head Fields or Table Fields node."""
    attrs = []
    for child in node.children:
        if len(child.values) >= 6:
            attrs.append(Attribute(
                id=child.value_at(0),
                name=child.value_at(1),
                synonym=child.value_at(2),
                comment=child.value_at(3),
                type=TYPE_CODES.get(child.value_at(4), child.value_at(4)),
                length=_safe_int(child.value_at(5)),
                precision=_safe_int(child.value_at(6)),
                ref_type_id=child.value_at(7),
            ))
    return attrs


def _parse_registers(node: BracketNode) -> list[Register]:
    """Parse the Registers section."""
    registers = []
    for child in node.children:
        if len(child.values) < 3:
            continue
        reg = Register(
            id=child.value_at(0),
            name=child.value_at(1),
            synonym=child.value_at(2),
            comment=child.value_at(3),
        )

        # Parse Props (dimensions)
        props_node = child.child_by_first_value("Props")
        if props_node:
            reg.dimensions = _parse_register_fields(props_node)

        # Parse Figures (resources)
        figures_node = child.child_by_first_value("Figures")
        if figures_node:
            reg.resources = _parse_register_fields(figures_node)

        # Parse Flds (attributes)
        flds_node = child.child_by_first_value("Flds")
        if flds_node:
            reg.attributes = _parse_register_fields(flds_node)

        registers.append(reg)
    return registers


def _parse_register_fields(node: BracketNode) -> list[Attribute]:
    """Parse register dimensions, resources, or fields."""
    attrs = []
    for child in node.children:
        if len(child.values) >= 6:
            attrs.append(Attribute(
                id=child.value_at(0),
                name=child.value_at(1),
                synonym=child.value_at(2),
                comment=child.value_at(3),
                type=TYPE_CODES.get(child.value_at(4), child.value_at(4)),
                length=_safe_int(child.value_at(5)),
                precision=_safe_int(child.value_at(6)),
                ref_type_id=child.value_at(7),
            ))
    return attrs


def _parse_enums(node: BracketNode) -> list[Enum]:
    """Parse the EnumList section."""
    enums = []
    for child in node.children:
        if len(child.values) < 3:
            continue
        enum = Enum(
            id=child.value_at(0),
            name=child.value_at(1),
            synonym=child.value_at(2),
            comment=child.value_at(3),
        )

        # Parse EnumVal children
        enum_val_node = child.child_by_first_value("EnumVal")
        if enum_val_node:
            for val_child in enum_val_node.children:
                if len(val_child.values) >= 2:
                    enum.values.append(EnumValue(
                        id=val_child.value_at(0),
                        name=val_child.value_at(1),
                        synonym=val_child.value_at(2),
                        comment=val_child.value_at(3),
                        order=val_child.value_at(4),
                    ))

        enums.append(enum)
    return enums


def _parse_reports(node: BracketNode) -> list[Report]:
    """Parse the ReportList section."""
    reports = []
    for child in node.children:
        if len(child.values) < 2:
            continue
        reports.append(Report(
            id=child.value_at(0),
            name=child.value_at(1),
            synonym=child.value_at(2),
            comment=child.value_at(3),
        ))
    return reports


def _parse_journals(node: BracketNode) -> list[DocumentJournal]:
    """Parse the Journalisters section."""
    journals = []
    for child in node.children:
        if len(child.values) < 3:
            continue
        journal = DocumentJournal(
            id=child.value_at(0),
            name=child.value_at(1),
            synonym=child.value_at(2),
            comment=child.value_at(3),
        )

        form_node = child.child_by_first_value("Form")
        if form_node:
            journal.forms = _parse_forms(form_node)

        journals.append(journal)
    return journals


def _parse_calcvars(node: BracketNode) -> list[CalcVar]:
    """Parse the CalcVars section."""
    calc_vars = []
    for child in node.children:
        if len(child.values) < 2:
            continue
        calc_vars.append(CalcVar(
            id=child.value_at(0),
            name=child.value_at(1),
            synonym=child.value_at(2),
            comment=child.value_at(3),
        ))
    return calc_vars


def _parse_chart_of_accounts(node: BracketNode) -> ChartOfAccounts:
    """Parse the Buh section."""
    chart = ChartOfAccounts()
    if node.children:
        buh_data = node.children[0]
        chart.id = buh_data.value_at(0)
        for form_child in buh_data.children:
            if form_child.first_value() == "Form":
                chart.forms.extend(_parse_forms(form_child))
    return chart


def _parse_forms(node: BracketNode) -> list[FormInfo]:
    """Parse form references from a Form node."""
    forms = []
    for child in node.children:
        if len(child.values) >= 2:
            forms.append(FormInfo(
                id=child.value_at(0),
                name=child.value_at(1),
                synonym=child.value_at(2),
                comment=child.value_at(3),
            ))
    return forms


def _type_to_container(obj_type: str) -> str | None:
    """Map object type name to OLE2 container directory."""
    type_lower = obj_type.lower()
    container_map = {
        "справочник": "Subconto",
        "документ": "Document",
        "отчёт": "Report",
        "отчет": "Report",
        "обработка": "Report",
        "видрасчёта": "CalcVar",
        "видрасчета": "CalcVar",
        "catalog": "Subconto",
        "document": "Document",
        "report": "Report",
        "calcvar": "CalcVar",
    }
    return container_map.get(type_lower)


def _safe_int(value: str, default: int = 0) -> int:
    """Convert string to int, returning default on failure."""
    try:
        return int(value)
    except (ValueError, TypeError):
        return default
