"""HTML bundle creator — scan, stage, rewrite paths, and zip."""

from __future__ import annotations

import os
import re
import shutil
import tempfile
import zipfile
from html.parser import HTMLParser
from pathlib import Path

# Schemes / prefixes to skip when scanning for local file refs.
_SKIP_PREFIXES = ("http://", "https://", "data:", "#", "mailto:", "tel:", "javascript:")

# HTML attributes that reference external files.
_REF_ATTRS = {"href", "src"}


class _RefScanner(HTMLParser):
    """Extract local file references from an HTML document."""

    def __init__(self):
        super().__init__()
        self.refs: list[str] = []

    def handle_starttag(self, tag, attrs):
        for attr, value in attrs:
            if attr in _REF_ATTRS and value:
                self._maybe_add(value)

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)

    def _maybe_add(self, value: str):
        stripped = value.strip()
        if not stripped:
            return
        if any(stripped.lower().startswith(p) for p in _SKIP_PREFIXES):
            return
        self.refs.append(stripped)


_CSS_URL_RE = re.compile(r'url\(\s*["\']?([^"\')\s]+)["\']?\s*\)')


def scan_html(html_path: Path) -> list[tuple[str, Path]]:
    """Parse one HTML file and return ``(raw_ref, resolved_path)`` pairs.

    Only references that resolve to existing local files are returned.
    Symlinks that resolve outside the entry file's directory are skipped
    to prevent symlink traversal attacks.
    """
    text = html_path.read_text(errors="replace")

    scanner = _RefScanner()
    scanner.feed(text)

    # Also pick up CSS url() references embedded in <style> blocks.
    for match in _CSS_URL_RE.finditer(text):
        raw = match.group(1).strip()
        if raw and not any(raw.lower().startswith(p) for p in _SKIP_PREFIXES):
            scanner.refs.append(raw)

    results: list[tuple[str, Path]] = []
    base_dir = html_path.parent
    for raw in scanner.refs:
        target = base_dir / raw
        # Reject symlinks whose real path differs from the resolved path
        # (i.e. the link points somewhere else on the filesystem).
        if target.is_symlink():
            real = target.resolve()
            # Allow symlinks within the same directory tree only.
            try:
                real.relative_to(base_dir.resolve())
            except ValueError:
                continue
        resolved = target.resolve()
        if resolved.is_file():
            results.append((raw, resolved))
    return results


def _collect_all_refs(entry_html: Path) -> dict[Path, list[tuple[str, Path]]]:
    """Recursively scan the entry HTML and all linked HTML files.

    Returns a dict mapping each scanned HTML file to its ref list.
    Uses a visited set to prevent infinite loops.
    """
    visited: set[Path] = set()
    result: dict[Path, list[tuple[str, Path]]] = {}
    queue = [entry_html.resolve()]

    while queue:
        current = queue.pop()
        if current in visited:
            continue
        visited.add(current)

        refs = scan_html(current)
        result[current] = refs

        # Queue any linked HTML files for recursive scanning.
        for _raw, resolved in refs:
            if resolved.suffix.lower() in {".html", ".htm"} and resolved not in visited:
                queue.append(resolved)

    return result


def _build_staging_dir(entry_html: Path, all_refs: dict[Path, list[tuple[str, Path]]]) -> Path:
    """Copy files into a temp staging directory and rewrite paths in HTML."""
    staging = Path(tempfile.mkdtemp(prefix="tinygo_bundle_"))
    entry_resolved = entry_html.resolve()
    entry_dir = entry_resolved.parent

    # Track where each resolved source file ends up in staging.
    placed: dict[Path, Path] = {}
    used_names: set[str] = set()

    def _relative_to_entry(p: Path) -> Path | None:
        """Return relative path from entry dir, or None if outside."""
        try:
            return p.relative_to(entry_dir)
        except ValueError:
            return None

    def _place_file(resolved: Path) -> Path:
        """Determine the staging destination for a resolved source file."""
        if resolved in placed:
            return placed[resolved]

        rel = _relative_to_entry(resolved)
        if rel is not None:
            # Preserve relative structure.
            dest = staging / rel
        else:
            # Absolute / external path — flatten into staging root with collision avoidance.
            name = resolved.name
            candidate = name
            counter = 1
            while candidate in used_names:
                stem = resolved.stem
                candidate = f"{stem}_{counter}{resolved.suffix}"
                counter += 1
            used_names.add(candidate)
            dest = staging / candidate

        dest.parent.mkdir(parents=True, exist_ok=True)
        if not dest.exists():
            shutil.copy2(resolved, dest)
        placed[resolved] = dest
        return dest

    # First, copy and place the entry HTML itself.
    entry_dest = staging / entry_resolved.name
    shutil.copy2(entry_resolved, entry_dest)
    placed[entry_resolved] = entry_dest
    used_names.add(entry_resolved.name)

    # Place all other scanned HTML files.
    for html_path in all_refs:
        if html_path != entry_resolved:
            _place_file(html_path)

    # Place all referenced files.
    for refs in all_refs.values():
        for _raw, resolved in refs:
            _place_file(resolved)

    # Rewrite paths in staged HTML files.
    for html_resolved, refs in all_refs.items():
        staged_html = placed[html_resolved]
        if not staged_html.exists():
            continue
        text = staged_html.read_text(errors="replace")
        for raw, resolved in refs:
            staged_target = placed.get(resolved)
            if staged_target is None:
                continue
            # Compute the new relative path from the staged HTML to the staged target.
            try:
                new_rel = os.path.relpath(staged_target, staged_html.parent)
            except ValueError:
                continue
            # Normalize to forward slashes.
            new_rel = new_rel.replace("\\", "/")
            text = text.replace(raw, new_rel)
        staged_html.write_text(text)

    return staging


def create_bundle_dir(html_path: str | Path) -> Path:
    """Scan an HTML file, bundle dependencies, and return the staging directory.

    The caller is responsible for cleaning up via :func:`cleanup_bundle_dir`.
    """
    html_path = Path(html_path).resolve()
    all_refs = _collect_all_refs(html_path)
    return _build_staging_dir(html_path, all_refs)


def cleanup_bundle_dir(staging_dir: Path) -> None:
    """Remove a staging directory created by :func:`create_bundle_dir`."""
    shutil.rmtree(staging_dir, ignore_errors=True)


def create_bundle(html_path: str | Path) -> Path:
    """Scan an HTML file, bundle dependencies, and return the path to a temp zip."""
    staging = create_bundle_dir(html_path)

    tmp = tempfile.NamedTemporaryFile(prefix="tinygo_bundle_", suffix=".zip", delete=False)
    tmp.close()
    zip_path = Path(tmp.name)
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, _dirs, files in os.walk(staging):
            for fname in files:
                full = Path(root) / fname
                arcname = full.relative_to(staging)
                zf.write(full, arcname)

    cleanup_bundle_dir(staging)
    return zip_path


def cleanup_bundle(zip_path: Path) -> None:
    """Delete the temporary bundle zip."""
    try:
        zip_path.unlink(missing_ok=True)
    except OSError:
        pass
