# Load testing for BatteryCloud API using Locust
from locust import HttpUser, task, between
import uuid
import random
import time

class BatteryCloudUser(HttpUser):
    wait_time = between(1, 3)
    token = None
    username = None
    password = None
    uploaded_file_ids = []
    
    folder_ids = []
    headers = {}
    folder_create_times = {}

    def on_start(self):
        self.username = f"testuser_{uuid.uuid4().hex[:8]}"
        self.password = "TestPassword123!"
        reg_data = {
            "username": self.username,
            "email": f"{self.username}@example.com",
            "password": self.password
        }
        reg_resp = self.client.post("/users/", json=reg_data)
        if reg_resp.status_code not in (200, 400):
            self.token = None
            return
        login_data = {
            "username": self.username,
            "password": self.password
        }
        login_resp = self.client.post("/users/login", data=login_data)
        if login_resp.status_code == 200 and "access_token" in login_resp.json():
            self.token = login_resp.json()["access_token"]
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            self.token = None
            return
        # Updating user settings (as in integration tests)
        settings_data = {
            "storage_limit": 1024 * 1024 * 1024,
            "theme": "system",
            "language": "en",
            "notifications_enabled": True
        }
        self.client.put("/settings/user/me", json=settings_data, headers=self.headers)

    def auth_headers(self):
        return self.headers if self.token else {}

    def get_file_id_by_name(self, filename):
        resp = self.client.get("/files/", headers=self.auth_headers())
        if resp.status_code == 200:
            files = resp.json()
            for f in files:
                if f.get("filename") == filename:
                    return f.get("id")
        return None

    @task(2)
    def get_files(self):
        if self.token:
            self.client.get("/files/", headers=self.auth_headers())

    @task(2)
    def get_folders(self):
        if self.token:
            resp = self.client.get("/folders/", headers=self.auth_headers())
            if resp.status_code == 200:
                folders = resp.json()
                self.folder_ids = [f["id"] for f in folders] if isinstance(folders, list) else []

    @task(1)
    def get_user_settings(self):
        if self.token:
            self.client.get("/settings/user/me", headers=self.auth_headers())

    @task(2)
    def upload_file(self):
        if self.token:
            filename = f"locust_{uuid.uuid4().hex[:6]}.txt"
            file_content = b"locust_test_file" + uuid.uuid4().bytes[:4]
            files = {"file": (filename, file_content, "text/plain")}
            resp = self.client.post("/files/", files=files, headers=self.auth_headers())
            if resp.status_code == 200 and "id" in resp.json():
                file_id = resp.json()["id"]
                self.uploaded_file_ids.append(file_id)
            elif resp.status_code == 409:
                file_id = self.get_file_id_by_name(filename)
                if file_id and file_id not in self.uploaded_file_ids:
                    self.uploaded_file_ids.append(file_id)

    @task(1)
    def delete_file(self):
        if self.token and self.uploaded_file_ids:
            file_id = random.choice(self.uploaded_file_ids)
            resp = self.client.delete(f"/files/{file_id}", headers=self.auth_headers())
            if resp.status_code in (404, 410, 500):
                if file_id in self.uploaded_file_ids:
                    self.uploaded_file_ids.remove(file_id)

    @task(1)
    def restore_file(self):
        if self.token and self.uploaded_file_ids:
            file_id = random.choice(self.uploaded_file_ids)
            resp = self.client.post(f"/files/restore/{file_id}", headers=self.auth_headers())
            if resp.status_code in (404, 409, 400, 413, 500):
                if file_id in self.uploaded_file_ids:
                    self.uploaded_file_ids.remove(file_id)

    @task(1)
    def create_folder(self):
        if self.token:
            folder_name = f"locust_folder_{uuid.uuid4().hex[:6]}"
            resp = self.client.post("/folders/", json={"name": folder_name}, headers=self.auth_headers())
            if resp.status_code == 200 and "id" in resp.json():
                folder_id = resp.json()["id"]
                file_content = b"locust_folder_file" + uuid.uuid4().bytes[:4]
                files = {"file": (f"locust_{uuid.uuid4().hex[:6]}.txt", file_content, "text/plain")}
                file_resp = self.client.post(f"/files/?folder_id={folder_id}", files=files, headers=self.auth_headers())
                if file_resp.status_code == 200:
                    # Проверяем, что папка реально существует (получаем список файлов)
                    check_resp = self.client.get(f"/folders/{folder_id}/files", headers=self.auth_headers())
                    if check_resp.status_code == 200:
                        self.folder_ids.append(folder_id)
                        self.folder_create_times[folder_id] = time.time()

    @task(1)
    def list_files_in_folder(self):
        if self.token and self.folder_ids:
            now = time.time()
            # We leave only folders created no more than 30 seconds ago
            valid_folders = [fid for fid in self.folder_ids if now - self.folder_create_times.get(fid, 0) < 30]
            if not valid_folders:
                return
            folder_id = random.choice(valid_folders)
            resp = self.client.get(f"/folders/{folder_id}/files", headers=self.auth_headers())
            if resp.status_code == 404:
                # The folder does not actually exist, delete it from all lists
                if folder_id in self.folder_ids:
                    self.folder_ids.remove(folder_id)
                if folder_id in self.folder_create_times:
                    del self.folder_create_times[folder_id]
            elif resp.status_code == 200:
                # The folder is confirmed as existing, do nothing
                pass


    @task(1)
    def search_files(self):
        if self.token:
            if random.random() < 0.5:
                filename = random.choice(["locust", "test", "file", "folder"]) + uuid.uuid4().hex[:2]
                resp = self.client.get(f"/files/search/?filename={filename}", headers=self.auth_headers())
            else:
                content_type = random.choice(["text/plain", "application/pdf", "image/png"])
                resp = self.client.get(f"/files/search/?content_type={content_type}", headers=self.auth_headers())

    @task(1)
    def get_user_activity_logs(self):
        if self.token:
            file_content = b"log_action_file" + uuid.uuid4().bytes[:4]
            files = {"file": (f"log_{uuid.uuid4().hex[:6]}.txt", file_content, "text/plain")}
            self.client.post("/files/", files=files, headers=self.auth_headers())
            resp = self.client.get("/activity_logs/user/me", headers=self.auth_headers())