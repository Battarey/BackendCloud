# paths
import sys
import os
import uuid
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
# app
from app.main import app
# other
from httpx import AsyncClient
import pytest

@pytest.mark.asyncio
async def test_folder_crud():
    unique = uuid.uuid4().hex[:8]
    user_data = {
        "username": f"folderuser_{unique}",
        "email": f"folderuser_{unique}@example.com",
        "password": "Test1234!"
    }

    async with app.router.lifespan_context(app):
        async with AsyncClient(app=app, base_url="http://test") as ac:
            # Create user
            resp = await ac.post("/users/", json=user_data)
            assert resp.status_code == 200, f"User create failed: {resp.text}"
            user_id = None
            token = None
            headers = {}

            login_resp = await ac.post("/users/login", data={"username": user_data["username"], "password": user_data["password"]})
            assert login_resp.status_code == 200, f"Login failed: {login_resp.text}"
            token = login_resp.json().get("access_token")
            headers = {"Authorization": f"Bearer {token}"} if token else {}
            user_id = login_resp.json().get("user_id")

            assert user_id is not None, "User ID could not be determined"
            assert token is not None, "Auth token could not be retrieved"


            # Create folder (user_id убран, только headers)
            folder_name = "Test Folder"
            create_resp = await ac.post(
                f"/folders/", 
                json={"name": folder_name}, 
                headers=headers
            )
            assert create_resp.status_code == 200, f"Create folder failed: {create_resp.text}"
            folder_id = create_resp.json()["id"]
            assert create_resp.json()["name"] == folder_name
            print(f"Created folder with ID: {folder_id}")

            # Get folder - check the receipt of the folder by id
            get_folder_resp = await ac.get(
                f"/folders/{folder_id}",
                headers=headers
            )
            assert get_folder_resp.status_code == 200, f"Get folder failed: {get_folder_resp.text}"
            assert get_folder_resp.json()["name"] == folder_name

            # Get folders (user_id убран, только headers)
            get_resp = await ac.get(
                f"/folders/", 
                headers=headers
            )
            assert get_resp.status_code == 200, f"Get folders failed: {get_resp.text}"
            assert isinstance(get_resp.json(), list)
            print("Successfully retrieved folders.")

            # Update folder - renaming
            new_folder_name = "Updated Test Folder"
            rename_resp = await ac.put(
                f"/folders/{folder_id}/rename",
                json={"new_name": new_folder_name},
                headers=headers
            )
            assert rename_resp.status_code == 200, f"Rename folder failed: {rename_resp.text}"

            # Check updated folder name
            get_updated_resp = await ac.get(
                f"/folders/{folder_id}",
                headers=headers
            )
            assert get_updated_resp.status_code == 200
            assert get_updated_resp.json()["name"] == new_folder_name

            # Delete folder
            delete_resp = await ac.delete(
                f"/folders/{folder_id}", 
                headers=headers
            )
            assert delete_resp.status_code == 200, f"Delete folder failed: {delete_resp.text}"
            print(f"Deleted folder with ID: {folder_id}")

            # Verify deletion - folder should no longer exist
            get_deleted_resp = await ac.get(
                f"/folders/{folder_id}",
                headers=headers
            )
            assert get_deleted_resp.status_code == 404, "Folder was not properly deleted"