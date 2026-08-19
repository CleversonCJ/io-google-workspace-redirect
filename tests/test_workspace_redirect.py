import base64
import json
from urllib.parse import parse_qs, urlparse

import pytest

from workspace_redirect import MAX_POINTER_SIZE, WorkspaceRedirectError, encode_redirect_target, parse_pointer

DOC_ID = "1PZe8Zv6480F-X3wVa-DWoZ-K-0yz2SE0CMnvKMAQ0Hg"


@pytest.mark.parametrize(
    ("filename", "expected_path"),
    [
        ("Briefing.gdoc", f"/document/d/{DOC_ID}/edit"),
        ("Budget.GSHEET", f"/spreadsheets/d/{DOC_ID}/edit"),
        ("Pitch.gslides", f"/presentation/d/{DOC_ID}/edit"),
    ],
)
def test_builds_google_workspace_urls(filename, expected_path):
    payload = json.dumps({"doc_id": DOC_ID, "resource_key": ""}).encode()

    result = parse_pointer(filename, payload)

    parsed = urlparse(result.url)
    assert parsed.scheme == "https"
    assert parsed.netloc == "docs.google.com"
    assert parsed.path == expected_path
    assert parsed.query == ""


def test_appends_resource_key_with_correct_query_name():
    payload = json.dumps({"doc_id": DOC_ID, "resource_key": "0-AbCd_123"}).encode()

    result = parse_pointer("Shared.gdoc", payload)

    assert parse_qs(urlparse(result.url).query) == {"resourcekey": ["0-AbCd_123"]}


def test_accepts_utf8_bom():
    payload = b"\xef\xbb\xbf" + json.dumps({"doc_id": DOC_ID}).encode()
    assert parse_pointer("Document.gdoc", payload).doc_id == DOC_ID


@pytest.mark.parametrize(
    ("filename", "payload", "message"),
    [
        ("Document.docx", b"{}", "não é compatível"),
        ("Document.gdoc", b"not-json", "JSON válido"),
        ("Document.gdoc", b"[]", "objeto JSON"),
        ("Document.gdoc", b"{}", "doc_id válido"),
        ("Document.gdoc", b'{"doc_id":"../../bad"}', "doc_id válido"),
        (
            "Document.gdoc",
            json.dumps({"doc_id": DOC_ID, "resource_key": "bad&next=https://example.com"}).encode(),
            "resource_key inválido",
        ),
    ],
)
def test_rejects_malformed_or_unsafe_pointers(filename, payload, message):
    with pytest.raises(WorkspaceRedirectError, match=message):
        parse_pointer(filename, payload)


def test_rejects_oversized_pointer():
    with pytest.raises(WorkspaceRedirectError, match="maior"):
        parse_pointer("Document.gdoc", b"x" * (MAX_POINTER_SIZE + 1))


def test_redirect_target_is_stateless_urlsafe_base64():
    target = f"https://docs.google.com/document/d/{DOC_ID}/edit?resourcekey=0-AbCd_123"

    route = encode_redirect_target(target)
    token = route.removeprefix("workspace/open/")
    padded = token + "=" * ((4 - len(token) % 4) % 4)

    assert route.startswith("workspace/open/")
    assert "/" not in token
    assert base64.urlsafe_b64decode(padded).decode("ascii") == target

