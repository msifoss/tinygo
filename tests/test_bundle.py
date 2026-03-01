"""Tests for tinygo.bundle module."""

import zipfile

import pytest

from tinygo.bundle import cleanup_bundle, create_bundle, scan_html


@pytest.fixture()
def project_dir(tmp_path):
    """Create a mini project with HTML and linked files."""
    # Main HTML
    css_dir = tmp_path / "css"
    css_dir.mkdir()
    (css_dir / "style.css").write_text("body { color: red; }")

    (tmp_path / "script.js").write_text("console.log('hi');")

    (tmp_path / "index.html").write_text(
        '<html><head>'
        '<link rel="stylesheet" href="css/style.css">'
        '<script src="script.js"></script>'
        '</head><body>Hello</body></html>'
    )
    return tmp_path


def test_scan_html_finds_refs(project_dir):
    refs = scan_html(project_dir / "index.html")
    raw_refs = [r for r, _p in refs]
    assert "css/style.css" in raw_refs
    assert "script.js" in raw_refs


def test_scan_html_skips_remote_urls(tmp_path):
    (tmp_path / "test.html").write_text(
        '<html><head>'
        '<link rel="stylesheet" href="https://cdn.example.com/style.css">'
        '<script src="http://example.com/app.js"></script>'
        '<a href="mailto:a@b.com">email</a>'
        '<a href="#section">anchor</a>'
        '<a href="javascript:void(0)">js</a>'
        '<a href="data:text/html,hello">data</a>'
        '</head></html>'
    )
    refs = scan_html(tmp_path / "test.html")
    assert refs == []


def test_scan_html_skips_missing_files(tmp_path):
    (tmp_path / "test.html").write_text(
        '<html><script src="nonexistent.js"></script></html>'
    )
    refs = scan_html(tmp_path / "test.html")
    assert refs == []


def test_scan_html_finds_css_url(tmp_path):
    (tmp_path / "bg.png").write_text("fake png")
    (tmp_path / "test.html").write_text(
        '<html><style>body { background: url("bg.png"); }</style></html>'
    )
    refs = scan_html(tmp_path / "test.html")
    raw_refs = [r for r, _p in refs]
    assert "bg.png" in raw_refs


def test_create_bundle_produces_zip(project_dir):
    zip_path = create_bundle(project_dir / "index.html")
    try:
        assert zip_path.exists()
        assert zip_path.suffix == ".zip"
        with zipfile.ZipFile(zip_path) as zf:
            names = zf.namelist()
            assert "index.html" in names
            assert "css/style.css" in names
            assert "script.js" in names
    finally:
        cleanup_bundle(zip_path)


def test_create_bundle_rewrites_paths(project_dir):
    zip_path = create_bundle(project_dir / "index.html")
    try:
        with zipfile.ZipFile(zip_path) as zf:
            html = zf.read("index.html").decode()
            # Paths should still be relative (css/style.css, script.js)
            assert "css/style.css" in html
            assert "script.js" in html
    finally:
        cleanup_bundle(zip_path)


def test_create_bundle_with_absolute_path(tmp_path):
    """Files from outside the project dir get flattened into the zip root."""
    project = tmp_path / "project"
    project.mkdir()
    external = tmp_path / "external"
    external.mkdir()

    (external / "report.html").write_text("<html>Report</html>")
    abs_path = str((external / "report.html").resolve())

    (project / "index.html").write_text(
        f'<html><a href="{abs_path}">Report</a></html>'
    )

    zip_path = create_bundle(project / "index.html")
    try:
        with zipfile.ZipFile(zip_path) as zf:
            names = zf.namelist()
            assert "index.html" in names
            assert "report.html" in names
            # Path in HTML should be rewritten to relative
            html = zf.read("index.html").decode()
            assert abs_path not in html
            assert "report.html" in html
    finally:
        cleanup_bundle(zip_path)


def test_create_bundle_recursive_html(tmp_path):
    """Linked HTML files are scanned recursively."""
    (tmp_path / "style.css").write_text("body {}")

    (tmp_path / "page2.html").write_text(
        '<html><link rel="stylesheet" href="style.css"></html>'
    )
    (tmp_path / "index.html").write_text(
        '<html><a href="page2.html">Page 2</a></html>'
    )

    zip_path = create_bundle(tmp_path / "index.html")
    try:
        with zipfile.ZipFile(zip_path) as zf:
            names = zf.namelist()
            assert "index.html" in names
            assert "page2.html" in names
            assert "style.css" in names
    finally:
        cleanup_bundle(zip_path)


def test_cleanup_bundle_removes_zip(tmp_path):
    zip_file = tmp_path / "test.zip"
    zip_file.write_text("fake")
    assert zip_file.exists()
    cleanup_bundle(zip_file)
    assert not zip_file.exists()


def test_cleanup_bundle_handles_missing_file(tmp_path):
    """cleanup_bundle should not raise if the file doesn't exist."""
    cleanup_bundle(tmp_path / "nonexistent.zip")
