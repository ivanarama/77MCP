"""Tests for the metadata parser module."""

import sys
import os

import pytest

sys.path.insert(0, "src")

from mcp_1c77.metadata import ConfigurationLoader, load_configuration

# Path to test file
TEST_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "1cv7.md")

# Skip all tests if test file is not available
pytestmark = pytest.mark.skipif(
    not os.path.exists(TEST_FILE),
    reason="Test file 1cv7.md not found",
)


@pytest.fixture
def loader():
    l = ConfigurationLoader()
    l.load(TEST_FILE)
    yield l
    l.close()


def test_load_configuration_basic():
    config = load_configuration(TEST_FILE)
    assert config.name != ""
    assert config.version != ""


def test_configuration_has_catalogs(loader):
    config = loader.config
    assert len(config.catalogs) > 0
    names = [c.name for c in config.catalogs]
    assert "Валюты" in names
    assert "Контрагенты" in names


def test_configuration_has_documents(loader):
    config = loader.config
    assert len(config.documents) > 0
    names = [d.name for d in config.documents]
    assert "БыстраяПродажа" in names


def test_configuration_has_registers(loader):
    config = loader.config
    assert len(config.registers) > 0


def test_configuration_has_enums(loader):
    config = loader.config
    assert len(config.enums) > 0
    # Check that enum values are parsed
    for e in config.enums:
        if e.name == "ВидыНоменклатуры":
            assert len(e.values) > 0
            value_names = [v.name for v in e.values]
            assert "Услуга" in value_names
            break
    else:
        pytest.fail("ВидыНоменклатуры enum not found")


def test_configuration_has_reports(loader):
    config = loader.config
    assert len(config.reports) > 0


def test_configuration_has_journals(loader):
    config = loader.config
    assert len(config.journals) > 0


def test_configuration_has_constants(loader):
    config = loader.config
    assert len(config.constants) > 0


def test_catalog_attributes(loader):
    config = loader.config
    for c in config.catalogs:
        if c.name == "Валюты":
            assert len(c.attributes) > 0
            attr_names = [a.name for a in c.attributes]
            assert "Курс" in attr_names
            break
    else:
        pytest.fail("Валюты catalog not found")


def test_document_head_and_table_fields(loader):
    config = loader.config
    for d in config.documents:
        if d.name == "БыстраяПродажа":
            assert len(d.head_attributes) > 0
            assert len(d.table_attributes) > 0
            head_names = [a.name for a in d.head_attributes]
            assert "Контрагент" in head_names
            break
    else:
        pytest.fail("БыстраяПродажа document not found")


def test_register_structure(loader):
    config = loader.config
    for r in config.registers:
        if r.name == "Банк":
            assert len(r.dimensions) > 0
            assert len(r.resources) > 0
            break
    else:
        pytest.fail("Банк register not found")


def test_get_module(loader):
    module = loader.get_module("Документ", "БыстраяПродажа")
    assert module is not None
    assert len(module) > 0
    # Module should contain 1C code
    assert "Процедура" in module or "Функция" in module or "Перем" in module


def test_get_module_catalog(loader):
    module = loader.get_module("Справочник", "Валюты")
    assert module is not None
    assert len(module) > 0


def test_get_module_not_found(loader):
    module = loader.get_module("Документ", "НесуществующийДокумент")
    assert module is None


def test_get_form(loader):
    form = loader.get_form("Документ", "БыстраяПродажа")
    assert form is not None
    assert "Dialogs" in form


def test_configuration_summary(loader):
    summary = loader.config.summary()
    assert "Конфигурация" in summary
    assert "Справочники" in summary
    assert "Документы" in summary
