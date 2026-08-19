"""IO Google Workspace Redirect ExApp."""

from __future__ import annotations

import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.responses import JSONResponse
from nc_py_api import AsyncNextcloudApp
from nc_py_api.ex_app import AppAPIAuthMiddleware, anc_app, run_app, set_handlers
from nc_py_api.files import ActionFileInfoEx

from workspace_redirect import MAX_POINTER_SIZE, WorkspaceRedirectError, encode_redirect_target, parse_pointer

FILE_ACTION_NAME = "io_google_workspace_open"
TOP_MENU_NAME = "workspace"
SUPPORTED_MIMES = "application/octet-stream,application/json,text/plain"


@asynccontextmanager
async def lifespan(app: FastAPI):
    set_handlers(app, enabled_handler)
    yield


APP = FastAPI(
    title="IO Google Workspace Redirect",
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
    lifespan=lifespan,
)
APP.add_middleware(AppAPIAuthMiddleware)


@APP.post("/open")
async def open_in_google(
    selected: ActionFileInfoEx,
    nc: Annotated[AsyncNextcloudApp, Depends(anc_app)],
) -> JSONResponse:
    """Read one selected pointer file and return an AppAPI UI redirect route."""
    if len(selected.files) != 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Selecione apenas um arquivo do Google Workspace por vez.",
        )

    selected_file = selected.files[0]
    if selected_file.fileType.lower() != "file":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="A ação só pode ser usada em arquivos.")
    if selected_file.size > MAX_POINTER_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="O arquivo de atalho é maior que o limite permitido.",
        )

    try:
        payload = await nc.files.download(selected_file.to_fs_node())
        pointer = parse_pointer(selected_file.name, payload)
    except WorkspaceRedirectError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Não foi possível ler o arquivo selecionado no Nextcloud.",
        ) from exc

    return JSONResponse({"redirect_handler": encode_redirect_target(pointer.url)})


async def enabled_handler(enabled: bool, nc: AsyncNextcloudApp) -> str:
    """Register the AppAPI 33 UI integrations when the ExApp is enabled."""
    if not enabled:
        return ""

    try:
        await nc.ui.top_menu.register(
            TOP_MENU_NAME,
            "IO Google Workspace",
            icon="img/icon.svg",
        )
        await nc.ui.resources.set_script(
            "top_menu",
            TOP_MENU_NAME,
            "js/redirect",
        )
        await nc.ui.files_dropdown_menu.register_ex(
            FILE_ACTION_NAME,
            "Abrir no Google Workspace",
            "/open",
            mime=SUPPORTED_MIMES,
            permissions=1,
            order=-20,
            icon="img/icon.svg",
        )
    except Exception as exc:
        return f"Falha ao registrar a integração do Google Workspace: {exc}"
    return ""


if __name__ == "__main__":
    os.chdir(Path(__file__).parent)
    run_app("main:APP", log_level=os.getenv("LOG_LEVEL", "info").lower())

