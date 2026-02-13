"""Parser for the nested curly braces format used in 1C 7.7 metadata.

Format example:
    {"MainDataContDef","8665","10011","7120"}
    {"SbCnts",
        {"552","Аналоги","","Аналоги номенклатуры","84","8",
            {"Params",
                {"553","Каталог","","Каталог аналога","B","0","0","538"}}}}
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class BracketNode:
    """A node in the bracket tree.

    values: list of string values at this level
    children: list of child BracketNode objects
    """

    values: list[str] = field(default_factory=list)
    children: list[BracketNode] = field(default_factory=list)

    def __repr__(self) -> str:
        if not self.children:
            return f"BracketNode({self.values!r})"
        return f"BracketNode({self.values!r}, children={len(self.children)})"

    def first_value(self) -> str:
        """Return the first value or empty string."""
        return self.values[0] if self.values else ""

    def value_at(self, index: int, default: str = "") -> str:
        """Return value at index or default."""
        if 0 <= index < len(self.values):
            return self.values[index]
        return default

    def child_by_first_value(self, name: str) -> BracketNode | None:
        """Find a child node whose first value matches name."""
        for child in self.children:
            if child.values and child.values[0] == name:
                return child
        return None


def parse(text: str) -> BracketNode:
    """Parse bracket-formatted text into a tree of BracketNode objects.

    Returns the root node representing the outermost {} block.
    """
    parser = _Parser(text)
    return parser.parse_root()


class _Parser:
    """Internal stateful parser for bracket format."""

    def __init__(self, text: str) -> None:
        self.text = text
        self.pos = 0
        self.length = len(text)

    def parse_root(self) -> BracketNode:
        """Parse the root level - find the outermost {} and parse it."""
        self._skip_whitespace()
        if self.pos < self.length and self.text[self.pos] == "{":
            return self._parse_node()
        # If no opening brace, wrap everything in a root node
        root = BracketNode()
        while self.pos < self.length:
            self._skip_whitespace()
            if self.pos >= self.length:
                break
            if self.text[self.pos] == "{":
                root.children.append(self._parse_node())
            else:
                break
        return root

    def _parse_node(self) -> BracketNode:
        """Parse a single {...} block into a BracketNode."""
        assert self.text[self.pos] == "{"
        self.pos += 1  # skip '{'

        node = BracketNode()

        while self.pos < self.length:
            self._skip_whitespace()

            if self.pos >= self.length:
                break

            ch = self.text[self.pos]

            if ch == "}":
                self.pos += 1  # skip '}'
                return node

            if ch == ",":
                self.pos += 1  # skip ','
                continue

            if ch == "{":
                node.children.append(self._parse_node())
            elif ch == '"':
                node.values.append(self._parse_quoted_string())
            else:
                node.values.append(self._parse_unquoted_value())

        return node

    def _parse_quoted_string(self) -> str:
        """Parse a quoted string value, handling "" escaping."""
        assert self.text[self.pos] == '"'
        self.pos += 1  # skip opening quote

        result = []
        while self.pos < self.length:
            ch = self.text[self.pos]
            if ch == '"':
                # Check for escaped quote ""
                if self.pos + 1 < self.length and self.text[self.pos + 1] == '"':
                    result.append('"')
                    self.pos += 2
                else:
                    self.pos += 1  # skip closing quote
                    return "".join(result)
            else:
                result.append(ch)
                self.pos += 1

        return "".join(result)

    def _parse_unquoted_value(self) -> str:
        """Parse an unquoted value (until comma, brace, or whitespace)."""
        start = self.pos
        while self.pos < self.length:
            ch = self.text[self.pos]
            if ch in (",", "}", "{", "\r", "\n"):
                break
            self.pos += 1
        return self.text[start : self.pos].strip()

    def _skip_whitespace(self) -> None:
        """Skip whitespace characters."""
        while self.pos < self.length and self.text[self.pos] in (" ", "\t", "\r", "\n"):
            self.pos += 1
