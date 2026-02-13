"""MCP tool definitions for 1C 7.7 metadata server."""

from __future__ import annotations

from .metadata import ConfigurationLoader

# Global loader instance shared across all tool calls
_loader = ConfigurationLoader()
_md_path: str = ""


def get_loader() -> ConfigurationLoader:
    """Get the global ConfigurationLoader instance."""
    return _loader


def init(md_path: str) -> None:
    """Initialize the loader with a configuration file. Called at server startup."""
    global _md_path
    _md_path = md_path
    _loader.load(md_path)


def reload_configuration(path: str = "") -> str:
    """Reload the current configuration or load a different file.

    Args:
        path: Path to 1Cv7.MD file. If empty, reloads the current file.

    Returns:
        Configuration summary text.
    """
    global _md_path
    target = path if path else _md_path
    if not target:
        return "Путь к файлу не указан."
    _md_path = target
    config = _loader.load(target)
    return config.summary()


def list_objects(object_type: str = "") -> str:
    """List metadata objects, optionally filtered by type."""
    config = _loader.config
    lines = []

    type_lower = object_type.lower() if object_type else ""

    def _should_include(type_name: str) -> bool:
        if not type_lower:
            return True
        return type_lower in type_name.lower()

    if _should_include("справочник") or _should_include("catalog"):
        if config.catalogs:
            lines.append(f"## Справочники ({len(config.catalogs)})")
            for obj in config.catalogs:
                comment = f" — {obj.comment}" if obj.comment else ""
                lines.append(f"  - {obj.name}{comment}")
            lines.append("")

    if _should_include("документ") or _should_include("document"):
        if config.documents:
            lines.append(f"## Документы ({len(config.documents)})")
            for obj in config.documents:
                comment = f" — {obj.comment}" if obj.comment else ""
                lines.append(f"  - {obj.name}{comment}")
            lines.append("")

    if _should_include("регистр") or _should_include("register"):
        if config.registers:
            lines.append(f"## Регистры ({len(config.registers)})")
            for obj in config.registers:
                comment = f" — {obj.comment}" if obj.comment else ""
                lines.append(f"  - {obj.name}{comment}")
            lines.append("")

    if _should_include("перечисление") or _should_include("enum"):
        if config.enums:
            lines.append(f"## Перечисления ({len(config.enums)})")
            for obj in config.enums:
                comment = f" — {obj.comment}" if obj.comment else ""
                lines.append(f"  - {obj.name}{comment}")
            lines.append("")

    if _should_include("отчёт") or _should_include("отчет") or _should_include("обработка") or _should_include("report"):
        if config.reports:
            lines.append(f"## Отчёты/Обработки ({len(config.reports)})")
            for obj in config.reports:
                comment = f" — {obj.comment}" if obj.comment else ""
                lines.append(f"  - {obj.name}{comment}")
            lines.append("")

    if _should_include("журнал") or _should_include("journal"):
        if config.journals:
            lines.append(f"## Журналы ({len(config.journals)})")
            for obj in config.journals:
                comment = f" — {obj.comment}" if obj.comment else ""
                lines.append(f"  - {obj.name}{comment}")
            lines.append("")

    if _should_include("константа") or _should_include("constant"):
        if config.constants:
            lines.append(f"## Константы ({len(config.constants)})")
            for obj in config.constants:
                comment = f" — {obj.comment}" if obj.comment else ""
                lines.append(f"  - {obj.name}: {obj.type}{comment}")
            lines.append("")

    if _should_include("видрасчёта") or _should_include("видрасчета") or _should_include("calcvar"):
        if config.calc_vars:
            lines.append(f"## Виды расчётов ({len(config.calc_vars)})")
            for obj in config.calc_vars:
                comment = f" — {obj.comment}" if obj.comment else ""
                lines.append(f"  - {obj.name}{comment}")
            lines.append("")

    if not lines:
        return f"Объекты типа '{object_type}' не найдены."

    return "\n".join(lines)


