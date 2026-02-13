"""MCP server for 1C:Enterprise 7.7 configuration metadata.

Provides LLM clients with access to metadata objects, attributes, modules,
and forms from 1Cv7.MD configuration files.

Usage:
    python -m mcp_1c77 --md-path C:\\path\\to\\1Cv7.MD
    MD_FILE_PATH=C:\\path\\to\\1Cv7.MD python -m mcp_1c77
"""

import argparse
import os
import sys

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


def main() -> None:
    """Run the MCP server with auto-loaded configuration."""
    parser = argparse.ArgumentParser(description="1C 7.7 Metadata MCP Server")
    parser.add_argument(
        "--md-path",
        default=os.environ.get("MD_FILE_PATH", ""),
        help="Path to 1Cv7.MD file (or set MD_FILE_PATH env var)",
    )
    args = parser.parse_args()

    md_path = args.md_path
    if not md_path:
        print("Error: specify --md-path or set MD_FILE_PATH environment variable", file=sys.stderr)
        sys.exit(1)

    # Auto-load configuration at startup
    try:
        tools.init(md_path)
        print(f"Loaded configuration: {md_path}", file=sys.stderr)
    except Exception as e:
        print(f"Error loading {md_path}: {e}", file=sys.stderr)
        sys.exit(1)

    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
