"""OLE2 reader for 1C:Enterprise 7.7 configuration files (1Cv7.MD)."""

import zlib
from pathlib import Path

import olefile


def open_md_file(path: str | Path) -> olefile.OleFileIO:
    """Open a 1Cv7.MD file as an OLE2 container."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    ole = olefile.OleFileIO(str(path))
    return ole


def list_streams(ole: olefile.OleFileIO) -> list[str]:
    """List all stream paths in the OLE2 container."""
    return ["/".join(entry) for entry in ole.listdir()]


def read_stream_raw(ole: olefile.OleFileIO, name: str) -> bytes:
    """Read raw bytes from a stream."""
    return ole.openstream(name).read()


def read_stream_text(ole: olefile.OleFileIO, name: str) -> str:
    """Read a text stream, stripping the length header and decoding from Windows-1251.

    Text streams in 1Cv7.MD may have a header:
    - N bytes of 0xFF followed by (N+1) bytes of LE integer length, then text
    - Or start directly with '{' (no header)
    """
    data = read_stream_raw(ole, name)
    text_data = _strip_header(data)
    return text_data.decode("windows-1251", errors="replace")


def read_module_text(ole: olefile.OleFileIO, name: str) -> str:
    """Read a module text stream (raw deflate compressed, Windows-1251)."""
    data = read_stream_raw(ole, name)
    try:
        decompressed = zlib.decompress(data, -15)
        return decompressed.decode("windows-1251", errors="replace")
    except zlib.error:
        return data.decode("windows-1251", errors="replace")


def get_main_metadata_stream(ole: olefile.OleFileIO) -> str:
    """Read the main metadata stream containing object definitions."""
    return read_stream_text(ole, "Metadata/Main MetaData Stream")


def get_root_container(ole: olefile.OleFileIO) -> str:
    """Read the root Container.Contents stream."""
    return read_stream_text(ole, "Container.Contents")


def list_top_level_dirs(ole: olefile.OleFileIO) -> list[str]:
    """List unique top-level directory names in the OLE2 container."""
    dirs = set()
    for entry in ole.listdir():
        dirs.add(entry[0])
    return sorted(dirs)


def get_object_streams(ole: olefile.OleFileIO, container: str, object_id: str) -> dict[str, str]:
    """Get the stream paths for a specific object (document, subconto, report, etc.).

    Returns a dict mapping stream type to full path, e.g.:
    {
        "dialog": "Document/Document_Number1582/WorkBook/Dialog Stream",
        "module": "Document/Document_Number1582/WorkBook/MD Programm text",
    }
    """
    prefix = f"{container}/{container}_Number{object_id}"
    result = {}
    for entry in ole.listdir():
        path = "/".join(entry)
        if path.startswith(prefix):
            if "Dialog Stream" in path:
                result["dialog"] = path
            elif "MD Programm text" in path:
                result["module"] = path
            elif path.endswith("Container.Contents"):
                result["container"] = path
    return result


def find_global_module_stream(ole: olefile.OleFileIO) -> str | None:
    """Find the global module stream path in the OLE container.

    The global module is stored under 'TypedText' container, typically as
    'TypedText/ModuleText_Number1'. Searches all TypedText entries for
    streams containing 'ModuleText'.
    """
    for entry in ole.listdir():
        if entry[0] != "TypedText":
            continue
        path = "/".join(entry)
        if "ModuleText" in path:
            return path
    return None


def list_all_module_streams(ole: olefile.OleFileIO) -> list[dict[str, str]]:
    """List all module streams found in the OLE container.

    Returns a list of dicts with keys:
        path: full stream path
        kind: 'global' for TypedText entries, 'object' for per-object modules
        container: top-level container name (e.g. 'Document', 'Subconto', 'TypedText')
    """
    modules = []
    for entry in ole.listdir():
        path = "/".join(entry)
        if "MD Programm text" not in path and "ModuleText" not in path:
            continue
        if entry[0] == "TypedText":
            modules.append({"path": path, "kind": "global", "container": "TypedText"})
        elif "MD Programm text" in path:
            modules.append({"path": path, "kind": "object", "container": entry[0]})
    return modules


def _strip_header(data: bytes) -> bytes:
    """Strip the length header from a text stream.

    Header format: N bytes of 0xFF, then (N+1) bytes LE integer length.
    If the data starts with '{', there's no header.
    """
    if not data:
        return data

    if data[0] == 0x7B:  # '{' - no header
        return data

    # Count leading 0xFF bytes
    n_ff = 0
    while n_ff < len(data) and data[n_ff] == 0xFF:
        n_ff += 1

    if n_ff == 0:
        return data

    # Length is stored in (n_ff + 1) bytes after the 0xFF bytes
    len_bytes = n_ff + 1
    header_size = n_ff + len_bytes

    if header_size > len(data):
        return data

    return data[header_size:]