def get_object(object_type: str, name: str) -> str:
    """Get detailed information about a metadata object."""
    config = _loader.config
    type_lower = object_type.lower()

    if type_lower in ("справочник", "catalog"):
        for obj in config.catalogs:
            if obj.name == name:
                return _format_catalog(obj)

    elif type_lower in ("документ", "document"):
        for obj in config.documents:
            if obj.name == name:
                return _format_document(obj)

    elif type_lower in ("регистр", "register"):
        for obj in config.registers:
            if obj.name == name:
                return _format_register(obj)

    elif type_lower in ("перечисление", "enum"):
        for obj in config.enums:
            if obj.name == name:
                return _format_enum(obj)

    elif type_lower in ("отчёт", "отчет", "обработка", "report"):
        for obj in config.reports:
            if obj.name == name:
                return _format_report(obj)

    elif type_lower in ("журнал", "journal"):
        for obj in config.journals:
            if obj.name == name:
                return _format_journal(obj)

    elif type_lower in ("константа", "constant"):
        for obj in config.constants:
            if obj.name == name:
                return _format_constant(obj)

    return f"Объект '{object_type}.{name}' не найден."


def get_module(object_type: str, name: str) -> str:
    """Get the module source code of a metadata object."""
    module = _loader.get_module(object_type, name)
    if module is None:
        return f"Модуль объекта '{object_type}.{name}' не найден."
    return module


def get_form(object_type: str, name: str) -> str:
    """Get the form definition of a metadata object."""
    form = _loader.get_form(object_type, name)
    if form is None:
        return f"Форма объекта '{object_type}.{name}' не найдена."
    return form


def search(query: str) -> str:
    """Search across all metadata objects by name, synonym, or comment."""
    config = _loader.config
    query_lower = query.lower()
    results = []

    for obj in config.constants:
        if _matches(obj, query_lower):
            results.append(f"Константа: {obj.name} — {obj.comment}")

    for obj in config.catalogs:
        if _matches(obj, query_lower):
            results.append(f"Справочник: {obj.name} — {obj.comment}")

    for obj in config.documents:
        if _matches(obj, query_lower):
            results.append(f"Документ: {obj.name} — {obj.comment}")

    for obj in config.registers:
        if _matches(obj, query_lower):
            results.append(f"Регистр: {obj.name} — {obj.comment}")

    for obj in config.enums:
        if _matches(obj, query_lower):
            results.append(f"Перечисление: {obj.name} — {obj.comment}")
        for val in obj.values:
            if query_lower in val.name.lower() or query_lower in val.comment.lower():
                results.append(f"Перечисление.Значение: {obj.name}.{val.name} — {val.comment}")

    for obj in config.reports:
        if _matches(obj, query_lower):
            results.append(f"Отчёт: {obj.name} — {obj.comment}")

    for obj in config.journals:
        if _matches(obj, query_lower):
            results.append(f"Журнал: {obj.name} — {obj.comment}")

    for obj in config.calc_vars:
        if _matches(obj, query_lower):
            results.append(f"ВидРасчёта: {obj.name} — {obj.comment}")

    if not results:
        return f"По запросу '{query}' ничего не найдено."

    return f"Найдено {len(results)} результатов:\n" + "\n".join(results)


def get_configuration_info() -> str:
    """Get general information about the loaded configuration."""
    return _loader.config.summary()


# --- Formatting helpers ---


def _format_catalog(obj) -> str:
    lines = [
        f"# Справочник: {obj.name}",
        f"ID: {obj.id}",
    ]
    if obj.comment:
        lines.append(f"Комментарий: {obj.comment}")
    if obj.synonym:
        lines.append(f"Синоним: {obj.synonym}")

    if obj.attributes:
        lines.append(f"\n## Реквизиты ({len(obj.attributes)})")
        for a in obj.attributes:
            ref = f" -> {a.ref_type_id}" if a.ref_type_id and a.type in ("Справочник", "Перечисление", "Документ") else ""
            lines.append(f"  - {a.name}: {a.type}({a.length}.{a.precision}){ref}")
            if a.comment:
                lines.append(f"    {a.comment}")

    if obj.forms:
        lines.append(f"\n## Формы ({len(obj.forms)})")
        for f in obj.forms:
            lines.append(f"  - {f.name} (id={f.id})")

    return "\n".join(lines)


