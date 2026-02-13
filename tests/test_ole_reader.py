"""Tests for the OLE2 reader module."""

import sys
import os

import pytest

sys.path.insert(0, "src")

from mcp_1c77 import ole_reader

# Path to test file
TEST_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "1cv7.md")

# Skip all tests if test file is not available
pytestmark = pytest.mark.skipif(
    not os.path.exists(TEST_FILE),
    reason="Test file 1cv7.md not found",
)


def test_open_md_file():
    ole = ole_reader.open_md_file(TEST_FILE)
    assert ole is not None
    ole.close()


def test_open_md_file_not_found():
    with pytest.raises(FileNotFoundError):
        ole_reader.open_md_file("nonexistent_file.md")


def test_list_streams():
    ole = ole_reader.open_md_file(TEST_FILE)
    streams = ole_reader.list_streams(ole)
    assert len(streams) > 0
    assert "Container.Contents" in streams
    assert "Metadata/Main MetaData Stream" in streams
    ole.close()


def test_list_top_level_dirs():
    ole = ole_reader.open_md_file(TEST_FILE)
    dirs = ole_reader.list_top_level_dirs(ole)
    assert "Metadata" in dirs
    assert "Document" in dirs
    assert "Subconto" in dirs
    assert "Report" in dirs
    ole.close()


def test_read_stream_text():
    ole = ole_reader.open_md_file(TEST_FILE)
    text = ole_reader.read_stream_text(ole, "Container.Contents")
    assert text.startswith('{"Container.Contents"')
    ole.close()


def test_get_main_metadata_stream():
    ole = ole_reader.open_md_file(TEST_FILE)
    text = ole_reader.get_main_metadata_stream(ole)
    assert "MainDataContDef" in text
    assert "SbCnts" in text
    assert "Documents" in text
    ole.close()


def test_read_module_text():
    ole = ole_reader.open_md_file(TEST_FILE)
    # Read a document module (deflate compressed)
    streams = ole_reader.list_streams(ole)
    module_streams = [s for s in streams if "MD Programm text" in s and "Document" in s]
    assert len(module_streams) > 0
    module_text = ole_reader.read_module_text(ole, module_streams[0])
    # Module text should contain 1C code
    assert len(module_text) > 0
    ole.close()


def test_get_root_container():
    ole = ole_reader.open_md_file(TEST_FILE)
    text = ole_reader.get_root_container(ole)
    assert "MetaDataContainer" in text
    assert "DocumentContainer" in text
    ole.close()


def test_get_object_streams():
    ole = ole_reader.open_md_file(TEST_FILE)
    # Test with a known document
    streams = ole_reader.get_object_streams(ole, "Document", "1582")
    assert "dialog" in streams or "module" in streams
    ole.close()


def test_strip_header_no_header():
    data = b'{"test"}'
    assert ole_reader._strip_header(data) == data


def test_strip_header_single_ff():
    # 1 × 0xFF + 2 bytes length + data
    text = b'hello'
    length = len(text)
    header = b'\xff' + length.to_bytes(2, 'little')
    data = header + text
    assert ole_reader._strip_header(data) == text


def test_strip_header_triple_ff():
    # 3 × 0xFF + 4 bytes length + data
    text = b'hello world'
    length = len(text)
    header = b'\xff\xff\xff' + length.to_bytes(4, 'little')
    data = header + text
    assert ole_reader._strip_header(data) == text


def test_strip_header_empty():
    assert ole_reader._strip_header(b'') == b''
