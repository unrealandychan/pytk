import pytest
from pytk.filters.curl import CurlFilter

f = CurlFilter()


def test_matches_curl():
    assert f.matches(['curl', 'https://example.com'])

def test_matches_http():
    assert f.matches(['http', 'GET', 'https://example.com'])

def test_matches_wget():
    assert f.matches(['wget', 'https://example.com'])

def test_no_match():
    assert not f.matches(['git', 'status'])
    assert not f.matches(['ls'])
    assert not f.matches([])


def test_curl_verbose_strips_tls():
    raw = (
        "* TLSv1.3 (OUT), TLS handshake, Client hello\n"
        "* SSL connection using TLSv1.3 / AES_256_GCM_SHA384\n"
        "* Cipher selection: ALL:!EXPORT:!EXPORT40\n"
        "< HTTP/2 200\n"
        "< content-type: application/json\n"
        "<\n"
        '{"status": "ok"}'
    )
    out = f.filter(raw, ['curl', '-v', 'https://example.com'])
    assert 'HTTP/2 200' in out
    assert '"status"' in out
    assert 'TLSv1.3' not in out
    assert 'SSL connection' not in out


def test_curl_json_truncated():
    # Build a 100-line JSON array
    items = list(range(100))
    import json
    body = json.dumps(items, indent=2)
    out = f.filter(body, ['curl', 'https://example.com'])
    lines = out.splitlines()
    assert any('[...' in l for l in lines), "Expected truncation marker"
    assert len(lines) <= 52  # 50 lines + marker + maybe bracket


def test_curl_error_kept_full():
    import json
    error_body = json.dumps({"error": "not found", "detail": "x" * 500}, indent=2)
    raw = (
        "< HTTP/1.1 404 Not Found\n"
        "< content-type: application/json\n"
        "<\n"
        + error_body
    )
    out = f.filter(raw, ['curl', '-v', 'https://example.com/missing'])
    # Full error body kept (no truncation marker)
    assert '[...' not in out
    assert 'not found' in out


def test_curl_strips_progress():
    raw = (
        "  % Total    % Received % Xferd  Average Speed   Time\n"
        "100  1234  100  1234    0     0  56789      0 --:--:-- --:--:--\n"
        "Hello World"
    )
    out = f.filter(raw, ['curl', 'https://example.com'])
    assert '% Total' not in out
    assert 'Hello World' in out


def test_wget_strips_progress():
    raw = (
        "--2024-01-01 12:00:00--  https://example.com/file.zip\n"
        "Resolving example.com... 1.2.3.4\n"
        "Connecting to example.com|1.2.3.4|:443... connected.\n"
        "file.zip          100%[===================>]   1.23M  5.67MB/s    in 0.2s\n"
        "\n"
        "'file.zip' saved [1234567/1234567]\n"
    )
    out = f.filter(raw, ['wget', 'https://example.com/file.zip'])
    assert '100%' not in out
    assert 'saved' in out


def test_curl_plain_response_passthrough():
    raw = "Hello, World!\nThis is a plain text response."
    out = f.filter(raw, ['curl', 'https://example.com'])
    assert 'Hello, World!' in out
    assert 'plain text response' in out