def _format_document(obj) -> str:
    lines = [
        f"# Документ: {obj.name}",
        f"ID: {obj.id}",
    ]
    if obj.comment:
        lines.append(f"Комментарий: {obj.comment}")
    if obj.number_length:
        lines.append(f"Длина номера: {obj.number_length}")

    if obj.head_attributes:
        lines.append(f"\n## Реквизиты шапки ({len(obj.head_attributes)})")
        for a in obj.head_attributes:
            ref = f" -> {a.ref_type_id}" if a.ref_type_id and a.type in ("Справочник", "Перечисление", "Документ") else ""
            lines.append(f"  - {a.name}: {a.type}({a.length}.{a.precision}){ref}")
            if a.comment:
                lines.append(f"    {a.comment}")

    if obj.table_attributes:
        lines.append(f"\n## Табличная часть ({len(obj.table_attributes)})")
        for a in obj.table_attributes:
            ref = f" -> {a.ref_type_id}" if a.ref_type_id and a.type in ("Справочник", "Перечисление", "Документ") else ""
            lines.append(f"  - {a.name}: {a.type}({a.length}.{a.precision}){ref}")
            if a.comment:
                lines.append(f"    {a.comment}")

    return "\n".join(lines)


def _format_register(obj) -> str:
    lines = [
        f"# Регистр: {obj.name}",
        f"ID: {obj.id}",
    ]
    if obj.comment:
        lines.append(f"Комментарий: {obj.comment}")
    if obj.synonym:
        lines.append(f"Синоним: {obj.synonym}")

    if obj.dimensions:
        lines.append(f"\n## Измерения ({len(obj.dimensions)})")
        for a in obj.dimensions:
            lines.append(f"  - {a.name}: {a.type}({a.length}.{a.precision})")

    if obj.resources:
        lines.append(f"\n## Ресурсы ({len(obj.resources)})")
        for a in obj.resources:
            lines.append(f"  - {a.name}: {a.type}({a.length}.{a.precision})")

    if obj.attributes:
        lines.append(f"\n## Реквизиты ({len(obj.attributes)})")
        for a in obj.attributes:
            lines.append(f"  - {a.name}: {a.type}({a.length}.{a.precision})")

    return "\n".join(lines)


def _format_enum(obj) -> str:
    lines = [
        f"# Перечисление: {obj.name}",
        f"ID: {obj.id}",
    ]
    if obj.comment:
        lines.append(f"Комментарий: {obj.comment}")
    if obj.synonym:
        lines.append(f"Синоним: {obj.synonym}")

    if obj.values:
        lines.append(f"\n## Значения ({len(obj.values)})")
        for v in obj.values:
            comment = f" — {v.comment}" if v.comment else ""
            lines.append(f"  - {v.name}{comment}")

    return "\n".join(lines)


def _format_report(obj) -> str:
    lines = [
        f"# Отчёт/Обработка: {obj.name}",
        f"ID: {obj.id}",
    ]
    if obj.comment:
        lines.append(f"Комментарий: {obj.comment}")
    if obj.synonym:
        lines.append(f"Синоним: {obj.synonym}")
    return "\n".join(lines)


def _format_journal(obj) -> str:
    lines = [
        f"# Журнал: {obj.name}",
        f"ID: {obj.id}",
    ]
    if obj.comment:
        lines.append(f"Комментарий: {obj.comment}")

    if obj.forms:
        lines.append(f"\n## Формы ({len(obj.forms)})")
        for f in obj.forms:
            lines.append(f"  - {f.name} (id={f.id})")

    return "\n".join(lines)


def _format_constant(obj) -> str:
    lines = [
        f"# Константа: {obj.name}",
        f"ID: {obj.id}",
        f"Тип: {obj.type}({obj.length}.{obj.precision})",
    ]
    if obj.comment:
        lines.append(f"Комментарий: {obj.comment}")
    if obj.synonym:
        lines.append(f"Синоним: {obj.synonym}")
    return "\n".join(lines)


def _matches(obj, query_lower: str) -> bool:
    """Check if object matches search query."""
    name = getattr(obj, "name", "").lower()
    synonym = getattr(obj, "synonym", "").lower()
    comment = getattr(obj, "comment", "").lower()
    return query_lower in name or query_lower in synonym or query_lower in comment
