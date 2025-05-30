from app.schemas.folder import FolderCreate
from app.schemas.user_session import UserSessionCreate

def test_folder_create_schema():
    folder = FolderCreate(name="Test", parent_id=None)
    assert folder.name == "Test"
    assert folder.parent_id is None

def test_user_session_create_schema():
    session = UserSessionCreate(device_info={"os": "win"})
    assert session.device_info["os"] == "win"
