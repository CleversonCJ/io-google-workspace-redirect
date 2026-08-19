"""Validation and URL construction for Google Workspace pointer files."""

from __future__ import annotations

import base64
import json
import re
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlencode

MAX_POINTER_SIZE = 64 * 1024
DOC_ID_RE = re.compile(r"[A-Za-z0-9_-]{10,256}")
RESOURCE_KEY_RE = re.compile(r"[A-Za-z0-9_-]{1,512}")

GOOGLE_PATHS = {
    ".gdoc": "document",
    ".gsheet": "spreadsheets",
    ".gslides": "presentation",
}


class WorkspaceRedirectError(ValueError):
    """A pointer file is malformed or unsupported."""


@dataclass(frozen=True)
class WorkspacePointer:
    """Validated target stored by a Google Workspace pointer file."""

    extension: str
    doc_id: str
    resource_key: str | None

    @property
    def url(self) -> str:
        product_path = GOOGLE_PATHS[self.extension]
        result = f"https://docs.google.com/{product_path}/d/{self.doc_id}/edit"
        if self.resource_key:
            result += "?" + urlencode({"resourcekey": self.resource_key})
        return result


def parse_pointer(filename: str, payload: bytes) -> WorkspacePointer:
    """Parse and validate a .gdoc, .gsheet, or .gslides JSON file."""
    extension = Path(filename).suffix.lower()
    if extension not in GOOGLE_PATHS:
        raise WorkspaceRedirectError("Este tipo de arquivo não é compatível com o Google Workspace Redirect.")

    if len(payload) > MAX_POINTER_SIZE:
        raise WorkspaceRedirectError("O arquivo de atalho é maior que o limite permitido.")

    try:
        raw = json.loads(payload.decode("utf-8-sig"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise WorkspaceRedirectError("O arquivo não contém um JSON válido.") from exc

    if not isinstance(raw, dict):
        raise WorkspaceRedirectError("O conteúdo do arquivo deve ser um objeto JSON.")

    doc_id = raw.get("doc_id")
    if not isinstance(doc_id, str) or not DOC_ID_RE.fullmatch(doc_id.strip()):
        raise WorkspaceRedirectError("O arquivo não contém um doc_id válido.")

    resource_key = raw.get("resource_key")
    if resource_key is None or resource_key == "":
        resource_key = None
    elif not isinstance(resource_key, str) or not RESOURCE_KEY_RE.fullmatch(resource_key.strip()):
        raise WorkspaceRedirectError("O arquivo contém um resource_key inválido.")
    else:
        resource_key = resource_key.strip()

    return WorkspacePointer(extension=extension, doc_id=doc_id.strip(), resource_key=resource_key)


def encode_redirect_target(target_url: str) -> str:
    """Encode a validated Google URL into a URL-safe, stateless handoff route."""
    token = base64.urlsafe_b64encode(target_url.encode("ascii")).decode("ascii").rstrip("=")
    return f"workspace/open/{token}"

