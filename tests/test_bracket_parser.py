"""Tests for the bracket format parser."""

import sys
sys.path.insert(0, "src")

from mcp_1c77.bracket_parser import BracketNode, parse


def test_simple_values():
    result = parse('{"Hello","World"}')
    assert result.values == ["Hello", "World"]
    assert result.children == []


def test_nested_node():
    result = parse('{"Root",{"Child1","Child2"}}')
    assert result.values == ["Root"]
    assert len(result.children) == 1
    assert result.children[0].values == ["Child1", "Child2"]


def test_multiple_children():
    result = parse('{"Root",{"A","1"},{"B","2"}}')
    assert result.values == ["Root"]
    assert len(result.children) == 2
    assert result.children[0].values == ["A", "1"]
    assert result.children[1].values == ["B", "2"]


def test_deeply_nested():
    result = parse('{"L1",{"L2",{"L3","deep"}}}')
    assert result.values == ["L1"]
    child = result.children[0]
    assert child.values == ["L2"]
    grandchild = child.children[0]
    assert grandchild.values == ["L3", "deep"]


def test_empty_values():
    result = parse('{"","",""}')
    assert result.values == ["", "", ""]


def test_escaped_quotes():
    result = parse('{"He said ""hello""","OK"}')
    assert result.values == ['He said "hello"', "OK"]


def test_newlines_in_data():
    result = parse('{"Key",\n"Value",\n{"Child"}}')
    assert result.values == ["Key", "Value"]
    assert len(result.children) == 1
    assert result.children[0].values == ["Child"]


def test_first_value():
    node = BracketNode(values=["Hello", "World"])
    assert node.first_value() == "Hello"


def test_first_value_empty():
    node = BracketNode()
    assert node.first_value() == ""


def test_value_at():
    node = BracketNode(values=["a", "b", "c"])
    assert node.value_at(0) == "a"
    assert node.value_at(1) == "b"
    assert node.value_at(2) == "c"
    assert node.value_at(3) == ""
    assert node.value_at(3, "default") == "default"


def test_child_by_first_value():
    node = BracketNode(children=[
        BracketNode(values=["Params", "data"]),
        BracketNode(values=["Form", "data2"]),
    ])
    params = node.child_by_first_value("Params")
    assert params is not None
    assert params.values == ["Params", "data"]

    missing = node.child_by_first_value("Missing")
    assert missing is None


def test_empty_braces():
    result = parse("{}")
    assert result.values == []
    assert result.children == []


def test_mixed_values_and_children():
    result = parse('{"ID","Name","Comment",{"SubNode1"},{"SubNode2"}}')
    assert result.values == ["ID", "Name", "Comment"]
    assert len(result.children) == 2
    assert result.children[0].values == ["SubNode1"]
    assert result.children[1].values == ["SubNode2"]


def test_real_metadata_format():
    """Test with a realistic 1C 7.7 metadata snippet."""
    text = '{"SbCnts",\n{"14","Валюты","","","0","3","1","1","1","10",\n{"Params",\n{"17","Курс","","","N","10","4"}},\n{"Form",\n{"19","ФормаСписка","",""}}}}'
    result = parse(text)
    assert result.first_value() == "SbCnts"
    assert len(result.children) == 1
    catalog = result.children[0]
    assert catalog.value_at(0) == "14"
    assert catalog.value_at(1) == "Валюты"
    params = catalog.child_by_first_value("Params")
    assert params is not None
    assert len(params.children) == 1
    form = catalog.child_by_first_value("Form")
    assert form is not None
