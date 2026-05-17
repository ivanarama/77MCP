# -*- coding: utf-8 -*-
"""Tests for module range slicing and search context features."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from mcp_1c77.tools import (
    _find_lines_in_text,
    _slice_module,
    search_in_modules,
)

# ---------------------------------------------------------------------------
# _slice_module
# ---------------------------------------------------------------------------

_SHORT_TEXT = "\n".join(f"line {i}" for i in range(1, 21))  # 20 lines
# Make each line long enough so 3000 lines exceeds 50K chars
_LONG_TEXT = "\n".join(
    f"line {i}: {'x' * 70}" for i in range(1, 3001)
)  # ~3000 * 80 = 240K chars


class TestSliceModuleExplicitRange:
    def test_returns_specified_lines(self):
        result = _slice_module(_SHORT_TEXT, 10, 15, "Test")
        assert "10" in result.split("\n")[0]  # header mentions range
        assert "line 10" in result
        assert "line 15" in result
        assert "line 9" not in result
        assert "line 16" not in result

    def test_start_only_goes_to_end(self):
        result = _slice_module(_SHORT_TEXT, 18, 0, "Test")
        assert "18" in result.split("\n")[0]
        assert "line 18" in result
        assert "line 20" in result

    def test_start_past_end_returns_error(self):
        result = _slice_module(_SHORT_TEXT, 999, 0, "Test")
        assert "20" in result  # total lines
        assert "999" in result

    def test_single_line(self):
        result = _slice_module(_SHORT_TEXT, 5, 5, "Test")
        assert "line 5" in result


class TestSliceModuleAutoTruncate:
    def test_short_module_returned_in_full(self):
        result = _slice_module(_SHORT_TEXT, 0, 0, "Test")
        assert "line 1" in result
        assert "line 20" in result

    def test_long_module_truncated(self):
        result = _slice_module(_LONG_TEXT, 0, 0, "GlobalModule")
        assert "1500" in result.split("\n")[0]
        assert "line 1:" in result
        assert "line 1500:" in result
        assert "line 1501:" not in result.split("\n")[0]

    def test_truncated_has_footer_hint(self):
        result = _slice_module(_LONG_TEXT, 0, 0, "GlobalModule")
        assert "start_line" in result
        assert "end_line" in result


# ---------------------------------------------------------------------------
# _find_lines_in_text
# ---------------------------------------------------------------------------

_SAMPLE_MODULE = """\
Var gTrade;
Var gVersion;

Procedure Start()
    gTrade = 1;
EndProcedure

Function GetVersion()
    Return gVersion;
EndFunction
"""


class TestFindLinesInText:
    def test_basic_search(self):
        results = _find_lines_in_text(_SAMPLE_MODULE, "gtrade")
        assert len(results) == 2
        assert results[0][0] == 1  # line number
        assert results[1][0] == 5

    def test_with_context(self):
        results = _find_lines_in_text(_SAMPLE_MODULE, "gtrade", context_lines=1)
        # first match at line 1: context = lines 1-2
        assert len(results[0][2]) == 2
        # second match at line 5: context = lines 4-6
        assert len(results[1][2]) == 3

    def test_max_results(self):
        results = _find_lines_in_text(_SAMPLE_MODULE, "gtrade", max_results=1)
        assert len(results) == 1

    def test_no_match(self):
        results = _find_lines_in_text(_SAMPLE_MODULE, "nonexistent")
        assert len(results) == 0

    def test_context_no_overflow(self):
        """Context at file boundaries doesn't go negative."""
        results = _find_lines_in_text(_SAMPLE_MODULE, "gtrade", context_lines=5)
        # first match at line 1: ctx_start clamped to 0
        assert results[0][2][0][0] == 1  # first context line is line 1


# ---------------------------------------------------------------------------
# search_in_modules (integration with mocked loader)
# ---------------------------------------------------------------------------


class TestSearchInModules:
    @patch("mcp_1c77.tools._loader")
    def test_context_lines(self, mock_loader):
        mock_loader.is_loaded = True
        mock_loader.iter_module_entries.return_value = [
            ("GlobalModule", _SAMPLE_MODULE),
        ]
        result = search_in_modules("gtrade", context_lines=1)
        assert "GlobalModule:1:" in result
        assert "GlobalModule:2:" in result
        assert "--" in result

    @patch("mcp_1c77.tools._loader")
    def test_limit(self, mock_loader):
        mock_loader.is_loaded = True
        mock_loader.iter_module_entries.return_value = [
            ("GlobalModule", _SAMPLE_MODULE),
        ]
        result = search_in_modules("gtrade", limit=1)
        assert "1 " in result  # "Найдено 1 совпадений"
        assert "limit" in result.lower() or "лимит" in result.lower()

    @patch("mcp_1c77.tools._loader")
    def test_no_context_backward_compat(self, mock_loader):
        mock_loader.is_loaded = True
        mock_loader.iter_module_entries.return_value = [
            ("GlobalModule", _SAMPLE_MODULE),
        ]
        result = search_in_modules("gtrade")
        assert "--" not in result
        assert "2 " in result  # "Найдено 2 совпадений"
