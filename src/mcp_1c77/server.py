"""MCP server for 1C:Enterprise 7.7 configuration metadata.

Provides LLM clients with access to metadata objects, attributes, modules,
and forms from 1Cv7.MD configuration files.
"""

from mcp.server.fastmcp import FastMCP

from . import tools

mcp = FastMCP("1c77-metadata")


@mcp.tool()
def reload_configuration(path: str = "") -> str:
    """Перезагрузить конфигурацию (или загрузить другой файл).

    Args:
        path: Путь к файлу 1Cv7.MD. Если пустой — перезагружает текущий файл.
    """
    return tools.reload_configuration(path)


@mcp.tool()
def list_objects(object_type: str = "") -> str:
    """Список объектов метаданных конфигурации.

    Args:
        object_type: Тип объекта для фильтрации (Справочник, Документ, Регистр,
                     Перечисление, Отчёт, Журнал, Константа, ВидРасчёта).
                     Пустая строка — показать все типы.
    """
    return tools.list_objects(object_type)


@mcp.tool()
def get_object(object_type: str, name: str) -> str:
    """Детальная информация об объекте метаданных (реквизиты, табличные части).

    Args:
        object_type: Тип объекта (Справочник, Документ, Регистр, Перечисление, и т.д.)
        name: Имя объекта.
    """
    return tools.get_object(object_type, name)


@mcp.tool()
def get_module(object_type: str, name: str) -> str:
    """Получить исходный код модуля объекта метаданных.

    Args:
        object_type: Тип объекта (Справочник, Документ, Отчёт, ВидРасчёта).
        name: Имя объекта.
    """
    return tools.get_module(object_type, name)


@mcp.tool()
def get_form(object_type: str, name: str) -> str:
    """Получить описание формы объекта (элементы управления).

    Args:
        object_type: Тип объекта (Справочник, Документ, Отчёт, ВидРасчёта).
        name: Имя объекта.
    """
    return tools.get_form(object_type, name)


@mcp.tool()
def search(query: str) -> str:
    """Поиск по объектам метаданных (по имени, синониму, комментарию).

    Args:
        query: Строка поиска.
    """
    return tools.search(query)


@mcp.tool()
def get_configuration_info() -> str:
    """Общая информация о загруженной конфигурации."""
    return tools.get_configuration_info()


@mcp.tool()
def validate_field_path(object_type: str, name: str, path: str) -> str:
    """Проверить валидность пути обращения к реквизиту объекта.

    Args:
        object_type: Тип (Документ, Справочник, Регистр, Перечисление)
        name: Имя объекта
        path: Путь к реквизиту (напр. "Сумма", "Товар.Артикул", "Партия.ГТД.Наименование")
    """
    return tools.validate_field_path(object_type, name, path)


@mcp.tool()
def validate_query(query_text: str) -> str:
    """Проверить все пути обращений к реквизитам в тексте запроса/кода 1С 7.7.

    Args:
        query_text: Полный текст запроса или фрагмент кода
    """
    return tools.validate_query(query_text)


@mcp.tool()
def search_field(field_name: str, object_type: str = "") -> str:
    """Найти все объекты, содержащие реквизит с данным именем (обратный поиск).

    Args:
        field_name: Имя реквизита для поиска
        object_type: Опционально: Документ, Справочник, Регистр
    """
    return tools.search_field(field_name, object_type)


@mcp.tool()
def get_objects_batch(object_type: str, names: list[str]) -> str:
    """Пакетное получение метаданных нескольких объектов за один вызов.

    Args:
        object_type: Тип объектов (Документ, Справочник, и т.д.)
        names: Список имён объектов
    """
    return tools.get_objects_batch(object_type, names)
