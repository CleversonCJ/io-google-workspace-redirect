import asyncio
import json

import pytest
from fastapi import HTTPException
from nc_py_api.files import ActionFileInfo, ActionFileInfoEx

from main import FILE_ACTION_NAME, SUPPORTED_MIMES, TOP_MENU_NAME, enabled_handler, open_in_google

DOC_ID = "1PZe8Zv6480F-X3wVa-DWoZ-K-0yz2SE0CMnvKMAQ0Hg"


def selected_file(name="Pitch.gslides", size=120):
    return ActionFileInfo(
        fileId=123,
        name=name,
        directory="/Clientes",
        etag='"etag"',
        mime="application/octet-stream",
        fileType="file",
        mtime=1_700_000_000,
        size=size,
        favorite="false",
        permissions=1,
        userId="test-user",
        instanceId="abc123",
    )


class FakeFiles:
    def __init__(self, content):
        self.content = content
        self.downloaded = None

    async def download(self, node):
        self.downloaded = node
        return self.content


class FakeNc:
    def __init__(self, content):
        self.files = FakeFiles(content)


def test_action_reads_file_as_clicking_user_and_returns_redirect_route():
    nc = FakeNc(json.dumps({"doc_id": DOC_ID}).encode())

    response = asyncio.run(open_in_google(ActionFileInfoEx(files=[selected_file()]), nc))

    assert response.status_code == 200
    assert json.loads(response.body)["redirect_handler"].startswith("workspace/open/")
    assert nc.files.downloaded.user == "test-user"
    assert nc.files.downloaded.user_path == "Clientes/Pitch.gslides"


def test_action_rejects_multiple_files():
    nc = FakeNc(b"{}")
    with pytest.raises(HTTPException) as error:
        asyncio.run(open_in_google(ActionFileInfoEx(files=[selected_file(), selected_file("Other.gslides")]), nc))
    assert error.value.status_code == 400


class Calls:
    def __init__(self):
        self.values = []

    async def register(self, *args, **kwargs):
        self.values.append(("register", args, kwargs))

    async def register_ex(self, *args, **kwargs):
        self.values.append(("register_ex", args, kwargs))

    async def set_script(self, *args, **kwargs):
        self.values.append(("set_script", args, kwargs))


class FakeUi:
    def __init__(self):
        self.top_menu = Calls()
        self.resources = Calls()
        self.files_dropdown_menu = Calls()


class FakeEnableNc:
    def __init__(self):
        self.ui = FakeUi()


def test_enable_registers_appapi_33_file_action_and_handoff_page():
    nc = FakeEnableNc()

    assert asyncio.run(enabled_handler(True, nc)) == ""

    assert nc.ui.top_menu.values[0][1][0] == TOP_MENU_NAME
    assert nc.ui.resources.values[0][1] == ("top_menu", TOP_MENU_NAME, "js/redirect")
    action = nc.ui.files_dropdown_menu.values[0]
    assert action[0] == "register_ex"
    assert action[1][0] == FILE_ACTION_NAME
    assert action[2]["mime"] == SUPPORTED_MIMES
    assert action[2]["permissions"] == 1
