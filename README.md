# BattareyCloud — Backend

## Features
- Asynchronous API on FastAPI (Python 3.11+)
- File storage in MinIO (S3-compatible cloud)
- PostgreSQL (or SQLite for tests)
- Background task processing via Celery + Redis (antivirus, trash cleaning)
- Antivirus file scanning (ClamAV)
- AES file encryption
- JWT authentication, sessions, individual settings
- Centralized logging and action audit
- Request rate limiting
- Docker and docker-compose support for a quick start
- Integration, unit and load tests (pytest, locust)

## For whom
BattareyCloud is a ready-made backend for cloud storage, corporate file services, SaaS solutions and integrations. Suitable for startups, businesses, integrators.

## Architecture and structure description

### General architecture

The backend is implemented on FastAPI (Python) with asynchronous interaction with PostgreSQL via SQLAlchemy. MinIO (S3-compatible storage) is used to store files. Background tasks (file scanning, trash cleaning) are performed via Celery with a Redis broker. Anti-virus scanning (ClamAV) and file encryption (AES) are implemented. All business logic is divided into layers: routes, repositories, models, schemes, utilities.

### Main components and structure
- **app/** — main application code (FastAPI, business logic, models, schemes, repositories, routes, utilities)
- **tasks/** — Celery background tasks (file scanning, recycle bin cleaning, etc.)
- **alembic/** — database migrations (Alembic)
- **tests/** — automated tests (integration, unit, load)
- **.env** — environment variables (DB, MinIO, Redis, ClamAV, etc.)
- **Dockerfile, docker-compose.yml** — containerization and orchestration
- **requirements.txt** — Python dependencies

### Technologies used
- **FastAPI** — asynchronous web framework
- **SQLAlchemy (asyncio)** — ORM for PostgreSQL/SQLite
- **PostgreSQL** — main DBMS (SQLite is supported in tests)
- **MinIO** — object storage (S3)
- **Celery + Redis** — background tasks and message broker
- **Pydantic** — validation and settings management
- **Pytest** — testing (async, httpx)
- **ClamAV (pyclamd)** — antivirus file scanning
- **Cryptography** — file encryption (AES)
- **Passlib[bcrypt]** — password hashing
- **python-jose** — working with JWT
- **Alembic** — DB migrations
- **Locust** — load testing
- **fastapi-limiter** — rate limiting, Redis

### Organization principles
- Clear separation of layers: routes, business logic (repositories), data access, models, schemes
- Asynchrony for high performance
- Security: password hashing, file encryption, antivirus scanning, data validation, session and token management
- Scalability: modular structure for easy extension
- Testability: autotests for all major API functions
- DB migrations: via Alembic
- Rate limiting for sensitive endpoints (login, password reset) implemented using fastapi-limiter and Redis. When the limit is exceeded, 429 Too Many Requests is returned.

---

## Cross-DBMS features
- All UUID fields use the GUID type (see app/db/types.py), which works with both PostgreSQL and SQLite.
- JSON data is stored in the JSON type (cross-DBMS).
- This allows you to run tests on SQLite without type errors, and use PostgreSQL in production without changing the models.

---

## Testing on SQLite and PostgreSQL
- To speed up and isolate tests, you can run them on SQLite without changing the code of models and tests.
- For this, the following variables have been added to .env:
- `TEST_USE_SQLITE=1` — enables testing on SQLite
- `TEST_DATABASE_URL=sqlite+aiosqlite:///./test.db` — path to the test database
- For PostgreSQL tests, comment out these lines.
- All types (GUID, JSON) work the same with both DBMS.

- For integration tests, it is recommended to use unique username/email (e.g. via uuid4) to avoid conflicts when re-registering users.
- To speed up CI and prevent false positives of rate limiting, use the environment variable `TESTING=1` (it automatically disables registration and login limits in the test environment).

---

## Quick Start (Docker)

1. Clone the repository and go to the BackEnd folder
2. Copy `.env.example` to `.env` and specify your values ​​(secrets, passwords, domains)
3. Start services:
```powershell
docker-compose up -d --build
```
4. Apply DB migrations:
```powershell
docker-compose exec backend alembic upgrade head
```
5. Start Celery worker and beat (for background tasks):
```powershell
docker-compose up -d celery_worker celery_beat
```
6. To view logs:
```powershell
docker-compose logs -f backend
```

---

# Deployment to VPS or cloud

## Requirements
- VPS/cloud with Ubuntu 22.04+ (or compatible OS)
- Docker and Docker Compose
- Domain name (for HTTPS)
- Open ports: 80, 443, 9000 (MinIO), 5432 (PostgreSQL, optional), 6379 (Redis, optional)

## Deployment steps
1. Install Docker and Docker Compose
2. Clone the repository
3. Configure .env (secrets, passwords, domains)
4. Start services via docker-compose
5. Apply DB migrations
6. Check logs
7. (Recommended) Configure nginx + HTTPS (certbot)
8. (Optional) Configure data backup and DB

## Example nginx config
```nginx
server { 
listen 80; 
server_name your-domain.com; 
location/{ 
proxy_pass http://127.0.0.1:8000; 
proxy_set_header Host $host; 
proxy_set_header X-Real-IP $remote_addr; 
proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for; 
proxy_set_header X-Forwarded-Proto $scheme; 
}
}
```

## Security tips
- Use complex passwords and secrets
- Only expose necessary ports
- Regularly update Docker images and dependencies
- Set up a firewall (ufw)
- Keep backups of .env and data

---

# Description of the app folder structure

The `app` folder contains the main source code of the BattareyCloud FastAPI application.
- **main.py** — entry point, FastAPI initialization, router connection, middleware (CORS) configuration, startup events (e.g. MinIO check)
- **config.py** — application configuration. Loading settings (DB URL, Redis, MinIO, secrets) from environment variables via Pydantic `BaseSettings`
- **core/** — core components: security (passwords, JWT), file encryption (cryptography)
- **db/** — database connection, SQLAlchemy sessions, GUID/JSON types
- **models/** — ORM models (User, File, Folder, FileEncryption, etc.)
- **repositories/** — data access layer (CRUD and complex selections)
- **routes/** — HTTP request handlers (API endpoints, grouped by entities)
- **schemas/** — Pydantic schemas for request and response validation
- **utils/** — auxiliary functions (working with MinIO, file previews, etc.)

---

# Description of the folder structure tasks

The `tasks` folder contains Celery background tasks.
- **scan.py** — antivirus scanning of files after downloading (ClamAV)
- **cleanup.py** — automatic deletion of files from the recycle bin (after 24 hours)
- All tasks use the Celery application configured via app.config (REDIS_URL)
- MinIO is used to work with files, and asynchronous SQLAlchemy sessions are used to work with the database
- Tasks can be periodic (Celery Beat) or launched by an event

Example of running worker:
```bash
celery -A tasks.scan.celery_app worker --loglevel=info
```

---

# Description of the alembic folder structure

The `alembic` folder contains scripts and configuration for database migrations.
- Alembic is used to manage the PostgreSQL database schema
- All changes to the database structure are processed as migrations
- The database connection configuration is taken from the environment variables (see `.env`)
- To apply migrations, use:
```bash
alembic upgrade head
```
or via Docker Compose:
```bash
docker-compose exec backend alembic upgrade head
```

---

# Description of the tests folder structure

The `tests` folder contains autotests for checking the API and backend business logic.
- **integration_tests/** — API integration tests (registration, login, files, folders, cart, etc.)
- **unit_tests/** — unit tests (as needed)
- **load_tests/** — load tests using Locust

---

# Description of business logic

- **Registration and authentication:** The user registers with email and password. The password is hashed with bcrypt. JWT is used to access the API.
- **File upload:** Files are encrypted (AES), saved in MinIO. After uploading, the ClamAV background scanning task is launched.
- **File deletion:** The file is marked as deleted (is_deleted=True), physically deleted from MinIO after 24 hours (background cleanup task).
- **Recycle bin:** Recovery is possible before physical deletion. The recycle bin displays only files marked for deletion.
- **Folders:** Nested folders, moving, renaming, recursive deletion are supported.
- **Statistics:** The user has access to the number of files, total volume, top 10 by size.
- **Sessions:** Storing and managing user sessions (user_sessions)
- **Logs:** Logging user activities (user_activity_logs)
- **Settings:** Individual user settings (user_settings)
- **Search and preview:** Search files by name/type, generate previews for popular formats

---

## Centralized logging

The project implements centralized logging of all HTTP requests and errors via the FastAPI middleware (`app/middleware/logging_middleware.py`).

- The method, path, status code, request processing time, and errors are logged.
- Private data (passwords, tokens) are automatically filtered and do not get into the logs.
- By default, logs are output to the console (stdout). To output to a file, configure logging in `app/main.py`:
```python
logging.basicConfig(filename='app.log', level=logging.INFO, format='%(asctime)s %(levelname)s %(name)s %(message)s')
```
- For integration with external monitoring systems (Sentry, ELK, etc.), use the corresponding logging handlers.

For more information, see `app/middleware/logging_middleware.py` and the connection in `app/main.py`.

---

# Typical usage scenarios

1. A new user registers, uploads files, receives a download link
2. The user deletes a file — it is moved to the trash, physically deleted after 24 hours
3. The user restores the file from the trash before 24 hours have passed
4. The user receives statistics on their files and the top 10 largest files
5. The user creates nested folders, moves files between them
6. After uploading a file, an antivirus scan is automatically launched

---

# Examples of API requests

## User registration
```http
POST /users/
Content-Type: application/json
{
"username": "user1",
"email": "user1@example.com",
"password": "StrongPassword123"
}
```

## Login
```http
POST /users/login
Content-Type: application/x-www-form-urlencoded
username=user1&password=StrongPassword123
```

> Important: for login and password reset endpoints, there is a rate limiting (5 requests per minute from one IP).
> In the test environment (if TESTING=1), the limiting is disabled automatically.

## Uploading a file
```http
POST /files/upload
Authorization: Bearer <JWT>
Content-Type: multipart/form-data
file: <binary>
folder_id: <uuid>
```

## Getting a list of files
```http
GET /files/?folder_id=<uuid>
Authorization: Bearer <JWT>
```

## Getting user statistics
```http
GET /files/stats
Authorization: Bearer <JWT>
```

---

# Environment variables

- **DATABASE_URL** — PostgreSQL connection string
- **MINIO_ENDPOINT, MINIO_ACCESS_KEY, MINIO_SECRET_KEY** — MinIO settings
- **REDIS_URL** — Redis broker address for Celery
- **CLAMAV_HOST, CLAMAV_PORT** — ClamAV settings
- **SECRET_KEY** — secret for JWT
- **TEST_USE_SQLITE, TEST_DATABASE_URL** — parameters for testing on SQLite
- **TESTING** — if set to 1, disables rate limiting for login and registration (used for integration tests)

---

# Installing and updating dependencies

All dependencies are listed in requirements.txt. To install:
```bash
pip install -r requirements.txt
```
For Docker — rebuild the image:
```bash
docker-compose build backend
```

Important dependencies for rate limiting:
- fastapi-limiter
- redis

---

## Testing
- Integration tests: `docker-compose run --rm backend pytest /tests/integration_tests`
- Load tests: see `tests/README.md` (Locust)
- Coverage: main API scenarios are covered by automated tests

## API documentation
Swagger/OpenAPI is available at `/docs` after backend startup.

## Long ClamAV loading
ClamAV loading takes on average 40-60 seconds due to the fact that virus databases (freshclam) are updated when the container starts.